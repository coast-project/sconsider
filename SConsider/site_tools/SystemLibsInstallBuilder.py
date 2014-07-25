"""SConsider.site_tools.SystemLibsInstallBuilder.

Tool to collect system libraries needed by an executable/shared library

"""

# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import functools
import threading
import SCons
import LibFinder

# needs locking because it is manipulated during multi-threaded build phase
systemLibTargets = {}
systemLibTargetsRLock = threading.RLock()
aliasPrefix = '__SystemLibs_'


def notInDir(env, dir, path):
    return not env.File(path).is_under(dir)


def installSystemLibs(source):
    """This function is called during the build phase and adds targets
    dynamically to the dependency tree."""
    if not SCons.Util.is_List(source):
        source = [source]

    if not source:
        return None

    env = source[0].get_env()
    finder = LibFinder.FinderFactory.getForPlatform(env["PLATFORM"])
    libdirs = env['LIBPATH']
    libdirs.extend(finder.getSystemLibDirs(env))
    deplibs = finder.getLibs(env, source, libdirs=libdirs)

    ownlibDir = env['BASEOUTDIR'].Dir(env['LIBDIR']).Dir(env['VARIANTDIR'])

    # don't create cycles by copying our own libs
    deplibs = filter(functools.partial(notInDir, env, ownlibDir), deplibs)

    target = []

    # build phase could be multi-threaded
    with systemLibTargetsRLock:
        for deplib in deplibs:
            # take care of already created targets otherwise we would have
            # multiple ways to build the same target
            if deplib in systemLibTargets:
                libtarget = systemLibTargets[deplib]
            else:
                libtarget = env.Install(ownlibDir, env.File(deplib))
                systemLibTargets[deplib] = libtarget
            target.extend(libtarget)

    # add targets as dependency of the intermediate target
    env.Depends(aliasPrefix + source[0].name, target)


def generate(env):
    """Add the options, builders and wrappers to the current Environment."""
    createDeferredAction = SCons.Action.ActionFactory(
        installSystemLibs,
        lambda source: '')

    def createDeferredTarget(env, source):
        # bind 'source' parameter to an Action which is called in the build phase and
        # create a dummy target which always will be built
        target = env.Command(
            source[0].name +
            '_dummy',
            source,
            createDeferredAction(source))
        # create intermediate target to which we add dependency in the build
        # phase
        return env.Alias(aliasPrefix + source[0].name, target)
    env.AddMethod(createDeferredTarget, "InstallSystemLibs")


def exists(env):
    return True
