import os, platform, SCons, glob, re, atexit, sys, traceback, commands, pdb, dircache
import SomeUtils

from SCons.Script import AddOption, GetOption, Dir, DefaultEnvironment, Split, Flatten, SConsignFile, Export, BUILD_TARGETS
from SomeUtils import *

# SconsBuilder may work with earlier version,
# but it was build and tested against SCons 1.0.0
SCons.Script.EnsureSConsVersion(1, 0, 0)
# SconsBuilder may work with earlier version,
# but it was build and tested against Python 2.4
SCons.Script.EnsurePythonVersion(2, 5)

if False:
    print "platform.dist:", platform.dist()
    print "platform.arch:", platform.architecture()
    print "platform.machine:", platform.machine()
    print "platform.libc:", platform.libc_ver()
    print "platform.release:", platform.release()
    print "platform.version:", platform.version()
    print "platform.proc:", platform.processor()
    print "platform.system:", platform.system()

AddOption('--baseoutdir', dest='baseoutdir', action='store', nargs=1, type='string', default='#', metavar='DIR', help='Directory containing packages superseding installed ones. Relative paths not supported!')
AddOption('--exclude', dest='exclude', action='append', nargs=1, type='string', metavar='DIR', help='Directory containing a SConscript file that should be ignored.')
AddOption('--usetool', dest='usetools', action='append', nargs=1, type='string', default=[], metavar='VAR', help='tools to use when constructing default environment')
AddOption('--appendPath', dest='appendPath', action='append', nargs=1, type='string', metavar='DIR', help='Directory to append to PATH environment variable.')
AddOption('--prependPath', dest='prependPath', action='append', nargs=1, type='string', metavar='DIR', help='Directory to prepend to PATH environment variable.')

baseoutdir = Dir(GetOption('baseoutdir'))
print 'base output dir [%s]' % baseoutdir.abspath

def requireTargets(env, target, requiredTargets, **kw):
    if not SCons.Util.is_List(requiredTargets):
        requiredTargets = [requiredTargets]
    for targ in requiredTargets:
        env.Requires(target, env.Alias(targ)[0])

def copyConfigFiles(env, pkgname, baseoutdir, buildSettings):
    if buildSettings.has_key('configFiles'):
        cfiles = buildSettings.get('configFiles')
        instTargets = copyFileNodes(env, cfiles, baseoutdir.Dir(pkgname))
        if instTargets:
            env.Alias(pkgname, instTargets)
            env.Alias('all', instTargets)

def copyConfigFilesTarget(env, pkgname, baseoutdir, buildSettings, target):
    if buildSettings.has_key('configFiles'):
        cfiles = buildSettings.get('configFiles')
        instTargets = copyFileNodes(env, cfiles, baseoutdir.Dir(pkgname))
        if instTargets:
            env.Requires(target, instTargets)

def programTest(env, name, sources, pkgname, buildSettings, **kw):
    plaintarget = env.Program(name, sources)

    baseoutdir = env['BASEOUTDIR']
    basereldir = 'tests'
    baseoutdir = baseoutdir.Dir(basereldir)
    instApps = env.InstallAs(baseoutdir.Dir(pkgname).Dir(env['TESTDIR']).File(name), plaintarget)

    if buildSettings.has_key('requires'):
        requireTargets(env, instApps, buildSettings.get('requires', []))

    env.Tool('generateScript')
    env['PackageName'] = pkgname
    env['TargetType'] = basereldir
    wrappers = env.GenerateWrapperScript(instApps)

    env.Alias(pkgname, wrappers)
    env.Alias('all', wrappers)
    env.Alias('test', wrappers)
    env.Clean('test', wrappers)

    copyConfigFiles(env, pkgname, baseoutdir, buildSettings)

    return (plaintarget, wrappers)

