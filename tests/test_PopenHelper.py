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
from SConsider.PopenHelper import PopenHelper, PIPE, has_timeout_param


def test_CommandStringWithOutput():
    executor = PopenHelper('ls', stdout=PIPE, stderr=PIPE)
    stdout, _ = executor.communicate()
    assert 0 == executor.returncode
    assert stdout


def test_CommandArrayWithOutput():
    executor = PopenHelper(['ls'], stdout=PIPE, stderr=PIPE)
    stdout, _ = executor.communicate()
    assert 0 == executor.returncode
    assert stdout


def test_CommandStringWithOutputFromInput():
    executor = PopenHelper('cat -', stdin=PIPE, stdout=PIPE, stderr=PIPE)
    send_on_stdin = 'loopback string'
    stdout, _ = executor.communicate(stdincontent=send_on_stdin)
    assert 0 == executor.returncode
    assert send_on_stdin in stdout


@pytest.mark.skipif(not has_timeout_param, reason='only works with subprocess32 or python3.x')
def test_CommandStringWithTimeoutResultsInKill():
    executor = PopenHelper('sleep 3', stdout=PIPE, stderr=PIPE)
    _, _ = executor.communicate(timeout=1)
    assert -9 == executor.returncode


def test_CommandStringNotSplitWhenUsingShell():
    shell_string = r"""for n in 1 2 3; do
    echo $n;
done"""
    executor = PopenHelper(shell_string, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, _ = executor.communicate()
    assert 0 == executor.returncode
    assert '1\n2\n3\n' in stdout
