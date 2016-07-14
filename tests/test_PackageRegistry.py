# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from SConsider.PackageRegistry import PackageRegistry


class TestSplitTargetname(object):
    def test_SplitTargetname(self):
        pkgname, tgtname = PackageRegistry.splitFulltargetname('package.target')
        assert 'package' == pkgname
        assert 'target' == tgtname

    def test_SplitTargetnameNoTarget(self):
        pkgname, tgtname = PackageRegistry.splitFulltargetname('package')
        assert 'package' == pkgname
        assert None == tgtname

    def test_SplitTargetnameDefault(self):
        pkgname, tgtname = PackageRegistry.splitFulltargetname('package', True)
        assert 'package' == pkgname
        assert 'package' == tgtname


class TestGenerateFulltargetname(object):
    def test_GenerateFulltargetname(self):
        ftn = PackageRegistry.createFulltargetname('package', 'target')
        assert 'package.target' == ftn

    def test_GenerateFulltargetnameNoTarget(self):
        ftn = PackageRegistry.createFulltargetname('package')
        assert 'package' == ftn

    def test_GenerateFulltargetnameDefault(self):
        ftn = PackageRegistry.createFulltargetname('package', default=True)
        assert 'package.package' == ftn
