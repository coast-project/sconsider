# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import unittest
from SConsider.PackageRegistry import PackageRegistry


class TestSplitTargetname(unittest.TestCase):
    def test_SplitTargetname(self):
        pkgname, tgtname = PackageRegistry.splitFulltargetname('package.target')
        self.assertEqual('package', pkgname)
        self.assertEqual('target', tgtname)

    def test_SplitTargetnameNoTarget(self):
        pkgname, tgtname = PackageRegistry.splitFulltargetname('package')
        self.assertEqual('package', pkgname)
        self.assertEqual(None, tgtname)

    def test_SplitTargetnameDefault(self):
        pkgname, tgtname = PackageRegistry.splitFulltargetname('package', True)
        self.assertEqual('package', pkgname)
        self.assertEqual('package', tgtname)


class TestGenerateFulltargetname(unittest.TestCase):
    def test_GenerateFulltargetname(self):
        ftn = PackageRegistry.createFulltargetname('package', 'target')
        self.assertEqual('package.target', ftn)

    def test_GenerateFulltargetnameNoTarget(self):
        ftn = PackageRegistry.createFulltargetname('package')
        self.assertEqual('package', ftn)

    def test_GenerateFulltargetnameDefault(self):
        ftn = PackageRegistry.createFulltargetname('package', default=True)
        self.assertEqual('package.package', ftn)
