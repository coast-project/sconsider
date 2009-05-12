#import eol_scons
import os, platform, SCons, glob, re, atexit, sys, traceback, commands, pdb, dircache

from SCons.Script import *

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
#globaltools = Split("""default coast_options""")
usetools = globaltools + GetOption('usetools')
print 'tools to use %s' % Flatten(usetools)

baseEnv = dEnv.Clone(tools=usetools)

baseEnv.Alias("NoTarget")
# do not try to fetch sources from a SCM repository if not there
baseEnv.SourceCode(".", None)

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

Export('baseEnv')

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

baseEnv.Append(PFILESDIR=Dir('syspfiles'))
baseEnv.Append(CONFIGDIR=Dir('config'))
baseEnv.Append(DATADIR=Dir('data'))
baseEnv.Append(XMLDIR=Dir('xml'))
baseEnv.Append(PYTHONDIR=Dir(baseoutdir).Dir('python'))
baseEnv['CONFIGURELOG'] = str(Dir(baseoutdir).File("config.log"))
baseEnv['CONFIGUREDIR'] = str(Dir(baseoutdir).Dir(".sconf_temp"))
#baseEnv.AppendUnique(CPPPATH = ['.'])
#baseEnv.AppendUnique(CPPPATH = ['src'])
#baseEnv.AppendUnique(CPPPATH = [baseEnv['INCDIR']])
baseEnv.AppendUnique(LIBPATH=[baseoutdir.Dir(baseEnv['LIBDIR'])])

def CoastFindPackages(directory, direxcludes=[]):
    packages = []
    reLib = re.compile('^.*Lib.py$')
    reSconscript = re.compile('^SConscript$')
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not d in direxcludes]
        for name in filenames:
            if reLib.match(name):
                thePath = os.path.abspath(dirpath)
                SCons.Tool.DefaultToolpath.append(thePath)
                print 'appended toolpath  [%s]' % thePath
            elif reSconscript.match(name):
                thePath = dirpath
                packages.append(thePath)
                print 'appended sconspath [%s]' % thePath
    return packages

if True: #not baseEnv.GetOption('help'):
    direxcludes = ['build', 'CVS', 'src', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules', 'config']
    if not baseEnv.GetOption('exclude') == None:
        direxcludes.extend(baseEnv.GetOption('exclude'))
    packages = CoastFindPackages(Dir('#').path, direxcludes)
    Export('packages')

    for pkg in packages:
        try:
            print 'executing SConscript for package [%s]' % pkg
            baseEnv.SConscript(os.path.join(pkg, "SConscript"), build_dir=os.path.join(baseoutdir.path, pkg, 'build', variant), duplicate=0)
        except Exception, inst:
            print "scons: Skipped " + pkg.lstrip(baseoutdir.path + os.sep) + " because of exceptions: " + str(inst)
            traceback.print_tb(sys.exc_info()[2])
    if baseEnv.GetOption('clean'):
        baseEnv.Default('test')

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
