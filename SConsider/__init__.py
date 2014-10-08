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
import re
import atexit
import sys
import commands
import stat
import SCons
from SCons.Script import AddOption, GetOption, Dir, File, DefaultEnvironment,\
    Flatten, SConsignFile
from SomeUtils import *
from Callback import addCallbackFeature
from Logging import setup_logging
from logging import getLogger
from SCons.Tool import DefaultToolpath

__author__ = "Marcel Huber <marcel.huber@hsr.ch>"
__version__ = "0.3.3"

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

_baseout_dir_default = '#'

globaltools = [
    "setupBuildTools",
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
    '--baseoutdir',
    dest='baseoutdir',
    action='store',
    nargs=1,
    type='string',
    default=_baseout_dir_default,
    metavar='DIR',
    help='Directory to store build target files. Helps keeping your source\
 directory clean, default="' + Dir(_baseout_dir_default).abspath + '"')
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
AddOption(
    '--ignore-missing',
    dest='ignore-missing',
    action='store_true',
    help='Ignore missing dependencies instead of failing the build.')

baseoutdir = Dir(GetOption('baseoutdir'))
logger.info('base output dir [%s]', baseoutdir.abspath)
try:
    if not os.path.isdir(baseoutdir.abspath):
        os.makedirs(baseoutdir.abspath)
    # test if we are able to create a file
    testfile = os.path.join(baseoutdir.abspath, '.writefiletest')
    fp = open(testfile, 'w+')
    fp.close()
    os.remove(testfile)
except (os.error, IOError) as e:
    logger.error(
        'Output directory [%s] not writable',
        baseoutdir.abspath,
        exc_info=True)
    raise SCons.Errors.UserError(
        'Build aborted, baseoutdir [' +
        baseoutdir.abspath +
        '] not writable for us!')


