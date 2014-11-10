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
import functools
import threading
import SCons
import LibFinder
from TargetMaker import getRealTarget

# needs locking because it is manipulated during multi-threaded build phase
systemLibTargets = {}
systemLibTargetsRLock = threading.RLock()
aliasPrefix = '__SystemLibs_'


def notInDir(env, dir, path):
    return not env.File(path).is_under(dir)


def installSystemLibs(source):
    """This function is called during the build phase and adds targets
    dynamically to the dependency tree."""
    sourcenode = getRealTarget(source)
    if not sourcenode:
        return None
    source = [sourcenode]

    env = sourcenode.get_env()
    finder = LibFinder.FinderFactory.getForPlatform(env["PLATFORM"])
    libdirs = []
    libdirs.extend(env.get('LIBPATH', []))
    libdirs.extend(finder.getSystemLibDirs(env))
    deplibs = finder.getLibs(env, source, libdirs=libdirs)
    if not hasattr(env, 'getLibraryInstallDir'):
        raise SCons.Errors.UserError(
            'environment on node [%s] is not a SConsider environment, can not continue' %
            (str(sourcenode)))
    ownlibDir = env.getLibraryInstallDir()

    # don't create cycles by copying our own libs
    deplibs = filter(functools.partial(notInDir, env, ownlibDir), deplibs)
    target = []

    from stat import S_IRUSR, S_IRGRP, S_IROTH, S_IXUSR
    # ensure executable flag on installed shared libs
    mode = S_IRUSR | S_IRGRP | S_IROTH | S_IXUSR
    # build phase could be multi-threaded
    with systemLibTargetsRLock:
        for deplib in deplibs:
            # take care of already created targets otherwise we would have
            # multiple ways to build the same target
            srcfile = os.path.basename(deplib)
            linkfile = srcfile
            if linkfile in systemLibTargets:
                libtarget = systemLibTargets[linkfile]
            else:
                libpathname = deplib
                reallibpath = os.path.realpath(libpathname)
                if reallibpath != libpathname:
                    srcfile = os.path.basename(reallibpath)
                lib = env.File(reallibpath)
                if not os.path.dirname(lib.get_abspath()) == ownlibDir.get_abspath():
                    libtarget = env.Install(ownlibDir, lib)
                    env.AddPostAction(
                        libtarget,
                        SCons.Defaults.Chmod(str(libtarget[0]), mode))
                    if srcfile != linkfile:
                        libtarget = env.Symlink(
                            ownlibDir.File(linkfile),
                            libtarget)
                    systemLibTargets[linkfile] = libtarget
            if not libtarget[0] in target:
                target.extend(libtarget)

    # add targets as dependency of the intermediate target
    env.Depends(aliasPrefix + sourcenode.name, target)


def generate(env, *args, **kw):
    """Add the options, builders and wrappers to the current Environment."""
    createDeferredAction = SCons.Action.ActionFactory(
        installSystemLibs,
        lambda *args, **kw: '')

    def createDeferredTarget(env, source):
        # bind 'source' parameter to an Action which is called in the build phase and
        # create a dummy target which always will be built
        sourcenode = getRealTarget(source)
        if not sourcenode:
            return []
        source = [sourcenode]
        if not env.GetOption('clean') and not env.GetOption('help'):
            target = env.Command(
                sourcenode.name + '_dummy',
                sourcenode,
                createDeferredAction(source))
            # create intermediate target to which we add dependency in the
            # build phase
            return env.Alias(aliasPrefix + sourcenode.name, target)
        else:
            """It makes no sense to find nodes to delete when target doesn't
            exist..."""
            if not os.path.exists(sourcenode.get_abspath()):
                return []
            env = sourcenode.get_env()
            finder = LibFinder.FinderFactory.getForPlatform(env["PLATFORM"])
            libdirs = []
            libdirs.extend(env.get('LIBPATH', []))
            libdirs.extend(finder.getSystemLibDirs(env))
            deplibs = finder.getLibs(env, source, libdirs=libdirs)
            ownlibdir = env.getLibraryInstallDir()
            for deplib in deplibs:
                srcfile = os.path.basename(deplib)
                libfile = ownlibdir.File(srcfile)
                if os.path.isfile(
                        libfile.get_abspath()) or os.path.islink(
                        libfile.get_abspath()):
                    env.Clean(sourcenode, libfile)
                    if os.path.islink(libfile.get_abspath()):
                        env.Clean(
                            sourcenode,
                            ownlibdir.File(os.readlink(libfile.get_abspath())))
            return []

    env.AddMethod(createDeferredTarget, "InstallSystemLibs")


def exists(env):
    return True
