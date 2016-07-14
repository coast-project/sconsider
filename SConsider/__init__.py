"""SConsider.

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
import optparse
from logging import getLogger
try:
    from collections import OrderedDict
except ImportError:
    # support python < 2.7
    from ordereddict import OrderedDict
from pkg_resources import get_distribution as pkg_get_dist,\
    get_build_platform, ResolutionError

import SCons
from SCons.Script import AddOption, GetOption, Dir, DefaultEnvironment,\
    Flatten, SConsignFile
from SCons.Tool import DefaultToolpath
from SConsider.Callback import Callback
from SConsider.Logging import setup_logging
from SConsider.PackageRegistry import PackageRegistry, PackageNotFound, TargetNotFound, PackageRequirementsNotFulfilled, NoPackageTargetsFound
from ._version import get_versions
from .deprecation import deprecated

__author__ = "Marcel Huber <marcel.huber@hsr.ch>"
__version__ = get_versions()['version']
__date__ = get_versions().get('date')
del get_versions

_base_path = os.path.dirname(__file__)
sys.path[:0] = [_base_path]

setup_logging(os.path.join(_base_path, 'logging.yaml'))
logger = getLogger(__name__)

SCons.Script.EnsureSConsVersion(2, 3, 0)
SCons.Script.EnsurePythonVersion(2, 6)

logger.info("SCons version %s", SCons.__version__)
_project_name = 'SConsider'
_project_version = __version__
try:
    sconsider_package_info = pkg_get_dist(_project_name)
    _project_name = sconsider_package_info.project_name
    _project_version = sconsider_package_info.version
except ResolutionError:
    pass
finally:
    logger.info("%s version %s (%s)", _project_name, _project_version,
                get_build_platform())


class Null(SCons.Util.Null):
    def __getitem__(self, key):
        return self

    def __contains__(self, key):
        return False


for platform_func in [platform.dist, platform.architecture, platform.machine,
                      platform.libc_ver, platform.release, platform.version,
                      platform.processor, platform.system, platform.uname]:
    func_value = platform_func()
    if func_value:
        logger.debug("platform.%s: %s", platform_func.__name__, func_value)

dEnv = DefaultEnvironment()

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
if GetOption('prependPath'):
    dEnv.PrependENVPath('PATH', GetOption('prependPath'))
    logger.debug('prepended path is [%s]', dEnv['ENV']['PATH'])
if GetOption('appendPath'):
    dEnv.AppendENVPath('PATH', GetOption('appendPath'))
    logger.debug('appended path is [%s]', dEnv['ENV']['PATH'])

globaltools = [
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

AddOption(
    '--usetool',
    dest='usetools',
    action='append',
    nargs=1,
    type='string',
    default=[],
    metavar='VAR',
    help='SCons tools to use for constructing the default environment. Default\
 tools are %s' % Flatten(globaltools))

# Keep order of tools in list but remove duplicates
option_tools = GetOption('usetools')
if option_tools is None:
    option_tools = []
usetools = OrderedDict.fromkeys(globaltools + DefaultEnvironment().get(
    '_SCONSIDER_TOOLS_', []) + option_tools).keys()
logger.debug('tools to use %s', Flatten(usetools))

# insert the site_tools path for our own tools
DefaultToolpath.insert(0, os.path.join(_base_path, 'site_tools'))
try:
    baseEnv = dEnv.Clone(tools=usetools)
except SCons.Errors.EnvironmentError as ex:
    for t in usetools:
        if t not in dEnv['TOOLS']:
            try:
                dEnv.Tool(t)
            except optparse.OptionConflictError:
                pass
            except SCons.Errors.EnvironmentError as ex:
                logger.error('loading Tool [%s] failed', t, exc_info=False)
                raise


def cloneBaseEnv():
    return baseEnv.Clone()


variant = baseEnv.getRelativeVariantDirectory()
logger.info('compilation variant [%s]', variant)

baseoutdir = baseEnv.getBaseOutDir()
logger.info('base output dir [%s]', baseoutdir.get_abspath())

ssfile = os.path.join(baseoutdir.get_abspath(), '.sconsign.' + variant)
SConsignFile(ssfile)

# FIXME: move to some link helper?
baseEnv.AppendUnique(LIBPATH=[baseEnv.getLibraryInstallDir()])

Callback().run('PrePackageCollection', env=baseEnv)
logger.debug("Exclude dirs rel: %s", baseEnv.relativeExcludeDirs())
logger.debug("Exclude dirs abs: %s", baseEnv.absoluteExcludeDirs())
logger.debug("Exclude dirs toplevel: %s", baseEnv.toplevelExcludeDirs())

_sconsider_toplevel_scandirs = [
    dirname for dirname in os.listdir(Dir('#').path)
    if os.path.isdir(dirname) and dirname not in baseEnv.toplevelExcludeDirs()
]
logger.debug("Toplevel dirs to scan for package files: %s",
             _sconsider_toplevel_scandirs)

logger.info("Collecting .sconsider packages ...")
packageRegistry = PackageRegistry(baseEnv, _sconsider_toplevel_scandirs,
                                  baseEnv.relativeExcludeDirs(),
                                  baseEnv.absoluteExcludeDirs())


@deprecated(
    "Use the static method splitFulltargetname of PackageRegistry instead.")
def splitTargetname(*args, **kwargs):
    return PackageRegistry.splitFulltargetname(*args, **kwargs)


@deprecated(
    "Use the static method createUniqueTargetname of PackageRegistry instead.")
def createUniqueTargetname(*args, **kwargs):
    return PackageRegistry.createUniqueTargetname(*args, **kwargs)


@deprecated(
    "Use the static method createFulltargetname of PackageRegistry instead.")
def generateFulltargetname(*args, **kwargs):
    return PackageRegistry.createFulltargetname(*args, **kwargs)

# Using LoadNode and extending the lookup_list has the advantage that SCons
# is looking for a matching Alias node when our own lookup returns no result.
baseEnv.AddMethod(PackageRegistry.loadNode, 'LoadNode')
baseEnv.lookup_list.insert(0, packageRegistry.lookup)

Callback().run('PostPackageCollection', env=baseEnv, registry=packageRegistry)


def createTargets(pkg_name, buildSettings):
    """Creates the targets for the package 'packagename' which are defined in
    'buildSettings'.

    This is a helper function which must be called from SConscript to
    create the targets.

    """
    packageRegistry.setBuildSettings(pkg_name, buildSettings)
    # do not create/build empty packages like the ones where Configure() fails
    if not buildSettings:
        return
    from SConsider.site_tools.TargetMaker import TargetMaker
    tmk = TargetMaker(pkg_name, buildSettings, packageRegistry)
    if not tmk.createTargets():
        return
    SCons.Script.Default(pkg_name)


logger.info("Loading packages and their targets ...")
# we need to define the targets before entering the build phase:
try:

    def tryLoadPackageTarget(pkg_name, tgt_name=None):
        try:
            if packageRegistry.loadPackageTarget(pkg_name, tgt_name) is None:
                # raising PackageNotFound aborts the implicit package loading
                # part and steps into loading all packages to find an alias
                raise PackageNotFound(packagename)
        except (PackageNotFound) as ex:
            # catch PackageNotFound separately as it is derived from
            # TargetNotFound
            raise
        except (TargetNotFound, NoPackageTargetsFound) as ex:
            ftn = PackageRegistry.createFulltargetname(pkg_name, tgt_name)
            if ftn in SCons.Script.BUILD_TARGETS:
                ex.message = 'explicit targetname [%s] has no targets' % ftn
                ex.lookupStack = []
                raise
            if int(GetOption('ignore-missing')) or GetOption('help'):
                logger.warning('%s', ex, exc_info=False)

    launchDir = Dir(SCons.Script.GetLaunchDir())
    dirfilter = lambda directory: True

    def namefilter(pkg_name):
        return dirfilter(packageRegistry.getPackageDir(pkg_name))

    if GetOption("climb_up") in [1, 3]:  # 1: -u, 3: -U
        if GetOption("climb_up") == 1:
            dirfilter = lambda directory: directory.is_under(launchDir)
        else:
            dirfilter = lambda directory: directory == launchDir

    try:
        buildtargets = SCons.Script.BUILD_TARGETS
        _LAUNCHDIR_RELATIVE = launchDir.path
        if not buildtargets:
            buildtargets = [item for item in packageRegistry.getPackageNames()
                            if namefilter(item)]
        elif '.' in buildtargets:
            builddir = baseoutdir.Dir(_LAUNCHDIR_RELATIVE).Dir(
                baseEnv.getRelativeBuildDirectory()).Dir(
                    baseEnv.getRelativeVariantDirectory()).get_abspath()
            buildtargets[buildtargets.index('.')] = builddir

        for ftname in buildtargets:
            packagename, targetname = PackageRegistry.splitFulltargetname(
                ftname)
            tryLoadPackageTarget(packagename, targetname)

    except PackageNotFound as ex:
        logger.warning(
            '%s, loading all packages to find potential alias target',
            ex,
            exc_info=False)

        buildtargets = [item for item in packageRegistry.getPackageNames()
                        if namefilter(item)]

        for packagename in buildtargets:
            try:
                baseEnv.LoadNode(packagename)
            except NoPackageTargetsFound as ex:
                if not GetOption('help'):
                    logger.warning('%s', ex, exc_info=False)
        logger.info(
            "Completed loading possible targets and aliases from %d available package files",
            len(buildtargets))

except (PackageNotFound, TargetNotFound, PackageRequirementsNotFulfilled) as ex:
    if not isinstance(ex, PackageRequirementsNotFulfilled):
        logger.error('%s', ex, exc_info=False)
    if not GetOption('help'):
        raise SCons.Errors.UserError('{0}, build aborted!'.format(ex))

# <!NOTE: buildTargets is passed by reference and might be extended
# in callback functions!
Callback().run("PreBuild",
               registry=packageRegistry,
               buildTargets=SCons.Script.BUILD_TARGETS)

logger.info('BUILD_TARGETS is %s',
            sorted([str(item) for item in SCons.Script.BUILD_TARGETS]))


def print_build_failures():
    if SCons.Script.GetBuildFailures():
        failednodes = ['scons: printing failed nodes']
        for failure_node in SCons.Script.GetBuildFailures():
            if str(failure_node.action) != "installFunc(target, source, env)":
                failednodes.append(str(failure_node.node))
        failednodes.append('scons: done printing failed nodes')
        logger.warning('\n'.join(failednodes))


atexit.register(print_build_failures)
