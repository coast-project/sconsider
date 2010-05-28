from __future__ import with_statement
import os, pdb, subprocess, optparse, sys
import SCons.Action, SCons.Builder, SCons.Script
from SCons.Script import AddOption, GetOption
import SConsider
import Callback
Callback.addCallbackFeature(__name__)

runtargets = {}
def setTarget(packagename, targetname, target):
    if SCons.Util.is_List(target) and len(target) > 0:
        target = target[0]
    runtargets.setdefault(packagename, {})[targetname] = target

def getTargets(packagename, targetname=None):
    if not targetname:
        return [target for tname, target in runtargets.get(packagename, {}).iteritems()]
    else:
        return filter(bool, [runtargets.get(packagename, {}).get(targetname, None)])

class Tee(object):
    def __init__(self):
        self.writers = []
    def add(self, writer, flush=False, close=True):
        self.writers.append((writer, flush, close))
    def write(self, output):
        for writer, flush, close in self.writers:
            writer.write(output)
            if flush:
                writer.flush()
    def close(self):
        for writer, flush, close in self.writers:
            if close:
                writer.close()

def run(cmd, logfile=None, **kw):
    """Run a Unix command and return the exit code."""
    import shlex
    command=shlex.split(cmd)
    tee = Tee()
    tee.add(sys.stdout, flush=True, close=False)
    try:
        if logfile:
            if not os.path.isdir(logfile.dir.abspath):
                os.makedirs(logfile.dir.abspath)
            tee.add(open(logfile.abspath, 'w'))
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)
        while True:
            out = proc.stdout.readline()
            if out == '' and proc.poll() != None:
                break
            tee.write(out)
    finally:
        tee.close()

    return proc.returncode

def emitPassedFile(target, source, env):
    target = []
    for src in source:
        path, scriptname = os.path.split(src.abspath)
        target.append(env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['LOGDIR']).Dir(env['VARIANTDIR']).File(scriptname+'.passed'))
    return (target, source)

def doTest(target, source, env):
    if '__SKIP_TEST__' in env:
        print 'Test skipped: '+str(env['__SKIP_TEST__'])
        return 0

    res = run(source[0].abspath + ' ' + env.get('runParams', ''), env=SConsider.getFlatENV(env), logfile=env.get('logfile', None))
    if res == 0:
        with open(target[0].abspath, 'w') as file:
            file.write("PASSED\n")
    runCallback('__PostTestOrRun')
    runCallback('__PostAction_'+str(id(target[0])))
    return res

def doRun(target, source, env):
    res = run(source[0].abspath + ' ' + env.get('runParams', ''), env=SConsider.getFlatENV(env), logfile=env.get('logfile', None))
    runCallback('__PostTestOrRun')
    runCallback('__PostAction_'+str(id(target[0])))
    return res

def getRunParams(buildSettings, defaultRunParams):
    runConfig = buildSettings.get('runConfig', {})
    if GetOption('runParams'):
        runParams = " ".join(GetOption('runParams'))
    else:
        runParams = runConfig.get('runParams', defaultRunParams)
    return runParams

class SkipTest(Exception):
    def __init__(self, message='No reason given'):
        self.message = message

def wrapSetUp(setUpFunc):
    def setUp(target, source, env):
        try:
            return setUpFunc(target, source, env)
        except SkipTest as e:
            env['__SKIP_TEST__'] = e.message
            return 0
    return setUp

def addRunConfigHooks(env, source, runner, buildSettings):
    runConfig = buildSettings.get('runConfig', {})
    setUp = runConfig.get('setUp', '')
    tearDown = runConfig.get('tearDown', '')

    if callable(setUp):
        env.AddPreAction(runner, SCons.Action.Action(wrapSetUp(setUp), lambda *args, **kw: ''))
    if callable(tearDown):
        registerCallback('__PostAction_'+str(id(runner[0])), lambda: tearDown(target=runner, source=source, env=env))

