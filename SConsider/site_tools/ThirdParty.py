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
import re
from logging import getLogger
from SCons.Script import Dir, GetOption, AddOption, Exit
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


def collectPackages(directory, direxcludesrel=None):
    packages = {}

    package_file_re = re.compile(r'^(?P<packagename>.*)\.(?P<type>sys|src|bin)\.sconsider$')

    def scanmatchfun(root, filename):
        match = package_file_re.match(filename)
        if match:
            dirobj = Dir(root)
            fileobj = dirobj.File(filename)
            if 0:
                logger.debug('found package [%s](%s) in [%s]', match.group('packagename'),
                             match.group('type'), fileobj.path)
            packages.setdefault(match.group('packagename'), {})[match.group('type')] = fileobj

    from SConsider.PackageRegistry import PackageRegistry
    PackageRegistry().collectPackageFiles(directory, scanmatchfun, excludes_rel=direxcludesrel)
    return packages


def registerDist(registry, packagename, package, distType, distDir, duplicate):
    package_dir = package[distType].get_dir()
    logger.debug('using package [%s](%s) in [%s]', packagename, distType, package_dir)
    registry.setPackage(packagename,
                        package[distType],
                        package_dir,
                        duplicate,
                        package_relpath=os.path.join(str(GetOption('3rdparty-build-prefix')), packagename))
    package_dir.addRepository(distDir)
    thirdPartyPackages.setdefault(packagename, {})[distType] = distDir


def postPackageCollection(env, registry, **kw):
    thirdPartyPathList = GetOption('3rdparty')
    if thirdPartyPathList is None:
        thirdPartyPathList = [get_third_party_default()]
    packages = {}
    for packageDir in thirdPartyPathList:
        packages.update(collectPackages(packageDir, env.relativeExcludeDirs()))

    for packagename, package in packages.iteritems():
        if registry.hasPackage(packagename):
            logger.warning('package [%s] already registered, skipping [%s]', packagename,
                           package.items()[0][1].get_dir().get_abspath())
            continue
        AddOption('--with-src-' + packagename,
                  dest='with-src-' + packagename,
                  action='store',
                  default='',
                  metavar=packagename + '_SOURCEDIR',
                  help='Specify the ' + packagename + ' source directory')
        AddOption('--with-bin-' + packagename,
                  dest='with-bin-' + packagename,
                  action='store',
                  default='',
                  metavar=packagename + '_DIR',
                  help='Specify the ' + packagename + ' legacy binary directory')
        AddOption('--with-' + packagename,
                  dest='with-' + packagename,
                  action='store',
                  default='',
                  metavar=packagename + '_DIR',
                  help='Specify the ' + packagename + ' binary directory')

        libpath = GetOption('with-src-' + packagename)
        if libpath:
            if 'src' not in package:
                logger.error('Third party source distribution definition for %s not found, aborting!',
                             packagename)
                Exit(1)
            registerDist(registry, packagename, package, 'src', env.Dir(libpath), True)
        else:
            distpath = GetOption('with-bin-' + packagename)
            if distpath:
                if 'bin' not in package:
                    logger.error('Third party binary distribution definition for %s not found, aborting!',
                                 packagename)
                    Exit(1)
                registerDist(registry, packagename, package, 'bin', env.Dir(distpath), False)
            else:
                if 'sys' not in package:
                    logger.error('Third party system definition for %s not found, aborting!', packagename)
                    Exit(1)
                path = GetOption('with-' + packagename)
                if path:
                    baseDir = env.Dir(path)
                    env.AppendUnique(LIBPATH=baseDir.Dir('lib'))
                    # add first available include dir
                    includeDirList = os.getenv('INCLUDEDIRLIST', 'include:inc:.').split(':')
                    for incdir in includeDirList:
                        try:
                            includeDir = baseDir.Dir(incdir)
                            if includeDir.isdir():
                                env.AppendUnique(CPPPATH=[includeDir])
                                break
                        except TypeError:
                            pass
                    env.PrependENVPath('PATH', baseDir.Dir('bin').get_abspath())
                logger.debug('using package [%s](%s) in [%s]', packagename, 'sys', package['sys'].get_dir())
                registry.setPackage(packagename, package['sys'], package['sys'].get_dir(), False)


def prePackageCollection(env, **_):
    # we require ConfigureHelper
    if 'ConfigureHelper' not in env['TOOLS']:
        env.Tool('ConfigureHelper')


def get_third_party_default():
    from SConsider import get_sconsider_root
    return os.path.join(get_sconsider_root(), '3rdparty')


def generate(env):
    from SConsider.Callback import Callback
    AddOption('--3rdparty',
              dest='3rdparty',
              action='append',
              help='Specify directory containing package files for third party libraries, default=["' +
              get_third_party_default() + '"]')
    prefix_default = '.ThirdParty'
    AddOption('--3rdparty-build-prefix',
              dest='3rdparty-build-prefix',
              nargs='?',
              default=prefix_default,
              const=prefix_default,
              help='Specify directory prefix for third party build output, default=["' + prefix_default +
              '"]')

    Callback().register('PostPackageCollection', postPackageCollection)
    Callback().register('PrePackageCollection', prePackageCollection)


def exists(env):
    return True