def programApp(env, name, sources, pkgname, buildSettings, **kw):
    plaintarget = env.Program(name, sources)

    baseoutdir = env['BASEOUTDIR']
    basereldir = 'apps'
    baseoutdir = baseoutdir.Dir(basereldir)
    instApps = env.InstallAs(baseoutdir.Dir(pkgname).Dir(env['BINDIR']).File(name), plaintarget)

    if buildSettings.has_key('requires'):
        requireTargets(env, instApps, buildSettings.get('requires', []))

    env.Tool('generateScript')
    env['PackageName'] = pkgname
    env['TargetType'] = basereldir
    wrappers = env.GenerateWrapperScript(instApps)

    env.Alias(pkgname, wrappers)
    env.Alias('all', wrappers)
    env.Alias('binaries', wrappers)

    copyConfigFiles(env, pkgname, baseoutdir, buildSettings)

    return (plaintarget, wrappers)

def appTest(env, name, sources, pkgname, buildSettings, **kw):
    fulltargetname = buildSettings.get('usedTarget', None)
    plaintarget = None
    if fulltargetname:
        packagename, targetname = splitTargetname(fulltargetname)
        theModule = loadPackage(packagename)
        if not targetname:
            targetname = buildSettings.keys()[0]
        plaintarget = programLookup.getPackageTarget(packagename, targetname)['plaintarget']

    baseoutdir = env['BASEOUTDIR']
    basereldir = 'tests'
    baseoutdir = baseoutdir.Dir(basereldir)
    instApps = env.InstallAs(baseoutdir.Dir(pkgname).Dir(env['TESTDIR']).File(name), plaintarget)

    if buildSettings.has_key('requires'):
        requireTargets(env, instApps, buildSettings.get('requires', []))

    env.Tool('generateScript')
    env['PackageName'] = pkgname
    env['TargetType'] = basereldir
    wrappers = env.GenerateWrapperScript(instApps)

    copyConfigFilesTarget(env, pkgname, baseoutdir, buildSettings, wrappers)

    env.Alias(pkgname, wrappers)
    env.Alias('all', wrappers)
    env.Alias('test', wrappers)
    env.Clean('test', wrappers)

    return (plaintarget, wrappers)

def includeOnly(env, name, sources, pkgname, buildSettings, **kw):
    baseoutdir = env['BASEOUTDIR']
    target = None
    if buildSettings.has_key('public'):
        instTargets = None
        if buildSettings['public'].has_key('includes') and buildSettings['public'].get('copyIncludes', True):
            ifiles = buildSettings['public'].get('includes', [])
            instTargets = copyFileNodes(env, ifiles, baseoutdir.Dir(os.path.join(env['INCDIR'], pkgname)))
        target = env.Alias(pkgname + '.' + name, instTargets)
        env.Alias(pkgname, target)
        env.Alias('all', target)
    reqTargets = buildSettings.get('linkDependencies', []) + buildSettings.get('requires', [])
    if target and reqTargets:
        requireTargets(env, target, reqTargets)
    return (target, target)

def includeOnlyTarget(env, name, sources, pkgname, buildSettings, target, **kw):
    baseoutdir = env['BASEOUTDIR']
    if buildSettings.has_key('public'):
        ifiles = buildSettings['public'].get('includes', [])
        instTargets = copyFileNodes(env, ifiles, baseoutdir.Dir(os.path.join(env['INCDIR'], pkgname)))
        if instTargets:
            env.Requires(target, instTargets)
    return None

def sharedLibrary(env, name, sources, pkgname, buildSettings, **kw):
    if buildSettings.get('lazylinking', False):
        env['_NONLAZYLINKFLAGS'] = ''

    plaintarget = env.SharedLibrary(name, sources)

    baseoutdir = env['BASEOUTDIR']
    instTarg = env.Install(baseoutdir.Dir(env['LIBDIR']), plaintarget)
    env.Alias(pkgname, instTarg)
    env.Alias('all', instTarg)

    includeOnlyTarget(env, name, sources, pkgname, buildSettings, instTarg, **kw)

    return (plaintarget, instTarg)

def precompiledLibrary(env, name, sources, pkgname, buildSettings, **kw):
    ss

