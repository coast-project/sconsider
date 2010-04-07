import os, unittest, Package, functools

class AllFuncsTest(unittest.TestCase):
    def setUp(self):
        self.funcs = [lambda *attrs: True, lambda *attrs: True, lambda *attrs: True]
    
    def testAllFuncsTrue(self):        
        self.assertTrue(Package.allFuncs(self.funcs, "blub"))
        
    def testAllFuncsFalse(self):
        self.funcs.append(lambda *attrs: False)        
        self.assertFalse(Package.allFuncs(self.funcs, "blub"))
        
    def testAllFuncsMultipleArgs(self):        
        self.assertTrue(Package.allFuncs(self.funcs, "blub", "bla", "bloek"))

class UpdateableObject(object):
    def __init__(self, **kw):
        self.update(kw)
        
    def update(self, dict):
        for key, value in dict.iteritems():
            setattr(self, key, value)

class TargetStub(UpdateableObject):
    sources = []
    depends = []
    prerequisites = []
    
    def is_derived(self):
        """Try to imitate SCons.Node.is_derived()
        
        No builder (or None as builder means this is not a derived target.
        """
        return hasattr(self, 'builder') and not self.builder is None

class TargetFilterTest(unittest.TestCase):  
    def testIsFileDependencyTrue(self):
        target = TargetStub(path = os.path.dirname(__file__))
        self.assertTrue(Package.isFileDependency(target))
        
    def testIsFileDependencyFalse(self):
        target = TargetStub()
        self.assertFalse(Package.isFileDependency(target))
    
    def testIsDerivedDependencyTrue(self):
        target = TargetStub(builder = object())
        self.assertTrue(Package.isDerivedDependency(target))
    
    def testIsDerivedDependencyFalseNoBuilder(self):
        target = TargetStub()
        self.assertFalse(Package.isDerivedDependency(target))
    
    def testIsDerivedDependencyFalseBuilderNone(self):
        target = TargetStub(builder = None)
        self.assertFalse(Package.isDerivedDependency(target))

class NotHasPathPartFilterTest(unittest.TestCase):
    def hasPathPart(self, path, part):
        target = TargetStub(path = path)
        return Package.hasPathPart(target, part)
    
    def testNotHasPathPart(self):
        self.assertFalse(self.hasPathPart('bla/blub/bloek', '.build'))
    
    def testHasPathPartFirst(self):
        self.assertTrue(self.hasPathPart('.build/blub/bloek', '.build'))

    def testHasPathPartMiddle(self):      
        self.assertTrue(self.hasPathPart('bla/.build/bloek', '.build'))
    
    def testHasPathPartLast(self):
        self.assertTrue(self.hasPathPart('bla/blub/.build', '.build'))

    def testNotHasPathPartMulti(self):
        self.assertFalse(self.hasPathPart('bla/.build/blub/bloek', '.build/bloek'))
    
    def testHasPathPartMultiFirst(self):
        self.assertTrue(self.hasPathPart('bla/.build/blub/bloek', 'bla/.build/blub'))
        
    def testHasPathPartMultiMiddle(self):
        self.assertTrue(self.hasPathPart('bla/.build/bloek/blim', '.build/bloek'))
    
    def testHasPathPartMultiLast(self):
        self.assertTrue(self.hasPathPart('bla/blub/bloek/.build', 'bloek/.build'))

class PackageToolTest(unittest.TestCase):
    def setUp(self):
        self.source1 = TargetStub(path = "source1")
        self.source2 = TargetStub(path = "source2")
        self.source3 = TargetStub(path = "source3")
        
        self.blub = TargetStub(path = "blub", sources = [self.source1])
        self.bla = TargetStub(path = "bla", sources = [self.source1, self.source2])
        self.bloek = TargetStub(path = "bloek", sources = [self.source2, self.source3])
        
        self.alias = TargetStub(sources = [self.blub], depends=[self.bla], prerequisites=[self.bloek])
    
    def testTargetDependenciesAlias(self):
        deps = Package.getTargetDependencies(self.alias)
        self.assertEqual(len(deps), 6)
    
    def testDerivedTargetDependenciesZero(self):
        deps = Package.getTargetDependencies(self.alias, Package.isDerivedDependency)
        self.assertEqual(len(deps), 0)
    
    def testDerivedTargetDependencies(self):
        self.blub.builder = object()
        self.bla.builder = object()
        deps = Package.getTargetDependencies(self.alias, Package.isDerivedDependency)
        self.assertEqual(len(deps), 2)

    def testTargetDependenciesTarget(self):
        self.alias.path = "target1"
        self.alias.builder = object() 
        deps = Package.getTargetDependencies(self.alias, Package.isDerivedDependency)
        self.assertEqual(len(deps), 1)

class InstalledDependencyTest(unittest.TestCase):
    def setUp(self):
        self.node1 = TargetStub(path = "3rdparty/blub")
        self.node2 = TargetStub(path = "bin/blub",
                                sources = [self.node1],
                                builder = UpdateableObject(name='InstallBuilder'))
        self.node3 = TargetStub(path = "tests/bla/bin/blub",
                                sources = [self.node2],
                                builder = UpdateableObject(name='InstallBuilder'))
        self.testnode = TargetStub(path = "bin/blub")

    def testIsInstalledDependency(self):
        self.assertTrue(Package.isInstalledDependency(self.testnode, self.node3))

    def testNotIsInstalledDependency(self):
        self.node3.builder.name = "BlaBuilder"
        self.assertFalse(Package.isInstalledDependency(self.testnode, self.node3))
