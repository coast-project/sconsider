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
import platform
import shutil
from py.path import local


@pytest.fixture
def popen_timeout():
    timout_value = 30
    if platform.system().lower() == 'sunos':
        timout_value = 60
    timout_value = int(os.getenv('POPEN_COMMUNICATE_TIMEOUT', timout_value))
    return timout_value


@pytest.fixture
def tests_path():
    return local(os.path.dirname(__file__))


@pytest.fixture
def invocation_path(tests_path):
    return tests_path.join('invocation').join


@pytest.fixture
def pypath_extended_env():
    from . import effective_sconsider_path
    sconsider_path = os.path.dirname(effective_sconsider_path)
    the_env = os.environ
    the_env.update({'PYTHONPATH': sconsider_path})
    return the_env


@pytest.fixture
def scons_platform_options():
    specific_options = ''
    for i in ['cc', 'cxx']:
        if os.getenv(i + '_compiler'):
            specific_options += ' --with-' + i + '=' + os.getenv(i + '_compiler')
    return specific_options


@pytest.fixture
def current_testdir():
    return 'staticprog'


@pytest.fixture(scope='function')
def copy_testdir_to_tmp(tmpdir_factory, invocation_path, current_testdir):
    def ignorefiles(the_dir, names):
        ignored_list = [j for j in names if j.startswith('.sconsign') or j.endswith('.log')]
        return ignored_list

    fn = tmpdir_factory.mktemp(current_testdir, numbered=True).join('sources')
    sources_path = invocation_path(current_testdir)
    shutil.copytree(str(sources_path), str(fn), ignore=ignorefiles)
    return fn
