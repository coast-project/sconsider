# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import os
import shutil
import tempfile
import WorkingSetWriter
from SConsider.PackageRegistry import PackageRegistry


class DirStub(object):
    def __init__(self, path):
        self.path = path

    def get_abspath(self):
        return self.path


class RegistryStub(object):
    def __init__(self, pkgdict):
        self.pkgdict = pkgdict
        self.registry = PackageRegistry(None, [])
        self.registry.getPackageDir = self.__getPackageDir

    def __getPackageDir(self, packagename):
        return self.pkgdict[packagename]

    def __getattr__(self, name):
        return getattr(self.registry, name)


class TestProjectFuncs(object):
    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()
        self.noprojectdir = os.path.join(self.tempdir, 'noproject')
        self.noprojecteitherdir = os.path.join(self.noprojectdir,
                                               'noprojecteither')
        self.projectdir = os.path.join(self.noprojecteitherdir, 'project')
        os.makedirs(self.projectdir)

        self.topproject = os.path.join(self.tempdir, '.project')
        with open(self.topproject, 'w') as file:
            file.write(
                '<projectDescription><name>Top</name></projectDescription>')
        self.bottomproject = os.path.join(self.projectdir, '.project')
        with open(self.bottomproject, 'w') as file:
            file.write(
                '<projectDescription><name>Bottom</name></projectDescription>')

        self.invalidprojectdesc = os.path.join(self.tempdir,
                                               'invalidprojectdesc')
        with open(self.invalidprojectdesc, 'w') as file:
            file.write('<projectDescription></projectDescription>')

    def teardown_method(self, method):
        shutil.rmtree(self.tempdir)

    def test_DetermineProjectFilePathTop(self):
        projectPath = WorkingSetWriter.determineProjectFilePath(self.tempdir,
                                                                self.tempdir)
        assert self.topproject == projectPath

    def test_DetermineProjectFilePathBottom(self):
        projectPath = WorkingSetWriter.determineProjectFilePath(self.projectdir,
                                                                self.tempdir)
        assert self.bottomproject == projectPath

    def test_DetermineProjectFilePathNoProject(self):
        assert self.topproject == WorkingSetWriter.determineProjectFilePath(
            self.noprojectdir, self.tempdir)
        assert self.topproject == WorkingSetWriter.determineProjectFilePath(
            self.noprojecteitherdir, self.tempdir)

    def test_GetProjectNameFromProjectFile(self):
        assert 'Top' == WorkingSetWriter.getProjectNameFromProjectFile(
            self.topproject)
        assert 'Bottom' == WorkingSetWriter.getProjectNameFromProjectFile(
            self.bottomproject)
        assert None == WorkingSetWriter.getProjectNameFromProjectFile(
            os.path.join(self.noprojectdir, '.project'))
        assert None == WorkingSetWriter.getProjectNameFromProjectFile(
            self.invalidprojectdesc)

    def test_DetermineProjectDependencies(self):
        pkgdict = {
            'Top': DirStub(self.tempdir),
            'Bottom': DirStub(self.projectdir),
            'NoProject1': DirStub(self.noprojectdir),
            'NoProject2': DirStub(self.noprojecteitherdir)
        }
        registry = RegistryStub(pkgdict)

        dependencyDict = {'Top.t1': {'NoProject1.t1': {}, 'NoProject2.t1': {}}}
        deps = WorkingSetWriter.determineProjectDependencies(
            dependencyDict, registry, self.tempdir)
        assert set(['Top']) == deps

        dependencyDict = {
            'Top.t1': {
                'NoProject1.t1': {},
                'NoProject2.t1': {
                    'Bottom.t1': {}
                }
            }
        }
        deps = WorkingSetWriter.determineProjectDependencies(
            dependencyDict, registry, self.tempdir)
        assert set(['Top', 'Bottom']) == deps
