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
import sys
import optparse
import functools
from SCons.Util import print_tree
from SCons.Node.Alias import Alias
from SCons.Script import AddOption, GetOption
from SConsider.Callback import Callback
from SConsider.PackageRegistry import PackageRegistry, getTargetExtension
from SConsider.SomeUtils import allFuncs
from SConsider import cloneBaseEnv


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
    env = cloneBaseEnv()

    def isPackage(alias):
        pkg, _ = PackageRegistry.splitFulltargetname(alias)
        return registry.hasPackage(pkg)

    filters = [lambda alias: not isPackage(alias)]
    if not GetOption("showallaliases"):
        filters.append(lambda alias: not alias.startswith('_'))

    predicate = functools.partial(allFuncs, filters)

    for alias in sorted([j for j in env.ans.keys() if predicate(j)]):
        print(alias)

    print "\nOption 'showtargets' active, exiting."
    exit()


def getDependencies(registry, callerdeps, packagename, targetname=None):
    if targetname:
        return registry.getPackageTargetDependencies(packagename, targetname, callerdeps)
    return registry.getPackageDependencies(packagename, callerdeps)


def getAliasDependencies(registry, deps, aliasname):
    alias_node = registry.loadNode(registry.env, aliasname)
    new_deps = dict()
    if isinstance(alias_node, list) and len(alias_node) == 1:
        for depnode in alias_node[0].sources:
            ext = getTargetExtension(depnode)
            if ext is not None:
                new_deps[ext.getFulltargetname()] = getDependencies(registry, deps, ext.packagename,
                                                                    ext.targetname)
    return new_deps


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
    deps = dict()
    prune = 0
    if GetOption("showtree") == 'prune':
        prune = 1
    print "\nTarget Tree"
    print "-----------"
    for fulltargetname in targets:
        if isinstance(fulltargetname, Alias):
            packagename, targetname = (fulltargetname.name, None)
        else:
            packagename, targetname = PackageRegistry.splitFulltargetname(fulltargetname, True)
        if existsTarget(registry, packagename, targetname):
            node = Node(PackageRegistry.createFulltargetname(packagename, targetname),
                        getDependencies(registry, deps, packagename, targetname))
            print_tree(node, lambda node: node.children, prune=prune, visited={})
            sys.stdout.write('\n')
        else:
            # maybe we have an alias name given
            node = Node(fulltargetname, getAliasDependencies(registry, deps, fulltargetname))
            print_tree(node, lambda node: node.children, prune=prune, visited={})
            sys.stdout.write('\n')

    print "\nOption 'showtree' active, exiting."
    exit()


def generate(env):
    """Add the options, builders and wrappers to the current Environment."""
    try:
        AddOption('--showtargets',
                  dest='showtargets',
                  action='store_true',
                  default=False,
                  help='Show available targets')
        tree_choices = ['all', 'prune']
        AddOption('--showtree',
                  dest='showtree',
                  nargs='?',
                  action='store',
                  type='choice',
                  const='all',
                  default=None,
                  choices=tree_choices,
                  metavar='OPTIONS',
                  help='Show target dependency tree in the format ' + str(tree_choices) + ', default=' +
                  tree_choices[0])
        AddOption('--showallaliases',
                  dest='showallaliases',
                  action='store_true',
                  default=False,
                  help='Show all defined aliases')
    except optparse.OptionConflictError:
        pass

    if GetOption("showtargets"):
        Callback().register("PreBuild", printTargets)
    if GetOption("showtree") is not None:
        Callback().register("PreBuild", printTree)


def exists(env):
    return 1
