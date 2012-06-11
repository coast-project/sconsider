"""site_scons.SConsider

SCons build tool extension allowing automatic target finding within a directoy tree.

"""
#-----------------------------------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or modify it under the terms of
# the license that is included with this library/application in the file license.txt.
#-----------------------------------------------------------------------------------------------------
from __future__ import with_statement
import os, platform, SCons, glob, re, atexit, sys, traceback, commands, dircache, stat
import SomeUtils

from SCons.Script import AddOption, GetOption, Dir, File, DefaultEnvironment, Split, Flatten, SConsignFile
from SomeUtils import *
from ConfigureHelper import *

SCons.Script.EnsureSConsVersion(1, 3, 0)
SCons.Script.EnsurePythonVersion(2, 6)

import Callback
Callback.addCallbackFeature(__name__)

if False:
    print "platform.dist:", platform.dist()
    print "platform.arch:", platform.architecture()
    print "platform.machine:", platform.machine()
    print "platform.libc:", platform.libc_ver()
    print "platform.release:", platform.release()
    print "platform.version:", platform.version()
    print "platform.proc:", platform.processor()
    print "platform.system:", platform.system()
    print "platform.uname:", platform.uname()

AddOption('--baseoutdir', dest='baseoutdir', action='store', nargs=1, type='string', default='#', metavar='DIR', help='Directory containing packages superseding installed ones. Relative paths not supported!')
AddOption('--exclude', dest='exclude', action='append', nargs=1, type='string', default=[], metavar='DIR', help='Directory containing a SConscript file that should be ignored.')
AddOption('--usetool', dest='usetools', action='append', nargs=1, type='string', default=[], metavar='VAR', help='tools to use when constructing default environment')
AddOption('--appendPath', dest='appendPath', action='append', nargs=1, type='string', metavar='DIR', help='Directory to append to PATH environment variable.')
AddOption('--prependPath', dest='prependPath', action='append', nargs=1, type='string', metavar='DIR', help='Directory to prepend to PATH environment variable.')
AddOption('--ignore-missing', dest='ignore-missing', action='store_true', help='Ignore missing dependencies instead of failing the whole build.')

baseoutdir = Dir(GetOption('baseoutdir'))
print 'base output dir [%s]' % baseoutdir.abspath
try:
    if not os.path.isdir(baseoutdir.abspath):
        os.makedirs(baseoutdir.abspath)
    # test if we are able to create a file
    testfile=os.path.join(baseoutdir.abspath,'.writefiletest')
    fp = open(testfile,'w+')
    fp.close()
except (os.error, IOError) as e:
    print e
    raise SCons.Errors.UserError('Build aborted, baseoutdir [' + baseoutdir.abspath + '] not writable for us!')

def changed_timestamp_or_content(dependency, target, prev_ni):
    return dependency.changed_content(target, prev_ni) or dependency.changed_timestamp_newer(target, prev_ni)

def getUsedTarget(env, buildSettings):
    plaintarget = None
    usedFullTargetname = buildSettings.get('usedTarget', None)
    if usedFullTargetname:
        usedPackagename, usedTargetname = splitTargetname(usedFullTargetname, default=True)
        plaintarget = packageRegistry.loadPackagePlaintarget(usedPackagename, usedTargetname)
    return plaintarget

def usedOrProgramTarget(env, name, sources, buildSettings):
    plaintarget = getUsedTarget(env, buildSettings)
    if not plaintarget:
        # env.File is a workaround, otherwise if an Alias with the same 'name' is defined
        # arg2nodes (called from all builders) would return the Alias, but we would need a file node
        plaintarget = env.Program(env.File(name), sources)

    return plaintarget

def setupTargetDirAndWrapperScripts(env, name, packagename, plaintarget, basetargetdir):
    baseoutdir = env['BASEOUTDIR']
    env['RELTARGETDIR'] = os.path.join(basetargetdir, packagename)
    instApps = env.InstallAs(baseoutdir.Dir(env['RELTARGETDIR']).Dir(env['BINDIR']).Dir(env['VARIANTDIR']).File(name), plaintarget)
    env.Tool('generateScript')
    wrappers = env.GenerateWrapperScript(instApps)
    return (plaintarget, wrappers)

