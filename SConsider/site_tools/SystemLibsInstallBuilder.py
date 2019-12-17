"""SConsider.site_tools.SystemLibsInstallBuilder.

Tool to collect system libraries needed by an executable/shared library
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import os
import threading
from logging import getLogger
from SCons.Errors import UserError
from SCons.Node.Alias import default_ans
from SConsider.LibFinder import FinderFactory
from SCons.Tool import install as inst_tool, VersionShLibLinkNames
logger = getLogger(__name__)

# needs locking because it is manipulated during multi-threaded build phase
systemLibTargets = {}
systemLibTargetsRLock = threading.RLock()
aliasPrefix = '__SystemLibs_'


def versionedLibVersion(dest, source, env):
    # handle interface change for scons >=2.3.6
    try:
        return inst_tool.versionedLibVersion(dest, source, env)
    except TypeError:
        return inst_tool.versionedLibVersion(dest.path, env)


def notInDir(env, directory, path):
    return not env.File(path).is_under(directory)


def get_library_install_dir(env, sourcenode):
    if not hasattr(env, 'getLibraryInstallDir'):
        raise UserError('environment on node [%s] is not a SConsider environment, can not continue' %
                        (str(sourcenode)))
    return env.getLibraryInstallDir()


def get_libdirs(env, ownlibDir, finder):
    libdirs = [ownlibDir]
    libdirs.extend([j for j in env.get('LIBPATH', []) if j is not ownlibDir])
    libdirs.extend(finder.getSystemLibDirs(env))
    return libdirs


def get_dependent_libs(env, sourcenode, library_install_dir, libdirs_func=get_libdirs):
    finder = FinderFactory.getForPlatform(env["PLATFORM"])
    libdirs = libdirs_func(env, library_install_dir, finder)
    return finder.getLibs(env, [sourcenode], libdirs=libdirs)


def real_lib_path(env, target):
    node = target
    while node.islink():
        if node.sources:
            node = node.sources[0]
        else:
            node = env.File(os.path.realpath(node.get_abspath()))
    return node


def installSystemLibs(source):
    """This function is called during the build phase and adds targets
    dynamically to the dependency tree."""
    from SConsider.PackageRegistry import PackageRegistry
    sourcenode = PackageRegistry().getRealTarget(source)
    if not sourcenode:
        return None
    source = [sourcenode]

    env = sourcenode.get_env()
    ownlibDir = get_library_install_dir(env, sourcenode)
    deplibs = get_dependent_libs(env, sourcenode, ownlibDir)

    # don't create cycles by copying our own libs
    # but don't mask system libs
    deplibs = [env.File(j) for j in deplibs if notInDir(env, ownlibDir, j)]
    source_syslibs = []

    def install_node_to_destdir(targets_list, node, install_path, fn=env.Install):
        from stat import S_IRUSR, S_IRGRP, S_IROTH, S_IXUSR
        from SCons.Defaults import Chmod
        # ensure executable flag on installed shared libs
        mode = S_IRUSR | S_IRGRP | S_IROTH | S_IXUSR
        target = fn(dir=install_path, source=node)
        env.AddPostAction(target, Chmod(str(target[0]), mode))
        targets_list[node.name] = target
        return target

    global systemLibTargets, systemLibTargetsRLock

    # build phase could be multi-threaded
    with systemLibTargetsRLock:
        install_dir = env.makeInstallablePathFromDir(ownlibDir)
        for libnode in deplibs:
            real_libnode = real_lib_path(env, libnode)
            node_name = real_libnode.name
            target = []
            if node_name in systemLibTargets:
                target = systemLibTargets[node_name]
            else:
                # figure out if we deal with a versioned shared library
                # otherwise we need to fall back to Install builder and Symlink
                version, libname, _ = versionedLibVersion(real_libnode, source, env)
                linknames = []
                if version:
                    target = install_node_to_destdir(systemLibTargets,
                                                     real_libnode,
                                                     install_dir,
                                                     fn=env.InstallVersionedLib)
                    linknames = VersionShLibLinkNames(version, libname, env)
                else:
                    target = install_node_to_destdir(systemLibTargets, real_libnode, install_dir)
                    if not node_name == libnode.name:
                        fulllinkname = os.path.join(install_dir, libnode.name)
                        ln_target = env.Symlink(fulllinkname, target[0])
                        target.extend(ln_target)
                for linkname in linknames:
                    systemLibTargets[linkname] = target
            if target and not target[0] in source_syslibs:
                source_syslibs.extend(target)

    # add targets as dependency of the intermediate target
    env.Depends(aliasPrefix + sourcenode.name, source_syslibs)


def generate(env, *args, **kw):
    from SCons.Action import ActionFactory
    """Add the options, builders and wrappers to the current Environment."""
    createDeferredAction = ActionFactory(installSystemLibs, lambda *args, **kw: '')

    def createDeferredTarget(env, source):
        # bind 'source' parameter to an Action which is called in the build phase and
        # create a dummy target which always will be built
        from SConsider.PackageRegistry import PackageRegistry
        sourcenode = PackageRegistry().getRealTarget(source)
        if not sourcenode:
            return []
        source = [sourcenode]
        if not env.GetOption('help'):
            # install syslibs once per target
            if default_ans.lookup(aliasPrefix + sourcenode.name):
                return []
            target = env.Command(sourcenode.name + '_syslibs_dummy', sourcenode, createDeferredAction(source))
            if env.GetOption('clean'):
                """It makes no sense to find nodes to delete when target
                doesn't exist..."""
                if not sourcenode.exists():
                    return []

                env = sourcenode.get_env()
                ownlibDir = get_library_install_dir(env, sourcenode)
                deplibs = get_dependent_libs(env, sourcenode, ownlibDir, lambda e, l, f: [ownlibDir])
                global systemLibTargets, systemLibTargetsRLock
                # build phase could be multi-threaded
                with systemLibTargetsRLock:
                    for libpath in deplibs:
                        libfile = env.arg2nodes(libpath)[0]
                        real_libnode = real_lib_path(env, libfile)
                        node_name_short = real_libnode.name
                        if node_name_short not in systemLibTargets:
                            if real_libnode.is_under(ownlibDir):
                                version, libname, _ = versionedLibVersion(real_libnode, source, env)
                                linknames = []
                                if version:
                                    linknames = VersionShLibLinkNames(version, libname, env)
                                else:
                                    libname = os.path.basename(libpath)
                                    if not libname == real_libnode.name:
                                        linknames.append(libname)
                                systemLibTargets[node_name_short] = real_libnode
                                if real_libnode.isfile() or real_libnode.islink():
                                    env.Clean(sourcenode, real_libnode)
                                for linkname in linknames:
                                    fulllinkname = ownlibDir.File(linkname)
                                    systemLibTargets[fulllinkname.name] = fulllinkname
                                    env.Clean(sourcenode, fulllinkname)
                            else:
                                logger.debug('library [%s] is not in ownlibdir', str(real_libnode))

            # create intermediate target to which we add dependency in the
            # build phase
            return env.Alias(aliasPrefix + sourcenode.name, target)
        return []

    env.AddMethod(createDeferredTarget, "InstallSystemLibs")


def exists(env):
    return True
