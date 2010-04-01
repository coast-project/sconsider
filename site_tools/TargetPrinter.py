from __future__ import with_statement
import os, pdb, subprocess, optparse
import SCons.Action, SCons.Builder
from SCons.Script import AddOption, GetOption
import SConsider, SomeUtils

def printTargets(registry, **kw):
    print "\nAvailable Packages"
    print "------------------"
    packagenames = sorted(registry.getPackageNames(), key=str.lower)
    for pkg in packagenames:
        targets = sorted(registry.getPackageTargetNames(pkg), key=str.lower)
        if targets:
            print "%s:" % pkg
            print " - " + ", ".join(targets)

    print "\nAvailable Aliases"
    print "-----------------"
    env = SConsider.cloneBaseEnv()
    for al in env.ans.keys():
        pkg, target = SConsider.splitTargetname(al)
        if not registry.hasPackage(pkg):
            print al

    print "\nOption 'showtargets' active, exiting."
    exit()

def printDependencies(deps, indent=0):
    keys = sorted(deps.iterkeys(), key=str.lower)
    for targetname in keys:
        print ("  "*indent)+"+-"+targetname
        printDependencies(deps[targetname], indent+1)

def getDependencies(registry, packagename, targetname=None):
    if targetname:
        return registry.getPackageTargetDependencies(packagename, targetname)
    return registry.getPackageDependencies(packagename)

def existsTarget(registry, packagename, targetname=None):
    if targetname:
        return registry.hasPackageTarget(packagename, targetname)
    return registry.hasPackage(packagename)

def printTree(registry, buildTargets, **kw):
    targets = buildTargets
    if not targets:
        targets = registry.getPackageNames()

    deps = dict()
    for fulltargetname in targets:
        packagename, targetname = SConsider.splitTargetname(fulltargetname)
        if existsTarget(registry, packagename, targetname):
            deps[SConsider.generateFulltargetname(packagename, targetname)] = getDependencies(registry, packagename, targetname)
 
    printDependencies(deps)

    print "\nOption 'showtree' active, exiting."
    exit()

def generate(env):
    """
    Add the options, builders and wrappers to the current Environment.
    """
    try:
        AddOption('--showtargets', dest='showtargets', action='store_true', default=False, help='Show available targets')
        AddOption('--showtree', dest='showtree', action='store_true', default=False, help='Show dependencytree')
    except optparse.OptionConflictError:
        pass

    if GetOption("showtargets"):
        SConsider.registerCallback("PreBuild", printTargets)
    if GetOption("showtree"):
        SConsider.registerCallback("PreBuild", printTree)

def exists(env):
   return 1
