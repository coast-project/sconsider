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
import sys
from SConsider.PopenHelper import ProcessRunner, TimeoutExpired


def test_CommandStringWithOutput(capfd):
    cmd = 'ls'
    with ProcessRunner(cmd) as executor:
        for out in executor:
            sys.stdout.write(out)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'setup.py' in captured.out


def test_CommandArrayWithOutput(capfd):
    cmd = ['ls']
    with ProcessRunner(cmd) as executor:
        for out in executor:
            sys.stdout.write(out)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'setup.py' in captured.out


# def test_CommandStringWithOutputFromInput(capfd):
#     cmd = 'cat -'
#     send_on_stdin = 'loopback string'
#     with ProcessRunner(cmd, timeout=3, stdin_handle=send_on_stdin) as executor:
#         for out in executor:
#             sys.stdout.write(out)
#     captured = capfd.readouterr()
#     assert 0 == executor.returncode
#     assert send_on_stdin in captured.out


def test_CommandStringWithTimeoutResultsInKill():
    with pytest.raises(TimeoutExpired) as excinfo:
        cmd = 'sleep 3'
        with ProcessRunner(cmd, timeout=1) as executor:
            for out in executor:
                sys.stdout.write(out)
    assert 'sleep' in str(excinfo.value.cmd)


def test_CommandStringNotSplitWhenUsingShell(capfd):
    cmd = r"""for n in 1 2 3; do
    echo $n;
done"""
    with ProcessRunner(cmd, timeout=1, shell=True) as executor:
        for out in executor:
            sys.stdout.write(out)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert '1\n2\n3\n' in captured.out
