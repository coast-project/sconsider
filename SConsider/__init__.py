"""SConsider.

SCons build tool extension allowing automatic target finding within a
directoy tree.

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
from __future__ import with_statement
import os
import platform
import atexit
import sys
import commands
import SCons
from SCons.Script import AddOption, GetOption, Dir, DefaultEnvironment,\
    Flatten, SConsignFile
from SomeUtils import getLibCVersion, listFiles, findFiles, removeFiles,\
    getfqdn
from Callback import addCallbackFeature
from Logging import setup_logging
from logging import getLogger
from SCons.Tool import DefaultToolpath

__author__ = "Marcel Huber <marcel.huber@hsr.ch>"
__version__ = "0.3.5"

_base_path = os.path.dirname(__file__)
sys.path[:0] = [_base_path]

setup_logging(os.path.join(_base_path, 'logging.yaml'))
logger = getLogger(__name__)

addCallbackFeature(__name__)

SCons.Script.EnsureSConsVersion(1, 3, 0)
SCons.Script.EnsurePythonVersion(2, 6)

from pkg_resources import get_distribution as pkg_get_dist,\
    get_build_platform, ResolutionError

try:
    sconsider_package_info = pkg_get_dist('sconsider')
    logger.info("{0} version {1} ({2})".format(
        sconsider_package_info.project_name,
        sconsider_package_info.version,
        get_build_platform()))
except ResolutionError:
    pass

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

_baseout_dir_default = '#'

globaltools = [
    "setupBuildTools",
    "TargetHelpers",
    "TargetMaker",
    "coast_options",
    "TargetPrinter",
    "precompiledLibraryInstallBuilder",
    "RunBuilder",
    "DoxygenBuilder",
    "SystemLibsInstallBuilder",
    "Package",
    "SubstInFileBuilder",
    "ThirdParty"]

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

usetools = globaltools + GetOption('usetools')
logger.debug('tools in use %s', Flatten(usetools))

# insert the site_tools path for our own tools
DefaultToolpath.insert(
    0,
    os.path.join(
        _base_path,
        'site_tools'))
baseEnv = dEnv.Clone(tools=usetools)

variant = "Unknown-"
myplatf = str(SCons.Platform.Platform())

if myplatf == "posix":
    bitwidth = baseEnv.get('ARCHBITS', '32')
    libcver = getLibCVersion(bitwidth)
    variant = platform.system(
    ) + "_" + libcver[0] + "_" + libcver[1] + "-" + platform.machine()
elif myplatf == "sunos":
    variant = platform.system(
    ) + "_" + platform.release() + "-" + platform.processor()
elif myplatf == "darwin":
    version = commands.getoutput("sw_vers -productVersion")
    cpu = commands.getoutput("arch")
    if version.startswith("10.7"):
        variant = "lion-"
    elif version.startswith("10.6"):
        variant = "snowleopard-"
    elif version.startswith("10.5"):
        variant = "leopard-"
    elif version.startswith("10.4"):
        variant = "tiger-"
    variant += cpu
elif myplatf == "cygwin":
    variant = platform.system() + "-" + platform.machine()
elif myplatf == "win32":
    variant = platform.system(
    ) + "_" + platform.release() + "-" + platform.machine()
    baseEnv.Append(WINDOWS_INSERT_DEF=1)

variant += ''.join(baseEnv.get('VARIANT_SUFFIX', []))

logger.info('compilation variant [{0}]'.format(variant))

AddOption(
    '--baseoutdir',
    dest='baseoutdir',
    action='store',
    nargs=1,
    type='string',
    default=_baseout_dir_default,
    metavar='DIR',
    help='Directory to store build target files. Helps keeping your source\
 directory clean, default="' + Dir(_baseout_dir_default).abspath + '"')

baseoutdir = Dir(GetOption('baseoutdir'))
logger.info('base output dir [{0}]'.format(baseoutdir.abspath))

testfile = os.path.join(baseoutdir.abspath, '.writefiletest')
try:
    if not os.path.isdir(baseoutdir.abspath):
        os.makedirs(baseoutdir.abspath)
    # test if we are able to create a file
    fp = open(testfile, 'w+')
    fp.close()
except (os.error, IOError) as e:
    logger.error(
        'Output directory [{0}] not writable'.format(
            baseoutdir.abspath),
        exc_info=True)
    raise SCons.Errors.UserError(
        'Build aborted, baseoutdir [' +
        baseoutdir.abspath +
        '] not writable for us!')
finally:
    os.unlink(testfile)

ssfile = os.path.join(baseoutdir.abspath, '.sconsign.' + variant)
SConsignFile(ssfile)

#########################
#  Project Environment  #
#########################
baseEnv.Append(BASEOUTDIR=baseoutdir)
baseEnv.Append(VARIANTDIR=variant)

baseEnv.Append(INCDIR='include')
baseEnv.Append(LOGDIR='log')
baseEnv.Append(BINDIR='bin')
baseEnv.Append(LIBDIR='lib')
baseEnv.Append(SCRIPTDIR='scripts')
baseEnv.Append(CONFIGDIR='config')
baseEnv.Append(DOCDIR='doc')
baseEnv.Append(BUILDDIR='.build')

# directory relative to BASEOUTDIR where we are going to install target
# specific files mainly used to rebase/group test or app specific target files
baseEnv.Append(RELTARGETDIR='')
baseEnv.AppendUnique(
    LIBPATH=[
        baseoutdir.Dir(
            baseEnv['LIBDIR']).Dir(
                baseEnv['VARIANTDIR'])])


def cloneBaseEnv():
    return baseEnv.Clone()

AddOption(
    '--exclude',
    dest='exclude',
    action='append',
    nargs=1,
    type='string',
    default=[],
    metavar='DIR',
    help='Ignore sconsider files within this directory and its\
 subdirectories.')

_exclude_dirs_rel = ['CVS', '.git', '.svn']
_exclude_dirs_toplevel = _exclude_dirs_rel + ['.sconf_temp']
if baseoutdir == Dir('#'):
    _exclude_dirs_toplevel += [baseEnv[varname] for varname in ['BUILDDIR',
                                                                'BINDIR',
                                                                'LIBDIR',
                                                                'LOGDIR',
                                                                'CONFIGDIR']]
_exclude_dirs_abs = []
for exclude_path in baseEnv.GetOption('exclude'):
    absolute_path = exclude_path
    if not os.path.isabs(exclude_path):
        absolute_path = Dir(exclude_path).abspath
    else:
        exclude_path = os.path.relpath(exclude_path, Dir('#').abspath)
    if not exclude_path.startswith('..'):
        first_segment = exclude_path.split(os.pathsep)[0]
        _exclude_dirs_toplevel.append(first_segment)
    _exclude_dirs_abs.append(absolute_path)

scanDirs = filter(
    lambda
    dirname: os.path.isdir(dirname)
    and dirname not in _exclude_dirs_toplevel, os.listdir(
        Dir('#').path))
logger.debug("Toplevel dirs to scan for package files: {0}".format(scanDirs))

logger.debug("calling PrePackageCollection callback")
runCallback(
    'PrePackageCollection',
    env=baseEnv,
    directories=scanDirs)

logger.info("Collecting .sconsider packages ...")
import PackageRegistry
from PackageRegistry import targetnameseparator,\
    splitTargetname, createUniqueTargetname, generateFulltargetname
packageRegistry = PackageRegistry.PackageRegistry(
    baseEnv,
    scanDirs,
    _exclude_dirs_rel,
    _exclude_dirs_abs)


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
    def tryLoadPackage(packagename, targetname=None):
        try:
            packageRegistry.loadPackage(packagename)
        except (ResolutionError, PackageRegistry.PackageTargetNotFound) as e:
            if not GetOption('ignore-missing'):
                raise
            logger.warning(
                'ignoring target [{0}]'
                ' because of missing requirements [{1}]'.format(
                    PackageRegistry.generateFulltargetname(
                        packagename,
                        targetname),
                    e.message),
                exc_info=False)

    if GetOption("climb_up") in [1, 3]:  # 1: -u, 3: -U
        if GetOption("climb_up") == 1:
            dirfilter = lambda directory: directory.is_under(launchDir)
        else:
            dirfilter = lambda directory: directory == launchDir

        def namefilter(packagename):
            return dirfilter(
                packageRegistry.getPackageDir(packagename))

    try:
        buildtargets = SCons.Script.BUILD_TARGETS
        launchDir = Dir(SCons.Script.GetLaunchDir())
        _launchdir_relative = launchDir.path
        if not buildtargets:
            buildtargets = filter(
                namefilter,
                packageRegistry.getPackageNames())
        elif '.' in buildtargets:
            builddir = baseoutdir.Dir(_launchdir_relative).Dir(
                baseEnv['BUILDDIR']).Dir(baseEnv['VARIANTDIR']).abspath
            buildtargets[buildtargets.index('.')] = builddir

        for ftname in buildtargets:
            packagename, targetname = PackageRegistry.splitTargetname(ftname)
            tryLoadPackage(packagename, targetname)

    except PackageRegistry.PackageNotFound as e:
        logger.warning(
            '{0}, loading all packages to find potential alias target'.format(
                e),
            exc_info=False)

        buildtargets = filter(
            namefilter,
            packageRegistry.getPackageNames())

        for packagename in buildtargets:
            tryLoadPackage(packagename)

except (PackageRegistry.PackageNotFound, PackageRegistry.PackageTargetNotFound, PackageRegistry.PackageRequirementsNotFulfilled) as e:
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
