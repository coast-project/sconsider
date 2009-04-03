import os,platform,SCons,glob,re,atexit,sys,traceback,commands,pdb

from SCons.Script import *

# SconsBuilder may work with earlier version,
# but it was build and tested against SCons 1.0.0
SCons.Script.EnsureSConsVersion(1,0,0)
# SconsBuilder may work with earlier version,
# but it was build and tested against Python 2.4
SCons.Script.EnsurePythonVersion(2,4)

baseEnv=Environment()

baseEnv.Tool('generateScript')
baseEnv.Alias("NoTarget")
baseEnv.SourceCode(".", None)

variant = "Unknown"
if baseEnv['PLATFORM'] == "posix":
    #variant = platform.dist()[0]+platform.dist()[1]+"-"+platform.machine()+"-"+platform.architecture()[0]
    variant = platform.system()+"_"+platform.libc_ver()[0]+"-"+platform.libc_ver()[1]+"_"+platform.machine()+"-"+platform.architecture()[0]
if baseEnv['PLATFORM'] == "darwin":
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
if baseEnv['PLATFORM'] == "win32":
    variant = platform.release()+"-"+"i386"+"-"+platform.architecture()[0]

objdir="."+variant
pbasepath=os.path.abspath(os.getcwd())

print "compilation variant [",variant,"]"
print "object output variant [",objdir,"]"
print "object base output dir [",pbasepath,"]"

#print "platform.dist:",platform.dist()
#print "platform.arch:",platform.architecture()
#print "platform.machine:",platform.machine()
#print "platform.libc:",platform.libc_ver()
#print "platform.release:",platform.release()
#print "platform.version:",platform.version()
#print "platform.proc:",platform.processor()
#print "platform.system:",platform.system()

AddOption('--with-COAST-ROOT', dest = 'COAST-ROOT', action='store', nargs=1, type='string', default='.', metavar='DIR', help='location of COAST_ROOT directory')
AddOption('--with-COAST-OUTDIR', dest = 'COAST-OUTDIR', action='store', nargs=1, type='string', default='.', metavar='DIR', help='location of COAST_OUTDIR type directory where to place files to install')
AddOption('--rm', dest='rm', action='store_true', help='Enable output helpful for RM output parsing')
AddOption('--supersede', dest='supersede', action='store', nargs=1, type='string', default='.', metavar='DIR', help='Directory containing packages superseding installed ones. Relative paths not supported!')
AddOption('--exclude', dest='exclude', action='append', nargs=1, type='string', metavar='DIR', help='Directory containing a SConscript file that should be ignored.')
AddOption('--user-release', dest='userRelease', nargs=1, type='string', action='store', metavar='FILE', help='Creates a compressed user release and stores it in FILE')

override = baseEnv.GetOption('supersede')
print 'override dir [%s]' % os.path.abspath(override)
SConsignFile(os.path.join(override,'.sconsign.dblite'))

Export('baseEnv')

print 'variant object dir [%s]' % objdir
baseEnv['SCB_VARIANT_DIR'] = objdir

#sconscriptfile = os.path.join(os.path.abspath(objdir), '.sconsign')
#if not baseEnv.GetOption('clean'):
#    Mkdir(os.path.dirname(sconscriptfile))
#    SConsignFile(sconscriptfile)

