import os, unittest, Package, functools, SomeUtils

class UpdateableObject(object):
    def __init__(self, **kw):
        self.update(kw)
        
    def update(self, dict):
        for key, value in dict.iteritems():
            setattr(self, key, value)

class ExecutorStub(object):
    def __init__(self, targets):
        if not isinstance(targets, list):
            targets = [targets]
        self.targets = targets
    def get_all_targets(self):
        return self.targets

class TargetStub(UpdateableObject):
    sources = []
    depends = []
    prerequisites = []
    
    def get_executor(self):
        return ExecutorStub([self])

    def is_derived(self):
        """Try to imitate SCons.Node.is_derived()
        
        No builder (or None as builder means this is not a derived target.
        """
        return hasattr(self, 'builder') and not self.builder is None

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
        deps = Package.getTargetDependencies(self.alias, SomeUtils.isDerivedNode)
        self.assertEqual(len(deps), 0)
    
    def testDerivedTargetDependencies(self):
        self.blub.builder = object()
        self.bla.builder = object()
        deps = Package.getTargetDependencies(self.alias, SomeUtils.isDerivedNode)
        self.assertEqual(len(deps), 2)

    def testTargetDependenciesTarget(self):
        self.alias.path = "target1"
        self.alias.builder = object() 
        deps = Package.getTargetDependencies(self.alias, SomeUtils.isDerivedNode)
        self.assertEqual(len(deps), 1)

class InstalledNodeTest(unittest.TestCase):
    def setUp(self):
        self.node1 = TargetStub(path = "3rdparty/blub")
        self.node2 = TargetStub(path = "bin/blub",
                                sources = [self.node1],
                                builder = UpdateableObject(name='InstallBuilder'))
        self.node3 = TargetStub(path = "tests/bla/bin/blub",
                                sources = [self.node2],
                                builder = UpdateableObject(name='InstallBuilder'))
        self.testnode = TargetStub(path = "bin/blub")

    def testIsInstalledNode(self):
        self.assertTrue(Package.isInstalledNode(self.testnode, self.node3))

    def testNotIsInstalledNode(self):
        self.node3.builder.name = "BlaBuilder"
        self.assertFalse(Package.isInstalledNode(self.testnode, self.node3))

class PathFilterTest(unittest.TestCase):
    def setUp(self):
        self.path = "apps/package/bin/variant123/blub"

    def testFilterTestsAppsGlobalsPath(self):
        self.assertEqual(Package.filterTestsAppsGlobalsPath(self.path), "bin/variant123/blub")
        
    def testFilterVariantPath(self):
        env = {'VARIANTDIR': 'variant123'}
        self.assertEqual(Package.filterVariantPath(self.path, env=env), "apps/package/bin/blub")
