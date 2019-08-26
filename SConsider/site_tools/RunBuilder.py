"""SConsider.site_tools.RunBuilder.

This tool adds --run, --run-force and --runparams to the list of SCons options.

After successful creation of an executable target, it tries to execute it with
the possibility to add program options. Further it allows to specify specific
setup/teardown functions executed before and after running the program.
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from __future__ import with_statement
import os
import optparse
import sys
import shlex
from logging import getLogger
from SCons.Action import Action
from SCons.Builder import Builder
from SCons.Script import AddOption, GetOption, COMMAND_LINE_TARGETS
from SCons.Util import is_List
from SConsider.PackageRegistry import PackageRegistry
from SConsider.Callback import Callback
from SConsider.SomeUtils import hasPathPart, isFileNode, isDerivedNode, getNodeDependencies, getFlatENV
from SConsider.PopenHelper import PopenHelper, PIPE, STDOUT
logger = getLogger(__name__)

runtargets = {}


def setTarget(packagename, targetname, target):
    if is_List(target) and len(target) > 0:
        target = target[0]
    runtargets.setdefault(packagename, {})[targetname] = target


def getTargets(packagename=None, targetname=None):
    if not packagename:
        alltargets = []
        for packagename in runtargets:
            for _, target in runtargets.get(packagename, {}).iteritems():
                alltargets.append(target)
        return alltargets
    elif not targetname:
        return [target for _, target in runtargets.get(packagename, {}).iteritems()]
    targets = runtargets.get(packagename, {}).get(targetname, [])
    if not is_List(targets):
        targets = [targets]
    return targets


class Tee(object):
    def __init__(self):
        self.writers = []

    def add(self, writer, flush=False, close=True):
        self.writers.append((writer, flush, close))

    def write(self, output):
        for writer, flush, _ in self.writers:
            writer.write(output)
            if flush:
                writer.flush()

    def close(self):
        for writer, _, close in self.writers:
            if close:
                writer.close()


def run(cmd, logfile=None, **kw):
    """Run a Unix command and return the exit code."""
    tee = Tee()
    tee.add(sys.stdout, flush=True, close=False)
    rcode = 99
    proc = None
    try:
        if logfile:
            if not os.path.isdir(logfile.dir.get_abspath()):
                os.makedirs(logfile.dir.get_abspath())
            tee.add(open(logfile.get_abspath(), 'w'))
        proc = PopenHelper(cmd, stdin=None, stdout=PIPE, stderr=STDOUT, **kw)
        while True:
            out = proc.stdout.read(1)
            if out == '' and proc.poll() is not None:
                break
            tee.write(out)
        rcode = proc.returncode
    finally:
        while True and proc:
            out = proc.stdout.readline()
            if out == '' and proc.poll() is not None:
                break
            tee.write(out)
        tee.close()

    return rcode


def emitPassedFile(target, source, env):
    target = []
    for src in source:
        _, scriptname = os.path.split(src.get_abspath())
        target.append(env.getLogInstallDir().File(scriptname + '.passed'))
    return (target, source)


def execute(command, env):
    args = [command]
    args.extend(shlex.split(env.get('runParams', ''), posix=env["PLATFORM"] != 'win32'))

    if 'mingw' in env["TOOLS"]:
        args.insert(0, "sh.exe")

    return run(args, env=getFlatENV(env), logfile=env.get('logfile', None))


def doTest(target, source, env):
    if '__SKIP_TEST__' in env:
        logger.critical('%s', str(env['__SKIP_TEST__']))
        return 0

    res = execute(source[0].get_abspath(), env)
    if res == 0:
        with open(target[0].get_abspath(), 'w') as f:
            f.write("PASSED\n")
    Callback().run('__PostTestOrRun')
    Callback().run('__PostAction_' + str(id(target[0])))
    return res


def doRun(target, source, env):
    res = execute(source[0].get_abspath(), env)
    Callback().run('__PostTestOrRun')
    Callback().run('__PostAction_' + str(id(target[0])))
    return res


def getRunParams(buildSettings, defaultRunParams):
    runConfig = buildSettings.get('runConfig', {})
    if GetOption('runParams'):
        runParams = " ".join(GetOption('runParams'))
    else:
        if not runConfig:
            runConfig = dict()
        runParams = runConfig.get('runParams', defaultRunParams)
    return runParams


class SkipTest(Exception):
    def __init__(self, message='No reason given'):
        self.message = message


def wrapSetUp(setUpFunc):
    def setUp(target, source, env):
        try:
            return setUpFunc(target, source, env)
        except SkipTest as ex:
            env['__SKIP_TEST__'] = "Test skipped for target {0}: {1}".format(source[0].name, ex.message)
            return 0

    return setUp


def addRunConfigHooks(env, source, runner, buildSettings):
    if not buildSettings:
        buildSettings = dict()
    runConfig = buildSettings.get('runConfig', {})
    setUp = runConfig.get('setUp', '')
    tearDown = runConfig.get('tearDown', '')

    if callable(setUp):
        env.AddPreAction(runner, Action(wrapSetUp(setUp), lambda *args, **kw: ''))
    if callable(tearDown):
        Callback().register('__PostAction_' + str(id(runner[0])),
                            lambda: tearDown(target=runner, source=source, env=env))


def createTestTarget(env, source, packagename, targetname, settings, defaultRunParams='-- -all', **kw):
    """Creates a target which runs a target given in parameter 'source'.

    If ran successfully a file is generated (name given in parameter
    'target') which indicates that this runner-target doesn't need to be
    executed unless the dependencies changed. Command line parameters
    could be handed over by using --runparams="..." or by setting
    buildSettings['runConfig']['runParams']. The Fields 'setUp' and
    'tearDown' in 'runConfig' accept a string (executed as shell
    command), a Python function (with arguments 'target', 'source',
    'env') or any SCons.Action.
    """

    fullTargetName = PackageRegistry.createFulltargetname(packagename, targetname)
    source = PackageRegistry().getRealTarget(source)
    if not source or (not GetOption('run') and not GetOption('run-force')):
        return (source, fullTargetName)

    logfile = env.getLogInstallDir().File(targetname + '.test.log')
    runner = env.TestBuilder([], source, runParams=getRunParams(settings, defaultRunParams), logfile=logfile)
    if GetOption('run-force'):
        env.AlwaysBuild(runner)

    def isNotInBuilddir(node):
        return hasPathPart(node, pathpart=env.getRelativeBuildDirectory())

    def isNotCopiedInclude(node):
        return not node.path.startswith(env['INCDIR'])

    funcs = [isFileNode, isDerivedNode, isNotInBuilddir, isNotCopiedInclude]

    env.Depends(runner, sorted(getNodeDependencies(runner[0], funcs)))

    addRunConfigHooks(env, source, runner, settings)

    Callback().register(
        '__PostTestOrRun', lambda: Callback().run(
            'PostTest', target=source, packagename=packagename, targetname=targetname, logfile=logfile))

    setTarget(packagename, targetname, runner)
    if callable(kw.get('runner_hook_func', None)):
        kw.get('runner_hook_func')(env, runner)

    return (runner, fullTargetName)


def createRunTarget(env, source, packagename, targetname, settings, defaultRunParams='', **kw):
    """Creates a target which runs a target given in parameter 'source'.

    Command line parameters could be handed over by using
    --runparams="..." or by setting
    buildSettings['runConfig']['runParams']. The Fields 'setUp' and
    'tearDown' in 'runConfig' accept a string (executed as shell
    command), a Python function (with arguments 'target', 'source',
    'env') or any SCons.Action.
    """

    fullTargetName = PackageRegistry.createFulltargetname(packagename, targetname)
    source = PackageRegistry().getRealTarget(source)
    if not source or (not GetOption('run') and not GetOption('run-force')):
        return (source, fullTargetName)

    logfile = env.getLogInstallDir().File(targetname + '.run.log')
    runner = env.RunBuilder(['dummyRunner_' + fullTargetName],
                            source,
                            runParams=getRunParams(settings, defaultRunParams),
                            logfile=logfile)

    addRunConfigHooks(env, source, runner, settings)

    Callback().register(
        '__PostTestOrRun', lambda: Callback().run(
            'PostRun', target=source, packagename=packagename, targetname=targetname, logfile=logfile))

    setTarget(packagename, targetname, runner)
    if callable(kw.get('runner_hook_func', None)):
        kw.get('runner_hook_func')(env, runner)

    return (runner, fullTargetName)


def composeRunTargets(env, source, packagename, targetname, settings, defaultRunParams='', **kw):
    targets = []
    for ftname in settings.get('requires', []) + settings.get('linkDependencies', []):
        otherPackagename, otherTargetname = PackageRegistry.splitFulltargetname(ftname)
        targets.extend(getTargets(otherPackagename, otherTargetname))
    fullTargetName = PackageRegistry.createFulltargetname(packagename, targetname)
    runner = env.Alias('dummyRunner_' + fullTargetName, targets)
    setTarget(packagename, targetname, runner)
    if callable(kw.get('runner_hook_func', None)):
        kw.get('runner_hook_func')(env, runner)
    return (runner, fullTargetName)


def generate(env):
    try:
        AddOption('--run', dest='run', action='store_true', default=False, help='Should we run the target')
        AddOption('--run-force',
                  dest='run-force',
                  action='store_true',
                  default=False,
                  help='Should we run the target and ignore .passed files')
        AddOption('--runparams',
                  dest='runParams',
                  action='append',
                  type='string',
                  default=[],
                  help='The parameters to hand over')
    except optparse.OptionConflictError:
        pass

    TestAction = Action(doTest, "Running Test '$SOURCE'\n with runParams [$runParams]")
    TestBuilder = Builder(action=[TestAction], emitter=emitPassedFile, single_source=True)

    RunAction = Action(doRun, "Running Executable '$SOURCE'\n with runParams [$runParams]")
    RunBuilder = Builder(action=[RunAction], single_source=True)

    env.Append(BUILDERS={'TestBuilder': TestBuilder})
    env.Append(BUILDERS={'RunBuilder': RunBuilder})
    env.AddMethod(createTestTarget, "TestTarget")
    env.AddMethod(createRunTarget, "RunTarget")
    import SConsider
    SConsider.SkipTest = SkipTest

    def createTargetCallback(env, target, packagename, targetname, buildSettings, **kw):
        runConfig = buildSettings.get('runConfig', {})
        if not runConfig:
            return None

        runType = runConfig.get('type', 'run')

        factory = composeRunTargets
        runner_hook_func = None
        if runType == 'test':

            def runner_alias_for_tests(env, runner):
                env.Alias('tests', runner)
                env.Alias('all', runner)

            factory = createTestTarget
            runner_hook_func = runner_alias_for_tests
        elif runType == 'run':

            def runner_alias_for_run(env, runner):
                env.Alias('all', runner)

            factory = createRunTarget
            runner_hook_func = runner_alias_for_run
        _, _ = factory(env,
                       target,
                       packagename,
                       targetname,
                       buildSettings,
                       runner_hook_func=runner_hook_func,
                       **kw)

    def addBuildTargetCallback(buildTargets, **kw):
        if COMMAND_LINE_TARGETS:
            for ftname in COMMAND_LINE_TARGETS:
                packagename, targetname = PackageRegistry.splitFulltargetname(ftname)
                buildTargets.extend(getTargets(packagename, targetname))
        else:
            buildTargets.extend(getTargets())

    if GetOption("run") or GetOption("run-force"):
        Callback().register("PostCreateTarget", createTargetCallback)
        Callback().register("PreBuild", addBuildTargetCallback)


def exists(env):
    return 1
