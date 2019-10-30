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
import shlex
from logging import getLogger
import sys
from SCons.Action import Action
from SCons.Builder import Builder
from SCons.Script import AddOption, GetOption, COMMAND_LINE_TARGETS
from SCons.Util import is_List
from SConsider.PackageRegistry import PackageRegistry
from SConsider.Callback import Callback
from SConsider.SomeUtils import hasPathPart, isFileNode, isDerivedNode, getNodeDependencies, getFlatENV
from SConsider.PopenHelper import ProcessRunner, Tee, CalledProcessError, TimeoutExpired, STDOUT
logger = getLogger(__name__)

runtargets = {}
_DEFAULT_TIMEOUT_RUN = 0.0
_DEFAULT_TIMEOUT_TEST = 120.0


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


def run(cmd, logfile=None, **kw):
    """Run a Unix command and return the exit code."""
    exitcode = 99
    with Tee() as tee:
        tee.attach_std()
        if logfile:
            if not os.path.isdir(logfile.dir.get_abspath()):
                os.makedirs(logfile.dir.get_abspath())
            tee.attach_file(open(logfile.get_abspath(), 'w'))
        process_runner = None
        try:
            with ProcessRunner(cmd, stderr=STDOUT, seconds_to_wait=0.2, **kw) as process_runner:
                for out, _ in process_runner:
                    tee.write(out)
                exitcode = process_runner.returncode
        except CalledProcessError as e:
            logger.debug("non-zero exitcode: %s", e)
        except TimeoutExpired as e:
            logger.debug(e)
        except OSError as e:
            logger.debug("executable error: %s", e)
            # follow shell exit code
            exitcode = 127
        except Exception as e:
            logger.debug("process creation failure: %s", e)
        finally:
            if process_runner:
                exitcode = process_runner.returncode

    logger.debug("returncode: %d", exitcode)
    return exitcode


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

    return run(args,
               env=getFlatENV(env),
               logfile=env.get('logfile', None),
               timeout=env.get('timeout', _DEFAULT_TIMEOUT_RUN))


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


def getRunParams(buildSettings, default):
    runConfig = buildSettings.get('runConfig', {})
    params = GetOption('runParams')
    if not params:
        if not runConfig:
            runConfig = dict()
        params = runConfig.get('runParams', default)
    if isinstance(params, list):
        params = ' '.join(params)
    return params


def getRunTimeout(buildSettings, default):
    runConfig = buildSettings.get('runConfig', {})
    param = GetOption('runTimeout')
    if param < 0.0:
        if not runConfig:
            runConfig = dict()
        param = runConfig.get('runTimeout', default)
    if param <= 0.0:
        param = None
    return param


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
    runner = env.TestBuilder([],
                             source,
                             runParams=getRunParams(settings, defaultRunParams),
                             logfile=logfile,
                             timeout=getRunTimeout(settings, default=_DEFAULT_TIMEOUT_TEST))
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
                            logfile=logfile,
                            timeout=getRunTimeout(settings, default=_DEFAULT_TIMEOUT_RUN))

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
        AddOption('--run',
                  dest='run',
                  action='store_true',
                  default=False,
                  help='Run the target if not done yet')
        AddOption('--run-force',
                  dest='run-force',
                  action='store_true',
                  default=False,
                  help='Run the target regardless of the last state (.passed file)')
        AddOption('--runparams',
                  dest='runParams',
                  action='append',
                  type='string',
                  default=[],
                  help='The parameters to hand over')
        AddOption('--run-timeout',
                  dest='runTimeout',
                  action='store',
                  type='float',
                  help='Time in seconds after which the running process gets killed')
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
