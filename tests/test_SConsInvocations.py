# -------------------------------------------------------------------------
# Copyright (c) 2016, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import pytest
import os
import re
import sys
from glob import glob
from SConsider.PopenHelper import ProcessRunner, CalledProcessError, STDOUT


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['gethelp'])
def test_SConsiderGetHelp(copy_testdir_to_tmp, pypath_extended_env, popen_timeout, scons_platform_options,
                          invocation_path, capfd):

    pypath_extended_env.update({'LOG_CFG': str(invocation_path('debuglog.yaml'))})
    cmd = r'scons -h' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert '--baseoutdir' in captured.out
    assert '--archbits' in captured.out


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['gethelp'])
def test_SConsiderSconstructDirSameAsLaunchDir(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                               scons_platform_options, capfd):
    cmd = r'scons -h' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'get_sconstruct_dir=' + str(copy_testdir_to_tmp) in captured.out
    assert 'get_launch_dir=' + str(copy_testdir_to_tmp) in captured.out
    assert 'base_out_dir=' + str(copy_testdir_to_tmp) in captured.out


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['gethelp'])
def test_SConsiderSconstructDirBelowLaunchDir(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                              scons_platform_options, capfd):
    sconstruct_file = os.path.join(str(copy_testdir_to_tmp), 'SConstruct')
    cmd = r'scons -h -f ' + sconstruct_file + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'get_sconstruct_dir=' + str(copy_testdir_to_tmp) in captured.out
    assert 'get_launch_dir=' + os.getcwd() in captured.out
    assert 'base_out_dir=' + str(copy_testdir_to_tmp) in captured.out


@pytest.mark.invocation
def test_SConsiderSconstructAboveLaunchDir(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                           scons_platform_options, capfd):
    progdir_path = copy_testdir_to_tmp.join('progdir')
    cmd = r'scons -h -u ' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(progdir_path),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'get_sconstruct_dir=' + str(copy_testdir_to_tmp) in captured.out
    assert 'get_launch_dir=' + str(progdir_path) in captured.out
    assert 'base_out_dir=' + str(copy_testdir_to_tmp) in captured.out


@pytest.mark.invocation
def test_SConsiderStaticProgBuild(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                  scons_platform_options, capfd):
    cmd = r'scons --3rdparty=' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'done building targets.' in captured.out


@pytest.mark.invocation
def test_SConsiderStaticProgDoxygenOnly(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                        scons_platform_options, capfd):
    cmd = r'scons --usetool=DoxygenBuilder --doxygen-only hello' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'done building targets.' in captured.out
    assert re.search('BUILD_TARGETS.*doxygen', captured.out)


@pytest.mark.invocation
def test_SConsiderStaticProgIncludingDoxygen(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                             scons_platform_options, capfd):
    cmd = r'scons --usetool=DoxygenBuilder --doxygen hello' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'done building targets.' in captured.out
    assert re.search('BUILD_TARGETS.*doxygen', captured.out)
    assert re.search('BUILD_TARGETS.*hello', captured.out)


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithoutCommandLineTarget(copy_testdir_to_tmp, pypath_extended_env,
                                                        popen_timeout, scons_platform_options, capfd):
    cmd = r'scons --3rdparty= --run' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'Hello from SConsider' in captured.out


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithPackageAsTarget(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                                   scons_platform_options, capfd):
    cmd = r'scons --3rdparty= --run hello' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'Hello from SConsider' in captured.out


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithExplicitPackageTarget(copy_testdir_to_tmp, pypath_extended_env,
                                                         popen_timeout, scons_platform_options, capfd):
    cmd = r'scons --3rdparty= --run hello.runner' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'Hello from SConsider' in captured.out


def assert_outputfiles_exist(baseoutdir, predicate=lambda l: l >= 1):
    expected_files = [
        'apps/hello/log/*/runner.run.log', 'apps/hello/scripts/*/hello*.sh', 'apps/hello/bin/*/*hello*',
        'lib/*/*.so*'
    ]
    for glob_path in expected_files:
        assert predicate(len(glob(os.path.join(baseoutdir, glob_path))))


@pytest.mark.invocation
def test_SConsiderStaticProgBuildOutputFilesBelowStartdir(copy_testdir_to_tmp, pypath_extended_env,
                                                          popen_timeout, scons_platform_options):
    cmd = r'scons --3rdparty= --run hello.runner' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    assert copy_testdir_to_tmp.join('apps').isdir()
    assert copy_testdir_to_tmp.join('progdir').join('.build').isdir()
    assert_outputfiles_exist(str(copy_testdir_to_tmp))


