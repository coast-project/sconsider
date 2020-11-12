"""SConsider.Main.

SCons build tool extension allowing automatic target finding within a
directory tree.
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from __future__ import with_statement
import os
import platform
import atexit
import sys
from optparse import OptionConflictError
from logging import getLogger
try:
    from collections import OrderedDict
except ImportError:
    # support python < 2.7
    from ordereddict import OrderedDict
from pkg_resources import get_distribution as pkg_get_dist,\
    get_build_platform, ResolutionError
from SCons import __version__ as _scons_version
from SCons.Script import AddOption, GetOption, Dir, DefaultEnvironment,\
    Flatten, SConsignFile, EnsureSConsVersion, EnsurePythonVersion, BUILD_TARGETS, GetLaunchDir, GetBuildFailures
from SCons.Errors import UserError, EnvironmentError
from SCons.Tool import DefaultToolpath
from SCons.Util import Null as SConsNull
from SConsider.Callback import Callback
from SConsider.Logging import setup_logging, DEFAULT_LEVEL
from SConsider.PackageRegistry import PackageRegistry, PackageNotFound, TargetNotFound, PackageRequirementsNotFulfilled, NoPackageTargetsFound
from SConsider import __version__ as sconsider_version, get_sconsider_root
from .deprecation import deprecated

dEnv = None
baseEnv = None
baseoutdir = None
packageRegistry = None


def get_sconstruct_dir(the_env):
    """Returns the directory containing the SConstruct file."""
    return the_env.Dir(the_env.fs.SConstruct_dir)


def get_launch_dir(the_env):
    """Returns the directory from which scons was launched."""
    return the_env.Dir(the_env.GetLaunchDir())


def extend_sys_path():
    sys.path[:0] = [get_sconsider_root()]


def setup_main_logging(default_level=DEFAULT_LEVEL):
    from os import getenv
    the_level = getenv('LOG_LEVEL', None)
    if the_level is None:
        the_level = default_level
    else:
        import logging
        the_level = getattr(logging, the_level.upper())
    setup_logging(default_path=os.path.join(get_sconsider_root(), 'logging.yaml'), default_level=the_level)
    return getLogger(__name__)


def ensure_prerequisites():
    EnsureSConsVersion(2, 5, 0)
    EnsurePythonVersion(2, 6)


def print_scons_sconsider_info(logto, project_name, project_version):
    logto.info("SCons version %s", _scons_version)
    try:
        sconsider_package_info = pkg_get_dist(project_name)
        project_name = sconsider_package_info.project_name
        project_version = sconsider_package_info.version
    except ResolutionError:
        pass
    finally:
        logto.info("%s version %s (%s)", project_name, project_version, get_build_platform())


class Null(SConsNull):
    def __getitem__(self, key):
        return self

    def __contains__(self, key):
        return False


def print_platform_info(logto):
    for platform_func in [
            platform.dist, platform.architecture, platform.machine, platform.libc_ver, platform.release,
            platform.version, platform.processor, platform.system, platform.uname
    ]:
        func_value = platform_func()
        if func_value:
            logto.debug("platform.%s: %s", platform_func.__name__, func_value)


def create_default_environment():
    return DefaultEnvironment()


def add_path_extend_options():
    AddOption('--appendPath',
              dest='appendPath',
              action='append',
              nargs=1,
              type='string',
              metavar='DIR',
              help='Append this directory to the PATH environment variable.')
    AddOption('--prependPath',
              dest='prependPath',
              action='append',
              nargs=1,
              type='string',
              metavar='DIR',
              help='Prepend this directory to the PATH environment variable.')


def process_path_options(the_env, logto):
    if GetOption('prependPath'):
        the_env.PrependENVPath('PATH', GetOption('prependPath'))
        logto.debug('prepended path is [%s]\nfull path is [%s]', GetOption('prependPath'),
                    the_env['ENV']['PATH'])
    if GetOption('appendPath'):
        the_env.AppendENVPath('PATH', GetOption('appendPath'))
        logto.debug('appended path is [%s]\nfull path is [%s]', GetOption('appendPath'),
                    the_env['ENV']['PATH'])


sconsider_default_tools = [
    "setupBuildTools",
    "OutputDirectoryHelper",
    "ExcludeDirectoryHelper",
    "TargetHelpers",
    "TargetMaker",
    "TargetPrinter",
    "SubstInFileBuilder",
    "RunBuilder",
    "SystemLibsInstallBuilder",
    "precompiledLibraryInstallBuilder",
]


def add_options_for_tools():
    AddOption('--usetool',
              dest='usetools',
              action='append',
              nargs=1,
              type='string',
              default=[],
              metavar='VAR',
              help='SCons tools to use for constructing the default environment. Default\
 tools are %s' % Flatten(sconsider_default_tools))


def get_list_of_scons_tools(logto):
    # Keep order of tools in list but remove duplicates
    option_tools = GetOption('usetools')
    if option_tools is None:
        option_tools = []
    usetools = OrderedDict.fromkeys(sconsider_default_tools +
                                    DefaultEnvironment().get('_SCONSIDER_TOOLS_', []) + option_tools).keys()
    logto.debug('tools to use %s', Flatten(usetools))
    return usetools


def create_sconsider_env_with_tools(default_env, logto):
    usetools = get_list_of_scons_tools(logto)
    # insert the site_tools path for our own tools
    DefaultToolpath.insert(0, os.path.join(get_sconsider_root(), 'site_tools'))
    try:
        return default_env.Clone(tools=usetools)
    except EnvironmentError:
        for t in usetools:
            if t not in default_env['TOOLS']:
                try:
                    default_env.Tool(t)
                except OptionConflictError:
                    pass
                except EnvironmentError:
                    logto.error('loading Tool [%s] failed', t, exc_info=False)
                    raise


def cloneBaseEnv():
    return baseEnv.Clone()


def setup_base_output_dir(the_env, logto):
    global baseoutdir
    baseoutdir = the_env.getBaseOutDir()
    if baseoutdir is None:
        baseoutdir = get_sconstruct_dir(the_env)
    logto.info('base output dir [%s]', baseoutdir.get_abspath())


def setup_path_to_sconsign_file(the_env, logto, output_dir):
    variant = the_env.getRelativeVariantDirectory()
    logto.info('compilation variant [%s]', variant)
    ssfile = os.path.join(output_dir.get_abspath(), '.sconsign.' + variant)
    SConsignFile(ssfile)


def run_pre_package_collection_cb(the_env):
    Callback().run('PrePackageCollection', env=the_env, sconstruct_dir=get_sconstruct_dir(the_env))


@deprecated("Use the static method splitFulltargetname of PackageRegistry instead.")
def splitTargetname(*args, **kwargs):
    return PackageRegistry.splitFulltargetname(*args, **kwargs)


@deprecated("Use the static method createUniqueTargetname of PackageRegistry instead.")
def createUniqueTargetname(*args, **kwargs):
    return PackageRegistry.createUniqueTargetname(*args, **kwargs)


@deprecated("Use the static method createFulltargetname of PackageRegistry instead.")
def generateFulltargetname(*args, **kwargs):
    return PackageRegistry.createFulltargetname(*args, **kwargs)


@deprecated("Use listFiles from SConsider.SomeUtils instead.")
def listFiles(*args, **kwargs):
    from SConsider.SomeUtils import listFiles as func
    return func(*args, **kwargs)


@deprecated("Use findFiles from SConsider.SomeUtils instead.")
def findFiles(*args, **kwargs):
    from SConsider.SomeUtils import findFiles as func
    return func(*args, **kwargs)


@deprecated("Use removeFiles from SConsider.SomeUtils instead.")
def removeFiles(*args, **kwargs):
    from SConsider.SomeUtils import removeFiles as func
    func(*args, **kwargs)


@deprecated("Use getfqdn from SConsider.SomeUtils instead.")
def getfqdn(*args, **kwargs):
    from SConsider.SomeUtils import getfqdn as func
    return func(*args, **kwargs)


def create_package_registry(the_env):
    return PackageRegistry(the_env)


def scan_dirs_for_packagefiles(registry, the_env, start_dir):
    registry.scan_for_package_files(start_dir, the_env.relativeExcludeDirs(), the_env.absoluteExcludeDirs())


def extend_env_lookup_by_package_registry(the_env, registry):
    """Using LoadNode and extending the lookup_list has the advantage that
    SCons is looking for a matching Alias node when our own lookup returns no
    result."""
    the_env.AddMethod(PackageRegistry.loadNode, 'LoadNode')
    the_env.lookup_list.insert(0, registry.lookup)


def run_post_package_collection_cb(the_env, registry):
    Callback().run('PostPackageCollection',
                   env=the_env,
                   registry=registry,
                   sconstruct_dir=get_sconstruct_dir(the_env))


def createTargets(pkg_name, buildSettings):
    """Creates the targets for the package 'packagename' which are defined in
    'buildSettings'.

    This is a helper function which must be called from SConscript to
    create the targets.
    """
    packageRegistry.setBuildSettings(pkg_name, buildSettings)
    # do not create/build empty packages like the ones where Configure() fails
    if not buildSettings:
        return False
    from SConsider.site_tools.TargetMaker import TargetMaker
    tmk = TargetMaker(pkg_name, buildSettings, packageRegistry)
    return tmk.createTargets()


def print_build_failures(logto):
    if GetBuildFailures():
        failednodes = ['scons: printing failed nodes']
        for failure_node in GetBuildFailures():
            if str(failure_node.action) != "installFunc(target, source, env)":
                failednodes.append(str(failure_node.node))
        failednodes.append('scons: done printing failed nodes')
        logto.warning('\n'.join(failednodes))


def tryLoadPackageTarget(registry, pkg_name, tgt_name, logto, build_targets):
    try:
        if registry.loadPackageTarget(pkg_name, tgt_name) is None:
            # raising PackageNotFound aborts the implicit package loading
            # part and steps into loading all packages to find an alias
            raise PackageNotFound(pkg_name)
    except (PackageNotFound) as ex:
        # catch PackageNotFound separately as it is derived from
        # TargetNotFound
        raise
    except (TargetNotFound, NoPackageTargetsFound) as ex:
        ftn = PackageRegistry.createFulltargetname(pkg_name, tgt_name)
        if ftn in build_targets:
            ex.message = 'explicit targetname [%s] has no targets' % ftn
            ex.lookupStack = []
            raise
        if int(GetOption('ignore-missing')) or GetOption('help'):
            logto.warning('%s', ex, exc_info=False)


def load_targets_from_package_files(the_env, registry, logto):
    """Load potential targets before entering the build phase as SCons needs
    them there."""
    logto.info("Loading packages and their targets ...")
    try:
        launchDir = Dir(GetLaunchDir())

        if GetOption("climb_up") in [1, 3]:  # 1: -u, 3: -U
            if GetOption("climb_up") == 1:

                def dirfilter(directory):
                    return directory.is_under(launchDir)
            else:

                def dirfilter(directory):
                    return directory == launchDir
        else:

            def dirfilter(_):
                return True

        def namefilter(pkg_name):
            return dirfilter(registry.getPackageDir(pkg_name))

        try:
            buildtargets = BUILD_TARGETS
            _LAUNCHDIR_RELATIVE = launchDir.path
            if not buildtargets:
                buildtargets = [item for item in registry.getPackageNames() if namefilter(item)]
            elif '.' in buildtargets:
                builddir = baseoutdir.Dir(_LAUNCHDIR_RELATIVE).Dir(the_env.getRelativeBuildDirectory()).Dir(
                    the_env.getRelativeVariantDirectory()).get_abspath()
                buildtargets[buildtargets.index('.')] = builddir

            for ftname in buildtargets:
                packagename, targetname = PackageRegistry.splitFulltargetname(ftname)
                tryLoadPackageTarget(registry,
                                     pkg_name=packagename,
                                     tgt_name=targetname,
                                     logto=logto,
                                     build_targets=BUILD_TARGETS)

        except PackageNotFound as ex:
            logto.warning('%s, loading all packages to find potential alias target', ex, exc_info=False)

            buildtargets = [item for item in registry.getPackageNames() if namefilter(item)]

            for packagename in buildtargets:
                try:
                    the_env.LoadNode(packagename)
                except NoPackageTargetsFound as ex:
                    if not GetOption('help'):
                        logto.warning('%s', ex, exc_info=False)
            logto.info("Completed loading possible targets and aliases from %d available package files",
                       len(buildtargets))

    except (PackageNotFound, TargetNotFound, PackageRequirementsNotFulfilled) as ex:
        if not isinstance(ex, PackageRequirementsNotFulfilled):
            logto.error('%s', ex, exc_info=False)
        if not GetOption('help'):
            raise UserError('{0}, build aborted!'.format(ex))


def run_pre_build_cb(the_env, registry, build_targets):
    """Run registered PreBuild callbacks.

    Note: buildTargets is passed by reference and might be extended in callback functions!
    """
    Callback().run("PreBuild",
                   registry=registry,
                   buildTargets=build_targets,
                   sconstruct_dir=get_sconstruct_dir(the_env))


def print_collected_build_targets(build_targets, logto):
    """Just print out what we are going to build."""
    logto.info('BUILD_TARGETS is %s', sorted([str(item) for item in build_targets]))


def main():
    extend_sys_path()
    global dEnv, baseEnv, baseoutdir, packageRegistry
    logger = setup_main_logging()
    ensure_prerequisites()
    print_scons_sconsider_info(logger, 'SConsider', sconsider_version)
    print_platform_info(logger)
    dEnv = create_default_environment()
    add_path_extend_options()
    process_path_options(dEnv, logger)
    add_options_for_tools()
    baseEnv = create_sconsider_env_with_tools(dEnv, logger)
    setup_base_output_dir(baseEnv, logger)
    setup_path_to_sconsign_file(baseEnv, logger, baseoutdir)
    run_pre_package_collection_cb(baseEnv)
    packageRegistry = create_package_registry(baseEnv)
    scan_dirs_for_packagefiles(packageRegistry, baseEnv, get_sconstruct_dir(baseEnv))
    extend_env_lookup_by_package_registry(baseEnv, packageRegistry)
    run_post_package_collection_cb(baseEnv, packageRegistry)
    atexit.register(print_build_failures, logto=logger)
    load_targets_from_package_files(baseEnv, packageRegistry, logger)
    run_pre_build_cb(baseEnv, packageRegistry, BUILD_TARGETS)
    print_collected_build_targets(BUILD_TARGETS, logger)