def programApp(env, name, sources, packagename, buildSettings, **kw):
    plaintarget = usedOrProgramTarget(env, name, sources, buildSettings)
    plaintarget, wrappers = setupTargetDirAndWrapperScripts(env, name, packagename, plaintarget, 'apps')
    buildSettings.setdefault("runConfig", {}).setdefault("type", "run")
    env.Alias('binaries', wrappers)
    return (plaintarget, wrappers)

def programTest(env, name, sources, packagename, targetname, buildSettings, **kw):
    plaintarget = usedOrProgramTarget(env, name, sources, buildSettings)
    buildSettings.setdefault("runConfig", {}).setdefault("type", "test")
    return setupTargetDirAndWrapperScripts(env, name, packagename, plaintarget, 'tests')

def sharedLibrary(env, name, sources, packagename, targetname, buildSettings, **kw):
    libBuilder = env.SharedLibrary
    #DIXME: we should move this section out to the libraries needing it
    if buildSettings.get('lazylinking', False):
        env['_NONLAZYLINKFLAGS'] = ''
        if env["PLATFORM"] == "win32":
            libBuilder = env.StaticLibrary

    plaintarget = libBuilder(name, sources)

    baseoutdir = env['BASEOUTDIR']
    instTarg = env.Install(baseoutdir.Dir(env['LIBDIR']).Dir(env['VARIANTDIR']), plaintarget)
    env.Requires(instTarg[0], instTarg[1:])

    compLibs = env.InstallSystemLibs(plaintarget)
    env.Requires(instTarg[0], compLibs) # the first target should be the library

    return (plaintarget, instTarg)

def staticLibrary(env, name, sources, packagename, targetname, buildSettings, **kw):
    env['_NONLAZYLINKFLAGS'] = ''

    plaintarget = env.StaticLibrary(name, sources)

    baseoutdir = env['BASEOUTDIR']
    instTarg = env.Install(baseoutdir.Dir(env['LIBDIR']).Dir(env['VARIANTDIR']), plaintarget)
    env.Requires(instTarg[0], instTarg[1:])

    compLibs = env.InstallSystemLibs(plaintarget)
    env.Requires(instTarg[0], compLibs)

    return (plaintarget, instTarg)

def installPrecompiledBinary(env, name, sources, packagename, targetname, buildSettings, **kw):
    env['RELTARGETDIR'] = os.path.join('globals', packagename)
    plaintarget = env.PrecompiledBinaryInstallBuilder(name, sources)

    return (plaintarget, plaintarget)

def installBinary(env, name, sources, packagename, targetname, buildSettings, **kw):
    env['RELTARGETDIR'] = os.path.join('globals', packagename)
    installDir = env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['BINDIR']).Dir(env['VARIANTDIR'])
    instTarg = env.Install(installDir, sources)
    env.Requires(instTarg[0], instTarg[1:])

    return (instTarg, instTarg)

dEnv = DefaultEnvironment()

dEnv.AddMethod(programTest, "AppTest")	#@!FIXME: should use ProgramTest instead
dEnv.AddMethod(programTest, "ProgramTest")
dEnv.AddMethod(programApp, "ProgramApp")
dEnv.AddMethod(sharedLibrary, "LibraryShared")
dEnv.AddMethod(staticLibrary, "LibraryStatic")
dEnv.AddMethod(installPrecompiledBinary, "PrecompiledBinary")
dEnv.AddMethod(installBinary, "InstallBinary")

if GetOption('prependPath'):
    dEnv.PrependENVPath('PATH', GetOption('prependPath'))
    print 'prepended path is [%s]' % dEnv['ENV']['PATH']
if GetOption('appendPath'):
    dEnv.AppendENVPath('PATH', GetOption('appendPath'))
    print 'appended path is [%s]' % dEnv['ENV']['PATH']