def getUsedTarget(env, buildSettings):
    plaintarget = None
    usedFullTargetname = buildSettings.get('usedTarget', None)
    if usedFullTargetname:
        usedPackagename, usedTargetname = splitTargetname(
            usedFullTargetname, default=True)
        plaintarget = packageRegistry.loadPackagePlaintarget(
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

dEnv = DefaultEnvironment()

# @!FIXME: should use ProgramTest instead
dEnv.AddMethod(programTest, "AppTest")
dEnv.AddMethod(programTest, "ProgramTest")
dEnv.AddMethod(programApp, "ProgramApp")
dEnv.AddMethod(sharedLibrary, "LibraryShared")
dEnv.AddMethod(staticLibrary, "LibraryStatic")
dEnv.AddMethod(installPrecompiledBinary, "PrecompiledBinary")
dEnv.AddMethod(installBinary, "InstallBinary")

if GetOption('prependPath'):
    dEnv.PrependENVPath('PATH', GetOption('prependPath'))
    logger.debug('prepended path is [%s]', dEnv['ENV']['PATH'])
if GetOption('appendPath'):
    dEnv.AppendENVPath('PATH', GetOption('appendPath'))
    logger.debug('appended path is [%s]' % dEnv['ENV']['PATH'])

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
    import SomeUtils
    bitwidth = baseEnv.get('ARCHBITS', '32')
    libcver = SomeUtils.getLibCVersion(bitwidth)
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

logger.debug("compilation variant [%s]", variant)

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


class PackageNotFound(Exception):

    def __init__(self, package):
        self.package = package

    def __str__(self):
        return 'Package [{0}] not found'.format(self.package)


class PackageRequirementsNotFulfilled(Exception):

    def __init__(self, package, packagefile, message):
        self.package = package
        self.packagefile = packagefile
        self.message = message

    def __str__(self):
        return 'Package [{0}] not available (file {1}) '\
               'because of unsatisfied requirements: [{2}]'.format(
                   self.package,
                   self.packagefile,
                   self.message)


class PackageTargetNotFound(Exception):

    def __init__(self, target):
        self.target = target

    def __str__(self):
        return 'Target [{0}] not found'.format(self.target)


class PackageRegistry:

    def __init__(
            self,
            env,
            scan_dirs,
            scan_dirs_exclude_rel=[],
            scan_dirs_exclude_abs=[]):
        self.env = env
        self.packages = {}
        if not SCons.Util.is_List(scan_dirs):
            scan_dirs = [scan_dirs]
        for scandir in scan_dirs:
            self.collectPackages(
                scandir,
                scan_dirs_exclude_rel,
                scan_dirs_exclude_abs)

    def collectPackages(self, directory, excludes_rel=[], excludes_abs=[]):
        """Recursively collects SConsider packages.

        Walks recursively through 'directory' to collect package files
        but skipping dirs in 'excludes_rel' and absolute dirs
        from 'exclude_abs'.

        """
        rePackage = re.compile('^(.*).sconsider$')
        followlinks = False
        if sys.version_info[:2] >= (2, 6):
            followlinks = True
        for dirpath, dirnames, filenames in os.walk(directory,
                                                    followlinks=followlinks):
            thePath = os.path.abspath(dirpath)
            dirnames[:] = filter(
                lambda dirname: dirname not in excludes_rel and os.path.join(
                    thePath,
                    dirname) not in excludes_abs,
                dirnames)
            for name in filenames:
                rmatch = rePackage.match(name)
                if rmatch:
                    pkgname = rmatch.group(1)
                    logger.debug(
                        'found package [%s] in [%s]',
                        pkgname,
                        thePath)
                    self.setPackage(
                        pkgname,
                        Dir(thePath).File(name),
                        Dir(thePath))

    def setPackageTarget(self, packagename, targetname, plaintarget, target):
        if not self.hasPackage(packagename):
            logger.warning(
                'tried to register target [%s] for non existent package [%s]',
                targetname,
                packagename)
            return
        theTargets = self.packages[packagename].setdefault('targets', {})
        if plaintarget and SCons.Util.is_List(plaintarget):
            plaintarget = plaintarget[0]
        if target and SCons.Util.is_List(target):
            target = target[0]
        if not target:
            target = plaintarget
        theTargets[targetname] = {'plaintarget': plaintarget, 'target': target}

    def getPackageTargetTargets(self, packagename, targetname):
        if not self.hasPackage(packagename):
            logger.warning(
                'tried to access target [%s] of non existent package [%s]',
                targetname,
                packagename)
        return self.packages.get(
            packagename, {}).get(
                'targets', {}).get(
                    targetname, {
                        'plaintarget': None, 'target': None})

    def getPackageTarget(self, packagename, targetname):
        return self.getPackageTargetTargets(
            packagename,
            targetname).get(
                'target',
                None)

    def getPackagePlaintarget(self, packagename, targetname):
        return self.getPackageTargetTargets(
            packagename,
            targetname).get(
                'plaintarget',
                None)

    def getPackageDependencies(self, packagename):
        deps = dict()
        for targetname in self.getPackageTargetNames(packagename):
            deps[
                generateFulltargetname(
                    packagename,
                    targetname)] = self.getPackageTargetDependencies(
                        packagename,
                        targetname)
        return deps

    def getPackageTargetDependencies(self, packagename, targetname):
        targetBuildSettings = self.getBuildSettings(
            packagename).get(targetname, {})
        deps = dict()
        targetlist = targetBuildSettings.get('requires', [])
        targetlist.extend(targetBuildSettings.get('linkDependencies', []))
        targetlist.extend([targetBuildSettings.get('usedTarget', '')])
        for dep_fulltargetname in targetlist:
            if dep_fulltargetname:
                dep_packagename, dep_targetname = splitTargetname(
                    dep_fulltargetname)
                if not dep_targetname:
                    dep_targetname = dep_packagename
                deps[
                    generateFulltargetname(
                        dep_packagename,
                        dep_targetname)] = self.getPackageTargetDependencies(
                            dep_packagename,
                            dep_targetname)
        return deps

    def setPackage(
            self,
            packagename,
            packagefile,
            packagedir,
            duplicate=False):
        self.packages[packagename] = {
            'packagefile': packagefile,
            'packagedir': packagedir,
            'duplicate': duplicate}

    def hasPackage(self, packagename):
        """Check if packagename is found in list of packages.

        This solely relies on directories and <packagename>.sconscript
        files found

        """
        return packagename in self.packages

    def hasPackageTarget(self, packagename, targetname):
        return targetname in self.packages.get(
            packagename,
            {}).get(
            'targets',
            {})

    def isValidFulltargetname(self, fulltargetname):
        if self.hasPackage(str(fulltargetname)):
            return True
        packagename, targetname = splitTargetname(str(fulltargetname))
        return self.hasPackageTarget(packagename, targetname)

    def setPackageDir(self, packagename, dirname):
        if self.hasPackage(packagename):
            self.packages[packagename]['packagedir'] = dirname

    def getPackageDir(self, packagename):
        return self.packages.get(packagename, {}).get('packagedir', '')

    def getPackageFile(self, packagename):
        return self.packages.get(packagename, {}).get('packagefile', '')

    def getPackageDuplicate(self, packagename):
        return self.packages.get(packagename, {}).get('duplicate', False)

    def setPackageDuplicate(self, packagename, duplicate=True):
        if self.hasPackage(packagename):
            self.packages[packagename]['duplicate'] = duplicate

    def getPackageTargetNames(self, packagename):
        return self.packages.get(packagename, {}).get('targets', {}).keys()

    def getPackageNames(self):
        return self.packages.keys()

    def setBuildSettings(self, packagename, buildSettings):
        if self.hasPackage(packagename):
            self.packages[packagename]['buildsettings'] = buildSettings

    def hasBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return 'buildsettings' in self.packages.get(packagename, {})
        else:
            return targetname in self.packages.get(
                packagename,
                {}).get(
                'buildsettings',
                {})

    def getBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return self.packages.get(packagename, {}).get('buildsettings', {})
        else:
            return self.packages.get(
                packagename, {}).get(
                'buildsettings', {}).get(
                targetname, {})

    def loadPackage(self, packagename):
        if not self.hasPackage(packagename):
            raise PackageNotFound(packagename)
        self.lookup(packagename)

    def __loadPackageTarget(self, loadfunc, packagename, targetname):
        self.loadPackage(packagename)
        target = loadfunc(packagename, targetname)
        if not target:
            raise PackageTargetNotFound(
                generateFulltargetname(
                    packagename,
                    targetname))
        return target

    def loadPackageTarget(self, packagename, targetname):
        return self.__loadPackageTarget(
            self.getPackageTarget,
            packagename,
            targetname)

    def loadPackagePlaintarget(self, packagename, targetname):
        return self.__loadPackageTarget(
            self.getPackagePlaintarget,
            packagename,
            targetname)

    def isPackageLoaded(self, packagename):
        return 'loaded' in self.packages.get(packagename, {})

    def lookup(self, fulltargetname, **kw):
        packagename, targetname = splitTargetname(fulltargetname)
        logger.debug('looking up [%s]', fulltargetname)
        if self.hasPackage(packagename):
            if not self.isPackageLoaded(packagename):
                self.packages[packagename]['loaded'] = True
                packagedir = self.getPackageDir(packagename)
                packagefile = self.getPackageFile(packagename)
                builddir = self.env['BASEOUTDIR'].Dir(
                    packagedir.path).Dir(
                    self.env['BUILDDIR']).Dir(
                    self.env['VARIANTDIR'])
                logger.info(
                    'executing [%s] as SConscript for package [%s]',
                    packagefile.path,
                    packagename)
                try:
                    self.env.SConscript(
                        packagefile,
                        variant_dir=builddir,
                        duplicate=self.getPackageDuplicate(packagename),
                        exports=['packagename'])
                except ResolutionError as e:
                    raise PackageRequirementsNotFulfilled(
                        generateFulltargetname(
                            packagename,
                            targetname),
                        packagefile,
                        e)
            if targetname:
                return self.getPackageTarget(packagename, targetname)
        return None

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
runCallback('PrePackageCollection', env=baseEnv, directories=scanDirs)
logger.info("Collecting .sconsider packages ...")
packageRegistry = PackageRegistry(
    baseEnv,
    scanDirs,
    _exclude_dirs_rel,
    _exclude_dirs_abs)
logger.debug("calling PostPackageCollection callback")
runCallback('PostPackageCollection', env=baseEnv, registry=packageRegistry)


class TargetMaker:

    def __init__(self, packagename, tlist, registry):
        self.packagename = packagename
        self.targetlist = tlist.copy()
        self.registry = registry

    def createTargets(self):
        while self.targetlist:
            self.recurseCreate(self.targetlist.keys()[0])

    def recurseCreate(self, targetname):
        if self.targetlist:
            if targetname:
                k = targetname
                v = self.targetlist.pop(k)
            else:
                k, v = self.targetlist.popitem()
            depList = [
                item
                for item in v.get('requires', []) + v.get(
                    'linkDependencies', []) + [v.get('usedTarget', '')]
                if item.startswith(self.packagename + targetnameseparator)]
            for ftn in depList:
                pkgname, tname = splitTargetname(ftn)
                if self.packagename == pkgname and tname in self.targetlist:
                    self.recurseCreate(tname)
            self.doCreateTarget(self.packagename, k, v)

    def prepareFileNodeTuples(self, nodes, baseDir, alternativeDir=None):
        nodetuples = []
        for node in nodes:
            currentFile = node
            if isinstance(currentFile, str):
                currentFile = SCons.Script.File(currentFile)
            if hasattr(currentFile, 'srcnode'):
                currentFile = currentFile.srcnode()

            currentBaseDir = baseDir
            if hasattr(currentBaseDir, 'srcnode'):
                currentBaseDir = currentBaseDir.srcnode()

            if alternativeDir:
                # based on installRelPath and file, try to find an override
                # file to use instead
                fileWithRelpathToSearch = os.path.relpath(
                    currentFile.abspath,
                    currentBaseDir.abspath)
                # catch possible errors and stop when wanting to do relative
                # movements
                if not fileWithRelpathToSearch.startswith('..'):
                    fileToCheckFor = os.path.join(
                        alternativeDir.abspath,
                        fileWithRelpathToSearch)
                    if os.path.isfile(fileToCheckFor):
                        currentFile = File(fileToCheckFor)
                        currentBaseDir = alternativeDir

            nodetuples.append((currentFile, currentBaseDir))
        return nodetuples

    def copyIncludeFiles(self, env, pkgname, buildSettings):
        instTargets = []
        if 'public' in buildSettings:
            ifiles = buildSettings['public'].get('includes', [])
            destdir = env['BASEOUTDIR'].Dir(
                os.path.join(
                    env['INCDIR'],
                    pkgname))
            pkgdir = self.registry.getPackageDir(pkgname)
            stripRelDirs = []
            if buildSettings['public'].get('stripSubdir', True):
                stripRelDirs.append(
                    buildSettings['public'].get(
                        'includeSubdir',
                        ''))
            mode = None
            if str(env['PLATFORM']) not in ["cygwin", "win32"]:
                mode = stat.S_IREAD
                mode |= stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
            instTargets = copyFileNodes(
                env,
                self.prepareFileNodeTuples(
                    ifiles,
                    pkgdir),
                destdir,
                stripRelDirs=stripRelDirs,
                mode=mode)
        return instTargets

    def copyFiles(self, env, destdir, pkgname, copyFiles):
        instTargets = []

        pkgdir = self.registry.getPackageDir(pkgname)

        envconfigdir = env.get('__envconfigdir__', None)
        if envconfigdir:
            envconfigdir = envconfigdir.Dir(pkgname)

        for filetuple in copyFiles:
            if len(filetuple) == 3:
                files, mode, replaceDict = filetuple
            else:
                files, mode = filetuple
                replaceDict = {}
            if str(env['PLATFORM']) in ["cygwin", "win32"]:
                mode = None
            instTargets.extend(
                copyFileNodes(
                    env,
                    self.prepareFileNodeTuples(
                        files,
                        pkgdir,
                        envconfigdir),
                    destdir,
                    mode=mode,
                    replaceDict=replaceDict))

        return instTargets

    def requireTargets(self, env, target, requiredTargets, **kw):
        if not SCons.Util.is_List(requiredTargets):
            requiredTargets = [requiredTargets]
        for targ in requiredTargets:
            env.Depends(
                target,
                self.registry.loadPackageTarget(
                    *
                    splitTargetname(
                        targ,
                        default=True)))

    def doCreateTarget(self, packagename, targetname, targetBuildSettings):
        plaintarget = None
        target = None
        try:
            envVars = targetBuildSettings.get('appendUnique', {})
            targetEnv = self.createTargetEnv(
                targetname,
                targetBuildSettings,
                envVars)
            func = getattr(
                targetEnv,
                targetBuildSettings.get(
                    'targetType',
                    '__UNDEFINED_TARGETTYPE__'),
                None)
            if func:
                kw = {}
                kw['packagename'] = packagename
                kw['targetname'] = targetname
                kw['buildSettings'] = targetBuildSettings
                sources = targetBuildSettings.get('sourceFiles', [])
                name = targetBuildSettings.get(
                    'targetName',
                    createUniqueTargetname(
                        packagename,
                        targetname))
                targets = func(*[name, sources], **kw)
                if isinstance(targets, tuple):
                    plaintarget, target = targets
                else:
                    plaintarget = target = targets

            if plaintarget:
                targetEnv.Depends(
                    plaintarget,
                    self.registry.getPackageFile(packagename))
            else:
                # Actually includeOnlyTarget is obsolete, but we still need a
                # (dummy) targetType in build settings to get in here!
                # The following is a workaround, otherwise an alias won't get
                # built in newer SCons versions (because it has depends but no
                # sources)
                plaintarget = target = targetEnv.Alias(
                    packagename +
                    targetnameseparator +
                    targetname,
                    self.registry.getPackageFile(packagename))

            reqTargets = targetBuildSettings.get('linkDependencies', [])
            reqTargets.extend(targetBuildSettings.get('requires', []))
            self.requireTargets(targetEnv, target, reqTargets)

            includeTargets = self.copyIncludeFiles(
                targetEnv,
                packagename,
                targetBuildSettings)
            targetEnv.Depends(target, includeTargets)
            targetEnv.Alias('includes', includeTargets)

            if 'copyFiles' in targetBuildSettings:
                copyTargets = self.copyFiles(
                    targetEnv,
                    targetEnv['BASEOUTDIR'].Dir(targetEnv['RELTARGETDIR']),
                    packagename,
                    targetBuildSettings.get('copyFiles', []))
                targetEnv.Depends(target, copyTargets)

            targetEnv.Alias(packagename, target)
            targetEnv.Alias('all', target)
            if targetBuildSettings.get(
                    'runConfig',
                    {}).get(
                    'type',
                    '') == 'test':
                targetEnv.Alias('tests', target)

            runCallback(
                "PostCreateTarget",
                env=targetEnv,
                target=target,
                plaintarget=plaintarget,
                registry=self.registry,
                packagename=packagename,
                targetname=targetname,
                buildSettings=targetBuildSettings)

            self.registry.setPackageTarget(
                packagename,
                targetname,
                plaintarget,
                target)
        except (PackageNotFound, PackageTargetNotFound) as e:
            if not GetOption('ignore-missing'):
                raise
            logger.warning(
                '{0} (referenced by [{1}]), ignoring as requested'.format(
                    e,
                    generateFulltargetname(
                        packagename,
                        targetname)
                ),
                exc_info=False)

    def createTargetEnv(self, targetname, targetBuildSettings, envVars={}):
        # create environment for target
        targetEnv = cloneBaseEnv()

        # maybe we need to add this library's local include path when building
        # it (if different from .)
        includeSubdir = Dir(
            targetBuildSettings.get(
                'includeSubdir',
                '')).srcnode()
        includePublicSubdir = Dir(
            targetBuildSettings.get(
                'public',
                {}).get(
                'includeSubdir',
                '')).srcnode()
        include_dirs = includeSubdir.get_all_rdirs()
        include_dirs.extend(includePublicSubdir.get_all_rdirs())
        for incdir in include_dirs:
            targetEnv.AppendUnique(CPPPATH=[incdir])

        # update environment by adding dependencies to used modules
        linkDependencies = targetBuildSettings.get('linkDependencies', [])
        self.setModuleDependencies(targetEnv, linkDependencies)

        self.setExecEnv(
            targetEnv,
            linkDependencies +
            targetBuildSettings.get(
                'requires',
                []))

        targetVars = targetBuildSettings.get(
            'public',
            {}).get(
            'appendUnique',
            {})
        targetEnv.AppendUnique(**targetVars)

        targetEnv.AppendUnique(**envVars)

        return targetEnv

    def setModuleDependencies(self, env, modules, **kw):
        for fulltargetname in modules:
            packagename, targetname = splitTargetname(
                fulltargetname, default=True)
            plaintarget = self.registry.loadPackagePlaintarget(
                packagename,
                targetname)
            buildSettings = self.registry.getBuildSettings(
                packagename,
                targetname)
            self.setExternalDependencies(
                env,
                packagename,
                buildSettings,
                plaintarget=plaintarget,
                **kw)

    def setExecEnv(self, env, requiredTargets):
        for targ in requiredTargets:
            packagename, targetname = splitTargetname(targ, default=True)
            if self.registry.hasPackageTarget(packagename, targetname):
                settings = self.registry.getBuildSettings(
                    packagename,
                    targetname)
                target = self.registry.getPackagePlaintarget(
                    packagename,
                    targetname)
                public_execenv = settings.get('public', {}).get('execEnv', {})
                for key, value in public_execenv.iteritems():
                    env['ENV'][key] = target.env.subst(value)
                reqTargets = settings.get(
                    'linkDependencies', []) + settings.get('requires', [])
                self.setExecEnv(env, reqTargets)

    def setExternalDependencies(
            self,
            env,
            packagename,
            buildSettings,
            plaintarget=None,
            **kw):
        linkDependencies = buildSettings.get('linkDependencies', [])
        if 'public' in buildSettings:
            appendUnique = buildSettings['public'].get('appendUnique', {})
            # flags / settings used by this library and users of it
            env.AppendUnique(**appendUnique)

            includePublicSubdir = buildSettings[
                'public'].get('includeSubdir', '')
            if SCons.Util.is_String(includePublicSubdir):
                includePublicSubdir = self.registry.getPackageDir(
                    packagename).Dir(includePublicSubdir)

            for incdir in includePublicSubdir.get_all_rdirs():
                env.AppendUnique(CPPPATH=[incdir])

        # this libraries dependencies
        self.setModuleDependencies(env, linkDependencies)

        if plaintarget:
            # try block needed to block Alias only targets without concrete
            # builder
            try:
                strTargetType = plaintarget.builder.get_name(plaintarget.env)
                if strTargetType.find('Library') != -1:
                    libname = multiple_replace([
                        ('^' + re.escape(env.subst("$LIBPREFIX")), ''),
                        (re.escape(env.subst("$LIBSUFFIX")) + '$', ''),
                        ('^' + re.escape(env.subst("$SHLIBPREFIX")), ''),
                        (re.escape(env.subst("$SHLIBSUFFIX")) + '$', ''),
                    ], plaintarget.name)
                    env.AppendUnique(LIBS=[libname])
            except:
                pass


def createTargets(packagename, buildSettings):
    """Creates the targets for the package 'packagename' which are defined in
    'buildSettings'.

    This is a helper function which must be called from SConscript to
    create the targets.

    """
    packageRegistry.setBuildSettings(packagename, buildSettings)
    tmk = TargetMaker(packagename, buildSettings, packageRegistry)
    tmk.createTargets()
    SCons.Script.Default(packagename)
    runCallback(
        "PostCreatePackageTargets",
        registry=packageRegistry,
        packagename=packagename,
        buildSettings=buildSettings)

baseEnv.lookup_list.append(packageRegistry.lookup)

logger.info("Loading packages and their targets ...")
# we need to define the targets before entering the build phase:
try:
    def tryLoadPackage(packagename, targetname=None):
        try:
            packageRegistry.loadPackage(packagename)
        except ResolutionError as e:
            if not GetOption('ignore-missing'):
                raise
            logger.warning(
                'ignoring target [{0}]'
                ' because of missing requirements [{1}]'.format(
                    generateFulltargetname(
                        packagename,
                        targetname),
                    e.message),
                exc_info=False)

    try:
        buildtargets = SCons.Script.BUILD_TARGETS
        if not buildtargets:
            if GetOption("climb_up") in [1, 3]:  # 1: -u, 3: -U
                launchDir = Dir(SCons.Script.GetLaunchDir())
                if GetOption("climb_up") == 1:
                    dirfilter = lambda directory: directory.is_under(launchDir)
                else:
                    dirfilter = lambda directory: directory == launchDir

                def namefilter(packagename):
                    return dirfilter(
                        packageRegistry.getPackageDir(packagename))

                buildtargets = filter(
                    namefilter,
                    packageRegistry.getPackageNames())
            else:
                buildtargets = packageRegistry.getPackageNames()

        for ftname in buildtargets:
            packagename, targetname = splitTargetname(ftname)
            tryLoadPackage(packagename, targetname)

    except PackageNotFound as e:
        logger.warning(
            '{0}, loading all packages to find potential alias target'.format(
                e),
            exc_info=False)
        for packagename in packageRegistry.getPackageNames():
            tryLoadPackage(packagename)

except (PackageNotFound, PackageTargetNotFound, PackageRequirementsNotFulfilled) as e:
    if not isinstance(e, PackageRequirementsNotFulfilled):
        logger.error('{0}'.format(e), exc_info=True)
    if not GetOption('help'):
        raise SCons.Errors.UserError(
            '{0}, build aborted!'.format(e))

runCallback(
    "PreBuild",
    registry=packageRegistry,
    buildTargets=SCons.Script.BUILD_TARGETS)

logger.info("BUILD_TARGETS is %s", map(str, SCons.Script.BUILD_TARGETS))


def print_build_failures():
    if SCons.Script.GetBuildFailures():
        failednodes = ['scons: printing failed nodes']
        for bf in SCons.Script.GetBuildFailures():
            if str(bf.action) != "installFunc(target, source, env)":
                failednodes.append(str(bf.node))
        failednodes.append('scons: done printing failed nodes')
        logger.warning('\n'.join(failednodes))

atexit.register(print_build_failures)
