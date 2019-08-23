"""SConsider.site_tools.Package.

SConsider-specific tool to create a distributable package from compiled
sources
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

import re
import os
import threading
from logging import getLogger
from SConsider.SomeUtils import hasPathPart, isDerivedNode, multiple_replace, isFileNode, allFuncs, getNodeDependencies
logger = getLogger(__name__)

# needs locking because it is manipulated during multi-threaded build phase
packageTargets = {}
packageTargetsRLock = threading.RLock()

packageAliasName = 'makepackage'


def addPackageTarget(registry, buildTargets, env, destdir, **kw):
    from SCons.Action import ActionFactory
    createDeferredAction = ActionFactory(makePackage, lambda *args, **kw: '')

    sources = []
    for tn in buildTargets:
        if registry.isValidFulltargetname(tn):
            sources.extend(env.Alias(tn))

    # bind parameters to an Action which is called in the build phase
    # '$__env__' is used to supply the caller's environment to the action (see SCons -> Action.py -> ActionCaller)
    action = createDeferredAction(registry, buildTargets, '$__env__', destdir)
    # create a dummy target which always will be built
    maker = env.Command('Package_dummy', sources, action)
    # create intermediate alias target to which we add dependencies in the
    # build phase
    env.Alias(packageAliasName, maker)
    buildTargets.append(packageAliasName)


def makePackage(registry, buildTargets, env, destdir, **kw):
    def isNotInBuilddir(node):
        return not hasPathPart(node, pathpart=env.getRelativeBuildDirectory())

    includePathRel = env['INCDIR']
    includePathFull = includePathRel
    if not includePathFull.startswith(os.path.sep):
        includePathFull = os.path.join(env.getBaseOutDir().get_abspath(), includePathRel)

    def isIncludeFile(target):
        if os.path.splitext(target.path)[1].lower() in ['.h', '.hpp', '.hxx', '.ipp']:
            return target.path.startswith(includePathRel) or target.path.startswith(includePathFull)
        return False

    def isNotIncludeFile(target):
        return not isIncludeFile(target)

    copyfilters = [filterBaseOutDir, filterTestsAppsGlobalsPath, filterVariantPath]
    for tn in buildTargets:
        if registry.isValidFulltargetname(tn):
            tdeps = getTargetDependencies(
                env.Alias(tn)[0], [isDerivedNode, isNotInBuilddir, isNotIncludeFile])
            copyPackage(tn, tdeps, env, destdir, copyfilters)


def copyPackage(name, deps, env, destdir, filters=None):
    for target in deps:
        copyTarget(env, determineDirInPackage(name, env, destdir, target, filters), target)


def install_or_link_node(env, destdir, node):
    def install_node_to_destdir(targets_list, node, destdir):
        from stat import S_IRUSR, S_IRGRP, S_IROTH, S_IXUSR
        from SCons.Defaults import Chmod
        # ensure executable flag on installed shared libs
        mode = S_IRUSR | S_IRGRP | S_IROTH | S_IXUSR
        node_name = node.name
        if node_name in targets_list:
            return targets_list[node_name]
        install_path = env.makeInstallablePathFromDir(destdir)
        target = env.Install(dir=install_path, source=node)
        env.AddPostAction(target, Chmod(str(target[0]), mode))
        targets_list[node_name] = target
        return target

    # build phase could be multi-threaded
    with packageTargetsRLock:
        # take care of already created targets otherwise we would have
        # multiple ways to build the same target
        global packageTargets
        node_name = node.name
        if node_name in packageTargets:
            target = packageTargets[node_name]
        else:
            install_node = node
            is_link = node.islink()
            if is_link:
                install_node = node.sources[0]
            target = install_node_to_destdir(packageTargets, install_node, destdir)
            if is_link:
                target = env.Symlink(target[0].get_dir().File(node_name), target)

                packageTargets[node_name] = target

    return target


def copyTarget(env, destdir, node):
    old = env.Alias(destdir.File(node.name))
    if old and old[0].sources:
        if isInstalledNode(node, old[0].sources[0]) or isInstalledNode(old[0].sources[0], node):
            return None
    target = install_or_link_node(env, destdir, node)
    env.Alias(packageAliasName, target)
    return target


def isInstalledNode(testnode, node):
    if testnode.path == node.path:
        return True
    if not hasattr(node, 'builder') or not hasattr(node.builder,
                                                   'name') or node.builder.name != 'InstallBuilder':
        return False
    if len(node.sources) < 1:
        return False
    return isInstalledNode(testnode, node.sources[0])


def filterBaseOutDir(path, **kw):
    env = kw.get('env', {})
    if not path.startswith(os.sep):
        return path
    basedirprefix = env.getBaseOutDir().get_abspath()
    if not basedirprefix:
        return path
    replist = [('^' + basedirprefix + os.sep + '?', '')]
    return multiple_replace(replist, path)


def filterTestsAppsGlobalsPath(path, **kw):
    replist = [('^tests' + os.sep + '[^' + os.sep + ']*' + os.sep + '?', ''),
               ('^apps' + os.sep + '[^' + os.sep + ']*' + os.sep + '?', ''),
               ('^globals' + os.sep + '[^' + os.sep + ']*' + os.sep + '?', '')]
    for r in replist:
        res = multiple_replace([r], path)
        # leave as soon as we replaced a prefix, as only one can match per call
        if res != path:
            return res

    return path


def filterVariantPath(path, **kw):
    env = kw.get('env', {})
    variant = env.getRelativeVariantDirectory()
    if not variant:
        return path
    return re.sub(re.escape(variant) + os.sep + '?', '', path)


def determineDirInPackage(name, env, destdir, target, filters=None):
    path = target.get_dir().path
    if filters is not None:
        if not isinstance(filters, list):
            filters = [filters]
        for current_filter in filters:
            if path and callable(current_filter):
                path = current_filter(path, env=env)

    copydir = destdir.Dir(name)
    return copydir.Dir(path)


class PackageToolException(Exception):
    pass


def generate(env):
    from SCons.Script import GetOption, Dir, AddOption
    from SCons.Script.Main import OptionsParser
    AddOption('--package',
              dest='package',
              action='store',
              default='',
              help='Destination base directory for target specific files. Target\
    files will be put into a subdirectory named <packagename>. If a specific\
    package target is specified, the subdirectory will be named <packagename>.\
    <targetname>.')

    destination = GetOption('package')
    if destination:
        from SConsider.Callback import Callback
        if not os.path.isdir(destination):
            OptionsParser.error("given package destination path [{0}] doesn't exist".format(destination))
        else:
            Callback().register("PreBuild", addPackageTarget, env=env, destdir=Dir(destination))


def exists(env):
    return 1


def getTargetDependencies(target, filters=None):
    """Determines the recursive dependencies of a target (including itself).

    Specify additional target filters using 'filters'.
    """
    if filters is None:
        filters = []
    if not isinstance(filters, list):
        filters = [filters]
    filters = [isFileNode] + filters

    deps = set()
    if allFuncs(filters, target):
        executor = target.get_executor()
        if executor is not None:
            deps.update(executor.get_all_targets())
    deps.update(getNodeDependencies(target, filters))

    return deps
