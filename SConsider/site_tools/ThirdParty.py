"""SConsider.site_tools.ThirdParty.

SConsider-specific 3rdparty llibrary handling

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
import fnmatch
import SCons
from logging import getLogger
logger = getLogger(__name__)

thirdDartyPackages = {}


def hasSourceDist(packagename):
    return 'src' in thirdDartyPackages.get(packagename, {})


def getSourceDistDir(packagename):
    return thirdDartyPackages.get(packagename, {}).get('src', '')


def hasBinaryDist(packagename):
    return 'bin' in thirdDartyPackages.get(packagename, {})


def getBinaryDistDir(packagename):
    return thirdDartyPackages.get(packagename, {}).get('bin', '')


def collectPackages(startdir, exceptions=[]):
    package_re = re.compile(
        '^(?P<packagename>.*)\.(?P<type>sys|src|bin)\.sconsider$')
    packages = {}
    for root, dirnames, filenames in os.walk(startdir):
        dirnames[:] = [dir for dir in dirnames if dir not in exceptions]
        for filename in fnmatch.filter(filenames, '*.sconsider'):
            match = package_re.match(filename)
            if match:
                packages.setdefault(
                    match.group('packagename'),
                    {})[
                    match.group('type')] = SCons.Script.Dir(root).File(
                    filename)
    return packages


def registerDist(registry, packagename, package, distType, distDir, duplicate):
    package_dir = package[distType].get_dir()
    logger.debug(
        'found package [{0}]({1}) in [{2}]'.format(
            packagename,
            distType,
            package_dir))
    registry.setPackage(
        packagename,
        package[distType],
        package_dir,
        duplicate)
    package_dir.addRepository(distDir)
    thirdDartyPackages.setdefault(packagename, {})[distType] = distDir


def prepareLibraries(env, registry, **kw):
    thirdPartyPathList = SCons.Script.GetOption('3rdparty')
    packages = {}
    for packageDir in thirdPartyPathList:
        packages.update(collectPackages(packageDir, [env.get('BUILDDIR', '')]))

    for packagename, package in packages.iteritems():
        if registry.hasPackage(packagename):
            logger.warning(
                'package [{0}] already registered, skipping [{1}]'.format(
                    packagename,
                    package.items()[0][1].get_dir().abspath))
            continue
        SCons.Script.AddOption(
            '--with-src-' +
            packagename,
            dest='with-src-' +
            packagename,
            action='store',
            default='',
            metavar=packagename +
            '_SOURCEDIR',
            help='Specify the ' +
            packagename +
            ' source directory')
        SCons.Script.AddOption(
            '--with-bin-' +
            packagename,
            dest='with-bin-' +
            packagename,
            action='store',
            default='',
            metavar=packagename +
            '_DIR',
            help='Specify the ' +
            packagename +
            ' legacy binary directory')
        SCons.Script.AddOption(
            '--with-' +
            packagename,
            dest='with-' +
            packagename,
            action='store',
            default='',
            metavar=packagename +
            '_DIR',
            help='Specify the ' +
            packagename +
            ' binary directory')

        libpath = SCons.Script.GetOption('with-src-' + packagename)
        if libpath:
            if 'src' not in package:
                logger.error(
                    'Source distribution definition for {0} not found, aborting!'.format(packagename))
                SCons.Script.Exit(1)
            registerDist(
                registry,
                packagename,
                package,
                'src',
                env.Dir(libpath),
                True)
        else:
            distpath = SCons.Script.GetOption('with-bin-' + packagename)
            if distpath:
                if 'bin' not in package:
                    logger.error(
                        'Binary distribution definition for {0} not found, aborting!'.format(packagename))
                    SCons.Script.Exit(1)
                registerDist(
                    registry,
                    packagename,
                    package,
                    'bin',
                    env.Dir(distpath),
                    False)
            else:
                if 'sys' not in package:
                    logger.error(
                        'System definition for {0} not found, aborting!'.format(packagename))
                    SCons.Script.Exit(1)
                path = SCons.Script.GetOption('with-' + packagename)
                if path:
                    env.AppendUnique(LIBPATH=env.Dir(path).Dir('lib'))
                    env.PrependENVPath('PATH', env.Dir(path).Dir('bin'))
                logger.debug(
                    'found package [{0}]({1}) in [{2}]'.format(
                        packagename,
                        'sys',
                        package['sys'].get_dir()))
                registry.setPackage(
                    packagename,
                    package['sys'],
                    package['sys'].get_dir(),
                    False)


def generate(env):
    import SCons.Script
    from SConsider import _base_path, registerCallback
    siteDefault3rdparty = os.path.join(_base_path,
                                       '3rdparty')
    SCons.Script.AddOption(
        '--3rdparty',
        dest='3rdparty',
        action='append',
        default=[siteDefault3rdparty],
        help='Specify directory containing package files for third party\
 libraries, default=["' + siteDefault3rdparty + '"]')
    registerCallback('PostPackageCollection', prepareLibraries)


def exists(env):
    return 1
