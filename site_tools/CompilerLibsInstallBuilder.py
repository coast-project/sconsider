import pdb
import subprocess, re, os, functools, itertools, threading
import SCons, SConsider

compilerLibNames = ['stdc++', 'gcc_s', 'gcc']

compilerLibTargets = {} # needs locking because it is manipulated during multi-threaded build phase
compilerLibTargetsRLock = threading.RLock()

def unique(seq): 
    """
    Generates an order preserved list with unique items 
    """
    seen = set()
    result = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result

class UnixFinder(object):
    def __filterLibs(self, env, filename):
        basename = os.path.basename(filename)
        libnames = '('+'|'.join(map(re.escape, compilerLibNames))+')'
        match = re.match(r'^'+re.escape(env.subst('$SHLIBPREFIX'))+libnames+re.escape(env.subst('$SHLIBSUFFIX')), basename)
        return bool(match)

    def getLibs(self, env, source, libdirs):
        env['ENV']['LD_LIBRARY_PATH'] = libdirs
        ldd = subprocess.Popen(['ldd', source[0].abspath], stdout=subprocess.PIPE, env=SConsider.getFlatENV(env))
        out, err = ldd.communicate()
        return filter(functools.partial(self.__filterLibs, env), re.findall('^.*=>\s*([^\s^\(]*)', out, re.MULTILINE))

    def getSystemLibDirs(self, env, source):
        libdirs = []
        linkercmd = env.subst('$LINK', target=source, source=source[0].sources)
        cmdargs = [linkercmd, '-print-search-dirs'] + env.subst('$LINKFLAGS').split(' ')
        linker = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, env=SConsider.getFlatENV(env))
        out, err = linker.communicate()
        match = re.search('^libraries.*=(.*)$', out, re.MULTILINE)
        if match:
            libdirs.extend( unique(filter(os.path.exists, map(os.path.abspath, match.group(1).split(os.pathsep)))) )
        return libdirs

class Win32Finder(object):
    def __filterLibs(self, env, filename):
        basename = os.path.basename(filename)
        libnames = '('+'|'.join(map(re.escape, compilerLibNames))+')'
        match = re.match(r'^('+re.escape(env.subst('$LIBPREFIX'))+')?'+libnames+'.*'+re.escape(env.subst('$SHLIBSUFFIX'))+'$', basename)
        return bool(match)

    def __findFileInPath(self, filename, paths):
        for path in paths:
            if os.path.isfile(os.path.join(path, filename)):
                return os.path.abspath(os.path.join(path, filename))
        return None

    def getLibs(self, env, source, libdirs):
        ldd = subprocess.Popen(['objdump', '-p', source[0].abspath], stdout=subprocess.PIPE, env=SConsider.getFlatENV(env))
        out, err = ldd.communicate()
        deplibs = filter(functools.partial(self.__filterLibs, env), re.findall('DLL Name:\s*(\S*)', out, re.MULTILINE))
        return filter(lambda val: bool(val), itertools.imap(functools.partial(self.__findFileInPath, paths=libdirs), deplibs))

    def getSystemLibDirs(self, env, source):
        return os.environ['PATH'].split(os.pathsep)

def installCompilerLibs(source):
    """
    This function is called during the build phase and adds targets dynamically to the dependency tree.
    """
    if not SCons.Util.is_List(source):
        source = [source]
    
    if len(source) < 1:
        return None

    env = SConsider.cloneBaseEnv()
    
    if env["PLATFORM"] == 'win32':
        finder = Win32Finder()
    else:
        finder = UnixFinder()

    libdirs = finder.getSystemLibDirs(env, source)
    ownlibdir = env['BASEOUTDIR'].Dir(env['LIBDIR']).Dir(env['VARIANTDIR'])
    libdirs.append( ownlibdir.abspath )
    
    deplibs = finder.getLibs(env, source, libdirs)
    target = []
    
    # build phase could be multi-threaded
    with compilerLibTargetsRLock:
        for deplib in deplibs:
            # take care of already created targets otherwise we would have multiple ways to build the same target 
            if deplib in compilerLibTargets:
                libtarget = compilerLibTargets[deplib]
            else:
                libtarget = env.Install(ownlibdir, env.File(deplib))
                compilerLibTargets[deplib] = libtarget
            target.extend(libtarget)
    
    # add targets as dependency of the intermediate target
    env.Depends('__CompilerLibs_'+source[0].name, target)

def generate(env):
    """
    Add the options, builders and wrappers to the current Environment.
    """
    createDeferredAction = SCons.Action.ActionFactory(installCompilerLibs, lambda source: '')
    def createDeferredTarget(env, source):
        # bind 'source' parameter to an Action which is called in the build phase and
        # create a dummy target which always will be built
        target = env.Command(source[0].name+'_dummy', source, createDeferredAction(source))
        # create intermediate target to which we add dependency in the build phase
        return env.Alias('__CompilerLibs_'+source[0].name, target)
    env.AddMethod(createDeferredTarget, "InstallCompilerLibs")

def exists(env):
   return True
