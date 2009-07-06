import os, pdb
from SCons.Script import AddOption, GetOption
import SCons.Action
import SCons.Builder

def run(cmd):
    """Run a Unix command and return the exit code."""
    res = os.system(cmd)
    if (os.WIFEXITED(res)):
        code = os.WEXITSTATUS(res)
        return code
    # Assumes that if a process doesn't call exit, it was successful
    return 0

def doTest(target, source, env):
    res = run(source[0].abspath + ' ' + env.get('runParams', ''))
    if res == 0:
        open(target[0].abspath, 'w').write("PASSED\n")
    return res

def getRunParams(buildSettings, defaultRunParams):
    runConfig = buildSettings.get('runConfig', {})
    if GetOption('runParams'):
        runParams = " ".join(GetOption('runParams'))
    else:
        runParams = runConfig.get('runParams', defaultRunParams)
    return runParams

def createTestTarget(env, target, source, buildSettings, defaultRunParams=''):
    if not GetOption('run'):
        return False

    if SCons.Util.is_List(source):
        source = source[0]
    
    runner = env.__TestBuilder(target, source, runParams=getRunParams(buildSettings, defaultRunParams))
    return runner

def createRunTarget(env, source, buildSettings, defaultRunParams=''):
    if not GetOption('run'):
        return False

    if SCons.Util.is_List(target):
        target = target[0]

    runner = env.Command('dummyfile', source, source.abspath + ' ' + getRunParams(buildSettings, defaultRunParams))
    return runner

def generate(env):
    AddOption('--run', dest='run', action='store_true', default=False, help='Should we run the target')
    AddOption('--runparams', dest='runParams', action='append', type='string', default=[], help='The parameters to hand over')
    
    TestAction = SCons.Action.Action(doTest, "Running Test")
    TestBuilder = SCons.Builder.Builder(action=[TestAction],
                                              single_source=True)

    env.Append(BUILDERS={ '__TestBuilder' : TestBuilder })
    env.AddMethod(createTestTarget, "TestBuilder")
    env.AddMethod(createRunTarget, "RunBuilder")

def exists(env):
    return 1;
