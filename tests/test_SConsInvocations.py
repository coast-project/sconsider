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
import shutil
from glob import glob
from SConsider.PopenHelper import PopenHelper, PIPE


@pytest.fixture
def current_testdir():
    return 'staticprog'


@pytest.fixture(scope='function')
def copy_testdir_to_tmp(tmpdir_factory, invocation_path, current_testdir):
    def ignorefiles(the_dir, names):
        ignored_list = [j for j in names
                        if j.startswith('.sconsign') or j.endswith('.log')]
        return ignored_list

    fn = tmpdir_factory.mktemp(current_testdir, numbered=True).join('sources')
    sources_path = invocation_path(current_testdir)
    shutil.copytree(str(sources_path), str(fn), ignore=ignorefiles)
    return fn


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['gethelp'])
def test_SConsiderGetHelp(copy_testdir_to_tmp, pypath_extended_env,
                          popen_timeout, scons_platform_options):
    sub_p = PopenHelper(r'scons -h' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(copy_testdir_to_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert '--baseoutdir' in stdout
    assert '--archbits' in stdout


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['gethelp'])
def test_SConsiderSconstructDirSameAsLaunchDir(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(r'scons -h' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(copy_testdir_to_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'get_sconstruct_dir=' + str(copy_testdir_to_tmp) in stdout
    assert 'get_launch_dir=' + str(copy_testdir_to_tmp) in stdout
    assert 'base_out_dir=' + str(copy_testdir_to_tmp) in stdout


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir', ['gethelp'])
def test_SConsiderSconstructDirBelowLaunchDir(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sconstruct_file = os.path.join(str(copy_testdir_to_tmp), 'SConstruct')
    sub_p = PopenHelper(
        r'scons -h -f ' + sconstruct_file + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'get_sconstruct_dir=' + str(copy_testdir_to_tmp) in stdout
    assert 'get_launch_dir=' + os.getcwd() in stdout
    assert 'base_out_dir=' + str(copy_testdir_to_tmp) in stdout


@pytest.mark.invocation
def test_SConsiderSconstructAboveLaunchDir(copy_testdir_to_tmp,
                                           pypath_extended_env, popen_timeout,
                                           scons_platform_options):
    progdir_path = copy_testdir_to_tmp.join('progdir')
    sub_p = PopenHelper(r'scons -h -u ' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(progdir_path),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'get_sconstruct_dir=' + str(copy_testdir_to_tmp) in stdout
    assert 'get_launch_dir=' + str(progdir_path) in stdout
    assert 'base_out_dir=' + str(copy_testdir_to_tmp) in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgBuild(copy_testdir_to_tmp, pypath_extended_env,
                                  popen_timeout, scons_platform_options):
    sub_p = PopenHelper(r'scons --3rdparty=' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(copy_testdir_to_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'done building targets.' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithoutCommandLineTarget(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(r'scons --3rdparty= --run' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(copy_testdir_to_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithPackageAsTarget(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(copy_testdir_to_tmp),
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithExplicitPackageTarget(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello.runner' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(copy_testdir_to_tmp),
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


def assert_outputfiles_exist(baseoutdir, predicate=lambda l: l >= 1):
    expected_files = [
        'apps/hello/log/*/runner.run.log', 'apps/hello/scripts/*/hello*.sh',
        'apps/hello/bin/*/*hello*'
    ]
    for glob_path in expected_files:
        assert predicate(len(glob(os.path.join(baseoutdir, glob_path))))


@pytest.mark.invocation
def test_SConsiderStaticProgBuildOutputFilesBelowStartdir(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello.runner' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(copy_testdir_to_tmp),
        env=pypath_extended_env)
    _, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert copy_testdir_to_tmp.join('apps').isdir()
    assert copy_testdir_to_tmp.join('progdir').join('.build').isdir()
    assert_outputfiles_exist(str(copy_testdir_to_tmp))


@pytest.mark.invocation
def test_SConsiderStaticProgBuildOutputFilesInBaseoutdir(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options, tmpdir_factory):
    baseoutdir = str(tmpdir_factory.mktemp('baseoutdir', numbered=True))
    sub_p = PopenHelper(r'scons --3rdparty= --baseoutdir=' + baseoutdir +
                        ' --run hello.runner' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(copy_testdir_to_tmp),
                        env=pypath_extended_env)
    _, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert not copy_testdir_to_tmp.join('apps').isdir()
    assert not copy_testdir_to_tmp.join('progdir').join('.build').isdir()
    assert_outputfiles_exist(str(copy_testdir_to_tmp), lambda l: l == 0)
    assert_outputfiles_exist(baseoutdir)


@pytest.mark.invocation
@pytest.mark.parametrize('current_testdir,buildprefix,cpp_in_second_build',
                         [('3rdptest', '', lambda there: not there),
                          ('3rdptest', 'my3psrc', lambda there: there)])
def test_SConsiderThirdPartyBuildOnceOnly(
        copy_testdir_to_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options, current_testdir, buildprefix,
        cpp_in_second_build):
    """Show that using the source directory name as prefix of the 3rdparty
    build output always builds the sources over and over again."""
    cmdline = r'scons --3rdparty=my3pscons --with-src-3plib=my3psrc' + scons_platform_options
    if buildprefix:
        cmdline += ' --3rdparty-build-prefix=' + buildprefix
    sub_p = PopenHelper(cmdline,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(copy_testdir_to_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert os.sep + '3plib.cpp' in stdout
    sub_p = PopenHelper(cmdline,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(copy_testdir_to_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert cpp_in_second_build(os.sep + '3plib.cpp' in stdout)
