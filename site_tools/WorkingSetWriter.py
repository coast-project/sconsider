from __future__ import with_statement
import os, re, pdb, uuid, optparse
from SCons.Script import Dir, AddOption, GetOption
import SConsider
from xml.etree.ElementTree import ElementTree, Element

def determineProjectPath(path, topPath=None):
    path = os.path.abspath(path)
    projectFile = os.path.join(path, '.project')
    if os.path.isfile(projectFile):
        return path
    elif not topPath or path != os.path.abspath(topPath):
        return determineProjectPath(os.path.join(path, '..'), topPath)
    return None

def flattenDependencies(dependencyDict):
    dependencies = set()
    for fulltargetname, depDict in dependencyDict.iteritems():
        packagename, targetname = SConsider.splitTargetname(fulltargetname)
        dependencies.add(packagename)
        dependencies.update(flattenDependencies(depDict))
    return dependencies
        
dependencies = {}
def rememberWorkingSet(registry, packagename, buildSettings, **kw):
    dependencies[packagename] = flattenDependencies(registry.getPackageDependencies(packagename))

def writeWorkingSets(**kw):
    workspacePath = os.path.abspath(GetOption("workspace"))
    workingsetsPath = os.path.join(workspacePath, '.metadata', '.plugins', 'org.eclipse.ui.workbench')
    if not os.path.isdir(workingsetsPath):
       workingsetsPath = Dir('#').get_abspath()
    
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
            xmldeps[package]['items'].append({'factoryID': 'org.eclipse.cdt.ui.PersistableCElementFactory', 'path': '/'+dep, 'type': '4'})
            
    toXML(xmldeps, fname)
    
def fromXML(file):
    xmldeps = {}
    if os.path.isfile(file):
        tree = ElementTree()
        tree.parse(file)
        workingSetManager = tree.getroot()
        for workingSet in workingSetManager:
            items = []
            for item in workingSet:
                items.append(item.attrib)
            xmldeps[workingSet.get('label')] = {'attrs': workingSet.attrib, 'items': items}
    return xmldeps

def toXML(deps, file):
    workingSetManager = Element('workingSetManager')
    for package in deps.itervalues():
        workingSet = Element('workingSet', package['attrs'])
        for packageitem in package['items']:
            workingSet.append(Element('item', packageitem))
        workingSetManager.append(workingSet)
    ElementTree(workingSetManager).write(file, encoding="utf-8")

def generate(env):
    try:
        AddOption('--workspace', dest='workspace', action='store', default='', help='Select workspace directory')
    except optparse.OptionConflictError:
        pass
    
    SConsider.registerCallback('PostCreatePackageTargets', rememberWorkingSet)
    SConsider.registerCallback('PreBuild', writeWorkingSets)

def exists(env):
   return 1