globaltools = ["setupBuildTools", "coast_options", "TargetPrinter",
               "precompiledLibraryInstallBuilder", "RunBuilder", "DoxygenBuilder",
               "SystemLibsInstallBuilder", "Package", "SubstInFileBuilder", "ThirdParty"]
usetools = globaltools + GetOption('usetools')
print 'tools to use %s' % Flatten(usetools)

baseEnv = dEnv.Clone(tools=usetools)

variant = "Unknown-"
myplatf = str(SCons.Platform.Platform())

if myplatf == "posix":
    import SomeUtils
    bitwidth = baseEnv.get('ARCHBITS', '32')
    libcver=SomeUtils.getLibCVersion(bitwidth)
    variant = platform.system() + "_" + libcver[0] + "_" + libcver[1] + "-" + platform.machine()
elif myplatf == "sunos":
    variant = platform.system() + "_" + platform.release() + "-" + platform.processor()
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
    variant = platform.system() + "_" + platform.release() + "-" + platform.machine()
    baseEnv.Append(WINDOWS_INSERT_DEF=1)

variant += ''.join(baseEnv.get('VARIANT_SUFFIX', []))

print "compilation variant [", variant, "]"

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

# directory relative to BASEOUTDIR where we are going to install target specific files
# mainly used to rebase/group test or app specific target files
baseEnv.Append(RELTARGETDIR='')
baseEnv.AppendUnique(LIBPATH=[baseoutdir.Dir(baseEnv['LIBDIR']).Dir(baseEnv['VARIANTDIR'])])

def cloneBaseEnv():
    return baseEnv.Clone()

class PackageNotFound(Exception):
    def __init__(self, package):
        self.package = package
    def __str__(self):
        return 'Package [{0}] not found'.format(self.package)


class PackageTargetNotFound(Exception):
    def __init__(self, target):
        self.target = target
    def __str__(self):
        return 'Target [{0}] not found'.format(self.target)

