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


@pytest.fixture(scope='function')
def staticprog_tmp(tmpdir_factory, invocation_path):
    def ignorefiles(the_dir, names):
        ignored_list = [j for j in names
                        if j.startswith('.sconsign') or j.endswith('.log')]
        return ignored_list

    fn = tmpdir_factory.mktemp('staticprog', numbered=True).join('sources')
    sources_path = invocation_path('staticprog')
    shutil.copytree(str(sources_path), str(fn), ignore=ignorefiles)
    return fn


@pytest.mark.invocation
def test_SConsiderGetHelp(invocation_path, pypath_extended_env, popen_timeout,
                          scons_platform_options):
    sub_p = PopenHelper(r'scons -h' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(invocation_path('gethelp')),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert '--baseoutdir' in stdout
    assert '--archbits' in stdout


@pytest.mark.invocation
def test_SConsiderSconstructDirSameAsLaunchDir(
        invocation_path, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(r'scons -h' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(invocation_path('gethelp')),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'get_sconstruct_dir=' + str(invocation_path('gethelp')) in stdout
    assert 'get_launch_dir=' + str(invocation_path('gethelp')) in stdout
    assert 'base_out_dir=' + str(invocation_path('gethelp')) in stdout


@pytest.mark.invocation
def test_SConsiderSconstructDirBelowLaunchDir(
        invocation_path, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sconstruct_file = os.path.join(
        str(invocation_path('gethelp')), 'SConstruct')
    sub_p = PopenHelper(
        r'scons -h -f ' + sconstruct_file + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'get_sconstruct_dir=' + str(invocation_path('gethelp')) in stdout
    assert 'get_launch_dir=' + os.getcwd() in stdout
    assert 'base_out_dir=' + os.getcwd() in stdout


@pytest.mark.invocation
def test_SConsiderSconstructAboveLaunchDir(staticprog_tmp, pypath_extended_env,
                                           popen_timeout,
                                           scons_platform_options):
    progdir_path = staticprog_tmp.join('progdir')
    sub_p = PopenHelper(r'scons -h -u ' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(progdir_path),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'get_sconstruct_dir=' + str(staticprog_tmp) in stdout
    assert 'get_launch_dir=' + str(progdir_path) in stdout
    assert 'base_out_dir=' + str(staticprog_tmp) in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgBuild(staticprog_tmp, pypath_extended_env,
                                  popen_timeout, scons_platform_options):
    sub_p = PopenHelper(r'scons --3rdparty=' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(staticprog_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'done building targets.' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithoutCommandLineTarget(
        staticprog_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(r'scons --3rdparty= --run' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(staticprog_tmp),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithPackageAsTarget(
        staticprog_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(staticprog_tmp),
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithExplicitPackageTarget(
        staticprog_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello.runner' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(staticprog_tmp),
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


def assert_outputfiles_exist(baseoutdir, globcount=1):
    expected_files = [
        'apps/hello/log/*/runner.run.log',
        'apps/hello/scripts/*/hellorunner.sh', 'apps/hello/bin/*/hellorunner*'
    ]
    for glob_path in expected_files:
        assert globcount == len(glob(os.path.join(baseoutdir, glob_path)))


@pytest.mark.invocation
def test_SConsiderStaticProgBuildOutputFilesBelowStartdir(
        staticprog_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello.runner' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(staticprog_tmp),
        env=pypath_extended_env)
    _, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert staticprog_tmp.join('apps').isdir()
    assert staticprog_tmp.join('progdir').join('.build').isdir()
    assert_outputfiles_exist(str(staticprog_tmp))


@pytest.mark.invocation
def test_SConsiderStaticProgBuildOutputFilesInBaseoutdir(
        staticprog_tmp, pypath_extended_env, popen_timeout,
        scons_platform_options, tmpdir_factory):
    baseoutdir = str(tmpdir_factory.mktemp('baseoutdir', numbered=True))
    sub_p = PopenHelper(r'scons --3rdparty= --baseoutdir=' + baseoutdir +
                        ' --run hello.runner' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(staticprog_tmp),
                        env=pypath_extended_env)
    _, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert not staticprog_tmp.join('apps').isdir()
    assert not staticprog_tmp.join('progdir').join('.build').isdir()
    assert_outputfiles_exist(str(staticprog_tmp), globcount=0)
    assert_outputfiles_exist(baseoutdir)