def createTestTarget(env, source, registry, packagename, targetname, buildSettings, defaultRunParams='-- -all'):
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

    logfile = env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['LOGDIR']).Dir(env['VARIANTDIR']).File(targetname+'.test.log')

    runner = env.TestBuilder([], source, runParams=getRunParams(buildSettings, defaultRunParams), logfile=logfile)
    if GetOption('run-force'):
        env.AlwaysBuild(runner)

    addRunConfigHooks(env, source, runner, buildSettings)

    registerCallback('__PostTestOrRun', lambda: runCallback('PostTest', target=source, registry=registry, packagename=packagename, targetname=targetname, logfile=logfile))

    env.Alias('tests', runner)
    env.Alias('all', runner)

    setTarget(packagename, targetname, runner)
    return runner

def createRunTarget(env, source, registry, packagename, targetname, buildSettings, defaultRunParams=''):
    """Creates a target which runs a target given in parameter 'source'. Command line parameters could be
    handed over by using --runparams="..." or by setting buildSettings['runConfig']['runParams'].
    The Fields 'setUp' and 'tearDown' in 'runConfig' accept a string (executed as shell command),
    a Python function (with arguments 'target', 'source', 'env') or any SCons.Action."""

    if not GetOption('run') and not GetOption('run-force'):
        return source

    if not SCons.Util.is_List(source):
        source = [source]

    logfile = env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['LOGDIR']).Dir(env['VARIANTDIR']).File(targetname+'.run.log')

    runner = env.RunBuilder(['dummyfile_'+targetname], source, runParams=getRunParams(buildSettings, defaultRunParams), logfile=logfile)

    addRunConfigHooks(env, source, runner, buildSettings)

    registerCallback('__PostTestOrRun', lambda: runCallback('PostRun', target=source, registry=registry, packagename=packagename, targetname=targetname, logfile=logfile))

    env.Alias('all', runner)

    setTarget(packagename, targetname, runner)
    return runner

def generate(env):
    try:
        AddOption('--run', dest='run', action='store_true', default=False, help='Should we run the target')
        AddOption('--run-force', dest='run-force', action='store_true', default=False, help='Should we run the target and ignore .passed files')
        AddOption('--runparams', dest='runParams', action='append', type='string', default=[], help='The parameters to hand over')
    except optparse.OptionConflictError:
        pass

    TestAction = SCons.Action.Action(doTest, "Running Test '$SOURCE'\n with runParams [$runParams]")
    TestBuilder = SCons.Builder.Builder(action=[TestAction],
                                        emitter=emitPassedFile,
                                        single_source=True)

    RunAction = SCons.Action.Action(doRun, "Running Executable '$SOURCE'\n with runParams [$runParams]")
    RunBuilder = SCons.Builder.Builder(action=[RunAction],
                                              single_source=True)

    env.Append(BUILDERS={ 'TestBuilder' : TestBuilder })
    env.Append(BUILDERS={ 'RunBuilder' : RunBuilder })
    env.AddMethod(createTestTarget, "TestTarget")
    env.AddMethod(createRunTarget, "RunTarget")
    SConsider.SkipTest = SkipTest

    def createTargetCallback(env, target, registry, packagename, targetname, buildSettings, **kw):
        runConfig = buildSettings.get('runConfig', {})
        if not runConfig:
            return None
        factory = createRunTarget
        if runConfig.get('type', 'run') == 'test':
            factory = createTestTarget
        factory(env, target, registry, packagename, targetname, buildSettings, **kw)

    def addBuildTargetCallback(**kw):
        for ftname in SCons.Script.COMMAND_LINE_TARGETS:
            packagename, targetname = SConsider.splitTargetname(ftname)
            for target in getTargets(packagename, targetname):
                SCons.Script.BUILD_TARGETS.append(target)

    if GetOption("run") or GetOption("run-force"):
        SConsider.registerCallback("PostCreateTarget", createTargetCallback)
        SConsider.registerCallback("PreBuild", addBuildTargetCallback)

def exists(env):
    return 1;