class PackageRegistry:
    def __init__(self, env, scandirs, scanexcludes=[]):
        self.env = env
        self.packages = packages = {}
        if not SCons.Util.is_List(scandirs):
            scandirs = [scandirs]
        for scandir in scandirs:
            self.collectPackages(scandir, scanexcludes)

    def collectPackages(self, directory, direxcludes=[]):
        """
        Recursively collects SConsider packages.

        Walks recursively through 'directory' (without 'direxcludes')
        and collects found packages.
        """
        rePackage = re.compile('^(.*).sconsider$')
        followlinks = False
        if sys.version_info[:2] >= (2, 6):
            followlinks = True
        for dirpath, dirnames, filenames in os.walk(directory, followlinks=followlinks):
            dirnames[:] = [d for d in dirnames if not d in direxcludes]
            for name in filenames:
                rmatch = rePackage.match(name)
                if rmatch:
                    pkgname = rmatch.group(1)
                    thePath = os.path.abspath(dirpath)
                    print 'found package [%s] in [%s]' % (pkgname, thePath)
                    self.setPackage(pkgname, Dir(thePath).File(name), Dir(thePath))

    def setPackageTarget(self, packagename, targetname, plaintarget, target):
        if not self.hasPackage(packagename):
            print 'tried to register target [%s] for non existent package [%s]' % (targetname, packagename)
            return
        theTargets = self.packages[packagename].setdefault('targets', {})
        if plaintarget and SCons.Util.is_List(plaintarget):
            plaintarget = plaintarget[0]
        if target and SCons.Util.is_List(target):
            target = target[0]
        if not target:
            target = plaintarget
        theTargets[targetname] = {'plaintarget':plaintarget, 'target':target}

    def getPackageTargetTargets(self, packagename, targetname):
        if not self.hasPackage(packagename):
            print 'tried to access target [%s] of non existent package [%s]' % (targetname, packagename)
        return self.packages.get(packagename, {}).get('targets', {}).get(targetname, {'plaintarget':None, 'target':None})

    def getPackageTarget(self, packagename, targetname):
        return self.getPackageTargetTargets(packagename, targetname).get('target', None)

    def getPackagePlaintarget(self, packagename, targetname):
        return self.getPackageTargetTargets(packagename, targetname).get('plaintarget', None)

    def getPackageDependencies(self, packagename):
        deps = dict()
        for targetname in self.getPackageTargetNames(packagename):
            deps[generateFulltargetname(packagename, targetname)] = self.getPackageTargetDependencies(packagename, targetname)
        return deps

    def getPackageTargetDependencies(self, packagename, targetname):
        targetBuildSettings = self.getBuildSettings(packagename).get(targetname, {})
        deps = dict()
        for dep_fulltargetname in targetBuildSettings.get('requires', []) + targetBuildSettings.get('linkDependencies', []) + [targetBuildSettings.get('usedTarget', '')]:
            if dep_fulltargetname:
                dep_packagename, dep_targetname = splitTargetname(dep_fulltargetname)
                if not dep_targetname:
                    dep_targetname = dep_packagename
                deps[generateFulltargetname(dep_packagename, dep_targetname)] = self.getPackageTargetDependencies(dep_packagename, dep_targetname)
        return deps

    def setPackage(self, packagename, packagefile, packagedir, duplicate=False):
        self.packages[packagename] = {'packagefile': packagefile, 'packagedir': packagedir, 'duplicate': duplicate}

    def hasPackage(self, packagename):
        """
        Check if packagename is found in list of packages.

        This solely relies on directories and <packagename>.sconscript files found
        """
        return self.packages.has_key(packagename)

    def hasPackageTarget(self, packagename, targetname):
        return self.packages.get(packagename, {}).get('targets', {}).has_key(targetname)

    def isValidFulltargetname(self, fulltargetname):
        if self.hasPackage(str(fulltargetname)):
            return True
        packagename, targetname = splitTargetname(str(fulltargetname))
        return self.hasPackageTarget(packagename, targetname)

    def setPackageDir(self, packagename, dir):
        if self.hasPackage(packagename):
            self.packages[packagename]['packagedir'] = dir

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
            return self.packages.get(packagename, {}).has_key('buildsettings')
        else:
            return self.packages.get(packagename, {}).get('buildsettings', {}).has_key(targetname)

    def getBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return self.packages.get(packagename, {}).get('buildsettings', {})
        else:
            return self.packages.get(packagename, {}).get('buildsettings', {}).get(targetname, {})

    def loadPackage(self, packagename):
        if not self.hasPackage(packagename):
            raise PackageNotFound(packagename)
        self.lookup(packagename)

    def __loadPackageTarget(self, loadfunc, packagename, targetname):
        self.loadPackage(packagename)
        target = loadfunc(packagename, targetname)
        if not target:
            raise PackageTargetNotFound(generateFulltargetname(packagename, targetname))
        return target

    def loadPackageTarget(self, packagename, targetname):
        return self.__loadPackageTarget(self.getPackageTarget, packagename, targetname)

    def loadPackagePlaintarget(self, packagename, targetname):
        return self.__loadPackageTarget(self.getPackagePlaintarget, packagename, targetname)

    def isPackageLoaded(self, packagename):
        return self.packages.get(packagename, {}).has_key('loaded')

    def lookup(self, fulltargetname, **kw):
        packagename, targetname = splitTargetname(fulltargetname)
        #print 'looking up [%s]' % fulltargetname
        if self.hasPackage(packagename):
            if not self.isPackageLoaded(packagename):
                self.packages[packagename]['loaded'] = True
                packagedir = self.getPackageDir(packagename)
                packagefile = self.getPackageFile(packagename)
                builddir = self.env['BASEOUTDIR'].Dir(packagedir.path).Dir(self.env['BUILDDIR']).Dir(self.env['VARIANTDIR'])
                print 'executing [%s] as SConscript for package [%s]' % (packagefile.path, packagename)
                self.env.SConscript(packagefile, variant_dir=builddir, duplicate=self.getPackageDuplicate(packagename), exports=['packagename'])
            if targetname:
                return self.getPackageTarget(packagename, targetname)
        return None

