import unittest
import SomeUtils
import os
from .Package_Test import TargetStub


class SomeUtilsTest(unittest.TestCase):

    def testMultipleReplace(self):
        text = "this is a dummy text for testing"
        result = SomeUtils.multiple_replace([
            ('dummy', 'fantastic'),
            ('text', 'string'),
            ('^t\S*', 'blub')
        ], text)
        self.assertEqual("blub is a fantastic string for testing", result)


class AllFuncsTest(unittest.TestCase):

    def setUp(self):
        self.funcs = [
            lambda *
            attrs: True,
            lambda *
            attrs: True,
            lambda *
            attrs: True]

    def testAllFuncsTrue(self):
        self.assertTrue(SomeUtils.allFuncs(self.funcs, "blub"))

    def testAllFuncsFalse(self):
        self.funcs.append(lambda *attrs: False)
        self.assertFalse(SomeUtils.allFuncs(self.funcs, "blub"))

    def testAllFuncsMultipleArgs(self):
        self.assertTrue(SomeUtils.allFuncs(self.funcs, "blub", "bla", "bloek"))


class NodeFilterTest(unittest.TestCase):

    def testIsFileNodeTrue(self):
        target = TargetStub(path=os.path.dirname(__file__))
        self.assertTrue(SomeUtils.isFileNode(target))

    def testIsFileNodeFalse(self):
        target = TargetStub()
        self.assertFalse(SomeUtils.isFileNode(target))

    def testIsDerivedNodeTrue(self):
        target = TargetStub(builder=object())
        self.assertTrue(SomeUtils.isDerivedNode(target))

    def testIsDerivedNodeFalseNoBuilder(self):
        target = TargetStub()
        self.assertFalse(SomeUtils.isDerivedNode(target))

    def testIsDerivedNodeFalseBuilderNone(self):
        target = TargetStub(builder=None)
        self.assertFalse(SomeUtils.isDerivedNode(target))


class NotHasPathPartFilterTest(unittest.TestCase):

    def hasPathPart(self, path, part):
        target = TargetStub(path=path)
        return SomeUtils.hasPathPart(target, part)

    def testNotHasPathPart(self):
        self.assertFalse(self.hasPathPart('bla/blub/bloek', '.build'))

    def testHasPathPartFirst(self):
        self.assertTrue(self.hasPathPart('.build/blub/bloek', '.build'))

    def testHasPathPartMiddle(self):
        self.assertTrue(self.hasPathPart('bla/.build/bloek', '.build'))

    def testHasPathPartLast(self):
        self.assertTrue(self.hasPathPart('bla/blub/.build', '.build'))

    def testNotHasPathPartMulti(self):
        self.assertFalse(
            self.hasPathPart(
                'bla/.build/blub/bloek',
                '.build/bloek'))

    def testHasPathPartMultiFirst(self):
        self.assertTrue(
            self.hasPathPart(
                'bla/.build/blub/bloek',
                'bla/.build/blub'))

    def testHasPathPartMultiMiddle(self):
        self.assertTrue(
            self.hasPathPart(
                'bla/.build/bloek/blim',
                '.build/bloek'))

    def testHasPathPartMultiLast(self):
        self.assertTrue(
            self.hasPathPart(
                'bla/blub/bloek/.build',
                'bloek/.build'))


class GetNodeDependenciesTest(unittest.TestCase):

    def setUp(self):
        self.source1 = TargetStub(path="source1")
        self.source2 = TargetStub(path="source2")
        self.source3 = TargetStub(path="source3")

        self.blub = TargetStub(path="blub", sources=[self.source1])
        self.bla = TargetStub(path="bla", sources=[self.source1, self.source2])
        self.bloek = TargetStub(
            path="bloek",
            sources=[
                self.source2,
                self.source3])

        self.alias = TargetStub(
            sources=[
                self.blub], depends=[
                self.bla], prerequisites=[
                self.bloek])

    def testNodeDependencies(self):
        deps = SomeUtils.getNodeDependencies(self.bloek)
        self.assertEqual(len(deps), 2)

    def testNodeDependenciesAlias(self):
        deps = SomeUtils.getNodeDependencies(self.alias)
        self.assertEqual(len(deps), 6)

