"""SConsider.site_tools.ThirdParty.

SConsider-specific 3rdparty library handling

"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import os
import SCons
from SCons.Script import Clean
from ConfigureHelper import Configure
from logging import getLogger
logger = getLogger(__name__)

thirdPartyPackages = {}


def hasSourceDist(packagename):
    return 'src' in thirdPartyPackages.get(packagename, {})


def getSourceDistDir(packagename):
    return thirdPartyPackages.get(packagename, {}).get('src', '')


def hasBinaryDist(packagename):
    return 'bin' in thirdPartyPackages.get(packagename, {})


def getBinaryDistDir(packagename):
    return thirdPartyPackages.get(packagename, {}).get('bin', '')


def collectPackages(directory, direxcludesrel=[]):
    packages = {}

    def scanmatchfun(root, filename, match):
        dirobj = SCons.Script.Dir(root)
        fileobj = dirobj.File(filename)
        if 0:
            logger.debug(
                'found package [{0}]({1}) in [{2}]'.format(
                    match.group('packagename'),
                    match.group('type'),
                    fileobj.path))
        packages.setdefault(
            match.group('packagename'), {})[
            match.group('type')] = fileobj
    import SConsider.PackageRegistry
    SConsider.PackageRegistry.PackageRegistry.collectPackageFiles(
        directory,
        '^(?P<packagename>.*)\.(?P<type>sys|src|bin)\.sconsider$',
        scanmatchfun,
        excludes_rel=direxcludesrel)
    return packages


def registerDist(registry, packagename, package, distType, distDir, duplicate):
    package_dir = package[distType].get_dir()
    logger.debug(
        'using package [{0}]({1}) in [{2}]'.format(
            packagename,
            distType,
            package_dir))
    registry.setPackage(
        packagename,
        package[distType],
        package_dir,
        duplicate)
    package_dir.addRepository(distDir)
    thirdPartyPackages.setdefault(packagename, {})[distType] = distDir


def postPackageCollection(env, registry, **kw):
    thirdPartyPathList = SCons.Script.GetOption('3rdparty')
    packages = {}
    for packageDir in thirdPartyPathList:
        packages.update(collectPackages(packageDir,
                                        env.relativeExcludeDirs()))

    for packagename, package in packages.iteritems():
        if registry.hasPackage(packagename):
            logger.warning(
                'package [{0}] already registered, skipping [{1}]'.format(
                    packagename,
                    package.items()[0][1].get_dir().get_abspath()))
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
                    'Third party source distribution definition for {0} not found, aborting!'.format(packagename))
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
                        'Third party binary distribution definition for {0} not found, aborting!'.format(packagename))
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
                        'Third party system definition for {0} not found, aborting!'.format(packagename))
                    SCons.Script.Exit(1)
                path = SCons.Script.GetOption('with-' + packagename)
                if path:
                    env.AppendUnique(LIBPATH=env.Dir(path).Dir('lib'))
                    env.PrependENVPath('PATH', env.Dir(path).Dir('bin'))
                logger.debug(
                    'using package [{0}]({1}) in [{2}]'.format(
                        packagename,
                        'sys',
                        package['sys'].get_dir()))
                registry.setPackage(
                    packagename,
                    package['sys'],
                    package['sys'].get_dir(),
                    False)


def prePackageCollection(env):
    # we require ConfigureHelper
    if 'ConfigureHelper' not in env['TOOLS']:
        env.Tool('ConfigureHelper')


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

    registerCallback('PostPackageCollection', postPackageCollection)
    registerCallback('PrePackageCollection', prePackageCollection)


def exists(env):
    return True
