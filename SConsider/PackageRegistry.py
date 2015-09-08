"""SConsider.PackageRegistry.

SCons extension to manage targets by name in a global registry

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

import re
import sys
import os
from pkg_resources import ResolutionError
from logging import getLogger
logger = getLogger(__name__)


class TargetNotFound(Exception):

    def __init__(self, name):
        self.name = name
        self.lookupStack = []

    def prependItem(self, lookupItem):
        self.lookupStack[0:0] = [lookupItem]

    def __str__(self):
        message = 'Target [{0}] not found'.format(self.name)
        if len(self.lookupStack):
            message += ', required by [{0}]'.format('>'.join(self.lookupStack))
        return message


class PackageNotFound(TargetNotFound):

    def __str__(self):
        return 'Package [{0}] not found'.format(self.name)


class PackageRequirementsNotFulfilled(Exception):

    def __init__(self, package, packagefile, message):
        self.package = package
        self.packagefile = packagefile
        self.message = message

    def __str__(self):
        return 'Package [{0}] not available (file {1}) '\
               'because of unsatisfied requirements: [{2}]'.format(
                   self.package,
                   self.packagefile,
                   self.message)


class PackageRegistry:
    targetnameseparator = '.'

    @staticmethod
    def splitFulltargetname(fulltargetname, default=False):
        """Split fulltargetname into packagename and targetname."""
        parts = fulltargetname.split(PackageRegistry.targetnameseparator)
        pkgname = parts[0]
        targetname = None
        if len(parts) > 1:
            targetname = parts[1]
        elif default:
            targetname = pkgname
        return (pkgname, targetname)

    @staticmethod
    def splitTargetname(fulltargetname, default=False):
        return PackageRegistry.splitFulltargetname(fulltargetname, default)

    @staticmethod
    def createFulltargetname(packagename, targetname=None, default=False):
        """Generate fulltargetname using packagename and targetname."""
        if not targetname:
            if default:
                return packagename + PackageRegistry.targetnameseparator + packagename
            else:
                return packagename
        else:
            return packagename + PackageRegistry.targetnameseparator + targetname

    @staticmethod
    def generateFulltargetname(packagename, targetname=None, default=False):
        return PackageRegistry.createFulltargetname(
            packagename, targetname, default)

    @staticmethod
    def createUniqueTargetname(packagename, targetname):
        return packagename + targetname if packagename != targetname else targetname

    @staticmethod
    def collectPackageFiles(
            directory,
            filename_re,
            matchfun,
            file_ext='sconsider',
            excludes_rel=[],
            excludes_abs=[]):
        """Recursively collects SConsider packages.

        Walks recursively through 'directory' to collect package files
        but skipping dirs in 'excludes_rel' and absolute dirs
        from 'exclude_abs'.

        """
        import fnmatch
        package_re = re.compile(filename_re)
        followlinks = False
        if sys.version_info[:2] >= (2, 6):
            followlinks = True
        for root, dirnames, filenames in os.walk(directory,
                                                 followlinks=followlinks):
            _root_pathabs = os.path.abspath(root)
            dirnames[:] = filter(
                lambda dirname: dirname not in excludes_rel and os.path.join(
                    _root_pathabs,
                    dirname) not in excludes_abs,
                dirnames)
            for filename in fnmatch.filter(filenames, '*.' + file_ext):
                match = package_re.match(filename)
                if match:
                    matchfun(root, filename, match)

    def __init__(
            self,
            env,
            scan_dirs,
            scan_dirs_exclude_rel=[],
            scan_dirs_exclude_abs=[]):
        import SCons
        self.env = env
        self.packages = {}
        self.lookupStack = []
        if not SCons.Util.is_List(scan_dirs):
            scan_dirs = [scan_dirs]
        startDir = SCons.Script.Dir('#')

        def scanmatchfun(root, filename, match):
            rootDir = self.env.Dir(root)
            _filename = rootDir.File(filename)
            logger.debug(
                'found package [{0}] in [{1}]'.format(
                    match.group('packagename'),
                    startDir.rel_path(_filename)))
            self.setPackage(match.group('packagename'), _filename, rootDir)

        for scandir in scan_dirs:
            self.collectPackageFiles(
                scandir,
                '^(?P<packagename>.*)\.sconsider$',
                scanmatchfun,
                excludes_rel=scan_dirs_exclude_rel,
                excludes_abs=scan_dirs_exclude_abs)

    def setPackage(
            self,
            packagename,
            packagefile,
            packagedir,
            duplicate=False):
        self.packages[packagename] = {
            'packagefile': packagefile,
            'packagedir': packagedir,
            'duplicate': duplicate}

    def hasPackage(self, packagename):
        """Check if packagename is found in list of packages.

        This solely relies on directories and <packagename>.sconscript
        files found

        """
        return packagename in self.packages

    def setPackageDir(self, packagename, dirname):
        if self.hasPackage(packagename):
            self.packages[packagename]['packagedir'] = dirname

    def getPackageDir(self, packagename):
        return self.packages.get(packagename, {}).get('packagedir', '')

    def getPackageFile(self, packagename):
        return self.packages.get(packagename, {}).get('packagefile', '')

    def getPackageDuplicate(self, packagename):
        return self.packages.get(packagename, {}).get('duplicate', False)

    def setPackageDuplicate(self, packagename, duplicate=True):
        if self.hasPackage(packagename):
            self.packages[packagename]['duplicate'] = duplicate

    def getPackageNames(self):
        return self.packages.keys()

    def setPackageTarget(self, packagename, targetname, plaintarget, target):
        import SCons
        if not self.hasPackage(packagename):
            logger.warning(
                'tried to register target [%s] for non existent package [%s]',
                targetname,
                packagename)
            return
        theTargets = self.packages[packagename].setdefault('targets', {})
        if plaintarget and SCons.Util.is_List(plaintarget):
            plaintarget = plaintarget[0]
        if target and SCons.Util.is_List(target):
            target = target[0]
        if not target:
            target = plaintarget
        theTargets[targetname] = {'plaintarget': plaintarget, 'target': target}

    def getPackageTarget(self, packagename, targetname):
        return self.getPackageTargetTargets(
            packagename,
            targetname).get(
                'target',
                None)

    def hasPackageTarget(self, packagename, targetname):
        return targetname in self.packages.get(
            packagename,
            {}).get(
            'targets',
            {})

    def getPackageTargetTargets(self, packagename, targetname):
        if not self.hasPackage(packagename):
            logger.warning(
                'tried to access target [%s] of non existent package [%s]',
                targetname,
                packagename)
        return self.packages.get(
            packagename, {}).get(
                'targets', {}).get(
                    targetname, {
                        'plaintarget': None, 'target': None})

    def getPackagePlaintarget(self, packagename, targetname):
        return self.getPackageTargetTargets(
            packagename,
            targetname).get(
                'plaintarget',
                None)

    def getPackageTargetNames(self, packagename):
        return self.packages.get(packagename, {}).get('targets', {}).keys()

    def isValidFulltargetname(self, fulltargetname):
        if self.hasPackage(str(fulltargetname)):
            return True
        packagename, targetname = self.splitTargetname(str(fulltargetname))
        return self.hasPackageTarget(packagename, targetname)

    def getPackageTargetDependencies(
            self,
            packagename,
            targetname,
            callerdeps=None):
        targetBuildSettings = self.getBuildSettings(
            packagename).get(targetname, {})
        if callerdeps is None:
            callerdeps = dict()
        callerdeps.setdefault('pending', [])
        deps = dict()
        targetlist = targetBuildSettings.get('requires', [])
        targetlist.extend(targetBuildSettings.get('linkDependencies', []))
        targetlist.extend([targetBuildSettings.get('usedTarget', '')])
        for dep_fulltargetname in targetlist:
            if dep_fulltargetname:
                dep_packagename, dep_targetname = self.splitTargetname(
                    dep_fulltargetname)
                if not dep_targetname:
                    dep_targetname = dep_packagename
                deps[
                    self.generateFulltargetname(
                        dep_packagename,
                        dep_targetname)] = self.getPackageTargetDependencies(
                            dep_packagename,
                            dep_targetname)
        return deps

    def setBuildSettings(self, packagename, buildSettings):
        if self.hasPackage(packagename):
            self.packages[packagename]['buildsettings'] = buildSettings

    def hasBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return 'buildsettings' in self.packages.get(packagename, {})
        else:
            return targetname in self.packages.get(
                packagename,
                {}).get(
                'buildsettings',
                {})

    def getBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return self.packages.get(packagename, {}).get('buildsettings', {})
        else:
            return self.packages.get(
                packagename, {}).get(
                'buildsettings', {}).get(
                targetname, {})

    def __loadPackageTarget(self, loadfunc, packagename, targetname):
        self.loadPackage(packagename)
        target = loadfunc(packagename, targetname)
        if targetname and not target:
            raise TargetNotFound(
                self.generateFulltargetname(
                    packagename,
                    targetname))
        return target

    def loadPackageTarget(self, packagename, targetname):
        return self.__loadPackageTarget(
            self.getPackageTarget,
            packagename,
            targetname)

    def loadPackagePlaintarget(self, packagename, targetname):
        return self.__loadPackageTarget(
            self.getPackagePlaintarget,
            packagename,
            targetname)

    def getPackageDependencies(self, packagename, callerdeps=None):
        if callerdeps is None:
            callerdeps = dict()
        deps = dict()
        for targetname in self.getPackageTargetNames(packagename):
            deps[
                self.generateFulltargetname(
                    packagename,
                    targetname)] = self.getPackageTargetDependencies(
                        packagename,
                        targetname,
                        callerdeps=callerdeps)
        return deps

    def isPackageLoaded(self, packagename):
        return 'loaded' in self.packages.get(packagename, {})

    def __setPackageLoaded(self, packagename):
        self.packages[packagename]['loaded'] = True

    def lookup(self, fulltargetname, **kw):
        packagename, targetname = self.splitFulltargetname(fulltargetname)
        logger.debug('looking up [%s]', fulltargetname)
        if self.hasPackage(packagename):
            if not self.isPackageLoaded(packagename):
                self.__setPackageLoaded(packagename)
                packagedir = self.getPackageDir(packagename)
                packagefile = self.getPackageFile(packagename)
                packageduplicate = self.getPackageDuplicate(packagename)
                builddir = self.env.getBaseOutDir().Dir(
                    packagedir.path).Dir(
                    self.env.getRelativeBuildDirectory()).Dir(
                    self.env.getRelativeVariantDirectory())
                message = 'executing [{0}] as SConscript for package [{1}]'.format(
                    packagefile.path, packagename)
                if self.lookupStack:
                    message += ' required by [{0}]'.format(
                        '>'.join(self.lookupStack))
                logger.info(message)
                exports = {
                    'packagename': packagename,
                    'registry': self
                }
                self.lookupStack.append(fulltargetname)
                try:
                    self.env.SConscript(
                        packagefile,
                        variant_dir=builddir,
                        duplicate=packageduplicate,
                        exports=exports)
                except ResolutionError as e:
                    raise PackageRequirementsNotFulfilled(
                        self.generateFulltargetname(
                            packagename,
                            targetname),
                        packagefile,
                        e)
                except TargetNotFound as e:
                    e.prependItem(fulltargetname)
                    raise e
                finally:
                    if len(self.lookupStack):
                        del self.lookupStack[len(self.lookupStack) - 1]
            if targetname:
                return self.getPackageTarget(packagename, targetname)
        return None

    @staticmethod
    def loadNode(env, name):
        return env.arg2nodes(name, node_factory=None)

    def loadPackage(self, packagename):
        if not self.hasPackage(packagename):
            raise PackageNotFound(packagename)
        return self.lookup(packagename)

    def getRealTarget(self, target, doThrow=False, messagePrefix='', fullTargetName=''):
        from SCons.Util import is_Tuple, is_List, is_String
        from SCons.Errors import UserError
        from SCons.Node.Alias import Alias
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
            if not is_String(target_name) and doThrow:
                raise UserError(
                    "%s '%s' for target '%s' is not a valid string entry" %
                    (messagePrefix, target_name, fullTargetName))
        if is_List(target) and len(target) <= 1:
            target = target[0]
        if is_String(target):
            target = self.lookup(target)
        if isinstance(target, Alias):
            if doThrow:
                raise UserError(
                    "%s '%s' for target '%s' must be a string entry, not an alias node" %
                    (messagePrefix, str(target), fullTargetName))
            logger.error(
                '{0} [{1}] for target [{2}] must be a string entry, not an alias node'.format(
                    messagePrefix, str(target), fullTargetName))
        return target
