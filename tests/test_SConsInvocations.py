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
from SConsider.PopenHelper import PopenHelper, PIPE


@pytest.mark.invocation
def test_SConsiderGetHelp(invocation_path, pypath_extended_env, popen_timeout,
                          scons_platform_options):
    sub_p = PopenHelper(r'scons -f SConstruct -h' + scons_platform_options,
                        stdout=PIPE,
                        stderr=PIPE,
                        cwd=str(invocation_path('gethelp')),
                        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert '--baseoutdir' in stdout
    assert '--archbits' in stdout


@pytest.mark.invocation
def test_SConsiderStaticProgBuild(invocation_path, pypath_extended_env,
                                  popen_timeout, scons_platform_options):
    sub_p = PopenHelper(r'scons -f SConstruct' + scons_platform_options,
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
    sub_p = PopenHelper(r'scons -f SConstruct --run' + scons_platform_options,
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
        r'scons -f SConstruct --run hello' + scons_platform_options,
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
        r'scons -f SConstruct --run hello.runner' + scons_platform_options,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(invocation_path('staticprog')),
        env=pypath_extended_env)
    stdout, _ = sub_p.communicate(timeout=popen_timeout)
    assert 0 == sub_p.returncode
    assert 'Hello from SConsider' in stdout
