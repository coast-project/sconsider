from __future__ import with_statement
import os, pdb, subprocess, optparse, re, socket, time, math
from xmlbuilder import XMLBuilder

class Result(object):
    def __init__(self):
        self.sections = []
        self.currentSection = None
        self.total = {}
    
    def newSection(self, name):
        self.currentSection = {'name': name, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'hostname': socket.gethostname(), 'testcases': {}}
    def setSectionData(self, name, value):
        self.currentSection[name] = value
    def appendSectionData(self, name, value):
        self.currentSection.setdefault(name, '')
        self.currentSection[name] += value
        
    def addTest(self, name):
        self.currentSection['testcases'][name] = {'passed': True, 'message': ''}
    def setTestData(self, name, key, value):
        if self.currentSection['testcases'].has_key(name):
            self.currentSection['testcases'][name][key] = value
    def appendTestData(self, name, key, value):
        self.currentSection['testcases'][name].setdefault(key, '')
        self.currentSection['testcases'][name][key] += value
        
    def setTotal(self, name, value):
        self.total[name] = value
    def storeSection(self):
        self.sections.append(self.currentSection)
    
    def getTotal(self):
        return self.total
    def getSections(self):
        return self.sections
    
    def toXML(self, package=''):
        xml = XMLBuilder(format=True)
        with xml.testsuites():
            for section in self.getSections():
                classname = package+'.'+section.get('name', 'unknown')
                with xml.testsuite(tests=section.get('tests', 0),
                                   errors=section.get('errors', 0),
                                   failures=section.get('failures', 0),
                                   hostname=section.get('hostname', 'unknown'),
                                   time=section.get('msecs', 0),
                                   timestamp=section.get('time', ''),
                                   name=classname):
                    for name, testcase in section['testcases'].iteritems():
                        # Testfw prints 'Testcase.Testmethod', but we just need 'Testmethod' here
                        testname = re.sub('^'+section.get('name', 'unknown')+'\.', '', name)
                        with xml.testcase(name=testname, classname=classname, time=0):
                            if not testcase['passed']:
                                xml << ('failure', testcase['message'], {'message': testcase['cause'], 'type': 'Assertion' })
                    xml << ('system-out', section.get('content', '').strip())
                    xml << ('system-err', '')
        etree_node = ~xml
        return str(xml)

class State(object):
    def __init__(self, context):
        self.context = context
        self.result = context.result
    
    def __getattr__(self, attr):
        def method_missing(*args, **kw):
            pass
        return method_missing

class StartedState(State):
    def end(self, tests, assertions, msecs, **kw):
        self.result.setSectionData('tests', tests)
        self.result.setSectionData('assertions', assertions)
        self.result.setSectionData('msecs', msecs)
        self.result.storeSection()
        return 'ended'
    
    def fail(self, **kw):
        return 'failed'
    
    def test(self, name, **kw):
        self.result.addTest(name)
    
    def stop(self, assertions, msecs, failures, **kw):
        self.result.setTotal('assertions', assertions)
        self.result.setTotal('msecs', msecs)
        self.result.setTotal('failures', failures)
        return 'ended'

class EndedState(State):
    def start(self, name, **kw):
        self.result.newSection(name)
        return 'started'

class FailedState(State):    
    def start(self, name, **kw):
        self.result.storeSection()
        self.result.newSection(name)
        self.current_testcase = None
        return 'started'
    
    def stop(self, assertions, msecs, failures, **kw):
        self.result.setTotal('assertions', assertions)
        self.result.setTotal('msecs', msecs)
        self.result.setTotal('failures', failures)
        self.result.storeSection()
        self.current_testcase = None
        return 'ended'
    
    def handle(self, line, **kw):
        if isinstance(self.current_testcase, str):
            self.result.appendTestData(self.current_testcase, 'message', line)
        self.result.appendSectionData('content', line)
    
    def failResult(self, runs, failures, errors, **kw):
        self.result.setSectionData('tests', runs)
        self.result.setSectionData('failures', failures)
        self.result.setSectionData('errors', errors)
    
    def failSuccess(self, assertions, msecs, **kw):
        self.result.setSectionData('assertions', assertions)
        self.result.setSectionData('msecs', msecs)
    
    def failStartFailure(self, testcase, message, line, cause, **kw):
        self.result.setTestData(testcase, 'passed', False)
        self.result.setTestData(testcase, 'cause', cause)
        self.result.appendTestData(testcase, 'message', message.strip()+'\n')
        self.current_testcase = testcase
        self.result.appendSectionData('content', line)

