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
from SConsider.PopenHelper import PopenHelper, PIPE


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
def test_SConsiderSconstructAboveLaunchDir(invocation_path, pypath_extended_env,
                                           popen_timeout,
                                           scons_platform_options):
    progdir_path = invocation_path('staticprog', 'progdir')
    sub_p = PopenHelper(r'scons -h -u ' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(progdir_path),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'get_sconstruct_dir=' + str(invocation_path('staticprog')) in stdout
    assert 'get_launch_dir=' + str(progdir_path) in stdout
    assert 'base_out_dir=' + os.getcwd() in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgBuild(invocation_path, pypath_extended_env,
                                  popen_timeout, scons_platform_options):
    sub_p = PopenHelper(r'scons --3rdparty=' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(invocation_path('staticprog')),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'done building targets.' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithoutCommandLineTarget(
        invocation_path, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(r'scons --3rdparty= --run' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(invocation_path('staticprog')),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithPackageAsTarget(
        invocation_path, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(invocation_path('staticprog')),
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgRunWithExplicitPackageTarget(
        invocation_path, pypath_extended_env, popen_timeout,
        scons_platform_options):
    sub_p = PopenHelper(
        r'scons --3rdparty= --run hello.runner' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(invocation_path('staticprog')),
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout
