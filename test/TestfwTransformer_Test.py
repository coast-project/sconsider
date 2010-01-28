import unittest, TestfwTransformer
from mockito import *

class TestfwTranformerStateMachineTest(unittest.TestCase):
    def setUp(self):
        self.parser = TestfwTransformer.Parser()
        self.started = Mock(TestfwTransformer.StartedState)
        self.ended = Mock(TestfwTransformer.EndedState)
        self.failed = Mock(TestfwTransformer.FailedState)
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
        verify(self.ended).start(name='StringTokenizer2Test', line=line)
        
    def testParserStartedEnd(self):
        when(self.started).end(tests=any(), assertions=any(), msecs=any(), line=any()).thenReturn(None)
        self.parser.setState('started')
        line = "OK (12 tests 23 assertions 537 ms)"
        self.parser.parseLine(line)
        verify(self.started).end(tests='12', assertions='23', msecs='537', line=line)
          
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
        verify(self.started).test(name='SystemTest', line=line)
        
    def testParserStartedTime(self):
        when(self.started).handle(any()).thenReturn(None)
        self.parser.setState('started')
        line = "sfs dfjlk (12ms) dfsd fjl"
        self.parser.parseLine(line)
        verify(self.started).handle(line)

    def testParserStartedStop(self):
        when(self.started).stop(assertions=any(), msecs=any(), failures=any(), line=any()).thenReturn(None)
        self.parser.setState('started')
        line = "5 assertions 58 ms 2 failures"
        self.parser.parseLine(line)
        verify(self.started).stop(assertions="5", msecs="58", failures="2", line=line)

    def testParserFailedStart(self):
        when(self.failed).start(name=any(), line=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "Running StringTokenizer2Test"
        self.parser.parseLine(line)
        verify(self.failed).start(name='StringTokenizer2Test', line=line)
    
    def testParserFailedStop(self):
        when(self.failed).stop(assertions=any(), msecs=any(), failures=any(), line=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "5 assertions 58 ms 2 failures"
        self.parser.parseLine(line)
        verify(self.failed).stop(assertions="5", msecs="58", failures="2", line=line)
    
    def testParserFailedFailResult(self):
        when(self.failed).failResult(runs=any(), failures=any(), errors=any(), line=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "Run 55 Failure 1 Error 2"
        self.parser.parseLine(line)
        verify(self.failed).failResult(runs="55", failures="1", errors="2", line=line)
        
    def testParserFailedFailSuccess(self):
        when(self.failed).failSuccess(assertions=any(), msecs=any(), line=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "(2 assertions 35 ms)"
        self.parser.parseLine(line)
        verify(self.failed).failSuccess(assertions="2", msecs="35", line=line)

    def testParserFailedFailStartFailure(self):
        when(self.failed).failStartFailure(testcase=any(), message=any(), cause=any(), line=any()).thenReturn(None)
        self.parser.setState('failed')
        line = "21) SystemTest: File.cpp:123: this is the cause"
        self.parser.parseLine(line)
        verify(self.failed).failStartFailure(testcase="SystemTest", message="File.cpp:123: this is the cause", cause="this is the cause", line=line)

    def testParserFailedHandle(self):
        when(self.failed).handle(any()).thenReturn(None)
        self.parser.setState('failed')
        line = "this is a string which is not handled"
        self.parser.parseLine(line)
        verify(self.failed).handle(line)
