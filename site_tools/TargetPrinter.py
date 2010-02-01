from __future__ import with_statement
import os, pdb, subprocess, optparse
import SCons.Action, SCons.Builder
from SCons.Script import AddOption, GetOption
import SConsider, SomeUtils

def generate(env):
    """
    Add the options, builders and wrappers to the current Environment.
    """
    try:
        AddOption('--showtargets', dest='showtargets', action='store_true', default=False, help='Show available targets')
    except optparse.OptionConflictError:
        pass

    def printTargets(registry, **kw):
    
        print "\nAvailable Packages"
        print "------------------"
        packagenames = sorted(registry.packages.iterkeys())
        for pkg in packagenames:
            targets = sorted(registry.getPackageTargetNames(pkg))
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

    if GetOption("showtargets"):
        SConsider.registerCallback("PreBuild", printTargets)

def exists(env):
   return 1
