# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import pytest
from SConsider.PackageRegistry import PackageRegistry


@pytest.fixture(scope="module")
def registry():
    return PackageRegistry(None)


def test_SplitTargetname(registry):
    pkgname, tgtname = PackageRegistry.splitFulltargetname('package.target')
    assert 'package' == pkgname
    assert 'target' == tgtname


def test_SplitTargetnameNoTarget(registry):
    pkgname, tgtname = PackageRegistry.splitFulltargetname('package')
    assert 'package' == pkgname
    assert None is tgtname


def test_SplitTargetnameDefault(registry):
    pkgname, tgtname = PackageRegistry.splitFulltargetname('package', True)
    assert 'package' == pkgname
    assert 'package' == tgtname


def test_GenerateFulltargetname(registry):
    ftn = PackageRegistry.createFulltargetname('package', 'target')
    assert 'package.target' == ftn


def test_GenerateFulltargetnameNoTarget(registry):
    ftn = PackageRegistry.createFulltargetname('package')
    assert 'package' == ftn


def test_GenerateFulltargetnameDefault(registry):
    ftn = PackageRegistry.createFulltargetname('package', default=True)
    assert 'package.package' == ftn
