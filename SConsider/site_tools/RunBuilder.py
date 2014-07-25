"""SConsider.site_tools.RunBuilder.

This tool adds --run, --run-force and --runparams to the list of SCons options.

After successful creation of an executable target, it tries to execute it with
the possibility to add program options. Further it allows to specify specific
setup/teardown functions executed before and after running the program.

"""

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
import subprocess
import optparse
import sys
import functools
import SCons.Action
import SCons.Builder
import SCons.Script
from SCons.Script import AddOption, GetOption
import SConsider
import Callback
from logging import getLogger
logger = getLogger(__name__)

Callback.addCallbackFeature(__name__)

runtargets = {}


def setTarget(packagename, targetname, target):
    if SCons.Util.is_List(target) and len(target) > 0:
        target = target[0]
    runtargets.setdefault(packagename, {})[targetname] = target


def getTargets(packagename=None, targetname=None):
    if not packagename:
        alltargets = []
        for packagename in runtargets:
            for tname, target in runtargets.get(packagename, {}).iteritems():
                alltargets.append(target)
        return alltargets
    elif not targetname:
        return [
            target for tname,
            target in runtargets.get(
                packagename,
                {}).iteritems()]
    else:
        return filter(
            bool, [
                runtargets.get(
                    packagename, {}).get(
                    targetname, None)])


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
    tee = Tee()
    tee.add(sys.stdout, flush=True, close=False)
    rcode = 99
    try:
        if logfile:
            if not os.path.isdir(logfile.dir.abspath):
                os.makedirs(logfile.dir.abspath)
            tee.add(open(logfile.abspath, 'w'))
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kw)
        while True:
            out = proc.stdout.readline()
            if out == '' and proc.poll() is not None:
                break
            tee.write(out)
        rcode = proc.returncode
    finally:
        while True:
            out = proc.stdout.readline()
            if out == '' and proc.poll() is not None:
                break
            tee.write(out)
        tee.close()

    return rcode


def emitPassedFile(target, source, env):
    target = []
    for src in source:
        path, scriptname = os.path.split(src.abspath)
        target.append(
            env['BASEOUTDIR'].Dir(
                env['RELTARGETDIR']).Dir(
                env['LOGDIR']).Dir(
                env['VARIANTDIR']).File(
                    scriptname +
                '.passed'))
    return (target, source)


def execute(command, env):
    import shlex
    args = [command]
    args.extend(
        shlex.split(
            env.get(
                'runParams',
                ''),
            posix=env["PLATFORM"] != 'win32'))

    if 'mingw' in env["TOOLS"]:
        args.insert(0, "sh.exe")

    return run(
        args,
        env=SConsider.getFlatENV(env),
        logfile=env.get(
            'logfile',
            None))


def doTest(target, source, env):
    if '__SKIP_TEST__' in env:
        logger.info('Test skipped: %s', str(env['__SKIP_TEST__']))
        return 0

    res = execute(source[0].abspath, env)
    if res == 0:
        with open(target[0].abspath, 'w') as file:
            file.write("PASSED\n")
    runCallback('__PostTestOrRun')
    runCallback('__PostAction_' + str(id(target[0])))
    return res


def doRun(target, source, env):
    res = execute(source[0].abspath, env)
    runCallback('__PostTestOrRun')
    runCallback('__PostAction_' + str(id(target[0])))
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
        env.AddPreAction(
            runner,
            SCons.Action.Action(
                wrapSetUp(setUp),
                lambda *
                args,
                **kw: ''))
    if callable(tearDown):
        registerCallback(
            '__PostAction_' + str(id(runner[0])),
            lambda: tearDown(target=runner, source=source, env=env))


def createTestTarget(
        env,
        source,
        plainsource,
        registry,
        packagename,
        targetname,
        buildSettings,
        defaultRunParams='-- -all'):
    """Creates a target which runs a target given in parameter 'source'.

    If ran successfully a
    file is generated (name given in parameter 'target') which indicates that this runner-target
    doesn't need to be executed unless the dependencies changed. Command line parameters could be
    handed over by using --runparams="..." or by setting buildSettings['runConfig']['runParams'].
    The Fields 'setUp' and 'tearDown' in 'runConfig' accept a string (executed as shell command),
    a Python function (with arguments 'target', 'source', 'env') or any SCons.Action.

    """

    if not GetOption('run') and not GetOption('run-force'):
        return source

    if not SCons.Util.is_List(source):
        source = [source]

    logfile = env['BASEOUTDIR'].Dir(
        env['RELTARGETDIR']).Dir(
        env['LOGDIR']).Dir(
        env['VARIANTDIR']).File(
        targetname + '.test.log')

    runner = env.TestBuilder(
        [],
        source,
        runParams=getRunParams(
            buildSettings,
            defaultRunParams),
        logfile=logfile)
    if GetOption('run-force'):
        env.AlwaysBuild(runner)

    isInBuilddir = functools.partial(
        SConsider.hasPathPart,
        pathpart=env['BUILDDIR'])
    isCopiedInclude = lambda node: node.path.startswith(env['INCDIR'])

    funcs = [
        SConsider.isFileNode,
        SConsider.isDerivedNode,
        lambda node: not isInBuilddir(node),
        lambda node: not isCopiedInclude(node)
    ]

    env.Depends(
        runner,
        sorted(
            SConsider.getNodeDependencies(
                runner[0],
                funcs)))

    addRunConfigHooks(env, source, runner, buildSettings)

    registerCallback(
        '__PostTestOrRun',
        lambda: runCallback(
            'PostTest',
            target=source,
            registry=registry,
            packagename=packagename,
            targetname=targetname,
            logfile=logfile))

    env.Alias('tests', runner)
    env.Alias('all', runner)

    return runner


