from __future__ import with_statement
import os, pdb, subprocess, optparse
from SCons.Script import AddOption, GetOption
import SCons.Action
import SCons.Builder

runtargets = {}
def setTarget(packagename, targetname, target):
    if SCons.Util.is_List(target) and len(target) > 0:
        target = target[0]
    runtargets.setdefault(packagename, {})[targetname] = target

def getTarget(packagename, targetname):
    return runtargets.get(packagename, {}).get(targetname, None)

def run(cmd, **kw):
    """Run a Unix command and return the exit code."""
    args = cmd.split(' ')
    return subprocess.call(args, **kw)

def emitPassedFile(target, source, env):
    target = []
    for src in source:
        path, scriptname = os.path.split(src.abspath)
        target.append(env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['LOGDIR']).Dir(env['VARIANTDIR']).File(scriptname+'.passed'))
    return (target, source)

def doTest(target, source, env):
    res = run(source[0].abspath + ' ' + env.get('runParams', ''))
    if res == 0:
        with open(target[0].abspath, 'w') as file:
            file.write("PASSED\n")
    return res

def doRun(target, source, env):
    res = run(source[0].abspath + ' ' + env.get('runParams', ''))
    return res

def getRunParams(buildSettings, defaultRunParams):
    runConfig = buildSettings.get('runConfig', {})
    if GetOption('runParams'):
        runParams = " ".join(GetOption('runParams'))
    else:
        runParams = runConfig.get('runParams', defaultRunParams)
    return runParams

def createAutoTarget(env, source, packagename, targetname, buildSettings, **kw):
    runConfig = buildSettings.get('runConfig', {})
    if not runConfig:
        return None
    
    factory = createRunTarget
    if runConfig.get('type', 'run') == 'test':
        factory = createTestTarget

    return factory(env, source, packagename, targetname, buildSettings, kw)

def createTestTarget(env, source, packagename, targetname, buildSettings, defaultRunParams='-all'):
    """Creates a target which runs a target given in parameter 'source'. If ran successfully a
    file is generated (name given in parameter 'target') which indicates that this runner-target
    doesn't need to be executed unless the dependencies changed. Command line parameters could be
    handed over by using --runparams="..." or by setting buildSettings['runConfig']['runParams'].
    The Fields 'setUp' and 'tearDown' in 'runConfig' accept a string (executed as shell command),
    a Python function (with arguments 'target', 'source', 'env') or any SCons.Action."""

    if not GetOption('run') and not GetOption('run-force'):
        return source
    
    if not SCons.Util.is_List(source):
        source = [source]
    
    if GetOption('run-force'):
        runner = env.RunBuilder(['dummyfile'], source, runParams=getRunParams(buildSettings, defaultRunParams))
    else:
        runner = env.TestBuilder([], source, runParams=getRunParams(buildSettings, defaultRunParams))
        
    runConfig = buildSettings.get('runConfig', {})
    setUp = runConfig.get('setUp', '')
    tearDown = runConfig.get('tearDown', '')

    if setUp:
        env.AddPreAction(runner, setUp)
    if tearDown:
        env.AddPostAction(runner, tearDown)

    env.Alias('test', runner)
    env.Alias(packagename, runner)
    
    setTarget(packagename, targetname, runner)
    return runner

def createRunTarget(env, source, packagename, targetname, buildSettings, defaultRunParams=''):
    """Creates a target which runs a target given in parameter 'source'. Command line parameters could be
    handed over by using --runparams="..." or by setting buildSettings['runConfig']['runParams']."""
    
    if not GetOption('run') and not GetOption('run-force'):
        return source
    
    if not SCons.Util.is_List(source):
        source = [source]

    runner = env.RunBuilder(['dummyfile'], source, runParams=getRunParams(buildSettings, defaultRunParams))
    env.Alias(packagename, runner)
    
    setTarget(packagename, targetname, runner)
    return runner

def generate(env):
    try:
        AddOption('--run', dest='run', action='store_true', default=False, help='Should we run the target')
        AddOption('--run-force', dest='run-force', action='store_true', default=False, help='Should we run the target and ignore .passed files')
        AddOption('--runparams', dest='runParams', action='append', type='string', default=[], help='The parameters to hand over')
    except optparse.OptionConflictError:
        pass

    TestAction = SCons.Action.Action(doTest, "Running Test '$SOURCE'")
    TestBuilder = SCons.Builder.Builder(action=[TestAction],
                                        emitter=emitPassedFile,
                                        single_source=True)

    RunAction = SCons.Action.Action(doRun, "Running Executable '$SOURCE'")
    RunBuilder = SCons.Builder.Builder(action=[RunAction],
                                              single_source=True)

    env.Append(BUILDERS={ 'TestBuilder' : TestBuilder })
    env.Append(BUILDERS={ 'RunBuilder' : RunBuilder })
    env.AddMethod(createTestTarget, "TestTarget")
    env.AddMethod(createRunTarget, "RunTarget")
    env.AddMethod(createAutoTarget, "AutoRunTarget")

def exists(env):
    return 1;
