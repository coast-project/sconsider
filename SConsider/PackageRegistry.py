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
from SConsider.deprecation import deprecated
from SConsider.singleton import SingletonDecorator

logger = getLogger(__name__)


def hasTargetExtension(target):
    return hasattr(target, 'attributes') and hasattr(target.attributes, 'sconsider')


def getTargetExtension(target):
    if hasTargetExtension(target):
        return target.attributes.sconsider
    return None


def setTargetExtension(target, ext):
    target.attributes.sconsider = ext


class TargetNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, name)
        self.name = name
        self.lookupStack = []
        self.message = 'Target [{0}] not found'.format(self.name)

    def prependItem(self, lookupItem):
        self.lookupStack[0:0] = [lookupItem]

    def __str__(self):
        if len(self.lookupStack):
            self.message += ', required by [{0}]'.format('>'.join(self.lookupStack))
        return self.message


class PackageNotFound(TargetNotFound):
    def __init__(self, name):
        TargetNotFound.__init__(self, name)
        self.message = 'Package [{0}] not found'.format(self.name)


class NoPackageTargetsFound(TargetNotFound):
    def __init__(self, name):
        TargetNotFound.__init__(self, name)
        self.message = 'Package [{0}] has no targets'.format(self.name)


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


class TargetExtension(object):
    def __init__(self, packagename, targetname, exports=None):
        self.packagename = packagename
        self.targetname = targetname
        if not exports:
            exports = []
        self.exports = exports

    def getPackagename(self):
        return self.packagename

    def getTargetname(self):
        return self.targetname

    def getFulltargetname(self):
        return PackageRegistry.createFulltargetname(self.packagename, self.targetname)

    def setFulltargetname(self, fulltargetname):
        self.packagename, self.targetname = PackageRegistry.splitFulltargetname(fulltargetname)


class TargetIsAliasException(Exception):
    def __init__(self, target_name):
        Exception.__init__(self, target_name)
        self.name = target_name

    def __str__(self):
        return 'Target {0} is an Alias node'.format(self.name)