def EnvExtensions(baseenv):
    baseenv.RequireTargets = requireTargets
    baseenv.AppTest = appTest
    baseenv.ProgramTest = programTest
    baseenv.ProgramApp = programApp
    baseenv.LibraryShared = sharedLibrary
    baseenv.LibraryPrecompiled = precompiledLibrary
    baseenv.IncludeOnly = includeOnly

EnvExtensions(SCons.Environment.Environment)

dEnv = DefaultEnvironment()
if GetOption('prependPath'):
    dEnv.PrependENVPath('PATH', GetOption('prependPath'))
    print 'prepended path is [%s]' % dEnv['ENV']['PATH']
if GetOption('appendPath'):
    dEnv.AppendENVPath('PATH', GetOption('appendPath'))
    print 'appended path is [%s]' % dEnv['ENV']['PATH']

globaltools = Split("""setupBuildTools coast_options precompiledLibraryInstallBuilder""")
usetools = globaltools + GetOption('usetools')
print 'tools to use %s' % Flatten(usetools)

baseEnv = dEnv.Clone(tools=usetools)

variant = "Unknown"
myplatf = str(SCons.Platform.Platform())
targetbits = GetOption('archbits')

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

variant += "-" + targetbits

if GetOption('Trace'):
    variant += '_trace'

print "compilation variant [", variant, "]"

ssfile = os.path.join(Dir('#').path, '.sconsign.' + variant)
SConsignFile(ssfile)

#########################
#  Project Environment  #
#########################
baseEnv.Append(BASEOUTDIR=baseoutdir)
baseEnv.Append(VARIANTDIR=variant)
baseEnv.Append(LIBDIR=os.path.join('lib', variant))
baseEnv.Append(BINDIR=os.path.join('bin', variant))
baseEnv.Append(SCRIPTDIR=os.path.join('scripts', variant))
baseEnv.Append(INCDIR='include')
baseEnv.Append(TESTDIR=baseEnv['BINDIR'])
#baseEnv.Append(TESTSCRIPTDIR=baseEnv['SCRIPTDIR'])

baseEnv.Append(CONFIGDIR=Dir('config'))
baseEnv.Append(DATADIR=Dir('data'))
baseEnv.Append(XMLDIR=Dir('xml'))
baseEnv.Append(PYTHONDIR=Dir(baseoutdir).Dir('python'))
baseEnv['CONFIGURELOG'] = str(Dir(baseoutdir).File("config.log"))
baseEnv['CONFIGUREDIR'] = str(Dir(baseoutdir).Dir(".sconf_temp"))
baseEnv.AppendUnique(LIBPATH=[baseoutdir.Dir(baseEnv['LIBDIR'])])

def CoastFindPackagesDict(directory, direxcludes=[]):
    packages = {}
    reLib = re.compile('^(.*)Lib.py$')
    followln = {}
    try:
        v_major, v_minor, v_micro, release, serial = sys.version_info
        python_ver = (v_major, v_minor)
    except AttributeError:
        python_ver = self._get_major_minor_revision(sys.version)[:2]
    if python_ver >= (2, 6):
        followln = { 'followlinks' : True }
    for dirpath, dirnames, filenames in os.walk(directory, followln):
        dirnames[:] = [d for d in dirnames if not d in direxcludes]
        for name in filenames:
            rmatch = reLib.match(name)
            if rmatch:
                pkgname = rmatch.group(1)
                if not packages.has_key(pkgname):
                    packages[pkgname] = {}
                thePath = os.path.abspath(dirpath)
                ## append path to module path, otherwise we can not import someLib[.py]
                sys.path.append(thePath)
                packages[pkgname]['packagepath'] = Dir(thePath)
                print 'appended toolpath  [%s]' % thePath
                if not os.path.isfile(Dir(dirpath).File('SConscript').abspath):
                    print 'warning: SConscript not found in [%s]' % thePath
    return packages

def CloneBaseEnv():
    return baseEnv.Clone()