def createRunTarget(
        env,
        source,
        plainsource,
        registry,
        packagename,
        targetname,
        buildSettings,
        defaultRunParams=''):
    """Creates a target which runs a target given in parameter 'source'.

    Command line parameters could be
    handed over by using --runparams="..." or by setting buildSettings['runConfig']['runParams'].
    The Fields 'setUp' and 'tearDown' in 'runConfig' accept a string (executed as shell command),
    a Python function (with arguments 'target', 'source', 'env') or any SCons.Action.

    """

    if not GetOption('run') and not GetOption('run-force'):
        return source

    if not SCons.Util.is_List(source):
        source = [source]

    logfile = env['BASEOUTDIR'].Dir(
        env['RELTARGETDIR']).Dir(
        env['LOGDIR']).Dir(
        env['VARIANTDIR']).File(
        targetname + '.run.log')

    runner = env.RunBuilder(
        [
            'dummyRunner_' +
            SConsider.generateFulltargetname(
                packagename,
                targetname)],
        source,
        runParams=getRunParams(
            buildSettings,
            defaultRunParams),
        logfile=logfile)

    addRunConfigHooks(env, source, runner, buildSettings)

    registerCallback(
        '__PostTestOrRun',
        lambda: runCallback(
            'PostRun',
            target=source,
            registry=registry,
            packagename=packagename,
            targetname=targetname,
            logfile=logfile))

    env.Alias('all', runner)

    return runner


def composeRunTargets(
        env,
        source,
        plainsource,
        registry,
        packagename,
        targetname,
        buildSettings,
        defaultRunParams=''):
    targets = []
    for ftname in buildSettings.get('requires', []) + buildSettings.get('linkDependencies', []):
        otherPackagename, otherTargetname = SConsider.splitTargetname(ftname)
        targets.extend(getTargets(otherPackagename, otherTargetname))
    return env.Alias(
        'dummyRunner_' +
        SConsider.generateFulltargetname(
            packagename,
            targetname),
        targets)


def generate(env):
    try:
        AddOption(
            '--run',
            dest='run',
            action='store_true',
            default=False,
            help='Should we run the target')
        AddOption(
            '--run-force',
            dest='run-force',
            action='store_true',
            default=False,
            help='Should we run the target and ignore .passed files')
        AddOption(
            '--runparams',
            dest='runParams',
            action='append',
            type='string',
            default=[],
            help='The parameters to hand over')
    except optparse.OptionConflictError:
        pass

    TestAction = SCons.Action.Action(
        doTest,
        "Running Test '$SOURCE'\n with runParams [$runParams]")
    TestBuilder = SCons.Builder.Builder(action=[TestAction],
                                        emitter=emitPassedFile,
                                        single_source=True)

    RunAction = SCons.Action.Action(
        doRun,
        "Running Executable '$SOURCE'\n with runParams [$runParams]")
    RunBuilder = SCons.Builder.Builder(action=[RunAction],
                                       single_source=True)

    env.Append(BUILDERS={'TestBuilder': TestBuilder})
    env.Append(BUILDERS={'RunBuilder': RunBuilder})
    env.AddMethod(createTestTarget, "TestTarget")
    env.AddMethod(createRunTarget, "RunTarget")
    SConsider.SkipTest = SkipTest

    def createTargetCallback(
            env,
            target,
            plaintarget,
            registry,
            packagename,
            targetname,
            buildSettings,
            **kw):
        runConfig = buildSettings.get('runConfig', {})
        if not runConfig:
            return None

        runType = runConfig.get('type', 'run')

        factory = createRunTarget
        if runType == 'test':
            factory = createTestTarget
        elif runType == 'composite':
            factory = composeRunTargets
        runner = factory(
            env,
            target,
            plaintarget,
            registry,
            packagename,
            targetname,
            buildSettings,
            **kw)
        setTarget(packagename, targetname, runner)

    def addBuildTargetCallback(**kw):
        for ftname in SCons.Script.COMMAND_LINE_TARGETS:
            packagename, targetname = SConsider.splitTargetname(ftname)
            SCons.Script.BUILD_TARGETS.extend(
                getTargets(
                    packagename,
                    targetname))

    if GetOption("run") or GetOption("run-force"):
        SConsider.registerCallback("PostCreateTarget", createTargetCallback)
        SConsider.registerCallback("PreBuild", addBuildTargetCallback)


def exists(env):
    return 1
