"""SConsider.site_tools.Package.

SConsider-specific tool to create a distributable package  from compiled sources

"""

# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import re
import os
import optparse
import functools
import SomeUtils
from logging import getLogger
logger = getLogger(__name__)

packageAliasName = 'makepackage'


def addPackageTarget(registry, buildTargets, env, destdir, **kw):
    import SCons
    createDeferredAction = SCons.Action.ActionFactory(
        makePackage,
        lambda *
        args,
        **kw: '')

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
    import SCons
    isInBuilddir = functools.partial(
        SomeUtils.hasPathPart,
        pathpart=env['BUILDDIR'])
    notInBuilddir = lambda target: not isInBuilddir(target)
    includePathRel = env['INCDIR']
    includePathFull = includePathRel
    if not includePathFull.startswith(os.path.sep):
        includePathFull = os.path.join(env.get('BASEOUTDIR', SCons.Script.Dir('.')).abspath, includePathRel)
    def isIncludeFile(target):
        if os.path.splitext(target.path)[1].lower() in ['.h', '.hpp', '.hxx', '.ipp']:
            return target.path.startswith(includePathRel) or target.path.startswith(includePathFull)
        return False
    isNotIncludeFile = lambda target: not isIncludeFile(target)
    copyfilters = [
        filterBaseOutDir,
        filterTestsAppsGlobalsPath,
        filterVariantPath]
    for tn in buildTargets:
        if registry.isValidFulltargetname(tn):
            tdeps = getTargetDependencies(
                env.Alias(tn)[0], [
                    SomeUtils.isDerivedNode, notInBuilddir, isNotIncludeFile])
            copyPackage(tn, tdeps, env, destdir, copyfilters)


def copyPackage(name, deps, env, destdir, filters=[]):
    for target in deps:
        copyTarget(
            env,
            determineDirInPackage(
                name,
                env,
                destdir,
                target,
                filters),
            target)


def copyTarget(env, destdir, node):
    old = env.Alias(destdir.File(node.name))
    if old and old[0].sources:
        if isInstalledNode(
                node,
                old[0].sources[0]) or isInstalledNode(
                old[0].sources[0],
                node):
            return None
        else:
            logger.error(
                "Ambiguous target [%s] copied from [%s] and [%s].\nCan't create package! See errors below...",
                old[0].path,
                node.path,
                old[0].sources[0].path)
    target = env.Install(destdir, node)
    env.Alias(packageAliasName, target)
    return target


def isInstalledNode(testnode, node):
    if testnode.path == node.path:
        return True
    if not hasattr(
            node,
            'builder') or not hasattr(
            node.builder,
            'name') or node.builder.name != 'InstallBuilder':
        return False
    if len(node.sources) < 1:
        return False
    return isInstalledNode(testnode, node.sources[0])


def filterBaseOutDir(path, **kw):
    #FIXME: baseoutdir is always an absolute path except maybe windows?
    if not path.startswith(os.sep):
        return path
    basedirprefix = kw.get('env', {}).get('BASEOUTDIR', False).abspath
    replist = [('^' + basedirprefix + os.sep + '?', ''),
               ]
    return SomeUtils.multiple_replace(replist, path)


def filterTestsAppsGlobalsPath(path, **kw):
    replist = [('^tests' + os.sep + '[^' + os.sep + ']*' + os.sep + '?', ''),
               ('^apps' + os.sep + '[^' + os.sep + ']*' + os.sep + '?', ''),
               ('^globals' + os.sep + '[^' + os.sep + ']*' + os.sep + '?', '')]
    return SomeUtils.multiple_replace(replist, path)


def filterVariantPath(path, **kw):
    variant = kw.get('env', {}).get('VARIANTDIR', False)
    if not variant:
        return path

    return re.sub(re.escape(variant) + os.sep + '?', '', path)


def determineDirInPackage(name, env, destdir, target, filters=[]):
    path = target.get_dir().path

    if not isinstance(filters, list):
        filters = [filters]
    for filter in filters:
        if path and callable(filter):
            path = filter(path, env=env)

    copydir = destdir.Dir(name)
    return copydir.Dir(path)


class PackageToolException(Exception):
    pass


def generate(env):
    import SCons.Script
    import SCons.Script.Main
    import SConsider
    try:
        SCons.Script.AddOption(
            '--package',
            dest='package',
            action='store',
            default='',
            help='Destination base directory for target specific files. Target\
 files will be put into a subdirectory named <packagename>. If a specific\
 package target is specified, the subdirectory will be named <packagename>.\
 <targetname>.')
    except optparse.OptionConflictError:
        raise PackageToolException("Only one Package-Tool instance allowed")

    destination = SCons.Script.GetOption('package')
    if destination:
        if not os.path.isdir(destination):
            SCons.Script.Main.OptionsParser.error(
                "given package destination path doesn't exist")
        else:
            SConsider.registerCallback(
                "PreBuild",
                addPackageTarget,
                env=env,
                destdir=SCons.Script.Dir(destination))


def exists(env):
    return 1


def getTargetDependencies(target, filters=[]):
    """Determines the recursive dependencies of a target (including itself).

    Specify additional target filters using 'filters'.

    """
    if not isinstance(filters, list):
        filters = [filters]
    filters = [SomeUtils.isFileNode] + filters

    deps = set()
    if SomeUtils.allFuncs(filters, target):
        deps.update(target.get_executor().get_all_targets())
    deps.update(SomeUtils.getNodeDependencies(target, filters))

    return deps