def splitTargetname(fulltargetname):
    # split fulltargetname into module and target
    parts = fulltargetname.split('.')
    pkgname = parts[0]
    targetname = None
    if len(parts) > 1:
        targetname = parts[1]
    return (pkgname, targetname)

class ProgramLookup:
    def __init__(self, env, packages, baseoutdir, variant):
        self.env = env
        self.packages = packages
        self.baseoutdir = baseoutdir.abspath
        self.variant = variant

    def setPackageTarget(self, packagename, targetname, plaintarget, target):
        if not self.packages.has_key(packagename):
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
        if not self.packages.has_key(packagename):
            print 'tried to access target [%s] of non existent package [%s]' % (targetname, packagename)
            return
        theTargets = self.packages[packagename].setdefault('targets', {})
        if not theTargets.has_key(targetname):
            pass
        return theTargets.get(targetname, {'plaintarget':None, 'target':None})

    def hasPackage(self, packagename):
        """check if packagename is found in list of packages
        this solely relies on directories and <packagename>Lib.py files found"""
        return self.packages.has_key(packagename)

    def getPackageDir(self, packagename):
        return self.packages[packagename].get('packagepath', '')

    def lookup(self, fulltargetname, **kw):
        packagename, targetname = splitTargetname(fulltargetname)
#        print 'looking up [%s]' % packagename
        if self.hasPackage(packagename):
            if not self.packages[packagename].has_key('loaded'):
                self.packages[packagename]['loaded'] = True
                if self.packages[packagename].has_key('packagepath'):
                    path = self.packages[packagename]['packagepath']
                    relpath = path.path
                    scfile = os.path.join(path.abspath, 'SConscript')
                    if os.path.isfile(scfile):
                        builddir = os.path.join(self.baseoutdir, relpath, 'build', self.variant)
                        print 'executing SConscript for package [%s]' % packagename
                        self.env.SConscript(scfile, build_dir=builddir, duplicate=0)
            if targetname:
                return self.getPackageTarget(packagename, targetname)['target']
        return None


direxcludes = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules', 'config']
if not baseEnv.GetOption('exclude') == None:
    direxcludes.extend(baseEnv.GetOption('exclude'))
packages = CoastFindPackagesDict(Dir('#').path, direxcludes)
programLookup = ProgramLookup(baseEnv, packages, baseoutdir, variant)

def loadPackage(packagename):
    programLookup.lookup(packagename)
    modname = packagename + 'Lib'
    theModule = __import__(modname)
    sys.modules[modname] = theModule
    return theModule

def DependsOn(env, fulltargetname, **kw):
    packagename, targetname = splitTargetname(fulltargetname)
    theModule = loadPackage(packagename)
    modDict = theModule.__dict__
    ## support for old style module handling
    if modDict.get('generate', None):
        return theModule.generate(env, **kw)

    buildSettings = modDict.get('buildSettings', None)
    if not buildSettings:
        print 'Warning: buildSettings dictionary in module %s not defined!' % packagename
        return None
    # get default target name if not set already
    if not targetname:
        targetname = packagename
    targets = programLookup.getPackageTarget(packagename, targetname)
    ExternalDependencies(env, packagename, buildSettings.get(targetname, {}), plaintarget=targets['plaintarget'], **kw)
    return targets['target']

def setModuleDependencies(env, modules, **kw):
    for mod in modules:
        DependsOn(env, mod, **kw)

