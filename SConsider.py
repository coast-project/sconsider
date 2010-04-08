from __future__ import with_statement
import os, platform, SCons, glob, re, atexit, sys, traceback, commands, pdb, dircache, stat
import SomeUtils

from SCons.Script import AddOption, GetOption, Dir, File, DefaultEnvironment, Split, Flatten, SConsignFile
from SomeUtils import *

# SconsBuilder may work with earlier version,
# but it was build and tested against SCons 1.2.0
SCons.Script.EnsureSConsVersion(1, 2, 0)
# SconsBuilder may work with earlier version,
# but it was build and tested against Python 2.5
SCons.Script.EnsurePythonVersion(2, 5)

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

baseoutdir = Dir(GetOption('baseoutdir'))
print 'base output dir [%s]' % baseoutdir.abspath

def changed_timestamp_or_content(dependency, target, prev_ni):
    return dependency.changed_content(target, prev_ni) or dependency.changed_timestamp_newer(target, prev_ni)

def programApp(env, name, sources, packagename, buildSettings, **kw):
    plaintarget = env.Program(name, sources)

    baseoutdir = env['BASEOUTDIR']
    env['RELTARGETDIR'] = os.path.join('apps', packagename)
    instApps = env.InstallAs(baseoutdir.Dir(env['RELTARGETDIR']).Dir(env['BINDIR']).Dir(env['VARIANTDIR']).File(name), plaintarget)

    env.Tool('generateScript')
    wrappers = env.GenerateWrapperScript(instApps, GetOption('gdb'))

    env.Alias('binaries', wrappers)

    buildSettings.setdefault("runConfig", {}).setdefault("type", "run")

    return (plaintarget, wrappers)

def programTest(env, name, sources, packagename, targetname, buildSettings, **kw):
    env.Decider(changed_timestamp_or_content)
    plaintarget = env.Program(name, sources)

    baseoutdir = env['BASEOUTDIR']
    env['RELTARGETDIR'] = os.path.join('tests', packagename)
    instApps = env.InstallAs(baseoutdir.Dir(env['RELTARGETDIR']).Dir(env['BINDIR']).Dir(env['VARIANTDIR']).File(name), plaintarget)

    env.Tool('generateScript')
    wrappers = env.GenerateWrapperScript(instApps, GetOption('gdb'))

    buildSettings.setdefault("runConfig", {}).setdefault("type", "test")

    return (plaintarget, wrappers)

def appTest(env, name, sources, packagename, targetname, buildSettings, **kw):
    env.Decider(changed_timestamp_or_content)
    usedFullTargetname = buildSettings.get('usedTarget', None)
    plaintarget = None
    if usedFullTargetname:
        usedPackagename, usedTargetname = splitTargetname(usedFullTargetname)
        packageRegistry.loadPackage(usedPackagename)
        # get default target name if not set already
        if not usedTargetname:
            usedTargetname = usedPackagename
        plaintarget = packageRegistry.getPackageTarget(usedPackagename, usedTargetname)['plaintarget']

    baseoutdir = env['BASEOUTDIR']
    env['RELTARGETDIR'] = os.path.join('tests', packagename)
    instApps = env.InstallAs(baseoutdir.Dir(env['RELTARGETDIR']).Dir(env['BINDIR']).Dir(env['VARIANTDIR']).File(name), plaintarget)

    env.Tool('generateScript')
    wrappers = env.GenerateWrapperScript(instApps, GetOption('gdb'))

    buildSettings.setdefault("runConfig", {}).setdefault("type", "test")

    return (plaintarget, wrappers)

def sharedLibrary(env, name, sources, packagename, targetname, buildSettings, **kw):
    if buildSettings.get('lazylinking', False):
        env['_NONLAZYLINKFLAGS'] = ''

    plaintarget = env.SharedLibrary(name, sources)

    baseoutdir = env['BASEOUTDIR']
    instTarg = env.Install(baseoutdir.Dir(env['LIBDIR']).Dir(env['VARIANTDIR']), plaintarget)

    return (plaintarget, instTarg)

dEnv = DefaultEnvironment()

dEnv.AddMethod(appTest, "AppTest")
dEnv.AddMethod(programTest, "ProgramTest")
dEnv.AddMethod(programApp, "ProgramApp")
dEnv.AddMethod(sharedLibrary, "LibraryShared")

if GetOption('prependPath'):
    dEnv.PrependENVPath('PATH', GetOption('prependPath'))
    print 'prepended path is [%s]' % dEnv['ENV']['PATH']
if GetOption('appendPath'):
    dEnv.AppendENVPath('PATH', GetOption('appendPath'))
    print 'appended path is [%s]' % dEnv['ENV']['PATH']

globaltools = ["setupBuildTools", "coast_options", "SCBWriter", "TargetPrinter",
               "precompiledLibraryInstallBuilder", "RunBuilder", "DoxygenBuilder"]