dirExcludes = [baseEnv['BUILDDIR'], 'CVS', '.git', '.gitmodules', 'doc']
dirExcludes.extend(baseEnv.GetOption('exclude'))
dirExcludesTop = dirExcludes + ['site_scons', '3rdparty'] + [baseEnv[varname] for varname in ['BINDIR', 'LIBDIR', 'LOGDIR', 'CONFIGDIR']]
scanDirs = filter(lambda dir: os.path.isdir(dir) and dir not in dirExcludesTop, os.listdir(Dir('#').path))
runCallback('PrePackageCollection', env=baseEnv, directories=scanDirs)
packageRegistry = PackageRegistry(baseEnv, scanDirs, dirExcludes)
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
            depList = [item for item in v.get('requires', []) + v.get('linkDependencies', []) + [v.get('usedTarget', '')] if item.startswith(self.packagename + targetnameseparator)]
            for ftn in depList:
                pkgname, tname = splitTargetname(ftn)
                if self.packagename == pkgname and self.targetlist.has_key(tname):
                    self.recurseCreate(tname)
            self.doCreateTarget(self.packagename, k, v)

    def prepareFileNodeTuples(self, nodes, baseDir, alternativeDir=None):
        nodetuples = []
        for node in nodes:
            currentFile = node
            if isinstance( currentFile, str ):
               currentFile = SCons.Script.File(currentFile)
            if hasattr( currentFile, 'srcnode' ):
                currentFile = currentFile.srcnode()

            currentBaseDir = baseDir
            if hasattr( currentBaseDir, 'srcnode' ):
                currentBaseDir = currentBaseDir.srcnode()

            if alternativeDir:
                # based on installRelPath and file, try to find an override file to use instead
                fileWithRelpathToSearch = os.path.relpath(currentFile.abspath, currentBaseDir.abspath)
                # catch possible errors and stop when wanting to do relative movements
                if not fileWithRelpathToSearch.startswith('..'):
                    fileToCheckFor = os.path.join(alternativeDir.abspath, fileWithRelpathToSearch)
                    if os.path.isfile(fileToCheckFor):
                        currentFile = File(fileToCheckFor)
                        currentBaseDir = alternativeDir

            nodetuples.append((currentFile, currentBaseDir))
        return nodetuples

    def copyIncludeFiles(self, env, pkgname, buildSettings):
        instTargets = []
        if buildSettings.has_key('public'):
            ifiles = buildSettings['public'].get('includes', [])
            destdir = env['BASEOUTDIR'].Dir(os.path.join(env['INCDIR'], pkgname))
            pkgdir = self.registry.getPackageDir(pkgname)
            stripRelDirs = []
            if buildSettings['public'].get('stripSubdir', True):
                stripRelDirs.append( buildSettings['public'].get('includeSubdir', '') )
            mode = None
            if str( env['PLATFORM'] ) not in ["cygwin", "win32"]:
                mode = stat.S_IREAD | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
            instTargets = copyFileNodes(env, self.prepareFileNodeTuples(ifiles, pkgdir), destdir, stripRelDirs=stripRelDirs, mode=mode)
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
            if str( env['PLATFORM'] ) in ["cygwin", "win32"]:
                mode = None
            instTargets.extend( copyFileNodes(env, self.prepareFileNodeTuples(files, pkgdir, envconfigdir), destdir, mode=mode, replaceDict=replaceDict) )

        return instTargets

    def requireTargets(self, env, target, requiredTargets, **kw):
        if not SCons.Util.is_List(requiredTargets):
            requiredTargets = [requiredTargets]
        for targ in requiredTargets:
            env.Depends(target, self.registry.loadPackageTarget(*splitTargetname(targ, default=True)))

    def doCreateTarget(self, packagename, targetname, targetBuildSettings):
        plaintarget = None
        target = None
        try:
            envVars = targetBuildSettings.get('appendUnique', {})
            targetEnv = self.createTargetEnv(targetname, targetBuildSettings, envVars)
            func = getattr(targetEnv, targetBuildSettings.get('targetType', '__UNDEFINED_TARGETTYPE__'), None)
            if func:
                kw = {}
                kw['packagename'] = packagename
                kw['targetname'] = targetname
                kw['buildSettings'] = targetBuildSettings
                sources = targetBuildSettings.get('sourceFiles', [])
                name = createUniqueTargetname(packagename, targetname)
                targets = apply(func, [name, sources], kw)
                if isinstance(targets, tuple):
                    plaintarget, target = targets
                else:
                    plaintarget = target = targets

            if plaintarget:
                targetEnv.Depends(plaintarget, self.registry.getPackageFile(packagename))
            else:
                # Actually includeOnlyTarget is obsolete, but we still need a (dummy) targetType in build settings to get in here!
                # The following is a workaround, otherwise an alias won't get built in newer SCons versions (because it has depends but no sources)
                plaintarget = target = targetEnv.Alias(packagename+targetnameseparator+targetname, self.registry.getPackageFile(packagename))

            reqTargets = targetBuildSettings.get('linkDependencies', []) + targetBuildSettings.get('requires', [])
            self.requireTargets(targetEnv, target, reqTargets)

            includeTargets = self.copyIncludeFiles(targetEnv, packagename, targetBuildSettings)
            targetEnv.Depends(target, includeTargets)
            targetEnv.Alias('includes', includeTargets)

            if targetBuildSettings.has_key('copyFiles'):
                copyTargets = self.copyFiles(targetEnv, targetEnv['BASEOUTDIR'].Dir(targetEnv['RELTARGETDIR']), packagename, targetBuildSettings.get('copyFiles', []))
                targetEnv.Depends(target, copyTargets)

            targetEnv.Alias(packagename, target)
            targetEnv.Alias('all', target)
            if targetBuildSettings.get('runConfig', {}).get('type', '') == 'test':
                targetEnv.Alias('tests', target)

            runCallback("PostCreateTarget", env=targetEnv, target=target, plaintarget=plaintarget, registry=self.registry, packagename=packagename, targetname=targetname, buildSettings=targetBuildSettings)

            self.registry.setPackageTarget(packagename, targetname, plaintarget, target)
        except (PackageNotFound, PackageTargetNotFound) as e:
            if not GetOption('ignore-missing'):
                raise
            print str(e)+', ignoring target [{0}]'.format(generateFulltargetname(packagename, targetname))

    def createTargetEnv(self, targetname, targetBuildSettings, envVars={}):
        # create environment for target
        targetEnv = cloneBaseEnv()

        # maybe we need to add this library's local include path when building it (if different from .)
        includeSubdir = Dir(targetBuildSettings.get('includeSubdir', '')).srcnode()
        includePublicSubdir = Dir(targetBuildSettings.get('public', {}).get('includeSubdir', '')).srcnode()
        for incdir in includeSubdir.get_all_rdirs() + includePublicSubdir.get_all_rdirs():
            targetEnv.AppendUnique(CPPPATH=[incdir])

        # update environment by adding dependencies to used modules
        linkDependencies = targetBuildSettings.get('linkDependencies', [])
        self.setModuleDependencies(targetEnv, linkDependencies)

        self.setExecEnv(targetEnv, linkDependencies + targetBuildSettings.get('requires', []))

        targetVars = targetBuildSettings.get('public', {}).get('appendUnique', {})
        targetEnv.AppendUnique(**targetVars)

        targetEnv.AppendUnique(**envVars)

        return targetEnv

    def setModuleDependencies(self, env, modules, **kw):
        for fulltargetname in modules:
            packagename, targetname = splitTargetname(fulltargetname, default=True)
            plaintarget = self.registry.loadPackagePlaintarget(packagename, targetname)
            buildSettings = self.registry.getBuildSettings(packagename, targetname)
            self.setExternalDependencies(env, packagename, buildSettings, plaintarget=plaintarget, **kw)

    def setExecEnv(self, env, requiredTargets):
        for targ in requiredTargets:
            packagename, targetname = splitTargetname(targ, default=True)
            if self.registry.hasPackageTarget(packagename, targetname):
                settings = self.registry.getBuildSettings(packagename, targetname)
                target = self.registry.getPackagePlaintarget(packagename, targetname)
                for key, value in settings.get('public', {}).get('execEnv', {}).iteritems():
                    env['ENV'][key] = target.env.subst(value)
                reqTargets = settings.get('linkDependencies', []) + settings.get('requires', [])
                self.setExecEnv(env, reqTargets)

    def setExternalDependencies(self, env, packagename, buildSettings, plaintarget=None, **kw):
        linkDependencies = buildSettings.get('linkDependencies', [])
        if buildSettings.has_key('public'):
            appendUnique = buildSettings['public'].get('appendUnique', {})
            # flags / settings used by this library and users of it
            env.AppendUnique(**appendUnique)

            includePublicSubdir = buildSettings['public'].get('includeSubdir', '')
            if SCons.Util.is_String(includePublicSubdir):
                includePublicSubdir = self.registry.getPackageDir(packagename).Dir(includePublicSubdir)

            for incdir in includePublicSubdir.get_all_rdirs():
                env.AppendUnique(CPPPATH=[incdir])

        # this libraries dependencies
        self.setModuleDependencies(env, linkDependencies)

        if plaintarget:
            # try block needed to block Alias only targets without concrete builder
            try:
                strTargetType = plaintarget.builder.get_name(plaintarget.env)
                if strTargetType.find('Library') != -1:
                    libname = multiple_replace([
                                      ('^'+re.escape(env.subst("$LIBPREFIX")), ''),
                                      (re.escape(env.subst("$LIBSUFFIX"))+'$', ''),
                                      ('^'+re.escape(env.subst("$SHLIBPREFIX")), ''),
                                      (re.escape(env.subst("$SHLIBSUFFIX"))+'$', ''),
                                      ], plaintarget.name)
                    env.AppendUnique(LIBS=[libname])
            except:
                pass

