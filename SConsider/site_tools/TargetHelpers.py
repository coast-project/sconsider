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
from SConsider.deprecation import deprecated
logger = getLogger(__name__)


def getUsedTarget(env, buildSettings):
    from SConsider.PackageRegistry import PackageRegistry
    used_target = None
    usedFullTargetname = buildSettings.get('usedTarget', None)
    if usedFullTargetname:
        usedPackagename, usedTargetname = PackageRegistry.splitFulltargetname(usedFullTargetname,
                                                                              default=True)
        used_target = PackageRegistry().loadPackageTarget(usedPackagename, usedTargetname)
    return used_target


def usedOrProgramTarget(env, name, sources, buildSettings):
    used_target = getUsedTarget(env, buildSettings)
    if not used_target:
        # env.File is a workaround, otherwise if an Alias with the same 'name'
        # is defined arg2nodes (called from all builders) would return the
        # Alias, but we would need a file node
        used_target = env.Program(env.File(name), sources)

    return used_target


def setupTargetDirAndWrapperScripts(env, name, packagename, install_target, basetargetdir):
    env.setRelativeTargetDirectory(os.path.join(basetargetdir, packagename))
    install_path = env.makeInstallablePathFromDir(env.getBinaryInstallDir().File(name))
    installed_targets = env.InstallAs(target=install_path, source=install_target)
    installed_target = installed_targets[0]
    sysLibs = env.InstallSystemLibs(install_target)
    env.Requires(installed_target, sysLibs)
    for required_tool in ['generateScript']:
        if required_tool not in env['TOOLS']:
            env.Tool(required_tool)
    wrappers = env.GenerateWrapperScript(installed_targets)
    return (installed_target, wrappers)


def programApp(env, name, sources, packagename, buildSettings, **kw):
    used_target = usedOrProgramTarget(env, name, sources, buildSettings)
    used_target, wrappers = setupTargetDirAndWrapperScripts(env, name, packagename, used_target, 'apps')
    buildSettings.setdefault("runConfig", {}).setdefault("type", "run")
    env.Alias('binaries', wrappers)
    return (used_target, wrappers)


def programTest(env, name, sources, packagename, targetname, buildSettings, **kw):
    used_target = usedOrProgramTarget(env, name, sources, buildSettings)
    buildSettings.setdefault("runConfig", {}).setdefault("type", "test")
    used_target, wrappers = setupTargetDirAndWrapperScripts(env, name, packagename, used_target, 'tests')
    return (used_target, wrappers)


def sharedLibrary(env, name, sources, packagename, targetname, buildSettings, **kw):
    libBuilder = env.SharedLibrary
    # @!FIXME: we should move this section out to the libraries needing it
    if buildSettings.get('lazylinking', False):
        env['_NONLAZYLINKFLAGS'] = ''
        if env["PLATFORM"] == "win32":
            libBuilder = env.StaticLibrary

    lib_target = libBuilder(name, sources)
    install_path = env.makeInstallablePathFromDir(env.getLibraryInstallDir())
    installed_targets = env.Install(dir=install_path, source=lib_target)
    # the first target should be the real target
    installed_target = installed_targets[0]
    if len(installed_targets):
        env.Requires(installed_target, installed_targets[1:])
    sysLibs = env.InstallSystemLibs(lib_target)
    env.Requires(installed_target, sysLibs)
    return (installed_target, installed_targets)


def staticLibrary(env, name, sources, packagename, targetname, buildSettings, **kw):
    env['_NONLAZYLINKFLAGS'] = ''
    lib_target = env.StaticLibrary(name, sources)
    install_path = env.makeInstallablePathFromDir(env.getLibraryInstallDir())
    installed_targets = env.Install(dir=install_path, source=lib_target)
    env.Requires(installed_targets[0], installed_targets[1:])
    return (lib_target, installed_targets)


def installPrecompiledBinary(env, name, sources, packagename, targetname, buildSettings, **kw):
    env.setRelativeTargetDirectory(os.path.join('globals', packagename))
    target = env.PrecompiledBinaryInstallBuilder(name, sources)
    # use symlink target at index 1 if available
    target = target[-1:]
    return (target, target)


def installPrecompiledLibrary(env, name, sources, packagename, targetname, buildSettings, **kw):
    lib = env.PrecompiledLibraryInstallBuilder(name, sources)
    # use symlink target at index 1 if available
    lib = lib[-1:]
    return (lib, lib)


def installBinary(env, name, sources, packagename, targetname, buildSettings, **kw):
    env.setRelativeTargetDirectory(os.path.join('globals', packagename))
    install_path = env.makeInstallablePathFromDir(env.getBinaryInstallDir())
    installed_targets = env.Install(dir=install_path, source=sources)
    env.Requires(installed_targets[0], installed_targets[1:])
    return (installed_targets, installed_targets)


def prePackageCollection(env, **_):
    # we require ThirdParty
    for required_tool in ['ThirdParty']:
        if required_tool not in env['TOOLS']:
            env.Tool(required_tool)


def generate(env):
    def ProgramApp(env, *args, **kw):
        return programApp(env, *args, **kw)

    @deprecated("Use the method ProgramTest instead.")
    def AppTest(env, *args, **kw):
        return programTest(env, *args, **kw)

    def ProgramTest(env, *args, **kw):
        return programTest(env, *args, **kw)

    def LibraryShared(env, *args, **kw):
        return sharedLibrary(env, *args, **kw)

    def LibraryStatic(env, *args, **kw):
        return staticLibrary(env, *args, **kw)

    def PrecompiledBinary(env, *args, **kw):
        return installPrecompiledBinary(env, *args, **kw)

    def PrecompiledLibrary(env, *args, **kw):
        return installPrecompiledLibrary(env, *args, **kw)

    def InstallBinary(env, *args, **kw):
        return installBinary(env, *args, **kw)

    env.AddMethod(ProgramApp)
    env.AddMethod(AppTest)
    env.AddMethod(ProgramTest)
    env.AddMethod(LibraryShared)
    env.AddMethod(LibraryStatic)
    env.AddMethod(PrecompiledBinary)
    env.AddMethod(PrecompiledLibrary)
    env.AddMethod(InstallBinary)
    from SConsider.Callback import Callback
    Callback().register('PrePackageCollection', prePackageCollection)


def exists(env):
    return True
