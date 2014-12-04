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
import SCons
from SCons.Script import AddOption, GetOption, Dir, File, DefaultEnvironment,\
    Flatten, SConsignFile
from SomeUtils import listFiles, findFiles, removeFiles,\
    getfqdn
from Callback import addCallbackFeature
from Logging import setup_logging
from logging import getLogger
from SCons.Tool import DefaultToolpath

__author__ = "Marcel Huber <marcel.huber@hsr.ch>"
__version__ = "0.3.9"

_base_path = os.path.dirname(__file__)
sys.path[:0] = [_base_path]

setup_logging(os.path.join(_base_path, 'logging.yaml'))
logger = getLogger(__name__)

"""add callback feature early as it might be used from tools"""
addCallbackFeature(__name__)

SCons.Script.EnsureSConsVersion(1, 3, 0)
SCons.Script.EnsurePythonVersion(2, 6)

from pkg_resources import get_distribution as pkg_get_dist,\
    get_build_platform, ResolutionError

_project_name = 'SConsider'
_project_version = __version__
try:
    sconsider_package_info = pkg_get_dist(_project_name)
    _project_name = sconsider_package_info.project_name
    _project_version = sconsider_package_info.version
except ResolutionError:
    pass
finally:
    logger.info("{0} version {1} ({2})".format(
        _project_name,
        _project_version,
        get_build_platform()))


class Null(SCons.Util.Null):

    def __getitem__(self, key):
        return self

    def __contains__(self, key):
        return False

for platform_func in [platform.dist,
                      platform.architecture,
                      platform.machine,
                      platform.libc_ver,
                      platform.release,
                      platform.version,
                      platform.processor,
                      platform.system,
                      platform.uname]:
    func_value = platform_func()
    if func_value:
        logger.debug("platform.%s: %s", platform_func.__name__, func_value)

dEnv = DefaultEnvironment()

AddOption(
    '--appendPath',
    dest='appendPath',
    action='append',
    nargs=1,
    type='string',
    metavar='DIR',
    help='Append this directory to the PATH environment variable.')
