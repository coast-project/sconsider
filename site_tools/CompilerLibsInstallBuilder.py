import pdb
import subprocess, re, os, functools, threading
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

def filterLibs(env, filename):
    for name in compilerLibNames:
        if env.subst('$SHLIBPREFIX')+name+env.subst('$SHLIBSUFFIX') in os.path.basename(filename):
            return True
    return False

def installCompilerLibs(source):
    """
    This function is called during the build phase and adds targets dynamically to the dependency tree.
    """
    if not SCons.Util.is_List(source):
        source = [source]
    
    if len(source) != 1:
        return []

    env = SConsider.cloneBaseEnv()
    
    libdirs = []
    linkercmd = env.subst('$LINK', target=source, source=source[0].sources)
    cmdargs = [linkercmd, '-print-search-dirs'] + env.subst('$LINKFLAGS').split(' ')
    linker = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, env=SConsider.getFlatENV(env))
    out, err = linker.communicate()
    match = re.search('^libraries.*=(.*)$', out, re.MULTILINE)
    if match:
        libdirs.extend( unique(filter(os.path.exists, map(os.path.abspath, match.group(1).split(':')))) )
    ownlibdir = env['BASEOUTDIR'].Dir(env['LIBDIR']).Dir(env['VARIANTDIR'])
    libdirs.append( ownlibdir.abspath )
    
    env['ENV']['LD_LIBRARY_PATH'] = libdirs
    
    ldd = subprocess.Popen(['ldd', source[0].abspath], stdout=subprocess.PIPE, env=SConsider.getFlatENV(env))
    out, err = ldd.communicate()
    deplibs = filter(functools.partial(filterLibs, env), re.findall('^.*=>\s*([^\s^\(]*)', out, re.MULTILINE))

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
    env.Depends(source[0].name+'_CompilerLibs', target)

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
        return env.Alias(source[0].name+'_CompilerLibs', target)
    env.AddMethod(createDeferredTarget, "InstallCompilerLibs")

def exists(env):
   return True
