import os, platform, SCons, glob, re, atexit, sys, traceback, commands, pdb, dircache
import SomeUtils

from SCons.Script import AddOption, GetOption, Dir, DefaultEnvironment, Split, Flatten, SConsignFile, Export, BUILD_TARGETS
from SomeUtils import *

# SconsBuilder may work with earlier version,
# but it was build and tested against SCons 1.0.0
SCons.Script.EnsureSConsVersion(1, 0, 0)
# SconsBuilder may work with earlier version,
# but it was build and tested against Python 2.4
SCons.Script.EnsurePythonVersion(2, 4)

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

dEnv = DefaultEnvironment()
if GetOption('prependPath'):
    dEnv.PrependENVPath('PATH', GetOption('prependPath'))
    print 'prepended path is [%s]' % dEnv['ENV']['PATH']
if GetOption('appendPath'):
    dEnv.AppendENVPath('PATH', GetOption('appendPath'))
    print 'appended path is [%s]' % dEnv['ENV']['PATH']

globaltools = Split("""setupBuildTools coast_options""")
usetools = globaltools + GetOption('usetools')
print 'tools to use %s' % Flatten(usetools)

baseEnv = dEnv.Clone(tools=usetools)

variant = "Unknown"
myplatf = str(SCons.Platform.Platform())
targetbits = GetOption('archbits')

if myplatf == "posix":
    variant = platform.system() + "_" + platform.libc_ver()[0] + "_" + platform.libc_ver()[1] + "-" + platform.machine()
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
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not d in direxcludes]
        for name in filenames:
            rmatch = reLib.match(name)
            if rmatch:
                pkgname = rmatch.group(1)
                if not packages.has_key(pkgname):
                    packages[pkgname] = {}
                thePath = os.path.abspath(dirpath)
                sys.path.append(thePath)
                packages[pkgname]['libfile'] = Dir(thePath).File(name)
                print 'appended toolpath  [%s]' % thePath
                thePath = Dir(dirpath).File('SConscript')
                if os.path.isfile(thePath.abspath):
                    packages[pkgname]['scriptfile'] = thePath
                    print 'appended sconspath [%s]' % thePath
    return packages

def CloneBaseEnv():
    return baseEnv.Clone()

class ProgramLookup:
    def __init__(self, env, packages, baseoutdir, variant):
        self.env = env
        self.packages = packages
        self.baseoutdir = baseoutdir.abspath
        self.variant = variant

    def hasTarget(self, name):
        return self.packages.has_key(name)

    def lookup(self, name, **kw):
#        print 'looking up [%s]' % name
        if self.hasTarget(name):
            if not self.packages[name].has_key('loaded'):
                self.packages[name]['loaded'] = True
                if self.packages[name].has_key('scriptfile'):
                    scfile = self.packages[name]['scriptfile']
                    pkg = os.path.dirname(scfile.path)
                    builddir = os.path.join(self.baseoutdir, pkg, 'build', self.variant)
                    print 'executing SConscript for package [%s]' % name
                    self.env.SConscript(scfile, build_dir=builddir, duplicate=0)

        return None

direxcludes = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules', 'config']
if not baseEnv.GetOption('exclude') == None:
    direxcludes.extend(baseEnv.GetOption('exclude'))
packages = CoastFindPackagesDict(Dir('#').path, direxcludes)
programLookup = ProgramLookup(baseEnv, packages, baseoutdir, variant)

def DependsOn(env, targetname, **kw):
    programLookup.lookup(targetname)
    modname = targetname + 'Lib'
    sys.modules[modname] = __import__(modname)
    modDict = sys.modules[modname].__dict__
    if modDict.get('generate', None):
        return sys.modules[modname].generate(env, **kw)

    buildDict = modDict.get('buildSettings', None)
    if not buildDict:
        print 'Warning: buildSettings dictionary for module %s not defined!' % modname
        return None
    return ExternalDependencies(env, targetname, buildDict, target=modDict.get('target', None), **kw)

def setModuleDependencies(env, modules, **kw):
    for mod in modules:
        DependsOn(env, mod, **kw)

def ExternalDependencies(env, pkgname, buildDict, target=None, **kw):
    libDepends= buildDict.get('libDepends', [])
    includeBasedir= buildDict.get('includeBasedir', '')
    includeSubdir= buildDict.get('includeSubdir', '')
    appendUnique= buildDict.get('appendUnique', {})

    # this libraries dependencies
    setModuleDependencies(env, libDepends)

    try:
        strTargetType = target[0].builder.get_name(target[0].env)
        if strTargetType.find('Library'):
            env.Tool('addLibrary', library=[pkgname])
    except:
        pass

    # flags / settings used by this library and users of it
    env.AppendUnique(**appendUnique)

    # specify public headers here
    setIncludePath(env, pkgname, includeSubdir, basedir=includeBasedir, internal=False)

    return target

baseEnv.lookup_list.append(programLookup.lookup)

failedTargets = True
for tname in BUILD_TARGETS:
    print 'trying to find target [%s]' % tname
    if programLookup.hasTarget(tname):
        programLookup.lookup(tname)
        failedTargets = False
    else:
        print 'target [%s] not found, aborting' % tname
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
