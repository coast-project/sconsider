"""SConsider.site_tools.TargetHelpers.

Just a bunch of simple methods to help creating targets. Methods will be added
to the environment supplied in the generate call.

"""
# vim: set et ai ts=4 sw=4:
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


def getUsedTarget(env, buildSettings):
    from SConsider import getRegistry, splitTargetname
    plaintarget = None
    usedFullTargetname = buildSettings.get('usedTarget', None)
    if usedFullTargetname:
        usedPackagename, usedTargetname = splitTargetname(
            usedFullTargetname, default=True)
        plaintarget = getRegistry().loadPackagePlaintarget(
            usedPackagename,
            usedTargetname)
    return plaintarget


def usedOrProgramTarget(env, name, sources, buildSettings):
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
    env.setRelativeTargetDirectory(os.path.join(basetargetdir, packagename))
    instApps = env.InstallAs(env.getBinaryInstallDir().File(name), plaintarget)
    if 'generateScript' not in env['TOOLS']:
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
    instTarg = env.Install(env.getLibraryInstallDir(), plaintarget)
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
    instTarg = env.Install(env.getLibraryInstallDir(), plaintarget)
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
    env.setRelativeTargetDirectory(os.path.join('globals', packagename))
    target = env.PrecompiledBinaryInstallBuilder(name, sources)
    # use symlink target at index 1 if available
    target = target[-1:]
    return (target, target)


def installPrecompiledLibrary(
        env,
        name,
        sources,
        packagename,
        targetname,
        buildSettings,
        **kw):
    lib = env.PrecompiledLibraryInstallBuilder(name, sources)
    # use symlink target at index 1 if available
    lib = lib[-1:]
    return (lib, lib)


def installBinary(
        env,
        name,
        sources,
        packagename,
        targetname,
        buildSettings,
        **kw):
    env.setRelativeTargetDirectory(os.path.join('globals', packagename))
    instTarg = env.Install(env.getBinaryInstallDir(), sources)
    env.Requires(instTarg[0], instTarg[1:])

    return (instTarg, instTarg)


def prePackageCollection(env):
    # we require ThirdParty
    if 'ThirdParty' not in env['TOOLS']:
        env.Tool('ThirdParty')


def generate(env):
    env.AddMethod(programApp, "ProgramApp")
    # @!FIXME: should use ProgramTest instead
    env.AddMethod(programTest, "AppTest")
    env.AddMethod(programTest, "ProgramTest")
    env.AddMethod(sharedLibrary, "LibraryShared")
    env.AddMethod(staticLibrary, "LibraryStatic")
    env.AddMethod(installPrecompiledBinary, "PrecompiledBinary")
    env.AddMethod(installPrecompiledLibrary, "PrecompiledLibrary")
    env.AddMethod(installBinary, "InstallBinary")
    from SConsider import registerCallback
    registerCallback('PrePackageCollection', prePackageCollection)


def exists(env):
    return True