@SingletonDecorator
class PackageRegistry(object):
    targetnameseparator = '.'

    def __init__(self, env):
        self.env = env
        self.packages = {}
        self.lookupStack = []

    @staticmethod
    def subdirs_to_scan(scan_start_dir, toplevel_excludes):
        scandirs = [
            dirname for dirname in os.listdir(scan_start_dir.path) + ['.']
            if os.path.isdir(dirname) and dirname not in toplevel_excludes
        ]
        logger.debug("Toplevel dirs to scan for package files: %s", scandirs)
        return scandirs

    def scan_for_package_files(self, start_dir, scan_dirs_exclude_rel=None, scan_dirs_exclude_abs=None):
        scan_dirs = PackageRegistry.subdirs_to_scan(start_dir, self.env.toplevelExcludeDirs())
        if not scan_dirs:
            return

        package_file_re = re.compile(r'^(?P<packagename>.*)\.sconsider$')

        def scanmatchfun(root, filename, register_func):
            match = package_file_re.match(filename)
            if match:
                rootDir = self.env.Dir(root)
                _filename = rootDir.File(filename)
                _packagename = match.group('packagename')
                if not self.hasPackage(_packagename):
                    logger.debug('found package [%s] in [%s]', _packagename, start_dir.rel_path(_filename))
                    register_func(_packagename, _filename, rootDir, package_relpath=rootDir.path)

        logger.info("Recursively collecting package files ...")
        for scandir in scan_dirs:
            PackageRegistry.collectPackageFiles(scandir,
                                                lambda p, f: scanmatchfun(p, f, self.setPackage),
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
    @deprecated("Use the static method splitFulltargetname of PackageRegistry instead.")
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
    @deprecated("Use the static method createFulltargetname of PackageRegistry instead.")
    def generateFulltargetname(packagename, targetname=None, default=False):
        return PackageRegistry.createFulltargetname(packagename, targetname, default)

    @staticmethod
    def createUniqueTargetname(packagename, targetname):
        return packagename + targetname if packagename != targetname else targetname

    @staticmethod
    def collectPackageFiles(directory,
                            match_func,
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
        followlinks = False
        if sys.version_info[:2] >= (2, 6):
            followlinks = True
        for root, dirnames, filenames in os.walk(directory, followlinks=followlinks):
            _root_pathabs = os.path.abspath(root)
            dirnames[:] = [
                j for j in dirnames
                if j not in excludes_rel and os.path.join(_root_pathabs, j) not in excludes_abs
            ]
            for filename in filenames:
                match_func(root, filename)

    def setPackage(self, packagename, packagefile, packagedir, duplicate=False, **kw):
        self.packages[packagename] = {
            'packagefile': packagefile,
            'packagedir': packagedir,
            'duplicate': duplicate
        }
        self.packages[packagename].update(kw)

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

    def get_package_relpath(self, packagename):
        fallback_path = self.packages.get(packagename, {}).get('packagedir', '').path
        return self.packages.get(packagename, {}).get('package_relpath', fallback_path)

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
        from SCons.Errors import UserError, BuildError
        from SCons.Util import is_List
        from SCons.Node import Alias
        if not self.hasPackage(packagename):
            logger.warning('tried to register target [%s] for non existent package [%s]', targetname,
                           packagename)
            return
        if is_List(target):
            if len(target) > 1:
                self.env.Requires(target[0], target[1:])
            target = target[0]
        self.packages[packagename].setdefault('targets', {})[targetname] = target
        try:
            self.env.Alias(packagename, target)  # add to package alias
        except BuildError as e:
            message = e.errstr
            if isinstance(e.node, Alias.Alias):
                message = """
The name of your target [%s] evaluates to an alias node too.
To distinguish your target from the alias, you need to wrap it
using "env.File(targetname)".
Example:
env.program(env.File('%s'), [...])

Original exception message:
%s""" % (packagename, packagename, message)
            raise UserError(message)

    def getPackageTarget(self, packagename, targetname):
        return self.packages[packagename].get('targets', {}).get(targetname, None)

    def hasPackageTarget(self, packagename, targetname):
        return targetname in self.packages.get(packagename, {}).get('targets', {})

    def getPackageTargets(self, packagename):
        return self.packages.get(packagename, {}).get('targets', {}).values()

    def getPackageTargetNames(self, packagename):
        return self.packages.get(packagename, {}).get('targets', {}).keys()

    def isValidFulltargetname(self, fulltargetname):
        if self.hasPackage(str(fulltargetname)):
            return True
        packagename, targetname = self.splitFulltargetname(str(fulltargetname))
        return self.hasPackageTarget(packagename, targetname)

    def getPackageTargetDependencies(self, packagename, targetname, callerdeps=None):
        def get_dependent_targets(pname, tname):
            if hasattr(self, 'getBuildSettings'):
                targetBuildSettings = self.getBuildSettings(packagename, targetname)
                targetlist = targetBuildSettings.get('requires', [])
                targetlist.extend(targetBuildSettings.get('linkDependencies', []))
                targetlist.extend([targetBuildSettings.get('usedTarget', None)])
                return [j for j in targetlist if j is not None]
            else:
                target = self.getPackageTarget(pname, tname)
                prereq = target.prerequisites if target.prerequisites else []
                return target.depends + prereq

        def get_fulltargetname(target=None):
            if isinstance(target, str):
                return (True, self.createFulltargetname(*self.splitFulltargetname(target, True)))
            ext = getTargetExtension(target)
            return (ext, self.createFulltargetname(ext.getPackagename(), ext.getTargetname())
                    if ext else str(target))

        if callerdeps is None:
            callerdeps = dict()
        callerdeps.setdefault('pending', [])
        deps = dict()
        for deptarget in get_dependent_targets(packagename, targetname):
            ext, fulltargetname = get_fulltargetname(deptarget)
            if fulltargetname in callerdeps.get('pending', []):
                continue
            dep_targets = deps.get(fulltargetname, callerdeps.get(fulltargetname, None))
            if dep_targets is None and ext is not None:
                callerdeps.get('pending', []).extend([fulltargetname])
                dep_targets = self.getPackageTargetDependencies(*self.splitFulltargetname(fulltargetname),
                                                                callerdeps=callerdeps)
                callerdeps.get('pending', []).remove(fulltargetname)
            if dep_targets is not None:
                callerdeps.setdefault(fulltargetname, dep_targets)
                deps.setdefault(fulltargetname, dep_targets)
        if len(callerdeps.get('pending', [])) == 0:
            callerdeps.pop('pending', None)
        return deps

    def getPackageDependencies(self, packagename, callerdeps=None):
        if callerdeps is None:
            callerdeps = dict()
        deps = dict()
        for targetname in self.getPackageTargetNames(packagename):
            deps.update(self.getPackageTargetDependencies(packagename, targetname, callerdeps=callerdeps))
        return deps

    def setBuildSettings(self, packagename, buildSettings):
        if self.hasPackage(packagename):
            self.packages[packagename]['buildsettings'] = buildSettings

    def hasBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return 'buildsettings' in self.packages.get(packagename, {})
        else:
            return targetname in self.packages.get(packagename, {}).get('buildsettings', {})

    def getBuildSettings(self, packagename, targetname=None):
        if not targetname:
            return self.packages.get(packagename, {}).get('buildsettings', {})
        else:
            return self.packages.get(packagename, {}).get('buildsettings', {}).get(targetname, {})

    def loadPackage(self, packagename, targetname):
        if not self.hasPackage(packagename):
            raise PackageNotFound(packagename)
        return self.lookup(self.createFulltargetname(packagename, targetname, True))

    def loadPackageTarget(self, packagename, targetname):
        target = self.loadPackage(packagename, targetname)
        if not target and targetname:
            raise TargetNotFound(self.createFulltargetname(packagename, targetname))
        return target

    def isPackageLoaded(self, packagename):
        return 'loaded' in self.packages.get(packagename, {})

    def __setPackageLoaded(self, packagename):
        self.packages[packagename]['loaded'] = True

    def lookup(self, fulltargetname, **kw):
        try:
            # shortcut to bail out on file or dir based arg2nodes check
            self.env.fs.stat(fulltargetname)
            return None
        except OSError:
            pass
        packagename, targetname = self.splitFulltargetname(fulltargetname)
        logger.debug('looking up [%s]', fulltargetname)
        if self.hasPackage(packagename):
            if not self.isPackageLoaded(packagename):
                self.__setPackageLoaded(packagename)
                package_relpath = self.get_package_relpath(packagename)
                packagefile = self.getPackageFile(packagename)
                packageduplicate = self.getPackageDuplicate(packagename)
                builddir = self.env.getBaseOutDir().Dir(package_relpath).Dir(
                    self.env.getRelativeBuildDirectory()).Dir(self.env.getRelativeVariantDirectory())
                message = 'executing [{0}] as SConscript for package [{1}]'.format(
                    packagefile.path, packagename)
                if self.lookupStack:
                    message += ' required by [{0}]'.format('>'.join(self.lookupStack))
                logger.info(message)
                exports = {'packagename': packagename, 'registry': self}
                self.lookupStack.append(fulltargetname)
                try:
                    self.env.SConscript(packagefile,
                                        variant_dir=builddir,
                                        duplicate=packageduplicate,
                                        exports=exports)
                    if self.getPackageTargetNames(packagename):
                        from SConsider.Callback import Callback
                        self.env.Default(packagename)
                        Callback().run("PostCreatePackageTargets", registry=self, packagename=packagename)
                    else:
                        raise NoPackageTargetsFound(packagename)
                except ResolutionError as ex:
                    raise PackageRequirementsNotFulfilled(fulltargetname, packagefile, ex)
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
        if (is_Tuple(target) and target[0] is None) or (is_List(target) and not len(target)):
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
                logger.info("Alias target has %d source nodes", len(target.sources))
                if len(target.sources) == 1:
                    return self.getRealTarget(target.sources[0], resolve_alias)
            raise TargetIsAliasException(str(target))
        return target
