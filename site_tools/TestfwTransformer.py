from __future__ import with_statement
import os, pdb, subprocess, optparse, re, socket, time, math
import SCons.Action, SCons.Builder, SCons.Script
from SCons.Script import AddOption, GetOption
import StanfordUtils
import RunBuilder
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
                with xml.testsuite(tests=section.get('tests', 0),
                                   errors=section.get('errors', 0),
                                   failures=section.get('failures', 0),
                                   hostname=section.get('hostname', 'unknown'),
                                   time=section.get('msecs', 0),
                                   timestamp=section.get('time', ''),
                                   package=package,
                                   name=section.get('name', '')):
                    for name, testcase in section['testcases'].iteritems():
                        with xml.testcase(name=name, classname=section.get('name', ''), time=0):
                            if not testcase['passed']:
                                xml << ('failure', testcase['message'], {'message': 'failed', 'type': 'Assertion' })
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
    def end(self, tests, assertions, msecs):
        self.result.setSectionData('tests', tests)
        self.result.setSectionData('assertions', assertions)
        self.result.setSectionData('msecs', msecs)
        self.result.storeSection()
        self.context.setState(EndedState(self.context))
    
    def fail(self):
        self.context.setState(FailedState(self.context))
    
    def test(self, name):
        self.result.addTest(name)
    
    def stop(self, assertions, msecs, failures):
        self.result.setTotal('assertions', assertions)
        self.result.setTotal('msecs', msecs)
        self.result.setTotal('failures', failures)
        self.context.setState(EndedState(self.context))

class EndedState(State):
    def start(self, name):
        self.result.newSection(name)
        self.context.setState(StartedState(self.context))

class FailedState(State):    
    def start(self, name):
        self.result.storeSection()
        self.result.newSection(name)
        self.context.setState(StartedState(self.context))
    
    def stop(self, assertions, msecs, failures):
        self.result.setTotal('assertions', assertions)
        self.result.setTotal('msecs', msecs)
        self.result.setTotal('failures', failures)
        self.result.storeSection()
        self.context.setState(EndedState(self.context))
    
    def work(self, line):
        pattern = re.compile('^\d+\)\s+([^\s]+).*line:\s*(.*)')
        match = re.match(pattern, line)
        if match:
            self.result.setTestData(match.group(1), 'passed', False)
            self.result.appendTestData(match.group(1), 'message', match.group(2).strip()+'\n')
            self.current_testcase = match.group(1)
        else:
            if isinstance(self.current_testcase, str):
                self.result.appendTestData(self.current_testcase, 'message', line)
        self.result.appendSectionData('content', line)
    
    def failResult(self, runs, failures, errors):
        self.result.setSectionData('tests', runs)
        self.result.setSectionData('failures', failures)
        self.result.setSectionData('errors', errors)
    
    def failSuccess(self, assertions, msecs):
        self.result.setSectionData('assertions', assertions)
        self.result.setSectionData('msecs', msecs)

class Parser(object):
    def __init__(self):
        self.result = Result()
        self.patterns = [
                        ( re.compile('^Running (.*)'),
                          lambda match: self.state.start(name=match.group(1)) ),
                        ( re.compile('^OK \((\d+)\D*test\D*(\d+)\D*assertion\D*(\d+)\D*ms.*\)'),
                          lambda match: self.state.end(tests=match.group(1), assertions=match.group(2), msecs=match.group(3)) ),
                        ( re.compile('^--([^-]+)--'),
                          lambda match: self.state.test(name=match.group(1)) ),
                        ( re.compile('^!!!FAILURES!!!'),
                          lambda match: self.state.fail() ),
                        ( re.compile('^(\d+)\D*assertion\D*(\d+)\D*ms\D*(\d+)\D*failure.*'),
                          lambda match: self.state.stop(assertions=match.group(1), msecs=match.group(2), failures=match.group(3)) ),
                        ( re.compile('^Run\D*(\d+)\D*Failure\D*(\d+)\D*Error\D*(\d+)'),
                          lambda match: self.state.failResult(runs=match.group(1), failures=match.group(2), errors=match.group(3)) ),
                        ( re.compile('^\((\d+)\D*assertion\D*(\d+)\D*ms.*\)'),
                          lambda match: self.state.failSuccess(assertions=match.group(1), msecs=match.group(2)) )
                        ]
    
    def setState(self, state):
        self.state = state
    
    def parse(self, content):
        self.setState(EndedState(self))
        for line in content:
            found = False
            for pattern, event in self.patterns:
                match = re.match(pattern, line)
                if match:
                    event(match)
                    found = True
            if not found:
                self.state.work(line)
        return self.result

def dependsOnTestfw(target, registry):
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
    RunBuilder.registerCallback("PostTest", callPostTest)

def exists(env):
    return 1
