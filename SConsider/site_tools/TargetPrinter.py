"""SConsider.site_tools.TargetPrinter.

Tool to collect available targets for building

"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from __future__ import with_statement
import optparse
import functools
import SCons.Action
import SCons.Builder
import SCons.Util
from SCons.Script import AddOption, GetOption
import SConsider.PackageRegistry
import SomeUtils


def printTargets(registry, **kw):
    from SConsider import cloneBaseEnv
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
    env = cloneBaseEnv()

    def isPackage(alias):
        pkg, target = SConsider.PackageRegistry.PackageRegistry.splitFulltargetname(
            alias)
        return registry.hasPackage(pkg)
    filters = [lambda alias: not isPackage(alias)]
    if not GetOption("showallaliases"):
        filters.append(lambda alias: not alias.startswith('_'))

    predicate = functools.partial(SomeUtils.allFuncs, filters)

    for alias in filter(predicate, env.ans.keys()):
        print alias

    print "\nOption 'showtargets' active, exiting."
    exit()


def getDependencies(registry, packagename, targetname=None):
    if targetname:
        return registry.getPackageTargetDependencies(packagename, targetname)
    return registry.getPackageDependencies(packagename)


def existsTarget(registry, packagename, targetname=None):
    if targetname:
        return registry.hasPackageTarget(packagename, targetname)
    return registry.hasPackage(packagename)


class Node(object):

    def __init__(self, name, children):
        self.name = name
        self.children = [Node(k, v) for k, v in children.iteritems()]

    def __str__(self):
        return self.name


def printTree(registry, buildTargets, **kw):
    targets = buildTargets
    if not targets:
        targets = registry.getPackageNames()

    for fulltargetname in targets:
        packagename, targetname = SConsider.PackageRegistry.PackageRegistry.splitFulltargetname(
            fulltargetname, True)
        if existsTarget(registry, packagename, targetname):
            node = Node(
                SConsider.PackageRegistry.PackageRegistry.createFulltargetname(
                    packagename, targetname), getDependencies(
                    registry, packagename, targetname))
            SCons.Util.print_tree(node, lambda node: node.children)

    print "\nOption 'showtree' active, exiting."
    exit()


def generate(env):
    from SConsider import registerCallback
    """Add the options, builders and wrappers to the current Environment."""
    try:
        AddOption(
            '--showtargets',
            dest='showtargets',
            action='store_true',
            default=False,
            help='Show available targets')
        AddOption(
            '--showtree',
            dest='showtree',
            action='store_true',
            default=False,
            help='Show dependencytree')
        AddOption(
            '--showallaliases',
            dest='showallaliases',
            action='store_true',
            default=False,
            help='Show all defined aliases')
    except optparse.OptionConflictError:
        pass

    if GetOption("showtargets"):
        registerCallback("PreBuild", printTargets)
    if GetOption("showtree"):
        registerCallback("PreBuild", printTree)


def exists(env):
    return 1