@pytest.mark.invocation
def test_SConsiderStaticProgBuildOutputFilesInBaseoutdir(copy_testdir_to_tmp, pypath_extended_env,
                                                         popen_timeout, scons_platform_options,
                                                         tmpdir_factory):
    baseoutdir = str(tmpdir_factory.mktemp('baseoutdir', numbered=True))
    cmd = r'scons --3rdparty= --baseoutdir=' + baseoutdir + ' --run hello.runner' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    assert not copy_testdir_to_tmp.join('apps').isdir()
    assert not copy_testdir_to_tmp.join('progdir').join('.build').isdir()
    assert_outputfiles_exist(str(copy_testdir_to_tmp), lambda l: l == 0)
    assert_outputfiles_exist(baseoutdir)


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir,buildprefix,cpp_in_second_build',
                         [('3rdptest', '', lambda there: not there),
                          ('3rdptest', 'my3psrc', lambda there: there)])
def test_SConsiderThirdPartyBuildOnceOnly(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                          scons_platform_options, current_testdir, buildprefix,
                                          cpp_in_second_build, capfd):
    """Show that using the source directory name as prefix of the 3rdparty
    build output always builds the sources over and over again."""
    cmd = r'scons --3rdparty=my3pscons --with-src-3plib=my3psrc' + scons_platform_options
    if buildprefix:
        cmd += ' --3rdparty-build-prefix=' + buildprefix
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert os.sep + '3plib.cpp' in captured.out
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert cpp_in_second_build(os.sep + '3plib.cpp' in captured.out)


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['samedirtest'])
def test_SConstructAndSConsiderInSameDirBuild(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                              scons_platform_options, capfd):
    cmd = r'scons --3rdparty=' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'done building targets.' in captured.out


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['samedirtest'])
def test_SConstructAndSConsiderInSameDirRunWithoutCommandLineTarget(copy_testdir_to_tmp, pypath_extended_env,
                                                                    popen_timeout, scons_platform_options,
                                                                    capfd):
    cmd = r'scons --3rdparty= --run' + scons_platform_options
    with ProcessRunner(cmd, timeout=popen_timeout, cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'Hello from SConsider' in captured.out


@pytest.mark.invocation
def test_WrapperScriptHelpList(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                               scons_platform_options, capfd):
    with pytest.raises(CalledProcessError) as excinfo:
        cmd = r'scons --3rdparty= --run --runparams="-h"' + scons_platform_options
        with ProcessRunner(cmd,
                           timeout=popen_timeout,
                           stderr=STDOUT,
                           cwd=str(copy_testdir_to_tmp),
                           env=pypath_extended_env) as executor:
            for out, err in executor:
                sys.stdout.write(out)
                sys.stderr.write(err)
    assert 2 == excinfo.value.returncode
    captured = capfd.readouterr()
    assert 'usage: hellorunner.sh [options]' in captured.out
    assert 'where options are:' in captured.out


@pytest.mark.invocation
def test_WrapperScriptRun(copy_testdir_to_tmp, pypath_extended_env, popen_timeout, scons_platform_options,
                          capfd):
    cmd = r'scons --3rdparty= --run --runparams="-v"' + scons_platform_options
    with ProcessRunner(cmd,
                       timeout=popen_timeout,
                       stderr=STDOUT,
                       cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'Hello from SConsider' in captured.out


@pytest.mark.invocation
def test_WrapperScriptDebugRunSuccess(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                      scons_platform_options, capfd):
    cmd = r'scons --3rdparty= --run --runparams="-d -d"' + scons_platform_options
    with ProcessRunner(cmd,
                       timeout=popen_timeout,
                       stderr=STDOUT,
                       cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'Hello from SConsider' in captured.out
    assert 'Inferior' in captured.out
    assert 'exited normally' in captured.out


@pytest.mark.invocation
def test_WrapperScriptDebugRunStacktrace(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                         scons_platform_options, capfd):
    with pytest.raises(CalledProcessError) as excinfo:
        cmd = r'scons --3rdparty= --build-cfg=debug --run --runparams="-d -d -- crash"' + scons_platform_options
        with ProcessRunner(cmd,
                           timeout=popen_timeout,
                           stderr=STDOUT,
                           cwd=str(copy_testdir_to_tmp),
                           env=pypath_extended_env) as executor:
            for out, err in executor:
                sys.stdout.write(out)
                sys.stderr.write(err)
    assert 2 == excinfo.value.returncode
    captured = capfd.readouterr()
    assert 'GDB backtrace' in captured.out
    assert 'Inferior' in captured.out
    assert 'will be killed' in captured.out


@pytest.mark.invocation
def test_WrapperScriptCommandOverride(copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
                                      scons_platform_options, capfd):
    cmd = r'scons --3rdparty= --run --runparams="-x echo -x \"args to command:\""' + scons_platform_options
    with ProcessRunner(cmd,
                       timeout=popen_timeout,
                       stderr=STDOUT,
                       cwd=str(copy_testdir_to_tmp),
                       env=pypath_extended_env) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert re.search('args to command:.*hellorunner', captured.out, re.M)
