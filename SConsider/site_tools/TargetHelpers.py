"""SConsider.site_tools.TargetHelpers.

Just a bunch of simple methods to help creating targets. Methods will be
added to the environment supplied in the generate call.

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
    from SConsider.PackageRegistry import PackageRegistry
    used_target = None
    usedFullTargetname = buildSettings.get('usedTarget', None)
    if usedFullTargetname:
        usedPackagename, usedTargetname = PackageRegistry.splitFulltargetname(
            usedFullTargetname, default=True)
        used_target = PackageRegistry().loadPackageTarget(usedPackagename,
                                                          usedTargetname)
    return used_target


def usedOrProgramTarget(env, name, sources, buildSettings):
    used_target = getUsedTarget(env, buildSettings)
    if not used_target:
        # env.File is a workaround, otherwise if an Alias with the same 'name'
        # is defined arg2nodes (called from all builders) would return the
        # Alias, but we would need a file node
        used_target = env.Program(env.File(name), sources)

    return used_target


def setupTargetDirAndWrapperScripts(env, name, packagename, install_target,
                                    basetargetdir):
    env.setRelativeTargetDirectory(os.path.join(basetargetdir, packagename))
    instApps = env.InstallAs(env.getBinaryInstallDir().File(name).path,
                             install_target)
    if 'generateScript' not in env['TOOLS']:
        env.Tool('generateScript')
    wrappers = env.GenerateWrapperScript(instApps)
    return (install_target, wrappers)


def programApp(env, name, sources, packagename, buildSettings, **kw):
    used_target = usedOrProgramTarget(env, name, sources, buildSettings)
    used_target, wrappers = setupTargetDirAndWrapperScripts(
        env, name, packagename, used_target, 'apps')
    buildSettings.setdefault("runConfig", {}).setdefault("type", "run")
    env.Alias('binaries', wrappers)
    return (used_target, wrappers)


def programTest(env, name, sources, packagename, targetname, buildSettings,
                **kw):
    used_target = usedOrProgramTarget(env, name, sources, buildSettings)
    buildSettings.setdefault("runConfig", {}).setdefault("type", "test")
    return setupTargetDirAndWrapperScripts(env, name, packagename, used_target,
                                           'tests')


def sharedLibrary(env, name, sources, packagename, targetname, buildSettings,
                  **kw):
    libBuilder = env.SharedLibrary
    # @!FIXME: we should move this section out to the libraries needing it
    if buildSettings.get('lazylinking', False):
        env['_NONLAZYLINKFLAGS'] = ''
        if env["PLATFORM"] == "win32":
            libBuilder = env.StaticLibrary

    lib_target = libBuilder(name, sources)
    instTarg = env.Install(env.getLibraryInstallDir().path, lib_target)
    env.Requires(instTarg[0], instTarg[1:])

    compLibs = env.InstallSystemLibs(lib_target)
    # the first target should be the library
    env.Requires(instTarg[0], compLibs)

    return (lib_target, instTarg)


def staticLibrary(env, name, sources, packagename, targetname, buildSettings,
                  **kw):
    env['_NONLAZYLINKFLAGS'] = ''

    lib_target = env.StaticLibrary(name, sources)
    instTarg = env.Install(env.getLibraryInstallDir().path, lib_target)
    env.Requires(instTarg[0], instTarg[1:])

    compLibs = env.InstallSystemLibs(lib_target)
    env.Requires(instTarg[0], compLibs)

    return (lib_target, instTarg)


def installPrecompiledBinary(env, name, sources, packagename, targetname,
                             buildSettings, **kw):
    env.setRelativeTargetDirectory(os.path.join('globals', packagename))
    target = env.PrecompiledBinaryInstallBuilder(name, sources)
    # use symlink target at index 1 if available
    target = target[-1:]
    return (target, target)


def installPrecompiledLibrary(env, name, sources, packagename, targetname,
                              buildSettings, **kw):
    lib = env.PrecompiledLibraryInstallBuilder(name, sources)
    # use symlink target at index 1 if available
    lib = lib[-1:]
    return (lib, lib)


def installBinary(env, name, sources, packagename, targetname, buildSettings,
                  **kw):
    env.setRelativeTargetDirectory(os.path.join('globals', packagename))
    instTarg = env.Install(env.getBinaryInstallDir().path, sources)
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
    from SConsider.Callback import Callback
    Callback().register('PrePackageCollection', prePackageCollection)


def exists(env):
    return True
