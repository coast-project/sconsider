from __future__ import with_statement
import os, re, pdb, uuid, optparse
from SCons.Script import Dir, AddOption, GetOption
import SConsider
from xmlbuilder import XMLBuilder

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
def createWorkingSet(registry, packagename, buildSettings, **kw):
    dependencies[packagename] = flattenDependencies(registry.getPackageDependencies(packagename))
    
def writeWorkingSets(**kw):
    workspacePath = os.path.abspath(GetOption("workspace"))
    workingsetsPath = os.path.join(workspacePath, '.metadata', '.plugins', 'org.eclipse.ui.workbench')
    if not os.path.isdir(workingsetsPath):
       workingsetsPath = Dir('#').get_abspath()
    fname = os.path.join(workingsetsPath, 'workingsets.xml')
    with open(fname, 'w') as wsfile:
        print >>wsfile, '<?xml version="1.0" encoding="UTF-8"?>'
        print >>wsfile, '<workingSetManager>'
        for package, deps in dependencies.iteritems():
            print >>wsfile, toXML(package, deps)
        print >>wsfile, '</workingSetManager>'
        
def toXML(title, packages):
    xml = XMLBuilder(format=True)
    with xml.workingSet(editPageId='org.eclipse.cdt.ui.CElementWorkingSetPage',
                       factoryID='org.eclipse.ui.internal.WorkingSetFactory',
                       id=uuid.uuid1().int,
                       label=title,
                       name=title):
        for package in packages:
            xml << ('item', {'factoryID': 'org.eclipse.cdt.ui.PersistableCElementFactory', 'path': '/'+package, 'type': '4'})
    etree_node = ~xml
    return str(xml)

def generate(env):
    try:
        AddOption('--workspace', dest='workspace', action='store', default='', help='Select workspace directory')
    except optparse.OptionConflictError:
        pass
    
    SConsider.registerCallback('PostCreatePackageTargets', createWorkingSet)
    SConsider.registerCallback('PreBuild', writeWorkingSets)

def exists(env):
   return 1
