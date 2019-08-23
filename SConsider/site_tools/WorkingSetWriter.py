"""SConsider.site_tools.workingSetWriter.

Eclipse-SConsider-specific tool to create an eclipse working set filter
file.  Each directory containing an eclipse .project file is scanned for
its dependencies to other 'eclipse' project files.
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from __future__ import with_statement
import os
import uuid
from SConsider.PackageRegistry import PackageRegistry
from xml.etree.ElementTree import ElementTree, Element


def determineProjectFilePath(path, topPath=None):
    path = os.path.abspath(path)
    projectFile = os.path.join(path, '.project')
    if os.path.isfile(projectFile):
        return projectFile
    elif not topPath or path != os.path.abspath(topPath):
        return determineProjectFilePath(os.path.join(path, '..'), topPath)
    return None


def getProjectNameFromProjectFile(projectFile):
    if not os.path.isfile(projectFile):
        return None

    tree = ElementTree()
    tree.parse(projectFile)
    return tree.findtext('name')


def determineProjectDependencies(dependencyDict, registry, topPath):
    project_dependencies = set()
    for fulltargetname, depDict in dependencyDict.iteritems():
        packagename, _ = PackageRegistry.splitFulltargetname(fulltargetname)
        packagePath = registry.getPackageDir(packagename).get_abspath()
        projectFilePath = determineProjectFilePath(packagePath, topPath)
        projectName = getProjectNameFromProjectFile(projectFilePath)
        if projectName:
            project_dependencies.add(projectName)
        project_dependencies.update(determineProjectDependencies(depDict, registry, topPath))
    return project_dependencies


dependencies = {}


def rememberWorkingSet(registry, packagename, **kw):
    from SCons.Script import Dir

    dependencyDict = registry.getPackageDependencies(packagename)
    dependencies[packagename] = determineProjectDependencies(
        dependencyDict, registry,
        kw.get('sconstruct_dir', Dir('#')).srcnode().get_abspath())


def writeWorkingSets(**kw):
    from SCons.Script import GetOption, Dir

    workspacePath = os.path.abspath(GetOption("workspace"))
    workingsetsPath = os.path.join(workspacePath, '.metadata', '.plugins', 'org.eclipse.ui.workbench')
    if not os.path.isdir(workingsetsPath):
        workingsetsPath = kw.get('sconstruct_dir', Dir('#')).srcnode().get_abspath()

    fname = os.path.join(workingsetsPath, 'workingsets.xml')
    xmldeps = fromXML(fname)

    for package, packagedeps in dependencies.iteritems():
        if package not in xmldeps:
            xmldeps[package] = {
                'attrs': {
                    'editPageId': 'org.eclipse.cdt.ui.CElementWorkingSetPage',
                    'factoryID': 'org.eclipse.ui.internal.WorkingSetFactory',
                    'id': str(uuid.uuid1().int),
                    'label': package,
                    'name': package
                },
                'items': []
            }
        xmldeps[package]['items'] = []
        for dep in packagedeps:
            xmldeps[package]['items'].append({
                'factoryID': 'org.eclipse.cdt.ui.PersistableCElementFactory',
                'path': '/' + dep,
                'type': '4'
            })

    toXML(xmldeps, fname)


def fromXML(filename):
    xmldeps = {}
    if os.path.isfile(filename):
        tree = ElementTree()
        tree.parse(filename)
        workingSetManager = tree.getroot()
        for workingSet in workingSetManager:
            items = []
            for item in workingSet:
                items.append(item.attrib)
            xmldeps[workingSet.get('label')] = {'attrs': workingSet.attrib, 'items': items}
    return xmldeps


def toXML(deps, filename):
    workingSetManager = Element('workingSetManager')
    for package in deps.itervalues():
        workingSet = Element('workingSet', package['attrs'])
        for packageitem in package['items']:
            workingSet.append(Element('item', packageitem))
        workingSetManager.append(workingSet)
    ElementTree(workingSetManager).write(filename, encoding="utf-8")


def generate(env):
    from SCons.Script import AddOption
    from SConsider.Callback import Callback

    AddOption('--workspace', dest='workspace', action='store', default='', help='Select workspace directory')

    Callback().register('PostCreatePackageTargets', rememberWorkingSet)
    Callback().register('PreBuild', writeWorkingSets)


def exists(env):
    return 1