def ExternalDependencies(env, packagename, buildSettings, plaintarget=None, **kw):
    linkDependencies = buildSettings.get('linkDependencies', [])
    includeBasedir = env['BASEOUTDIR'].Dir(os.path.join(env['INCDIR'], packagename))
    includeSubdir = ''
    if buildSettings.has_key('public'):
        appendUnique = buildSettings['public'].get('appendUnique', {})
        # flags / settings used by this library and users of it
        env.AppendUnique(**appendUnique)
        includeSubdir = buildSettings['public'].get('includeSubdir', '')
        if not buildSettings['public'].get('copyIncludes', True):
            includeBasedir = programLookup.getPackageDir(packagename)

    # this libraries dependencies
    setModuleDependencies(env, linkDependencies)

    if plaintarget:
        # try block needed to block Alias only targets without concrete builder
        try:
            strTargetType = plaintarget.builder.get_name(plaintarget.env)
            if strTargetType.find('Library') != - 1:
                tName = plaintarget.name
                env.AppendUnique(LIBS=[tName])
        except:
            pass

    # specify public headers here
    installPath = Dir(includeBasedir).Dir(includeSubdir)
    env.AppendUnique(CPPPATH=[installPath])

class TargetMaker:
    def __init__(self, packagename, tlist, programLookup):
        self.packagename = packagename
        self.targetlist = tlist.copy()
        self.programLookup = programLookup

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
            depList = [item for item in v.get('requires', []) + v.get('linkDependencies', []) if item.startswith(self.packagename + '.')]
            for ftn in depList:
                pkgname, tname = splitTargetname(ftn)
                if self.packagename == pkgname and self.targetlist.has_key(tname):
                    self.recurseCreate(tname)
            self.doCreateTarget(self.packagename, k, v)

    def doCreateTarget(self, pkgname, name, targetBuildSettings):
        plaintarget = None
        target = None
        if targetBuildSettings.has_key('targetType'):
            envVars = targetBuildSettings.get('appendUnique', {})
            targetEnv = self.createTargetEnv(name, targetBuildSettings, envVars)
            func = getattr(targetEnv, targetBuildSettings.get('targetType', ''), None)
            if func:
                kw = {}
                kw['pkgname'] = pkgname
                kw['buildSettings'] = targetBuildSettings
                sources = targetBuildSettings.get('sourceFiles', [])
                targets = apply(func, [name, sources], kw)
                import types
                if isinstance(targets, types.TupleType):
                    plaintarget, target = targets
                else:
                    plaintarget = target = targets

        self.programLookup.setPackageTarget(pkgname, name, plaintarget, target)

    def createTargetEnv(self, targetname, targetBuildSettings, envVars={}):
        linkDependencies = targetBuildSettings.get('linkDependencies', [])
        includeSubdir = targetBuildSettings.get('includeSubdir', '')
        # create environment for target
        targetEnv = CloneBaseEnv()

        # update environment by adding dependencies to used modules
        setModuleDependencies(targetEnv, linkDependencies)

        # win32 specific define to export all symbols when creating a DLL
        newVars = targetBuildSettings.get('public', EnvVarDict())
        if newVars:
            newVars = newVars.get('appendUnique', EnvVarDict())
        newVars += EnvVarDict(envVars)
        targetEnv.AppendUnique(**newVars)

        # maybe we need to add this libraries local include path when building it (if different from .)
        targetEnv.AppendUnique(CPPPATH=[Dir(includeSubdir)])

        return targetEnv

def createTargets(packagename, buildSettings):
    TargetMaker(packagename, buildSettings, programLookup).createTargets()

baseEnv.lookup_list.append(programLookup.lookup)

failedTargets = True
for ftname in BUILD_TARGETS:
    packagename, target = splitTargetname(ftname)
    print 'trying to find target [%s]' % ftname
    if programLookup.hasPackage(packagename):
        programLookup.lookup(ftname)
        failedTargets = False
    else:
        print 'package [%s] not found, aborting' % packagename
        failedTargets = True
        break

if failedTargets:
    print 'loading all SConscript files to find target'
    for tname in packages:
        programLookup.lookup(tname)

print "BUILD_TARGETS is ", map(str, BUILD_TARGETS)

def print_build_failures():
    from SCons.Script import GetBuildFailures
    if GetBuildFailures():
        print "scons: printing failed nodes"
        for bf in GetBuildFailures():
            if str(bf.action) != "installFunc(target, source, env)":
                print bf.node
        print "scons: done printing failed nodes"

atexit.register(print_build_failures)
