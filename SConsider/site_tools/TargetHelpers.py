"""SConsider.TargetHelpers.

Just a bunch of simple methods to help creating targets. Methods will be added
to the environment supplied in the generate call.

"""

# -------------------------------------------------------------------------
# Copyright (c) 2014, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import os
from logging import getLogger
logger = getLogger(__name__)


def usedOrProgramTarget(env, name, sources, buildSettings):
    from PackageRegistry import getUsedTarget
    plaintarget = getUsedTarget(env, buildSettings)
    if not plaintarget:
        # env.File is a workaround, otherwise if an Alias with the same 'name'
        # is defined arg2nodes (called from all builders) would return the
        # Alias, but we would need a file node
        plaintarget = env.Program(env.File(name), sources)

    return plaintarget


def setupTargetDirAndWrapperScripts(
        env,
        name,
        packagename,
        plaintarget,
        basetargetdir):
    baseoutdir = env['BASEOUTDIR']
    env['RELTARGETDIR'] = os.path.join(basetargetdir, packagename)
    instApps = env.InstallAs(
        baseoutdir.Dir(
            env['RELTARGETDIR']).Dir(
                env['BINDIR']).Dir(
                    env['VARIANTDIR']).File(name),
        plaintarget)
    env.Tool('generateScript')
    wrappers = env.GenerateWrapperScript(instApps)
    return (plaintarget, wrappers)


def programApp(env, name, sources, packagename, buildSettings, **kw):
    plaintarget = usedOrProgramTarget(env, name, sources, buildSettings)
    plaintarget, wrappers = setupTargetDirAndWrapperScripts(
        env, name, packagename, plaintarget, 'apps')
    buildSettings.setdefault("runConfig", {}).setdefault("type", "run")
    env.Alias('binaries', wrappers)
    return (plaintarget, wrappers)


def programTest(
        env,
        name,
        sources,
        packagename,
        targetname,
        buildSettings,
        **kw):
    plaintarget = usedOrProgramTarget(env, name, sources, buildSettings)
    buildSettings.setdefault("runConfig", {}).setdefault("type", "test")
    return setupTargetDirAndWrapperScripts(
        env,
        name,
        packagename,
        plaintarget,
        'tests')


def sharedLibrary(
        env,
        name,
        sources,
        packagename,
        targetname,
        buildSettings,
        **kw):
    libBuilder = env.SharedLibrary
    # @!FIXME: we should move this section out to the libraries needing it
    if buildSettings.get('lazylinking', False):
        env['_NONLAZYLINKFLAGS'] = ''
        if env["PLATFORM"] == "win32":
            libBuilder = env.StaticLibrary

    plaintarget = libBuilder(name, sources)

    baseoutdir = env['BASEOUTDIR']
    instTarg = env.Install(
        baseoutdir.Dir(
            env['LIBDIR']).Dir(
                env['VARIANTDIR']),
        plaintarget)
    env.Requires(instTarg[0], instTarg[1:])

    compLibs = env.InstallSystemLibs(plaintarget)
    # the first target should be the library
    env.Requires(instTarg[0], compLibs)

    return (plaintarget, instTarg)


def staticLibrary(
        env,
        name,
        sources,
        packagename,
        targetname,
        buildSettings,
        **kw):
    env['_NONLAZYLINKFLAGS'] = ''

    plaintarget = env.StaticLibrary(name, sources)

    baseoutdir = env['BASEOUTDIR']
    instTarg = env.Install(
        baseoutdir.Dir(
            env['LIBDIR']).Dir(
                env['VARIANTDIR']),
        plaintarget)
    env.Requires(instTarg[0], instTarg[1:])

    compLibs = env.InstallSystemLibs(plaintarget)
    env.Requires(instTarg[0], compLibs)

    return (plaintarget, instTarg)


def installPrecompiledBinary(
        env,
        name,
        sources,
        packagename,
        targetname,
        buildSettings,
        **kw):
    env['RELTARGETDIR'] = os.path.join('globals', packagename)
    plaintarget = env.PrecompiledBinaryInstallBuilder(name, sources)

    return (plaintarget, plaintarget)


def installBinary(
        env,
        name,
        sources,
        packagename,
        targetname,
        buildSettings,
        **kw):
    env['RELTARGETDIR'] = os.path.join('globals', packagename)
    installDir = env['BASEOUTDIR'].Dir(
        env['RELTARGETDIR']).Dir(
            env['BINDIR']).Dir(
                env['VARIANTDIR'])
    instTarg = env.Install(installDir, sources)
    env.Requires(instTarg[0], instTarg[1:])

    return (instTarg, instTarg)


def generate(env):
    env.AddMethod(programApp, "ProgramApp")
    # @!FIXME: should use ProgramTest instead
    env.AddMethod(programTest, "AppTest")
    env.AddMethod(programTest, "ProgramTest")
    env.AddMethod(sharedLibrary, "LibraryShared")
    env.AddMethod(staticLibrary, "LibraryStatic")
    env.AddMethod(installPrecompiledBinary, "PrecompiledBinary")
    env.AddMethod(installBinary, "InstallBinary")


def exists(env):
    return 1
