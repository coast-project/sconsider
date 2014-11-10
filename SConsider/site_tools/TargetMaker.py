"""SConsider.site_tools.TargetMaker.

SCons extension to create target environments using EnvBuilder

"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2014, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import SCons
import re
import os
import stat
import SConsider
from SConsider.PackageRegistry import targetnameseparator,\
    splitTargetname, createUniqueTargetname, generateFulltargetname,\
    PackageNotFound, TargetNotFound
from SCons.Script import Dir, File, GetOption
from SomeUtils import copyFileNodes, multiple_replace
from logging import getLogger
logger = getLogger(__name__)


def getRealTarget(target, doThrow=False, messagePrefix='', fullTargetName=''):
    from SCons.Util import is_Tuple, is_List
    from SConsider import getRegistry
    if (is_Tuple(target) and target[0] is None) or (
            is_List(target) and not len(target)):
        if doThrow:
            raise TargetNotFound(
                target[1] if len(target) == 2 else '<unknown target>')
        return None
    target_name = None
    if is_List(target) and is_Tuple(target[0]):
        target = target[0]
    if is_Tuple(target):
        target_name = target[1]
        target = target[0]
        if not SCons.Util.is_String(target_name) and doThrow:
            raise SCons.Errors.UserError(
                "%s '%s' for target '%s' is not a valid string entry" %
                (messagePrefix, target_name, fullTargetName))
    if is_List(target) and len(target) <= 1:
        target = target[0]
    if SCons.Util.is_String(target):
        target = getRegistry().lookup(target)
    if isinstance(target, SCons.Node.Alias.Alias):
        if doThrow:
            raise SCons.Errors.UserError(
                "%s '%s' for target '%s' must be a string entry, not an alias node" %
                (messagePrefix, str(target), fullTargetName))
        logger.error(
            '{0} [{1}] for target [{2}] must be a string entry, not an alias node'.format(
                messagePrefix,
                str(target),
                fullTargetName))
    return target


class TargetMaker:

    def __init__(self, packagename, tlist, registry):
        self.packagename = packagename
        self.targetlist = tlist.copy()
        self.registry = registry

    def createTargets(self):
        while self.targetlist:
            if not self.recurseCreate(self.targetlist.keys()[0]):
                return False
        return True

    def recurseCreate(self, targetname):
        if self.targetlist:
            if targetname:
                k = targetname
                v = self.targetlist.pop(k)
            else:
                k, v = self.targetlist.popitem()
            depList = [
                item
                for item in v.get('requires', []) + v.get(
                    'linkDependencies', []) + [v.get('usedTarget', '')]
                if item.startswith(self.packagename + targetnameseparator)]
            for ftn in depList:
                pkgname, tname = splitTargetname(ftn)
                if self.packagename == pkgname and tname in self.targetlist:
                    self.recurseCreate(tname)
            return self.doCreateTarget(self.packagename, k, v)
        return False

    def prepareFileNodeTuples(self, nodes, baseDir, alternativeDir=None):
        nodetuples = []
        for node in nodes:
            currentFile = node
            if isinstance(currentFile, str):
                currentFile = File(currentFile)
            if hasattr(currentFile, 'srcnode'):
                currentFile = currentFile.srcnode()

            currentBaseDir = baseDir
            if hasattr(currentBaseDir, 'srcnode'):
                currentBaseDir = currentBaseDir.srcnode()

            if alternativeDir:
                # based on installRelPath and file, try to find an override
                # file to use instead
                fileWithRelpathToSearch = os.path.relpath(
                    currentFile.get_abspath(),
                    currentBaseDir.get_abspath())
                # catch possible errors and stop when wanting to do relative
                # movements
                if not fileWithRelpathToSearch.startswith('..'):
                    fileToCheckFor = os.path.join(
                        alternativeDir.get_abspath(),
                        fileWithRelpathToSearch)
                    if os.path.isfile(fileToCheckFor):
                        currentFile = File(fileToCheckFor)
                        currentBaseDir = alternativeDir

            nodetuples.append((currentFile, currentBaseDir))
        return nodetuples

    def copyIncludeFiles(self, env, pkgname, buildSettings):
        instTargets = []
        if 'public' in buildSettings:
            ifiles = buildSettings['public'].get('includes', [])
            destdir = env.getBaseOutDir().Dir(
                os.path.join(
                    env['INCDIR'],
                    pkgname))
            pkgdir = self.registry.getPackageDir(pkgname)
            stripRelDirs = []
            if buildSettings['public'].get('stripSubdir', True):
                stripRelDirs.append(
                    buildSettings['public'].get(
                        'includeSubdir',
                        ''))
            mode = None
            if str(env['PLATFORM']) not in ["cygwin", "win32"]:
                mode = stat.S_IREAD
                mode |= stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
            instTargets = copyFileNodes(
                env,
                self.prepareFileNodeTuples(
                    ifiles,
                    pkgdir),
                destdir,
                stripRelDirs=stripRelDirs,
                mode=mode)
        return instTargets

    def copyFiles(self, env, destdir, pkgname, copyFiles):
        instTargets = []

        pkgdir = self.registry.getPackageDir(pkgname)

        envconfigdir = env.get('__envconfigdir__', None)
        if envconfigdir:
            envconfigdir = envconfigdir.Dir(pkgname)

        for filetuple in copyFiles:
            if len(filetuple) == 3:
                files, mode, replaceDict = filetuple
            else:
                files, mode = filetuple
                replaceDict = {}
            if str(env['PLATFORM']) in ["cygwin", "win32"]:
                mode = None
            instTargets.extend(
                copyFileNodes(
                    env,
                    self.prepareFileNodeTuples(
                        files,
                        pkgdir,
                        envconfigdir),
                    destdir,
                    mode=mode,
                    replaceDict=replaceDict))

        return instTargets

    def requireTargets(self, env, target, requiredTargets, **kw):
        if not SCons.Util.is_List(requiredTargets):
            requiredTargets = [requiredTargets]
        for targ in requiredTargets:
            env.Depends(
                target,
                self.registry.loadPackageTarget(
                    *splitTargetname(
                        targ,
                        default=True)))

    def doCreateTarget(self, packagename, targetname, targetBuildSettings):
        plaintarget = None
        target = None
        try:
            envVars = targetBuildSettings.get('appendUnique', {})
            targetEnv = self.createTargetEnv(
                targetname,
                targetBuildSettings,
                envVars)
            func = getattr(
                targetEnv,
                targetBuildSettings.get(
                    'targetType',
                    '__UNDEFINED_TARGETTYPE__'),
                None)
            if func:
                kw = {}
                kw['packagename'] = packagename
                kw['targetname'] = targetname
                kw['buildSettings'] = targetBuildSettings
                sources = targetBuildSettings.get('sourceFiles', [])
                name = targetBuildSettings.get(
                    'targetName',
                    createUniqueTargetname(
                        packagename,
                        targetname))
                targets = func(*[name, sources], **kw)
                if isinstance(targets, tuple):
                    plaintarget, target = targets
                else:
                    plaintarget = target = targets

            if plaintarget:
                targetEnv.Depends(
                    plaintarget,
                    self.registry.getPackageFile(packagename))
            else:
                # Actually includeOnlyTarget is obsolete, but we still need a
                # (dummy) targetType in build settings to get in here!
                # The following is a workaround, otherwise an alias won't get
                # built in newer SCons versions (because it has depends but no
                # sources)
                plaintarget = target = targetEnv.Alias(
                    packagename +
                    targetnameseparator +
                    targetname,
                    self.registry.getPackageFile(packagename))

            reqTargets = targetBuildSettings.get('linkDependencies', [])
            reqTargets.extend(targetBuildSettings.get('requires', []))
            self.requireTargets(targetEnv, target, reqTargets)

            includeTargets = self.copyIncludeFiles(
                targetEnv,
                packagename,
                targetBuildSettings)
            targetEnv.Depends(target, includeTargets)
            targetEnv.Alias('includes', includeTargets)

            if 'copyFiles' in targetBuildSettings:
                copyTargets = self.copyFiles(
                    targetEnv,
                    targetEnv.getTargetBaseInstallDir(),
                    packagename,
                    targetBuildSettings.get('copyFiles', []))
                targetEnv.Depends(target, copyTargets)

            targetEnv.Alias(packagename, target)
            targetEnv.Alias('all', target)
            if targetBuildSettings.get(
                    'runConfig',
                    {}).get(
                    'type',
                    '') == 'test':
                targetEnv.Alias('tests', target)

            SConsider.runCallback(
                "PostCreateTarget",
                env=targetEnv,
                target=target,
                plaintarget=plaintarget,
                registry=self.registry,
                packagename=packagename,
                targetname=targetname,
                buildSettings=targetBuildSettings)

            self.registry.setPackageTarget(
                packagename,
                targetname,
                plaintarget,
                target)
            return True
        except (PackageNotFound, TargetNotFound) as e:
            if not GetOption('ignore-missing'):
                raise
            logger.warning(
                '{0} (referenced by [{1}]), ignoring as requested'.format(
                    e,
                    generateFulltargetname(
                        packagename,
                        targetname)
                ),
                exc_info=False)
            return False

    def createTargetEnv(self, targetname, targetBuildSettings, envVars={}):
        # create environment for target
        targetEnv = SConsider.cloneBaseEnv()

        # maybe we need to add this library's local include path when building
        # it (if different from .)
        includeSubdir = Dir(
            targetBuildSettings.get(
                'includeSubdir',
                '')).srcnode()
        includePublicSubdir = Dir(
            targetBuildSettings.get(
                'public',
                {}).get(
                'includeSubdir',
                '')).srcnode()
        include_dirs = includeSubdir.get_all_rdirs()
        include_dirs.extend(includePublicSubdir.get_all_rdirs())
        for incdir in include_dirs:
            targetEnv.AppendUnique(CPPPATH=[incdir])

        # update environment by adding dependencies to used modules
        linkDependencies = targetBuildSettings.get('linkDependencies', [])
        self.setModuleDependencies(targetEnv, linkDependencies)

        self.setExecEnv(
            targetEnv,
            linkDependencies +
            targetBuildSettings.get(
                'requires',
                []))

        targetVars = targetBuildSettings.get(
            'public',
            {}).get(
            'appendUnique',
            {})
        targetEnv.AppendUnique(**targetVars)
        targetEnv.AppendUnique(**envVars)
        return targetEnv

    def setModuleDependencies(self, env, modules, **kw):
        for fulltargetname in modules:
            packagename, targetname = splitTargetname(
                fulltargetname, default=True)
            plaintarget = self.registry.loadPackagePlaintarget(
                packagename,
                targetname)
            buildSettings = self.registry.getBuildSettings(
                packagename,
                targetname)
            self.setExternalDependencies(
                env,
                packagename,
                buildSettings,
                plaintarget=plaintarget,
                **kw)

    def setExecEnv(self, env, requiredTargets):
        for targ in requiredTargets:
            packagename, targetname = splitTargetname(targ, default=True)
            if self.registry.hasPackageTarget(packagename, targetname):
                settings = self.registry.getBuildSettings(
                    packagename,
                    targetname)
                target = self.registry.getPackagePlaintarget(
                    packagename,
                    targetname)
                public_execenv = settings.get('public', {}).get('execEnv', {})
                for key, value in public_execenv.iteritems():
                    env['ENV'][key] = target.env.subst(value)
                reqTargets = settings.get(
                    'linkDependencies', []) + settings.get('requires', [])
                self.setExecEnv(env, reqTargets)

    def setExternalDependencies(
            self,
            env,
            packagename,
            buildSettings,
            plaintarget=None,
            **kw):
        linkDependencies = buildSettings.get('linkDependencies', [])
        if 'public' in buildSettings:
            appendUnique = buildSettings['public'].get('appendUnique', {})
            # flags / settings used by this library and users of it
            env.AppendUnique(**appendUnique)

            includePublicSubdir = buildSettings[
                'public'].get('includeSubdir', '')
            if SCons.Util.is_String(includePublicSubdir):
                includePublicSubdir = self.registry.getPackageDir(
                    packagename).Dir(includePublicSubdir)

            for incdir in includePublicSubdir.get_all_rdirs():
                env.AppendUnique(CPPPATH=[incdir])

        # this libraries dependencies
        self.setModuleDependencies(env, linkDependencies)

        if plaintarget:
            # try block needed to block Alias only targets without concrete
            # builder
            try:
                strTargetType = plaintarget.builder.get_name(plaintarget.env)
                if strTargetType.find('Library') != -1:
                    libname = multiple_replace([
                        ('^' + re.escape(env.subst("$LIBPREFIX")), ''),
                        (re.escape(env.subst("$LIBSUFFIX")) + '$', ''),
                        ('^' + re.escape(env.subst("$SHLIBPREFIX")), ''),
                        (re.escape(env.subst("$SHLIBSUFFIX")) + '$', ''),
                    ], plaintarget.name)
                    env.AppendUnique(LIBS=[libname])
            except:
                pass


def generate(env):
    from SCons.Script import AddOption
    AddOption(
        '--ignore-missing',
        dest='ignore-missing',
        action='store_true',
        help='Ignore missing dependencies instead of failing the whole build.')


def exists(env):
    return 1
