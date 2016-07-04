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
from logging import getLogger
from pkg_resources import ResolutionError
from deprecation import deprecated
from singleton import SingletonDecorator

logger = getLogger(__name__)


class TargetNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, name)
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
        Exception.__init__(self, package, packagefile, message)
        self.package = package
        self.packagefile = packagefile
        self.message = message

    def __str__(self):
        return 'Package [{0}] not complete (file {1}) '\
               'because of unsatisfied requirements: [{2}]'.format(
                   self.package,
                   self.packagefile if self.packagefile else '???',
                   self.message)


class TargetIsAliasException(Exception):
    def __init__(self, target_name):
        Exception.__init__(self, target_name)
        self.name = target_name

    def __str__(self):
        return 'Target {0} is an Alias node'.format(self.name)


@SingletonDecorator
class PackageRegistry(object):
    targetnameseparator = '.'

    def __init__(self,
                 env,
                 scan_dirs,
                 scan_dirs_exclude_rel=None,
                 scan_dirs_exclude_abs=None):
        self.env = env
        self.packages = {}
        self.lookupStack = []
        if not isinstance(scan_dirs, list):
            scan_dirs = [scan_dirs]
        if not scan_dirs:
            return
        from SCons.Script import Dir
        startDir = Dir('#')

        def scanmatchfun(root, filename, match):
            rootDir = self.env.Dir(root)
            _filename = rootDir.File(filename)
            logger.debug('found package [%s] in [%s]',
                         match.group('packagename'),
                         startDir.rel_path(_filename))
            self.setPackage(match.group('packagename'), _filename, rootDir)

        for scandir in scan_dirs:
            self.collectPackageFiles(scandir,
                                     r'^(?P<packagename>.*)\.sconsider$',
                                     scanmatchfun,
                                     excludes_rel=scan_dirs_exclude_rel,
                                     excludes_abs=scan_dirs_exclude_abs)

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
    @deprecated(
        "Use the static method splitFulltargetname of PackageRegistry instead.")
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
    @deprecated(
        "Use the static method createFulltargetname of PackageRegistry instead."
    )
    def generateFulltargetname(packagename, targetname=None, default=False):
        return PackageRegistry.createFulltargetname(packagename, targetname,
                                                    default)

    @staticmethod
    def createUniqueTargetname(packagename, targetname):
        return packagename + targetname if packagename != targetname else targetname

    @staticmethod
    def collectPackageFiles(directory,
                            filename_re,
                            matchfun,
                            file_ext='sconsider',
                            excludes_rel=None,
                            excludes_abs=None):
        """Recursively collects SConsider packages.

        Walks recursively through 'directory' to collect package files
        but skipping dirs in 'excludes_rel' and absolute dirs from
        'exclude_abs'.

        """
        if excludes_rel is None:
            excludes_rel = []
        if excludes_abs is None:
            excludes_abs = []
        import fnmatch
        package_re = re.compile(filename_re)
        followlinks = False
        if sys.version_info[:2] >= (2, 6):
            followlinks = True
        for root, dirnames, filenames in os.walk(directory,
                                                 followlinks=followlinks):
            _root_pathabs = os.path.abspath(root)
            dirnames[:] = [j for j in dirnames
                           if j not in excludes_rel and os.path.join(
                               _root_pathabs, j) not in excludes_abs]
            for filename in fnmatch.filter(filenames, '*.' + file_ext):
                match = package_re.match(filename)
                if match:
                    matchfun(root, filename, match)

    def setPackage(self, packagename, packagefile, packagedir, duplicate=False):
        self.packages[packagename] = {
            'packagefile': packagefile,
            'packagedir': packagedir,
            'duplicate': duplicate
        }

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

    def setPackageTarget(self, packagename, targetname, target):
        from SCons.Util import is_List
        if not self.hasPackage(packagename):
            logger.warning(
                'tried to register target [%s] for non existent package [%s]',
                targetname, packagename)
            return
        theTargets = self.packages[packagename].setdefault('targets', {})
        if target and is_List(target):
            target = target[0]
        if not target:
            return
        theTargets[targetname] = {'target': target}

    def getPackageTarget(self, packagename, targetname):
        return self.getPackageTargetTargets(packagename,
                                            targetname).get('target', None)

    def hasPackageTarget(self, packagename, targetname):
        return targetname in self.packages.get(packagename, {}).get('targets',
                                                                    {})

    def getPackageTargetTargets(self, packagename, targetname):
        if not self.hasPackage(packagename):
            logger.warning(
                'tried to access target [%s] of non existent package [%s]',
                targetname, packagename)
        return self.packages.get(packagename, {}).get('targets',
                                                      {}).get(targetname, {
                                                          'target': None
                                                      })

    def getPackageTargetNames(self, packagename):
        return self.packages.get(packagename, {}).get('targets', {}).keys()

    def isValidFulltargetname(self, fulltargetname):
        if self.hasPackage(str(fulltargetname)):
            return True
        packagename, targetname = self.splitFulltargetname(str(fulltargetname))
        return self.hasPackageTarget(packagename, targetname)

    def getPackageTargetDependencies(self,
                                     packagename,
                                     targetname,
                                     callerdeps=None):
        def get_dependent_targets(pname, tname):
            targetBuildSettings = self.getBuildSettings(packagename).get(
                targetname, {})
            targetlist = targetBuildSettings.get('requires', [])
            targetlist.extend(targetBuildSettings.get('linkDependencies', []))
            targetlist.extend([targetBuildSettings.get('usedTarget', None)])
            return [j for j in targetlist if j is not None]

        def get_fulltargetname(target=None):
            return (True, self.createFulltargetname(*self.splitFulltargetname(
                target, True)))

        if callerdeps is None:
            callerdeps = dict()
        callerdeps.setdefault('pending', [])
        deps = dict()
        for deptarget in get_dependent_targets(packagename, targetname):
            ext, fulltargetname = get_fulltargetname(deptarget)
            if fulltargetname in callerdeps.get('pending', []):
                continue
            dep_targets = deps.get(fulltargetname,
                                   callerdeps.get(fulltargetname, None))
            if dep_targets is None and ext is not None:
                callerdeps.get('pending', []).extend([fulltargetname])
                dep_targets = self.getPackageTargetDependencies(
                    *self.splitFulltargetname(fulltargetname),
                    callerdeps=callerdeps)
                callerdeps.get('pending', []).remove(fulltargetname)
            if dep_targets is not None:
                callerdeps.setdefault(fulltargetname, dep_targets)
                deps.setdefault(fulltargetname, dep_targets)
        return deps

    def getPackageDependencies(self, packagename, callerdeps=None):
        if callerdeps is None:
            callerdeps = dict()
        deps = dict()
        for targetname in self.getPackageTargetNames(packagename):
            deps.update(self.getPackageTargetDependencies(
                packagename, targetname,
                callerdeps=callerdeps))
        return deps

    def setBuildSettings(self, packagename, buildSettings):
        if self.hasPackage(packagename):
            self.packages[packagename]['buildsettings'] = buildSettings

    def hasBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return 'buildsettings' in self.packages.get(packagename, {})
        else:
            return targetname in self.packages.get(packagename, {}).get(
                'buildsettings', {})

    def getBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return self.packages.get(packagename, {}).get('buildsettings', {})
        else:
            return self.packages.get(packagename, {}).get(
                'buildsettings', {}).get(targetname, {})

    def __loadPackageTarget(self, loadfunc, packagename, targetname):
        target = self.loadPackage(packagename, targetname)
        if self.getPackageTargetNames(packagename):
            target = loadfunc(packagename, targetname)
            if targetname and not target:
                raise TargetNotFound(self.createFulltargetname(packagename,
                                                               targetname))
        return target

    def loadPackage(self, packagename, targetname):
        if not self.hasPackage(packagename):
            raise PackageNotFound(packagename)
        return self.lookup(self.createFulltargetname(packagename, targetname))

    def loadPackageTarget(self, packagename, targetname):
        return self.__loadPackageTarget(self.getPackageTarget, packagename,
                                        targetname)

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
                builddir = self.env.getBaseOutDir().Dir(packagedir.path).Dir(
                    self.env.getRelativeBuildDirectory()).Dir(
                        self.env.getRelativeVariantDirectory())
                message = 'executing [{0}] as SConscript for package [{1}]'.format(
                    packagefile.path, packagename)
                if self.lookupStack:
                    message += ' required by [{0}]'.format('>'.join(
                        self.lookupStack))
                logger.info(message)
                exports = {'packagename': packagename, 'registry': self}
                self.lookupStack.append(fulltargetname)
                try:
                    self.env.SConscript(packagefile,
                                        variant_dir=builddir,
                                        duplicate=packageduplicate,
                                        exports=exports)
                except ResolutionError as ex:
                    raise PackageRequirementsNotFulfilled(fulltargetname,
                                                          packagefile, ex)
                except (PackageNotFound, TargetNotFound) as ex:
                    ex.prependItem(fulltargetname)
                    raise ex
                finally:
                    self.lookupStack = self.lookupStack[:-1]
            if targetname:
                return self.getPackageTarget(packagename, targetname)
        return None

    @staticmethod
    def loadNode(env, name):
        return env.arg2nodes(name, node_factory=None)

    def getRealTarget(self, target, resolve_alias=False):
        from SCons.Util import is_Tuple, is_List, is_String
        from SCons.Node.Alias import Alias
        if (is_Tuple(target) and target[0] is None) or (is_List(target)
                                                        and not len(target)):
            return None
        if is_List(target) and is_Tuple(target[0]):
            target = target[0]
        if is_Tuple(target):
            target = target[0]
        if is_List(target) and len(target) <= 1:
            target = target[0]
        if is_String(target):
            target = self.lookup(target)
        if isinstance(target, Alias):
            if resolve_alias:
                logger.info("Resolving real target for Alias (%s)", str(target))
                logger.info("Alias target has %d source nodes",
                            len(target.sources))
                if len(target.sources) == 1:
                    return self.getRealTarget(target.sources[0], resolve_alias)
            raise TargetIsAliasException(str(target))
        return target