AddOption(
    '--prependPath',
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
    logger.debug('appended path is [%s]' % dEnv['ENV']['PATH'])


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

try:
    from collections import OrderedDict
except:
    # support python < 2.7
    from ordereddict import OrderedDict

"""Keep order of tools in list but remove duplicates"""
usetools = OrderedDict.fromkeys(
    globaltools +
    DefaultEnvironment().get('_SCONSIDER_TOOLS_', []) +
    GetOption('usetools')).keys()
logger.debug('tools to use %s', Flatten(usetools))

# insert the site_tools path for our own tools
DefaultToolpath.insert(
    0,
    os.path.join(
        _base_path,
        'site_tools'))
baseEnv = dEnv.Clone(tools=usetools)


def cloneBaseEnv():
    return baseEnv.Clone()


variant = baseEnv.getRelativeVariantDirectory()
logger.info('compilation variant [{0}]'.format(variant))

baseoutdir = baseEnv.getBaseOutDir()
logger.info('base output dir [{0}]'.format(baseoutdir.get_abspath()))

ssfile = os.path.join(baseoutdir.get_abspath(), '.sconsign.' + variant)
SConsignFile(ssfile)

# FIXME: move to some link helper?
baseEnv.AppendUnique(LIBPATH=[baseEnv.getLibraryInstallDir()])

logger.debug("calling PrePackageCollection callback")
runCallback(
    'PrePackageCollection',
    env=baseEnv
)
logger.debug("Exclude dirs rel: {0}".format(baseEnv.relativeExcludeDirs()))
logger.debug("Exclude dirs abs: {0}".format(baseEnv.absoluteExcludeDirs()))
logger.debug(
    "Exclude dirs toplevel: {0}".format(
        baseEnv.toplevelExcludeDirs()))

_sconsider_toplevel_scandirs = filter(
    lambda dirname: os.path.isdir(dirname)
        and dirname not in baseEnv.toplevelExcludeDirs(),
    os.listdir(Dir('#').path))
logger.debug(
    "Toplevel dirs to scan for package files: {0}".format(
        _sconsider_toplevel_scandirs))

logger.info("Collecting .sconsider packages ...")
import PackageRegistry
from PackageRegistry import targetnameseparator,\
    splitTargetname, createUniqueTargetname, generateFulltargetname
packageRegistry = PackageRegistry.PackageRegistry(
    baseEnv,
    _sconsider_toplevel_scandirs,
    baseEnv.relativeExcludeDirs(),
    baseEnv.absoluteExcludeDirs())


def getRegistry():
    return packageRegistry


baseEnv.lookup_list.append(packageRegistry.lookup)

logger.debug("calling PostPackageCollection callback")
runCallback(
    'PostPackageCollection',
    env=baseEnv,
    registry=packageRegistry)


def createTargets(packagename, buildSettings):
    """Creates the targets for the package 'packagename' which are defined in
    'buildSettings'.

    This is a helper function which must be called from SConscript to
    create the targets.

    """
    packageRegistry.setBuildSettings(packagename, buildSettings)
    # do not create/build empty packages like the ones where Configure() fails
    if not buildSettings:
        return
    from TargetMaker import TargetMaker
    tmk = TargetMaker(packagename, buildSettings, packageRegistry)
    if not tmk.createTargets():
        return
    SCons.Script.Default(packagename)
    runCallback(
        "PostCreatePackageTargets",
        registry=packageRegistry,
        packagename=packagename,
        buildSettings=buildSettings)

logger.info("Loading packages and their targets ...")
# we need to define the targets before entering the build phase:
try:
    def tryLoadPackageTarget(packagename, targetname=None):
        try:
            packageRegistry.loadPackageTarget(packagename, targetname)
        except (PackageRegistry.PackageNotFound) as e:
            # catch PackageNotFound separately as we are derived
            #  from TargetNotFound
            raise
        except PackageRegistry.TargetNotFound as e:
            if not GetOption('ignore-missing'):
                raise
            logger.warning(
                '{0}'.format(e),
                exc_info=False)

    launchDir = Dir(SCons.Script.GetLaunchDir())
    dirfilter = lambda directory: True
    def namefilter(packagename):
        return dirfilter(
            packageRegistry.getPackageDir(packagename))

    if GetOption("climb_up") in [1, 3]:  # 1: -u, 3: -U
        if GetOption("climb_up") == 1:
            dirfilter = lambda directory: directory.is_under(launchDir)
        else:
            dirfilter = lambda directory: directory == launchDir

    try:
        buildtargets = SCons.Script.BUILD_TARGETS
        _launchdir_relative = launchDir.path
        if not buildtargets:
            buildtargets = filter(
                namefilter,
                packageRegistry.getPackageNames())
        elif '.' in buildtargets:
            builddir = baseoutdir.Dir(_launchdir_relative).Dir(
                baseEnv.getRelativeBuildDirectory()).Dir(
                baseEnv.getRelativeVariantDirectory()).get_abspath()
            buildtargets[buildtargets.index('.')] = builddir

        for ftname in buildtargets:
            packagename, targetname = PackageRegistry.splitTargetname(ftname)
            tryLoadPackageTarget(packagename, targetname)

    except PackageRegistry.PackageNotFound as e:
        logger.warning(
            '{0}, loading all packages to find potential alias target'.format(
                e),
            exc_info=False)

        buildtargets = filter(
            namefilter,
            packageRegistry.getPackageNames())

        for packagename in buildtargets:
            packageRegistry.loadPackage(packagename)

except (PackageRegistry.PackageNotFound, PackageRegistry.TargetNotFound, PackageRegistry.PackageRequirementsNotFulfilled) as e:
    if not isinstance(e, PackageRegistry.PackageRequirementsNotFulfilled):
        logger.error('{0}'.format(e), exc_info=True)
    if not GetOption('help'):
        raise SCons.Errors.UserError(
            '{0}, build aborted!'.format(e))

runCallback(
    "PreBuild",
    registry=packageRegistry,
    buildTargets=SCons.Script.BUILD_TARGETS)

logger.info('BUILD_TARGETS is {0}'.format(
    map(str, SCons.Script.BUILD_TARGETS)))


def print_build_failures():
    if SCons.Script.GetBuildFailures():
        failednodes = ['scons: printing failed nodes']
        for bf in SCons.Script.GetBuildFailures():
            if str(bf.action) != "installFunc(target, source, env)":
                failednodes.append(str(bf.node))
        failednodes.append('scons: done printing failed nodes')
        logger.warning('\n'.join(failednodes))

atexit.register(print_build_failures)
