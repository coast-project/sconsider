import pdb
import subprocess, re, os, functools, itertools, threading
import SCons, SConsider, LibFinder

compilerLibTargets = {} # needs locking because it is manipulated during multi-threaded build phase
compilerLibTargetsRLock = threading.RLock()

def installCompilerLibs(source):
    """
    This function is called during the build phase and adds targets dynamically to the dependency tree.
    """
    if not SCons.Util.is_List(source):
        source = [source]
    
    if len(source) < 1:
        return None

    env = SConsider.cloneBaseEnv()
    finder = LibFinder.FinderFactory.getForPlatform(env["PLATFORM"])

    libdirs = finder.getSystemLibDirs(env, source)
    ownlibdir = env['BASEOUTDIR'].Dir(env['LIBDIR']).Dir(env['VARIANTDIR'])
    libdirs.append( ownlibdir.abspath )
    
    deplibs = finder.getLibs(env, source, libdirs, ['stdc++', 'gcc_s', 'gcc'])
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
