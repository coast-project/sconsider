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
import Package
import SomeUtils


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


class EnvWrapper(dict):
    def __init__(self, values):
        super(EnvWrapper, self).__init__(values)

    def getRelativeVariantDirectory(self):
        return self['VARIANTDIR']


class TargetStub(UpdateableObject):
    sources = []
    depends = []
    prerequisites = []

    def get_executor(self):
        return ExecutorStub([self])

    def is_derived(self):
        """Try to imitate SCons.Node.is_derived()

        No builder (or None as builder means this is not a derived
        target.

        """
        return hasattr(self, 'builder') and not self.builder is None


class TestPackageTool(unittest.TestCase):
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

    def test_TargetDependenciesAlias(self):
        deps = Package.getTargetDependencies(self.alias)
        self.assertEqual(len(deps), 6)

    def test_DerivedTargetDependenciesZero(self):
        deps = Package.getTargetDependencies(self.alias,
                                             SomeUtils.isDerivedNode)
        self.assertEqual(len(deps), 0)

    def test_DerivedTargetDependencies(self):
        self.blub.builder = object()
        self.bla.builder = object()
        deps = Package.getTargetDependencies(self.alias,
                                             SomeUtils.isDerivedNode)
        self.assertEqual(len(deps), 2)

    def test_TargetDependenciesTarget(self):
        self.alias.path = "target1"
        self.alias.builder = object()
        deps = Package.getTargetDependencies(self.alias,
                                             SomeUtils.isDerivedNode)
        self.assertEqual(len(deps), 1)


class TestInstalledNode(unittest.TestCase):
    def setUp(self):
        self.node1 = TargetStub(path="3rdparty/blub")
        self.node2 = TargetStub(path="bin/blub",
                                sources=[
                                    self.node1
                                ],
                                builder=UpdateableObject(name='InstallBuilder'))
        self.node3 = TargetStub(path="tests/bla/bin/blub",
                                sources=[
                                    self.node2
                                ],
                                builder=UpdateableObject(name='InstallBuilder'))
        self.testnode = TargetStub(path="bin/blub")

    def test_IsInstalledNode(self):
        self.assertTrue(Package.isInstalledNode(self.testnode, self.node3))

    def test_NotIsInstalledNode(self):
        self.node3.builder.name = "BlaBuilder"
        self.assertFalse(Package.isInstalledNode(self.testnode, self.node3))


class TestPathFilter(unittest.TestCase):
    def setUp(self):
        self.path = "apps/package/bin/variant123/blub"

    def test_FilterTestsAppsGlobalsPath(self):
        self.assertEqual(
            Package.filterTestsAppsGlobalsPath(self.path),
            "bin/variant123/blub")

    def test_FilterVariantPath(self):
        env = EnvWrapper({'VARIANTDIR': 'variant123'})
        self.assertEqual(
            Package.filterVariantPath(self.path, env=env),
            "apps/package/bin/blub")