#########################
#  Project Environment  #
#########################
baseEnv.Append(LIBDIR        = Dir(override).Dir('lib').Dir(variant))
baseEnv.Append(BINDIR        = Dir(override).Dir('bin').Dir(variant))
baseEnv.Append(SCRIPTDIR     = Dir(override).Dir('scripts').Dir(variant))
baseEnv.Append(INCDIR        = Dir(override).Dir('include'))
baseEnv.Append(PFILESDIR     = Dir(override).Dir('syspfiles'))
baseEnv.Append(DATADIR       = Dir(override).Dir('data'))
baseEnv.Append(XMLDIR        = Dir(override).Dir('xml'))
baseEnv.Append(TOOLDIR       = Dir(override).Dir('sconsTools'))
baseEnv.Append(TESTDIR       = baseEnv['BINDIR'])
baseEnv.Append(TESTSCRIPTDIR = baseEnv['SCRIPTDIR'])
baseEnv.Append(PYTHONDIR     = Dir(override).Dir('python'))
baseEnv['CONFIGURELOG']      = str(Dir(override).File("config.log"))
baseEnv['CONFIGUREDIR']      = str(Dir(override).Dir(".sconf_temp"))
#baseEnv.AppendUnique(CPPPATH = ['.'])
#baseEnv.AppendUnique(CPPPATH = ['src'])
#baseEnv.AppendUnique(CPPPATH = [baseEnv['INCDIR']])
#baseEnv.AppendUnique(LIBPATH = [baseEnv['LIBDIR']])
baseEnv.AppendUnique(CPPPATH = os.path.join(os.path.abspath('.'),'include'))
baseEnv.AppendUnique(LIBPATH = os.path.join(os.path.abspath('.'),'lib',variant))
#inst_incdir = os.path.join(os.path.abspath(baseEnv.GetOption('COAST-OUTDIR')),'include')
#inst_libdir = os.path.join(os.path.abspath(baseEnv.GetOption('COAST-OUTDIR')),'lib',variant)
#inst_bindir = os.path.join(os.path.abspath(baseEnv.GetOption('COAST-OUTDIR')),'bin',variant)
#baseEnv['INST_INCDIR'] = Dir(inst_incdir)
#baseEnv['INST_LIBDIR'] = Dir(inst_libdir)
#baseEnv['INST_BINDIR'] = Dir(inst_bindir)
#baseEnv.AppendUnique(CPPPATH = inst_incdir)
#baseEnv.AppendUnique(LIBPATH = inst_libdir)

##################
# Create release #
##################
if baseEnv.GetOption('userRelease'):
    if baseEnv['PLATFORM'] != 'win32':
        baseEnv['TARFLAGS']+=' -z'
        baseEnv.Default(baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['LIBDIR']))
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['BINDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['SCRIPTDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['INCDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['PFILESDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['DATADIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['XMLDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['TOOLDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['TESTDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['TESTSCRIPTDIR'])
        baseEnv.Tar(baseEnv.GetOption('userRelease'), baseEnv['PYTHONDIR'])
    else:
        baseEnv.Default(baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['LIBDIR']))
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['BINDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['SCRIPTDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['INCDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['PFILESDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['DATADIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['XMLDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['TOOLDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['TESTDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['TESTSCRIPTDIR'])
        baseEnv.Zip(baseEnv.GetOption('userRelease'), baseEnv['PYTHONDIR'])
    Return()

#########################
#  External Libraries   #
#########################
globalexternalsfilename = 'externals.scons'
filename = globalexternalsfilename
#filename = os.path.join(GetOption('site_dir'), globalexternalsfilename)
SConscript(filename)

############################
# Package Specific Options #
############################
SConscript('package.scons')

def listFiles(files, **kw):
    allFiles = []
    for file in files:
        globFiles = Glob(file)
        newFiles = []
        for globFile in globFiles:
            if 'recursive' in kw and kw.get('recursive') and os.path.isdir(globFile.srcnode().abspath) and os.path.basename(globFile.srcnode().abspath) != 'CVS':
                allFiles+=listFiles([str(Dir('.').srcnode().rel_path(globFile.srcnode()))+"/*"], recursive = True)
            if os.path.isfile(globFile.srcnode().abspath):
                allFiles.append(globFile)
    return allFiles

Export('listFiles')

if not baseEnv.GetOption('help'):
    directories = [override]
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

    if not override == '.':
        SCons.Tool.DefaultToolpath.append(os.path.abspath(str(Dir('.').Dir('sconsTools'))))

    Export('packages')

    for pkg in packages:
        try:
            print 'executing SConscript for package [%s]' % pkg
            baseEnv.SConscript(os.path.join(pkg,"SConscript"), build_dir = os.path.join(pkg, 'build', variant))
        except Exception, inst:
            print "scons: Skipped "+pkg.lstrip(override+os.sep)+" because of exceptions: "+str(inst)
            traceback.print_tb(sys.exc_info()[2])
    if baseEnv.GetOption('clean'):
        baseEnv.Default('test')

def print_build_failures():
    from SCons.Script import GetBuildFailures
    if GetBuildFailures():
        print "scons: printing failed nodes"
        for bf in GetBuildFailures():
            if str(bf.action) != "installFunc(target, source, env)":
                print bf.node
        print "scons: done printing failed nodes"

atexit.register(print_build_failures)
