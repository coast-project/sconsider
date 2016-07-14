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
import SomeUtils
import os
from .test_Package import TargetStub


class TestSomeUtils(unittest.TestCase):
    def test_MultipleReplace(self):
        text = "this is a dummy text for testing"
        result = SomeUtils.multiple_replace([
            ('dummy', 'fantastic'), ('text', 'string'), ('^t\S*', 'blub')
        ], text)
        self.assertEqual("blub is a fantastic string for testing", result)


class TestAllFuncs(unittest.TestCase):
    def setUp(self):
        self.funcs = [
            lambda *attrs: True, lambda *attrs: True, lambda *attrs: True
        ]

    def test_AllFuncsTrue(self):
        self.assertTrue(SomeUtils.allFuncs(self.funcs, "blub"))

    def test_AllFuncsFalse(self):
        self.funcs.append(lambda *attrs: False)
        self.assertFalse(SomeUtils.allFuncs(self.funcs, "blub"))

    def test_AllFuncsMultipleArgs(self):
        self.assertTrue(SomeUtils.allFuncs(self.funcs, "blub", "bla", "bloek"))


class TestNodeFilter(unittest.TestCase):
    def test_IsFileNodeTrue(self):
        target = TargetStub(path=os.path.dirname(__file__))
        self.assertTrue(SomeUtils.isFileNode(target))

    def test_IsFileNodeFalse(self):
        target = TargetStub()
        self.assertFalse(SomeUtils.isFileNode(target))

    def test_IsDerivedNodeTrue(self):
        target = TargetStub(builder=object())
        self.assertTrue(SomeUtils.isDerivedNode(target))

    def test_IsDerivedNodeFalseNoBuilder(self):
        target = TargetStub()
        self.assertFalse(SomeUtils.isDerivedNode(target))

    def test_IsDerivedNodeFalseBuilderNone(self):
        target = TargetStub(builder=None)
        self.assertFalse(SomeUtils.isDerivedNode(target))


class TestNotHasPathPartFilter(unittest.TestCase):
    def hasPathPart(self, path, part):
        target = TargetStub(path=path)
        return SomeUtils.hasPathPart(target, part)

    def test_NotHasPathPart(self):
        self.assertFalse(self.hasPathPart('bla/blub/bloek', '.build'))

    def test_HasPathPartFirst(self):
        self.assertTrue(self.hasPathPart('.build/blub/bloek', '.build'))

    def test_HasPathPartMiddle(self):
        self.assertTrue(self.hasPathPart('bla/.build/bloek', '.build'))

    def test_HasPathPartLast(self):
        self.assertTrue(self.hasPathPart('bla/blub/.build', '.build'))

    def test_NotHasPathPartMulti(self):
        self.assertFalse(self.hasPathPart('bla/.build/blub/bloek',
                                          '.build/bloek'))

    def test_HasPathPartMultiFirst(self):
        self.assertTrue(self.hasPathPart('bla/.build/blub/bloek',
                                         'bla/.build/blub'))

    def test_HasPathPartMultiMiddle(self):
        self.assertTrue(self.hasPathPart('bla/.build/bloek/blim',
                                         '.build/bloek'))

    def test_HasPathPartMultiLast(self):
        self.assertTrue(self.hasPathPart('bla/blub/bloek/.build',
                                         'bloek/.build'))


class TestGetNodeDependencies(unittest.TestCase):
    def setUp(self):
        self.source1 = TargetStub(path="source1")
        self.source2 = TargetStub(path="source2")
        self.source3 = TargetStub(path="source3")

        self.blub = TargetStub(path="blub", sources=[self.source1])
        self.bla = TargetStub(path="bla", sources=[self.source1, self.source2])
        self.bloek = TargetStub(path="bloek",
                                sources=[
                                    self.source2, self.source3
                                ])

        self.alias = TargetStub(sources=[
            self.blub
        ], depends=[
            self.bla
        ], prerequisites=[
            self.bloek
        ])

    def test_NodeDependencies(self):
        deps = SomeUtils.getNodeDependencies(self.bloek)
        self.assertEqual(len(deps), 2)

    def test_NodeDependenciesAlias(self):
        deps = SomeUtils.getNodeDependencies(self.alias)
        self.assertEqual(len(deps), 6)