usetools = globaltools + GetOption('usetools')
print 'tools to use %s' % Flatten(usetools)

baseEnv = dEnv.Clone(tools=usetools)

variant = "Unknown"
myplatf = str(SCons.Platform.Platform())

if myplatf == "posix":
    libcver = platform.libc_ver(executable='/lib/libc.so.6')
    variant = platform.system() + "_" + libcver[0] + "_" + libcver[1] + "-" + platform.machine()
elif myplatf == "sunos":
    variant = platform.system() + "_" + platform.release() + "-" + platform.processor()
elif myplatf == "darwin":
    version = commands.getoutput("sw_vers -productVersion")
    cpu = commands.getoutput("arch")
    if version.startswith("10.5"):
        variant = "leopard-"
    if version.startswith("10.4"):
        variant = "tiger-"
    variant += cpu
elif myplatf == "cygwin":
    variant = platform.system() + "-" + platform.machine()
elif myplatf == "win32":
    variant = platform.release() + "-" + platform.machine()

runCallback('VARIANT_SUFFIX', env=baseEnv)
for v in baseEnv.get('VARIANT_SUFFIX', []):
    variant += v

print "compilation variant [", variant, "]"

ssfile = os.path.join(Dir('#').path, '.sconsign.' + variant)
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

# TODO: we should differentiate between absolute output dirs and relative dirnames
# TODO: why aren't those two rooted in baseoutdir? 
baseEnv.Append(DATADIR=Dir('data'))
baseEnv.Append(XMLDIR=Dir('xml'))
# TODO: what are those three for??? And why are they rooted in baseoutdir?
baseEnv.Append(PYTHONDIR=Dir(baseoutdir).Dir('python'))
baseEnv['CONFIGURELOG'] = str(Dir(baseoutdir).File("config.log"))
baseEnv['CONFIGUREDIR'] = str(Dir(baseoutdir).Dir(".sconf_temp"))
baseEnv.AppendUnique(LIBPATH=[baseoutdir.Dir(baseEnv['LIBDIR']).Dir(baseEnv['VARIANTDIR'])])

def cloneBaseEnv():
    return baseEnv.Clone()

def splitTargetname(fulltargetname):
    """
    Split fulltargetname into packagename and targetname.
    """
    parts = fulltargetname.split('.')
    pkgname = parts[0]
    targetname = None
    if len(parts) > 1:
        targetname = parts[1]
    return (pkgname, targetname)

def generateFulltargetname(packagename, targetname, default=False):
    """
    Generate fulltargetname using packagename and targetname.
    """
    if not targetname:
        if default:
            return packagename+"."+packagename
        else:
            return packagename
    else: 
        return packagename+"."+targetname

class PackageNotFound(Exception):
    pass

class PackageRegistry:
    def __init__(self, env, scandir, scanexcludes=[]):
        self.env = env
        self.packages = self.collectPackages(scandir, scanexcludes)

    def collectPackages(self, directory, direxcludes=[]):
        """
        Recursively collects SConsider packages.
        
        Walks recursively through 'directory' (without 'direxcludes')
        and collects found packages. 
        """
        packages = {}
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
                    if not packages.has_key(pkgname):
                        packages[pkgname] = {}
                    thePath = os.path.abspath(dirpath)
                    packages[pkgname]['packagepath'] = Dir(thePath)
                    packages[pkgname]['packagefile'] = Dir(thePath).File(name)
                    print 'found package [%s] in [%s]' % (pkgname, thePath)
        return packages

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

    def getPackageTarget(self, packagename, targetname):
        if not self.hasPackage(packagename):
            print 'tried to access target [%s] of non existent package [%s]' % (targetname, packagename)
            return
        theTargets = self.packages[packagename].setdefault('targets', {})
        return theTargets.get(targetname, {'plaintarget':None, 'target':None})

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

    def hasPackage(self, packagename):
        """
        Check if packagename is found in list of packages.
        
        This solely relies on directories and <packagename>.sconscript files found
        """
        return self.packages.has_key(packagename)

    def hasPackageTarget(self, packagename, targetname):
        return self.packages.get(packagename, {}).get('targets', {}).has_key(targetname)

    def getPackageDir(self, packagename):
        return self.packages.get(packagename, {}).get('packagepath', '')

    def getPackageFile(self, packagename):
        return self.packages.get(packagename, {}).get('packagefile', '')

    def getPackageTargetNames(self, packagename):
        return self.packages.get(packagename, {}).get('targets', {}).keys()
    
    def getPackageNames(self):
        return self.packages.keys()

    def setBuildSettings(self, packagename, buildSettings):
        if self.hasPackage(packagename):
            self.packages[packagename]['buildsettings'] = buildSettings

    def getBuildSettings(self, packagename):
        return self.packages.get(packagename, {}).get('buildsettings', {})

    def loadPackage(self, packagename):
        if not self.hasPackage(packagename):
            raise PackageNotFound(packagename)
        self.lookup(packagename)

    def isPackageLoaded(self, packagename):
        return self.packages.get(packagename, {}).has_key('loaded')

    def lookup(self, fulltargetname, **kw):
        packagename, targetname = splitTargetname(fulltargetname)
        #print 'looking up [%s]' % packagename
        if self.hasPackage(packagename):
            if not self.isPackageLoaded(packagename):
                self.packages[packagename]['loaded'] = True
                packagedir = self.getPackageDir(packagename)
                packagefile = self.getPackageFile(packagename)
                builddir = os.path.join(self.env['BASEOUTDIR'].abspath, packagedir.path, self.env['BUILDDIR'], self.env['VARIANTDIR'])
                print 'executing [%s] as SConscript for package [%s]' % (packagefile.path, packagename)
                self.env.SConscript(packagefile, build_dir=builddir, duplicate=0, exports=['packagename'])
            if targetname:
                return self.getPackageTarget(packagename, targetname)['target']
        return None

