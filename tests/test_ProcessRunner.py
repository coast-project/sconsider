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
from SConsider.PopenHelper import ProcessRunner, STDOUT, CalledProcessError, TimeoutExpired


def test_CommandStringWithStdout(capfd):
    cmd = 'ls'
    with ProcessRunner(cmd) as executor:
        for out, _ in executor:
            sys.stdout.write(out)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'setup.py' in captured.out


def test_CommandStringWithStderr(capfd):
    with pytest.raises(CalledProcessError) as excinfo:
        cmd = 'ls _NotEx.isting_'
        with ProcessRunner(cmd) as executor:
            for out, err in executor:
                sys.stdout.write(out)
                sys.stderr.write(err)
    assert 2 == excinfo.value.returncode
    captured = capfd.readouterr()
    assert 'cannot access' in captured.err
    assert '' == captured.out


def test_CommandStringWithStderrOnStdout(capfd):
    with pytest.raises(CalledProcessError) as excinfo:
        cmd = 'ls _NotEx.isting_'
        with ProcessRunner(cmd, stderr=STDOUT) as executor:
            for out, err in executor:
                sys.stdout.write(out)
                sys.stderr.write(err)
    assert 2 == excinfo.value.returncode
    captured = capfd.readouterr()
    assert 'cannot access' in captured.out
    assert '' == captured.err


def test_CommandArrayWithOutput(capfd):
    cmd = ['ls']
    with ProcessRunner(cmd) as executor:
        for out, _ in executor:
            sys.stdout.write(out)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert 'setup.py' in captured.out


def test_CommandStringWithOutputFromInput(capfd):
    cmd = 'cat -'
    send_on_stdin = 'loopback string'
    with ProcessRunner(cmd, timeout=3, stdin_handle=send_on_stdin) as executor:
        for out, err in executor:
            sys.stdout.write(out)
            sys.stderr.write(err)
    captured = capfd.readouterr()
    assert 0 == executor.returncode
    assert send_on_stdin in captured.out
    assert '' == captured.err


def test_CommandStringWithTimeoutResultsInKill():
    with pytest.raises(TimeoutExpired) as excinfo:
        cmd = 'sleep 3'
        with ProcessRunner(cmd, timeout=1) as executor:
            for out, _ in executor:
                sys.stdout.write(out)
    assert 'sleep' in str(excinfo.value.cmd)


def test_CommandStringNotSplitWhenUsingShell(capfd):
    cmd = r"""for n in 1 2 3; do
    echo $n;
done"""
    with ProcessRunner(cmd, timeout=1, shell=True) as executor:
        for out, _ in executor:
            sys.stdout.write(out)
    assert 0 == executor.returncode
    captured = capfd.readouterr()
    assert '1\n2\n3\n' in captured.out
