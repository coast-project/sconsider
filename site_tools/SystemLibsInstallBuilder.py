import subprocess, re, os, functools, itertools, operator, threading
import SCons, SConsider, LibFinder

systemLibTargets = {} # needs locking because it is manipulated during multi-threaded build phase
systemLibTargetsRLock = threading.RLock()
aliasPrefix = '__SystemLibs_'

def installSystemLibs(source):
    """
    This function is called during the build phase and adds targets dynamically to the dependency tree.
    """
    if not SCons.Util.is_List(source):
        source = [source]
    
    if len(source) < 1:
        return None

    env = source[0].get_env()
    ownlibdir = env['BASEOUTDIR'].Dir(env['LIBDIR']).Dir(env['VARIANTDIR'])
    libdirs = filter(functools.partial(operator.ne, ownlibdir), env['LIBPATH'])
    finder = LibFinder.FinderFactory.getForPlatform(env["PLATFORM"])
    libdirs.extend(finder.getSystemLibDirs(env))
    deplibs = finder.getLibs(env, source, libdirs=libdirs)
    target = []
    
    # build phase could be multi-threaded
    with systemLibTargetsRLock:
        for deplib in deplibs:
            # take care of already created targets otherwise we would have multiple ways to build the same target 
            if deplib in systemLibTargets:
                libtarget = systemLibTargets[deplib]
            else:
                libtarget = env.Install(ownlibdir, env.File(deplib))
                systemLibTargets[deplib] = libtarget
            target.extend(libtarget)
    
    # add targets as dependency of the intermediate target
    env.Depends(aliasPrefix+source[0].name, target)

def generate(env):
    """
    Add the options, builders and wrappers to the current Environment.
    """
    createDeferredAction = SCons.Action.ActionFactory(installSystemLibs, lambda source: '')
    def createDeferredTarget(env, source):
        # bind 'source' parameter to an Action which is called in the build phase and
        # create a dummy target which always will be built
        target = env.Command(source[0].name+'_dummy', source, createDeferredAction(source))
        # create intermediate target to which we add dependency in the build phase
        return env.Alias(aliasPrefix+source[0].name, target)
    env.AddMethod(createDeferredTarget, "InstallSystemLibs")

def exists(env):
   return True