direxcludes = [baseEnv['BUILDDIR'], 'CVS', '.git', '.gitmodules', 'doc']
direxcludes.extend(baseEnv.GetOption('exclude'))
direxcludes.extend([baseEnv[varname] for varname in ['BINDIR', 'LIBDIR', 'LOGDIR', 'CONFIGDIR']])
packageRegistry = PackageRegistry(baseEnv, Dir('#').path, direxcludes)

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
            depList = [item for item in v.get('requires', []) + v.get('linkDependencies', []) + [v.get('usedTarget', '')] if item.startswith(self.packagename + '.')]
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
            mode = stat.S_IREAD | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
            instTargets = copyFileNodes(env, self.prepareFileNodeTuples(ifiles, pkgdir), destdir, stripRelDirs=stripRelDirs, mode=mode)
        return instTargets

    def copyConfigFiles(self, env, destdir, pkgname, buildSettings):
        instTargets = []

        if buildSettings.has_key('copyFiles'):
            pkgdir = self.registry.getPackageDir(pkgname)

            envconfigdir = env.get('__envconfigdir__', None)
            if envconfigdir:
                envconfigdir = envconfigdir.Dir(pkgname)

            for (cfiles, mode) in buildSettings.get('copyFiles', []):
                instTargets.append( copyFileNodes(env, self.prepareFileNodeTuples(cfiles, pkgdir, envconfigdir), destdir, mode=mode) )

        return instTargets

    def requireTargets(self, env, target, requiredTargets, **kw):
        if not SCons.Util.is_List(requiredTargets):
            requiredTargets = [requiredTargets]
        for targ in requiredTargets:
            env.Depends(target, env.Alias(targ)[0])

    def doCreateTarget(self, pkgname, name, targetBuildSettings):
        plaintarget = None
        target = None
        try:
            if targetBuildSettings.has_key('targetType'):
                envVars = targetBuildSettings.get('appendUnique', {})
                targetEnv = self.createTargetEnv(name, targetBuildSettings, envVars)
                func = getattr(targetEnv, targetBuildSettings.get('targetType', ''), None)
                if func:
                    kw = {}
                    kw['packagename'] = pkgname
                    kw['targetname'] = name
                    kw['buildSettings'] = targetBuildSettings
                    sources = targetBuildSettings.get('sourceFiles', [])
                    targets = apply(func, [name, sources], kw)
                    if isinstance(targets, tuple):
                        plaintarget, target = targets
                    else:
                        plaintarget = target = targets

                if plaintarget:
                    targetEnv.Depends(plaintarget, self.registry.getPackageFile(pkgname))
                else:
                    # Actually includeOnlyTarget is obsolete, but we still need a (dummy) targetType in build settings to get in here!
                    # The following is a workaround, otherwise an alias won't get built in newer SCons versions (because it has depends but no sources)
                    plaintarget = target = targetEnv.Alias(pkgname+'.'+name, self.registry.getPackageFile(pkgname))

                reqTargets = targetBuildSettings.get('linkDependencies', []) + targetBuildSettings.get('requires', [])
                self.requireTargets(targetEnv, target, reqTargets)

                includeTargets = self.copyIncludeFiles(targetEnv, pkgname, targetBuildSettings)
                targetEnv.Depends(target, includeTargets)
                targetEnv.Alias('includes', includeTargets)

                configTargets = self.copyConfigFiles(targetEnv, targetEnv['BASEOUTDIR'].Dir(targetEnv['RELTARGETDIR']), pkgname, targetBuildSettings)
                targetEnv.Depends(target, configTargets)

                targetEnv.Alias(pkgname, target)
                targetEnv.Alias('all', target)
                if targetBuildSettings.get('runConfig', {}).get('type', '') == 'test':
                    targetEnv.Alias('tests', target)

                runCallback("PostCreateTarget", env=targetEnv, target=target, registry=self.registry, packagename=pkgname, targetname=name, buildSettings=targetBuildSettings)

            self.registry.setPackageTarget(pkgname, name, plaintarget, target)
        except PackageNotFound, e:
            print 'package [%s] not found, ignoring target [%s]' % (str(e), pkgname+'.'+name)

    def createTargetEnv(self, targetname, targetBuildSettings, envVars={}):
        # create environment for target
        targetEnv = cloneBaseEnv()

        # maybe we need to add this library's local include path when building it (if different from .)
        includeSubdir = Dir(targetBuildSettings.get('includeSubdir', '')).srcnode()
        includePublicSubdir = Dir(targetBuildSettings.get('public', {}).get('includeSubdir', '')).srcnode()
        targetEnv.AppendUnique(CPPPATH=[includeSubdir, includePublicSubdir])
        # just for info (p.e. scb-files)
        targetEnv.AppendUnique(CPPPATH_ORIGIN=[includeSubdir, includePublicSubdir])

        # update environment by adding dependencies to used modules
        linkDependencies = targetBuildSettings.get('linkDependencies', [])
        self.setModuleDependencies(targetEnv, linkDependencies)

        targetVars = targetBuildSettings.get('public', {}).get('appendUnique', {})
        targetEnv.AppendUnique(**targetVars)
        
        targetEnv.AppendUnique(**envVars)

        return targetEnv

    def setModuleDependencies(self, env, modules, **kw):
        for fulltargetname in modules:
            packagename, targetname = splitTargetname(fulltargetname)
            self.registry.loadPackage(packagename)
            buildSettings = self.registry.getBuildSettings(packagename)
            if not buildSettings:
                print 'Warning: buildSettings dictionary in module %s not defined!' % packagename
                return None

            # get default target name if not set already
            if not targetname:
                targetname = packagename
            targets = self.registry.getPackageTarget(packagename, targetname)
            self.setExternalDependencies(env, packagename, buildSettings.get(targetname, {}), plaintarget=targets['plaintarget'], **kw)

    def setExternalDependencies(self, env, packagename, buildSettings, plaintarget=None, **kw):
        linkDependencies = buildSettings.get('linkDependencies', [])
        if buildSettings.has_key('public'):
            appendUnique = buildSettings['public'].get('appendUnique', {})
            # flags / settings used by this library and users of it
            env.AppendUnique(**appendUnique)

            destIncludeDir = env['BASEOUTDIR'].Dir(os.path.join(env['INCDIR'], packagename))
            srcIncludeDir = self.registry.getPackageDir(packagename).Dir(buildSettings['public'].get('includeSubdir', ''))

            # destination dir if we have files to copy
            if buildSettings['public'].get('includes', []):
                env.AppendUnique(CPPPATH=[destIncludeDir])
            else:
                env.AppendUnique(CPPPATH=[srcIncludeDir])

            # just for info (p.e. scb-files)
            env.AppendUnique(CPPPATH_ORIGIN=[srcIncludeDir])

        # this libraries dependencies
        self.setModuleDependencies(env, linkDependencies)

        if plaintarget:
            # try block needed to block Alias only targets without concrete builder
            try:
                strTargetType = plaintarget.builder.get_name(plaintarget.env)
                if strTargetType.find('Library') != -1:
                    tName = plaintarget.name
                    env.AppendUnique(LIBS=[tName])
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

    runCallback("PostCreatePackageTargets", registry=packageRegistry, packagename=packagename, buildSettings=buildSettings)

baseEnv.lookup_list.append(packageRegistry.lookup)

# we need to define the targets before entering the build phase:
try:
    buildtargets = SCons.Script.BUILD_TARGETS
    if not buildtargets:
        buildtargets = packageRegistry.getPackageNames()
    for ftname in buildtargets:
        packagename, targetname = splitTargetname(ftname)
        packageRegistry.loadPackage(packagename)
except PackageNotFound, e:
    print 'package [%s] not found' % str(e)
    print 'loading all SConscript files to find target'
    for packagename in packageRegistry.getPackageNames():
        packageRegistry.loadPackage(packagename)

runCallback("PreBuild", registry=packageRegistry, buildTargets=SCons.Script.BUILD_TARGETS)

print "BUILD_TARGETS is ", map(str, SCons.Script.BUILD_TARGETS)

def print_build_failures():
    if SCons.Script.GetBuildFailures():
        print "scons: printing failed nodes"
        for bf in SCons.Script.GetBuildFailures():
            if str(bf.action) != "installFunc(target, source, env)":
                print bf.node
        print "scons: done printing failed nodes"

atexit.register(print_build_failures)