class Parser(object):
    def __init__(self):
        self.result = Result()
        self.states = {
                       'started': StartedState(self),
                       'ended': EndedState(self),
                       'failed': FailedState(self),
                       }
        self.patterns = [
                        ( re.compile('^Running (.*)'),
                          lambda line, match: self.state.start(line=line, name=match.group(1)) ),
                        ( re.compile('^OK \((\d+)\D*test\D*(\d+)\D*assertion\D*(\d+)\D*ms.*\)'),
                          lambda line, match: self.state.end(line=line, tests=match.group(1), assertions=match.group(2), msecs=match.group(3)) ),
                        ( re.compile('^--([^-]+)--'),
                          lambda line, match: self.state.test(line=line, name=match.group(1)) ),
                        ( re.compile('^!!!FAILURES!!!'),
                          lambda line, match: self.state.fail(line=line) ),
                        ( re.compile('^(\d+)\D*assertion\D*(\d+)\D*ms\D*(\d+)\D*failure.*'),
                          lambda line, match: self.state.stop(line=line, assertions=match.group(1), msecs=match.group(2), failures=match.group(3)) ),
                        ( re.compile('^Run\D*(\d+)\D*Failure\D*(\d+)\D*Error\D*(\d+)'),
                          lambda line, match: self.state.failResult(line=line, runs=match.group(1), failures=match.group(2), errors=match.group(3)) ),
                        ( re.compile('^\((\d+)\D*assertion\D*(\d+)\D*ms.*\)'),
                          lambda line, match: self.state.failSuccess(line=line, assertions=match.group(1), msecs=match.group(2)) ),
                        ( re.compile('^\d+\)\s+([^\s]+):\s*(.*:\d+:\s*(.*))'),
                          lambda line, match: self.state.failStartFailure(line=line, testcase=match.group(1), message=match.group(2), cause=match.group(3)) )
                        ]
    
    def setState(self, state):
        if isinstance(state, str):
            if self.states.has_key(state):
                self.state = self.states[state]
        elif isinstance(state, State):
            self.state = state
        else:
            raise TypeError('parameter has wrong type')
    
    def parseLine(self, line):
        found = False
        for pattern, event in self.patterns:
            match = re.match(pattern, line)
            if match:
                state = event(line, match)
                if state:
                    self.setState(state)
                found = True
        if not found:
            self.state.handle(line)
    
    def parse(self, content):
        self.setState('ended')
        for line in content:
            self.parseLine(line)
        return self.result

def dependsOnTestfw(target, registry):
    import SCons
    if SCons.Util.is_List(target):
        target = target[0]
    plaintarget = registry.getPackageTarget('testfw', 'testfw')['plaintarget']
    return plaintarget.name in target.get_env()['LIBS']

def callPostTest(target, registry, packagename, targetname, logfile, **kw):
    if dependsOnTestfw(target, registry):
        parser = Parser()
        if os.path.isfile(logfile.abspath):
            with open(logfile.abspath) as file:
                result = parser.parse(file)
                with open(logfile.dir.File(targetname+'.test.xml').abspath, 'w') as xmlfile:
                    xmlfile.write(result.toXML(packagename+'.'+targetname))
                
def generate(env):
    import RunBuilder
    RunBuilder.registerCallback("PostTest", callPostTest)

def exists(env):
    return 1
