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
import unittest
import WorkingSetWriter
import shutil
import SomeUtils
import tempfile


class DirStub(object):

    def __init__(self, path):
        self.path = path

    def get_abspath(self):
        return self.path


class RegistryStub(object):

    def __init__(self, pkgdict):
        self.pkgdict = pkgdict

    def getPackageDir(self, packagename):
        return self.pkgdict[packagename]


class TestProjectFuncs(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.noprojectdir = os.path.join(self.tempdir, 'noproject')
        self.noprojecteitherdir = os.path.join(
            self.noprojectdir,
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

        self.invalidprojectdesc = os.path.join(
            self.tempdir,
            'invalidprojectdesc')
        with open(self.invalidprojectdesc, 'w') as file:
            file.write('<projectDescription></projectDescription>')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testDetermineProjectFilePathTop(self):
        projectPath = WorkingSetWriter.determineProjectFilePath(
            self.tempdir,
            self.tempdir)
        self.assertEqual(self.topproject, projectPath)

    def testDetermineProjectFilePathBottom(self):
        projectPath = WorkingSetWriter.determineProjectFilePath(
            self.projectdir,
            self.tempdir)
        self.assertEqual(self.bottomproject, projectPath)

    def testDetermineProjectFilePathNoProject(self):
        self.assertEqual(
            self.topproject,
            WorkingSetWriter.determineProjectFilePath(
                self.noprojectdir,
                self.tempdir))
        self.assertEqual(
            self.topproject,
            WorkingSetWriter.determineProjectFilePath(
                self.noprojecteitherdir,
                self.tempdir))

    def testGetProjectNameFromProjectFile(self):
        self.assertEqual(
            'Top',
            WorkingSetWriter.getProjectNameFromProjectFile(
                self.topproject))
        self.assertEqual(
            'Bottom',
            WorkingSetWriter.getProjectNameFromProjectFile(
                self.bottomproject))
        self.assertEqual(
            None,
            WorkingSetWriter.getProjectNameFromProjectFile(
                os.path.join(
                    self.noprojectdir,
                    '.project')))
        self.assertEqual(
            None,
            WorkingSetWriter.getProjectNameFromProjectFile(
                self.invalidprojectdesc))

    def testDetermineProjectDependencies(self):
        pkgdict = {
            'Top': DirStub(self.tempdir),
            'Bottom': DirStub(self.projectdir),
            'NoProject1': DirStub(self.noprojectdir),
            'NoProject2': DirStub(self.noprojecteitherdir)
        }
        registry = RegistryStub(pkgdict)

        dependencyDict = {'Top.t1': {'NoProject1.t1': {}, 'NoProject2.t1': {}}}
        deps = WorkingSetWriter.determineProjectDependencies(
            dependencyDict,
            registry,
            self.tempdir)
        self.assertEqual(set(['Top']), deps)

        dependencyDict = {
            'Top.t1': {
                'NoProject1.t1': {},
                'NoProject2.t1': {
                    'Bottom.t1': {}}}}
        deps = WorkingSetWriter.determineProjectDependencies(
            dependencyDict,
            registry,
            self.tempdir)
        self.assertEqual(set(['Top', 'Bottom']), deps)
