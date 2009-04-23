#import eol_scons
import os,platform,SCons,glob,re,atexit,sys,traceback,commands,pdb

from SCons.Script import *

# SconsBuilder may work with earlier version,
# but it was build and tested against SCons 1.0.0
SCons.Script.EnsureSConsVersion(1,0,0)
# SconsBuilder may work with earlier version,
# but it was build and tested against Python 2.4
SCons.Script.EnsurePythonVersion(2,4)

variant = "Unknown"
myplatf = str(SCons.Platform.Platform())

if myplatf == "posix":
    variant = platform.system()+"_"+platform.libc_ver()[0]+"_"+platform.libc_ver()[1]+"-"+platform.machine()+"-"+platform.architecture()[0]
if myplatf == "sunos":
    variant = platform.system()+"_"+platform.release()+"-"+platform.processor()+"-"+platform.architecture()[0]
if myplatf == "darwin":
    version = commands.getoutput("sw_vers -productVersion")
    cpu = commands.getoutput("arch")
    if version.startswith("10.5"):
        variant="leopard-"
    if version.startswith("10.4"):
        variant="tiger-"
    variant+=cpu+"-"
    if cpu.endswith("64"):
        variant+="64bit"
    else:
        variant+="32bit"
if myplatf == "cygwin":
    variant = platform.system()+"-"+platform.machine()+"-"+platform.architecture()[0]
if myplatf == "win32":
    variant = platform.release()+"-"+platform.machine()+"-"+platform.architecture()[0]

print "compilation variant [",variant,"]"

if False:
    print "platform.dist:",platform.dist()
    print "platform.arch:",platform.architecture()
    print "platform.machine:",platform.machine()
    print "platform.libc:",platform.libc_ver()
    print "platform.release:",platform.release()
    print "platform.version:",platform.version()
    print "platform.proc:",platform.processor()
    print "platform.system:",platform.system()

AddOption('--baseoutdir', dest='baseoutdir', action='store', nargs=1, type='string', default='#', metavar='DIR', help='Directory containing packages superseding installed ones. Relative paths not supported!')
AddOption('--exclude', dest='exclude', action='append', nargs=1, type='string', metavar='DIR', help='Directory containing a SConscript file that should be ignored.')
AddOption('--usetool', dest='usetools', action='append', nargs=1, type='string', default=[], metavar='VAR', help='tools to use when constructing default environment')
AddOption('--appendPath', dest='appendPath', action='append', nargs=1, type='string', metavar='DIR', help='Directory to append to PATH environment variable.')
AddOption('--prependPath', dest='prependPath', action='append', nargs=1, type='string', metavar='DIR', help='Directory to prepend to PATH environment variable.')

baseoutdir = Dir(GetOption('baseoutdir'))
print 'base output dir [%s]' % baseoutdir.abspath

dEnv=DefaultEnvironment()
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

baseEnv=dEnv.Clone(tools=usetools)

baseEnv.Alias("NoTarget")
# do not try to fetch sources from a SCM repository if not there
baseEnv.SourceCode(".", None)

ssfile=os.path.join(Dir('#').path,'.sconsign.'+variant)
SConsignFile(ssfile)

Export('baseEnv')

#########################
#  Project Environment  #
#########################
baseEnv.Append(LIBDIR        = Dir(baseoutdir).Dir('lib').Dir(variant))
baseEnv.Append(BINDIR        = Dir(baseoutdir).Dir('bin').Dir(variant))
baseEnv.Append(SCRIPTDIR     = Dir(baseoutdir).Dir('scripts').Dir(variant))
baseEnv.Append(INCDIR        = Dir(baseoutdir).Dir('include'))
baseEnv.Append(PFILESDIR     = Dir(baseoutdir).Dir('syspfiles'))
baseEnv.Append(DATADIR       = Dir(baseoutdir).Dir('data'))
baseEnv.Append(XMLDIR        = Dir(baseoutdir).Dir('xml'))
baseEnv.Append(TESTDIR       = baseEnv['BINDIR'])
baseEnv.Append(TESTSCRIPTDIR = baseEnv['SCRIPTDIR'])
#baseEnv.Append(TESTDIR       = Dir(baseoutdir).Dir('tests').Dir(variant))
#baseEnv.Append(TESTSCRIPTDIR = baseEnv['TESTDIR'])
baseEnv.Append(PYTHONDIR     = Dir(baseoutdir).Dir('python'))
baseEnv['CONFIGURELOG']      = str(Dir(baseoutdir).File("config.log"))
baseEnv['CONFIGUREDIR']      = str(Dir(baseoutdir).Dir(".sconf_temp"))
#baseEnv.AppendUnique(CPPPATH = ['.'])
#baseEnv.AppendUnique(CPPPATH = ['src'])
#baseEnv.AppendUnique(CPPPATH = [baseEnv['INCDIR']])
baseEnv.AppendUnique(LIBPATH = [baseEnv['LIBDIR']])

#########################
#  External Libraries   #
#########################
globalexternalsfilename = 'externals.scons.py'
filename = os.path.join('#', 'site_scons', globalexternalsfilename)
SConscript(filename)

if True: #not baseEnv.GetOption('help'):
    directories = [Dir('#').path]
    packages = []
    # Add packages to package list and add packages to tool path if they have one
    while len(directories)>0:
        directory = directories.pop(0)
        listed = os.listdir(directory)
        listed.sort()
        pruned = []
        # Remove excluded directories
        if not baseEnv.GetOption('exclude') == None:
            for excluded in baseEnv.GetOption('exclude'):
                if excluded in listed:
                    listed.remove(excluded)
        # Remove duplicate packages
        while len(listed)>0:
            curDir = listed.pop(0)
            package = re.compile('-.*$').sub('', curDir)
            while len(listed)>0 and re.match(package+'-.*', listed[0]):
                curDir = listed.pop(0)
            pruned.append(curDir)
        # Check if they contain SConscript and tools
        for name in pruned:
            package = re.compile('-.*$').sub('',name)
            if not name in ['build', 'CVS', 'src', 'cmt', 'mgr', 'data', 'xml', 'pfiles', 'doc', 'bin', 'lib']:
                fullpath = os.path.join(directory,name)
                if os.path.isdir(fullpath):
                    directories.append(fullpath)
                    if os.path.isfile(os.path.join(fullpath,"SConscript")):
                        packages.append(fullpath)
                        print 'appended sconspath [%s]' % fullpath
                    if os.path.isfile(os.path.join(fullpath, package+'Lib.py')):
                        SCons.Tool.DefaultToolpath.append(os.path.abspath(fullpath))
                        print 'appended toolpath  [%s]' % os.path.abspath(fullpath)

    Export('packages')

    for pkg in packages:
        try:
            print 'executing SConscript for package [%s]' % pkg
            baseEnv.SConscript(os.path.join(pkg,"SConscript"), build_dir = os.path.join(baseoutdir.path, pkg, 'build', variant), duplicate = 0)
        except Exception, inst:
            print "scons: Skipped "+pkg.lstrip(baseoutdir.path+os.sep)+" because of exceptions: "+str(inst)
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
