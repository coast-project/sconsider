# -------------------------------------------------------------------------
# Copyright (c) 2012, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import unittest
import PackageRegistry
import os


class SplitTargetnameTest(unittest.TestCase):

    def testSplitTargetname(self):
        pkgname, tgtname = PackageRegistry.splitTargetname(
            'package.target')
        self.assertEqual('package', pkgname)
        self.assertEqual('target', tgtname)

    def testSplitTargetnameNoTarget(self):
        pkgname, tgtname = PackageRegistry.splitTargetname('package')
        self.assertEqual('package', pkgname)
        self.assertEqual(None, tgtname)

    def testSplitTargetnameDefault(self):
        pkgname, tgtname = PackageRegistry.splitTargetname('package', True)
        self.assertEqual('package', pkgname)
        self.assertEqual('package', tgtname)


class GenerateFulltargetnameTest(unittest.TestCase):

    def testGenerateFulltargetname(self):
        ftn = PackageRegistry.generateFulltargetname('package', 'target')
        self.assertEqual('package.target', ftn)

    def testGenerateFulltargetnameNoTarget(self):
        ftn = PackageRegistry.generateFulltargetname('package')
        self.assertEqual('package', ftn)

    def testGenerateFulltargetnameDefault(self):
        ftn = PackageRegistry.generateFulltargetname('package', default=True)
        self.assertEqual('package.package', ftn)
