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
logger = getLogger(__name__)

# needs locking because it is manipulated during multi-threaded build phase
systemLibTargets = {}
systemLibTargetsRLock = threading.RLock()
aliasPrefix = '__SystemLibs_'


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


def get_dependent_libs(env, sourcenode, libdirs_func=get_libdirs):
    ownlibDir = get_library_install_dir(env, sourcenode)
    finder = FinderFactory.getForPlatform(env["PLATFORM"])
    libdirs = libdirs_func(env, ownlibDir, finder)
    return finder.getLibs(env, [sourcenode], libdirs=libdirs)


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
    deplibs = get_dependent_libs(env, sourcenode)

    # don't create cycles by copying our own libs
    # but don't mask system libs
    deplibs = [env.File(j) for j in deplibs if notInDir(env, ownlibDir, j)]
    source_syslibs = []

    global systemLibTargets, systemLibTargetsRLock

    def install_node_to_destdir(targets_list, node, destdir):
        from stat import S_IRUSR, S_IRGRP, S_IROTH, S_IXUSR
        from SCons.Defaults import Chmod
        # ensure executable flag on installed shared libs
        mode = S_IRUSR | S_IRGRP | S_IROTH | S_IXUSR
        node_name = node.name
        if node_name in targets_list:
            return targets_list[node_name]
        install_path = env.makeInstallablePathFromDir(destdir)
        # make sure we do not install over an own node
        if env.Dir(install_path).File(node.name).has_builder():
            return None
        target = env.Install(dir=install_path, source=node)
        env.AddPostAction(target, Chmod(str(target[0]), mode))
        targets_list[node_name] = target
        return target

    # build phase could be multi-threaded
    with systemLibTargetsRLock:
        for node in deplibs:
            target = []
            node_name = node.name
            if node_name in systemLibTargets:
                target = systemLibTargets[node_name]
            else:
                install_node = node
                is_link = node.islink()
                if is_link:
                    if node.sources:
                        install_node = node.sources[0]
                    else:
                        install_node = env.File(os.path.realpath(node.get_abspath()))
                if not install_node.is_under(ownlibDir):
                    target = install_node_to_destdir(systemLibTargets, install_node, ownlibDir)
                    # do not create another node with the same name in this case
                    # /usr/lib/gcc/x86_64-linux-gnu/9/32/libgcc_s.so.1 -> ../../../../../lib32/libgcc_s.so.1
                    if target and is_link and not node_name == install_node.name:
                        target = env.Symlink(target[0].get_dir().File(node_name), target)
                        systemLibTargets[node_name] = target
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
                deplibs = get_dependent_libs(env, sourcenode, lambda e, l, f: [ownlibDir])
                global systemLibTargets, systemLibTargetsRLock
                # build phase could be multi-threaded
                with systemLibTargetsRLock:
                    # dummy env to resolv installed lib locations
                    for node_name in deplibs:
                        node_name_short = os.path.basename(node_name)
                        libfile = env.arg2nodes(node_name)[0]
                        if node_name_short not in systemLibTargets and libfile.is_under(
                                ownlibDir) and not libfile.has_builder():
                            systemLibTargets[node_name_short] = libfile
                            if libfile.isfile() or libfile.islink():
                                env.Clean(sourcenode, libfile)
                                if libfile.islink():
                                    path_to_real_lib = os.readlink(libfile.abspath)
                                    real_lib_name = os.path.basename(path_to_real_lib)
                                    if real_lib_name not in systemLibTargets:
                                        real_lib_node = libfile.get_dir().File(real_lib_name)
                                        if real_lib_node.exists():
                                            systemLibTargets[real_lib_name] = real_lib_node
                                            env.Clean(sourcenode, real_lib_node)
            # create intermediate target to which we add dependency in the
            # build phase
            return env.Alias(aliasPrefix + sourcenode.name, target)
        return []

    env.AddMethod(createDeferredTarget, "InstallSystemLibs")


def exists(env):
    return True
