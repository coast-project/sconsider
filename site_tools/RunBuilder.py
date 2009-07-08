from __future__ import with_statement
import os, pdb, subprocess
from SCons.Script import AddOption, GetOption
import SCons.Action
import SCons.Builder

def run(cmd, **kw):
    """Run a Unix command and return the exit code."""
    args = cmd.split(' ')
    return subprocess.call(args, **kw)

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

def createTarget(env, builder, target, source, buildSettings, defaultRunParams):
    if not SCons.Util.is_List(target):
        target = [target]
    if not SCons.Util.is_List(source):
        source = [source]

    return builder(target, source, runParams=getRunParams(buildSettings, defaultRunParams))

def createTestTarget(env, source, buildSettings, defaultRunParams='-all'):
    """Creates a target which runs a target given in parameter 'source'. If ran successfully a
    file is generated (name given in parameter 'target') which indicates that this runner-target
    doesn't need to be executed unless the dependencies changed. Command line parameters could be
    handed over by using --runparams="..." or by setting buildSettings['runConfig']['runParams'].
    The Fields 'setUp' and 'tearDown' in 'runConfig' accept a string (executed as shell command),
    a Python function (with arguments 'target', 'source', 'env') or any SCons.Action."""

    if not GetOption('run'):
        return source

    runner = createTarget(env, env.__TestBuilder, [], source, buildSettings, defaultRunParams)
    runConfig = buildSettings.get('runConfig', {})
    setUp = runConfig.get('setUp', '')
    tearDown = runConfig.get('tearDown', '')

    if setUp:
        env.AddPreAction(runner, setUp)
    if tearDown:
        env.AddPostAction(runner, tearDown)

    return runner

def createRunTarget(env, source, buildSettings, defaultRunParams=''):
    """Creates a target which runs a target given in parameter 'source'. Command line parameters could be
    handed over by using --runparams="..." or by setting buildSettings['runConfig']['runParams']."""

    if not GetOption('run'):
        return source

    return createTarget(env, env.__RunBuilder, 'dummyfile', source, buildSettings, defaultRunParams)

def passedFileEmitter(target, source, env):
    target = []
    for src in source:
        path, scriptname = os.path.split(src.abspath)
        target.append(env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['LOGDIR']).Dir(env['VARIANTDIR']).File(scriptname+'.passed'))
    return (target, source)

def generate(env):
    AddOption('--run', dest='run', action='store_true', default=False, help='Should we run the target')
    AddOption('--runparams', dest='runParams', action='append', type='string', default=[], help='The parameters to hand over')

    TestAction = SCons.Action.Action(doTest, "Running Test '$SOURCE'")
    TestBuilder = SCons.Builder.Builder(action=[TestAction],
                                        emitter=passedFileEmitter,
                                        single_source=True)

    RunAction = SCons.Action.Action(doRun, "Running Executable '$SOURCE'")
    RunBuilder = SCons.Builder.Builder(action=[RunAction],
                                              single_source=True)

    env.Append(BUILDERS={ '__TestBuilder' : TestBuilder })
    env.Append(BUILDERS={ '__RunBuilder' : TestBuilder })
    env.AddMethod(createTestTarget, "TestBuilder")
    env.AddMethod(createRunTarget, "RunBuilder")

def exists(env):
    return 1;
