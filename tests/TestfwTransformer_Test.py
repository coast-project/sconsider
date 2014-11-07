# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import unittest
import TestfwTransformer
from mockito import *


class TestfwTranformerStateMachineTest(unittest.TestCase):

    def setUp(self):
        self.parser = TestfwTransformer.Parser()
        self.started = mock(TestfwTransformer.StartedState)
        self.ended = mock(TestfwTransformer.EndedState)
        self.failed = mock(TestfwTransformer.FailedState)
        self.parser.states = {
            'started': self.started,
            'ended': self.ended,
            'failed': self.failed,
        }

    def testParserEndedStart(self):
        when(self.ended).start(name=any(), line=any()).thenReturn(None)
        self.parser.setState('ended')
        line = "Running StringTokenizer2Test"
        self.parser.parseLine(line)
        verify(self.ended).start(line=line, name='StringTokenizer2Test')

    def testParserStartedEnd(self):
        when(
            self.started).end(
            tests=any(),
            assertions=any(),
            msecs=any(),
            line=any()).thenReturn(None)
        self.parser.setState('started')
        line = "OK (12 tests 23 assertions 537 ms)"
        self.parser.parseLine(line)
        verify(
            self.started).end(
            line=line,
            tests='12',
            assertions='23',
            msecs='537')

    def testParserStartedFail(self):
        when(self.started).fail(line=any()).thenReturn(None)
        self.parser.setState('started')
        line = "!!!FAILURES!!!"
        self.parser.parseLine(line)
        verify(self.started).fail(line=line)

    def testParserStartedTest(self):
        when(self.started).test(name=any(), line=any()).thenReturn(None)
        self.parser.setState('started')
        line = "--SystemTest--"
        self.parser.parseLine(line)
        verify(self.started).test(line=line, name='SystemTest')

    def testParserStartedTime(self):
        when(self.started).handle(any()).thenReturn(None)
        self.parser.setState('started')
        line = "sfs dfjlk (12ms) dfsd fjl"
        self.parser.parseLine(line)
        verify(self.started).handle(line)

    def testParserStartedStop(self):
        when(
            self.started).stop(
            assertions=any(),
            msecs=any(),
            failures=any(),
            line=any()).thenReturn(None)
        self.parser.setState('started')
        line = "5 assertions 58 ms 2 failures"
        self.parser.parseLine(line)
        verify(
            self.started).stop(
            line=line,
            assertions="5",
            msecs="58",
            failures="2")

    def testParserFailedStart(self):
        when(self.failed).start(name=any(), line=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "Running StringTokenizer2Test"
        self.parser.parseLine(line)
        verify(self.failed).start(line=line, name='StringTokenizer2Test')

    def testParserFailedStop(self):
        when(
            self.failed).stop(
            assertions=any(),
            msecs=any(),
            failures=any(),
            line=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "5 assertions 58 ms 2 failures"
        self.parser.parseLine(line)
        verify(
            self.failed).stop(
            line=line,
            assertions="5",
            msecs="58",
            failures="2")

    def testParserFailedFailResult(self):
        when(
            self.failed).failResult(
            line=any(),
            runs=any(),
            failures=any(),
            errors=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "Run 55 Failure 1 Error 2"
        self.parser.parseLine(line)
        verify(
            self.failed).failResult(
            line=line,
            runs="55",
            failures="1",
            errors="2")

    def testParserFailedFailSuccess(self):
        when(
            self.failed).failSuccess(
            line=any(),
            assertions=any(),
            msecs=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "(2 assertions 35 ms)"
        self.parser.parseLine(line)
        verify(self.failed).failSuccess(line=line, assertions="2", msecs="35")

    def testParserFailedFailStartFailure(self):
        when(
            self.failed).failStartFailure(
            line=any(),
            testcase=any(),
            message=any(),
            cause=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "21) SystemTest: File.cpp:123: this is the cause"
        self.parser.parseLine(line)
        verify(
            self.failed).failStartFailure(
            line=line,
            testcase="SystemTest",
            message="File.cpp:123: this is the cause",
            cause="this is the cause")

    def testParserFailedHandle(self):
        when(self.failed).handle(any()).thenReturn(None)
        self.parser.setState('failed')
        line = "this is a string which is not handled"
        self.parser.parseLine(line)
        verify(self.failed).handle(line)