def createTargets(packagename, buildSettings):
    """
    Creates the targets for the package 'packagename' which are defined in 'buildSettings'.

    This is a helper function which must be called from SConscript to create the targets.
    """
    packageRegistry.setBuildSettings(packagename, buildSettings)
    tmk = TargetMaker(packagename, buildSettings, packageRegistry)
    tmk.createTargets()
    SCons.Script.Default(packagename)
    runCallback("PostCreatePackageTargets", registry=packageRegistry, packagename=packagename, buildSettings=buildSettings)

baseEnv.lookup_list.append(packageRegistry.lookup)

# we need to define the targets before entering the build phase:
try:
    try:
        buildtargets = SCons.Script.BUILD_TARGETS
        if not buildtargets:
            if GetOption("climb_up") in [1, 3]: # 1: -u, 3: -U
                launchDir = Dir(SCons.Script.GetLaunchDir())
                if GetOption("climb_up") == 1:
                    dirfilter = lambda directory: directory.is_under(launchDir)
                else:
                    dirfilter = lambda directory: directory == launchDir

                def namefilter(packagename):
                    return dirfilter(packageRegistry.getPackageDir(packagename))

                buildtargets = filter(namefilter, packageRegistry.getPackageNames())
            else:
                buildtargets = packageRegistry.getPackageNames()

        for ftname in buildtargets:
            packagename, targetname = splitTargetname(ftname)
            packageRegistry.loadPackage(packagename)

    except PackageNotFound as e:
        print e
        print 'loading all SConscript files to find target'
        for packagename in packageRegistry.getPackageNames():
            packageRegistry.loadPackage(packagename)

except (PackageNotFound, PackageTargetNotFound) as e:
    print e
    if not GetOption('help'):
        raise SCons.Errors.UserError('Build aborted, missing dependency!')

runCallback("PreBuild", registry=packageRegistry, buildTargets=SCons.Script.BUILD_TARGETS)

print "BUILD_TARGETS is", map(str, SCons.Script.BUILD_TARGETS)

def print_build_failures():
    if SCons.Script.GetBuildFailures():
        print "scons: printing failed nodes"
        for bf in SCons.Script.GetBuildFailures():
            if str(bf.action) != "installFunc(target, source, env)":
                print bf.node
        print "scons: done printing failed nodes"

atexit.register(print_build_failures)
