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


targetnameseparator = '.'


def splitTargetname(fulltargetname, default=False):
    """Split fulltargetname into packagename and targetname."""
    parts = fulltargetname.split(targetnameseparator)
    pkgname = parts[0]
    targetname = None
    if len(parts) > 1:
        targetname = parts[1]
    elif default:
        targetname = pkgname
    return (pkgname, targetname)


def generateFulltargetname(packagename, targetname=None, default=False):
    """Generate fulltargetname using packagename and targetname."""
    if not targetname:
        if default:
            return packagename + targetnameseparator + packagename
        else:
            return packagename
    else:
        return packagename + targetnameseparator + targetname


def createUniqueTargetname(packagename, targetname):
    return packagename + targetname if packagename != targetname else targetname


def getUsedTarget(env, buildSettings):
    plaintarget = None
    usedFullTargetname = buildSettings.get('usedTarget', None)
    if usedFullTargetname:
        usedPackagename, usedTargetname = splitTargetname(
            usedFullTargetname, default=True)
        from SConsider import getRegistry
        plaintarget = getRegistry().loadPackagePlaintarget(
            usedPackagename,
            usedTargetname)
    return plaintarget


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


class PackageNotFound(Exception):

    def __init__(self, package):
        self.package = package

    def __str__(self):
        return 'Package [{0}] not found'.format(self.package)


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


class PackageTargetNotFound(Exception):

    def __init__(self, target):
        self.target = target
        self.message = target

    def __str__(self):
        return 'Target [{0}] not found'.format(self.target)


class PackageRegistry:

    def __init__(
            self,
            env,
            scan_dirs,
            scan_dirs_exclude_rel=[],
            scan_dirs_exclude_abs=[]):
        import SCons
        self.env = env
        self.packages = {}
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
            collectPackageFiles(
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

    def getPackageTargetNames(self, packagename):
        return self.packages.get(packagename, {}).get('targets', {}).keys()

    def getPackagePlaintarget(self, packagename, targetname):
        return self.getPackageTargetTargets(
            packagename,
            targetname).get(
                'plaintarget',
                None)

    def isValidFulltargetname(self, fulltargetname):
        if self.hasPackage(str(fulltargetname)):
            return True
        packagename, targetname = splitTargetname(str(fulltargetname))
        return self.hasPackageTarget(packagename, targetname)

    def getPackageTargetDependencies(self, packagename, targetname):
        targetBuildSettings = self.getBuildSettings(
            packagename).get(targetname, {})
        deps = dict()
        targetlist = targetBuildSettings.get('requires', [])
        targetlist.extend(targetBuildSettings.get('linkDependencies', []))
        targetlist.extend([targetBuildSettings.get('usedTarget', '')])
        for dep_fulltargetname in targetlist:
            if dep_fulltargetname:
                dep_packagename, dep_targetname = splitTargetname(
                    dep_fulltargetname)
                if not dep_targetname:
                    dep_targetname = dep_packagename
                deps[
                    generateFulltargetname(
                        dep_packagename,
                        dep_targetname)] = self.getPackageTargetDependencies(
                            dep_packagename,
                            dep_targetname)
        return deps

    def getPackageDependencies(self, packagename):
        deps = dict()
        for targetname in self.getPackageTargetNames(packagename):
            deps[
                generateFulltargetname(
                    packagename,
                    targetname)] = self.getPackageTargetDependencies(
                        packagename,
                        targetname)
        return deps

    def isPackageLoaded(self, packagename):
        return 'loaded' in self.packages.get(packagename, {})

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
        if not target:
            raise PackageTargetNotFound(
                generateFulltargetname(
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

    def lookup(self, fulltargetname, **kw):
        packagename, targetname = splitTargetname(fulltargetname)
        logger.debug('looking up [%s]', fulltargetname)
        if self.hasPackage(packagename):
            if not self.isPackageLoaded(packagename):
                self.packages[packagename]['loaded'] = True
                packagedir = self.getPackageDir(packagename)
                packagefile = self.getPackageFile(packagename)
                builddir = self.env.getBaseOutDir().Dir(
                    packagedir.path).Dir(
                    self.env.getRelativeBuildDirectory()).Dir(
                    self.env.getRelativeVariantDirectory())
                logger.info(
                    'executing [%s] as SConscript for package [%s]',
                    packagefile.path,
                    packagename)
                try:
                    self.env.SConscript(
                        packagefile,
                        variant_dir=builddir,
                        duplicate=self.getPackageDuplicate(packagename),
                        exports=['packagename'])
                except ResolutionError as e:
                    raise PackageRequirementsNotFulfilled(
                        generateFulltargetname(
                            packagename,
                            targetname),
                        packagefile,
                        e)
                except PackageTargetNotFound as e:
                    raise e
            if targetname:
                return self.getPackageTarget(packagename, targetname)
        return None

    def loadPackage(self, packagename):
        if not self.hasPackage(packagename):
            raise PackageNotFound(packagename)
        self.lookup(packagename)
