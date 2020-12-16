"""SConsider.site_tools.precompiledLibraryInstallBuilder.

Coast-SConsider-specific tool to find precompiled third party libraries
A specific directory and library name scheme is assumed.  The tool tries
to find the 'best matching' library, with the possibility of a
downgrade.
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import os
import re
import platform
from logging import getLogger
from SCons.Action import Action
from SCons.Builder import Builder
from SConsider.LibFinder import EmitLibSymlinks, versionedLibVersion
logger = getLogger(__name__)


def findPlatformTargets(env,
                        basedir,
                        targetname,
                        prefixes=None,
                        suffixes=None,
                        dir_has_to_match=True,
                        strict_lib_name_matching=False):
    bitwidth = env.getBitwidth()
    targetRE = ''
    if prefixes is not None:
        for pre in prefixes:
            if targetRE:
                targetRE += '|'
            targetRE += re.escape(env.subst(pre))
    targetRE = '(' + targetRE + ')'
    # probably there are files like 'targetname64' or 'targetname_r':
    targetRE += '(' + targetname + ('' if strict_lib_name_matching else '[^.]*') + ')'
    targetSFX = ''
    if suffixes is not None:
        for suf in suffixes:
            if targetSFX:
                targetSFX += '|'
            targetSFX += re.escape(env.subst(suf))
    targetRE += '(' + targetSFX + ')(.*)'
    reTargetname = re.compile(targetRE)

    if dir_has_to_match:
        osStringSep = '[_-]'
        if env['PLATFORM'] in ['cygwin', 'win32']:
            dirRE = 'Win' + osStringSep + 'i386'
        elif env['PLATFORM'] == 'sunos':
            dirRE = platform.system() + osStringSep + r'([0-9]+(\.[0-9]+)*)'
        else:
            dirRE = platform.system() + osStringSep + 'glibc' + osStringSep + r'([0-9]+(\.[0-9]+)*)'
        dirRE += osStringSep + '?(.*)'
        reDirname = re.compile(dirRE)
    else:
        reDirname = re.compile('.*')

    reBits = re.compile('.*(32|64)')
    files = []
    _relExcludeList = env.relativeExcludeDirs()
    for dirpath, dirnames, filenames in os.walk(basedir):
        dirnames[:] = [d for d in dirnames if d not in _relExcludeList]
        dirMatch = reDirname.match(os.path.split(dirpath)[1])
        if not dirMatch:
            continue

        for name in filenames:
            targetMatch = reTargetname.match(name)
            if not targetMatch:
                continue
            bits = '32'
            reM = None
            target_os_version = None
            if len(dirMatch.groups()) > 2:
                reM = reBits.match(dirMatch.group(3))
                if reM:
                    bits = reM.group(1)
                target_os_version = tuple([int(x) for x in dirMatch.group(1).split('.')])

            files.append({
                'target_os_version': target_os_version,
                'bits': bits,
                'file': targetMatch.group(0),
                'path': dirpath,
                'linkfile': targetMatch.group(0).replace(targetMatch.group(4), ''),
                'filewoext': targetMatch.group(2),
                'suffix': targetMatch.group(3),
                'libVersion': targetMatch.group(4),
            })

    if not dir_has_to_match:
        return files

    # find best matching library
    # dirmatch: (xxver[1]:'2.9', xxx[2]:'.9', arch-bits[3]:'i686-32')
    # libmatch: ([1]:'lib', sufx[2]:'.so',vers[3]:'.0.9.7')

    # filter out wrong bit sizes
    files = [entry for entry in files if entry['bits'] == bitwidth]

    # check for best matching target_os_version entry, downgrade if non exact
    # match
    files.sort(cmp=lambda l, r: cmp(l['target_os_version'], r['target_os_version']), reverse=True)
    osvermatch = None
    current_os_version = env.getOsVersionTuple()
    for entry in files:
        if entry['target_os_version'] <= current_os_version:
            osvermatch = entry['target_os_version']
            break
    files = [entry for entry in files if entry['target_os_version'] == osvermatch]
    # shorter names are sorted first to prefer libtargetname.so over
    # libtargetname64.so
    files.sort(cmp=lambda l, r: cmp(len(l['filewoext']), len(r['filewoext'])))
    return files


def findLibrary(env, basedir, libname, dir_has_to_match=True, strict_lib_name_matching=False):
    # LIBPREFIXES = [ LIBPREFIX, SHLIBPREFIX ]
    # LIBSUFFIXES = [ LIBSUFFIX, SHLIBSUFFIX ]
    files = findPlatformTargets(env, basedir, libname, env['LIBPREFIXES'], env['LIBSUFFIXES'],
                                dir_has_to_match, strict_lib_name_matching)

    preferStaticLib = env.get('buildSettings', {}).get('preferStaticLib', False)

    staticLibs = [entry for entry in files if entry['suffix'] == env.subst(env['LIBSUFFIX'])]
    sharedLibs = [entry for entry in files if entry['suffix'] == env.subst(env['SHLIBSUFFIX'])]

    libVersion = env.get('buildSettings', {}).get('libVersion', '')
    # FIXME: libVersion on win
    if libVersion:
        sharedLibs = [entry for entry in sharedLibs if entry['libVersion'].startswith(libVersion)]

    if preferStaticLib:
        allLibs = staticLibs + sharedLibs
    else:
        allLibs = sharedLibs + staticLibs

    if allLibs:
        entry = allLibs[0]
        return (entry['path'], entry['file'], entry['linkfile'],
                (entry['suffix'] == env.subst(env['LIBSUFFIX'])))

    logger.warning('library [%s] not available for this platform [%s] and bitwidth[%s]', libname,
                   env['PLATFORM'], env.getBitwidth())
    return (None, None, None, None)


def findBinary(env, basedir, binaryname):
    files = findPlatformTargets(env, basedir, binaryname, [env['PROGPREFIX']], [env['PROGSUFFIX']])

    if files:
        entry = files[0]
        return (entry['path'], entry['file'], entry['linkfile'])

    logger.warning('binary [%s] not available for this platform [%s] and bitwidth[%s]', binaryname,
                   env['PLATFORM'], env.getBitwidth())
    return (None, None, None)


def precompBinNamesEmitter(target, source, env):
    del target[:]
    newsource = []
    binaryVariantDir = env.getBinaryInstallDir()
    for src in source:
        # catch misleading alias nodes with the same name as the binary to
        # search for
        if not hasattr(src, 'srcnode'):
            src = env.File(str(src))
        path, binaryname = os.path.split(src.srcnode().get_abspath())
        srcpath, srcfile, linkfile = findBinary(env, path, binaryname)
        if srcfile:
            sourcenode = env.File(os.path.join(srcpath, srcfile))
            """replace default environment with the current one to propagate settings"""
            sourcenode.env_set(env)
            newsource.append(sourcenode)
            installedTarget = binaryVariantDir.File(srcfile)
            target.append(installedTarget)
            if srcfile != linkfile:
                linkTarget = binaryVariantDir.File(linkfile)
                target.append(linkTarget)
    return (target, newsource)


def precompLibNamesEmitter(target, source, env):
    del target[:]
    newsource = []
    libraryVariantDir = env.getLibraryInstallDir(withRelTarget=True)
    for src in source:
        # catch misleading alias nodes with the same name as the library to
        # search for
        if not hasattr(src, 'srcnode'):
            src = env.File(str(src))
        path, libname = os.path.split(src.srcnode().get_abspath())
        srcpath, srcfile, _, isStaticLib = findLibrary(env, path, libname)
        if srcfile:
            sourcenode = env.File(os.path.join(srcpath, srcfile))
            """replace default environment with the current one to propagate settings"""
            sourcenode.env_set(env)
            newsource.append(sourcenode)
            if isStaticLib:
                target.append(SCons.Script.Dir('.').File(srcfile))
            else:
                installedTarget = libraryVariantDir.File(srcfile)
                version, linknames = versionedLibVersion(sourcenode, source, env)
                if version:
                    symlinks = map(lambda n: (env.fs.File(n, libraryVariantDir), installedTarget), linknames)
                    EmitLibSymlinks(env, symlinks, installedTarget)
                    sourcenode.attributes.shliblinks = symlinks

                target.append(installedTarget)
    return (target, newsource)


def createSymLink(target, source, env):
    from SConsider.PackageRegistry import PackageRegistry
    source = PackageRegistry().getRealTarget(source)
    target = PackageRegistry().getRealTarget(target)
    src, dest = source.get_abspath(), target.get_abspath()
    relSrc = os.path.relpath(src, os.path.dirname(dest))
    os.symlink(relSrc, dest)


def prePackageCollection(env, **_):
    # ensure we have getBitwidth() and other functions available
    for required_tool in ['setupBuildTools']:
        if required_tool not in env['TOOLS']:
            env.Tool(required_tool)


def generate(env):
    from SConsider.Callback import Callback
    from SCons.Tool import install
    import SCons.Defaults

    def _local_add_versioned_targets_to_INSTALLED_FILES(target, source, env):
        if source:
            return install.add_versioned_targets_to_INSTALLED_FILES(target, source, env)
        return (None, None)

    SymbolicLinkAction = Action(createSymLink, "Generating symbolic link for '$SOURCE' as '$TARGET'")
    SymbolicLinkBuilder = Builder(
        action=[SymbolicLinkAction],
        emitter=[install.add_targets_to_INSTALLED_FILES],
    )
    env.Append(BUILDERS={"Symlink": SymbolicLinkBuilder})

    def wrapPrecompLibAction(target, source, env):
        return install.installVerLib_action(target, source, env)

    PrecompLibAction = Action(wrapPrecompLibAction, "Installing precompiled library '$SOURCE' as '$TARGET'")
    PrecompLibBuilder = Builder(action=[PrecompLibAction],
                                emitter=[
                                    precompLibNamesEmitter, SCons.Defaults.SharedObjectEmitter,
                                    _local_add_versioned_targets_to_INSTALLED_FILES
                                ],
                                multi=0,
                                source_factory=env.fs.Entry,
                                single_source=True)

    env.Append(BUILDERS={'PrecompiledLibraryInstallBuilder': PrecompLibBuilder})

    PrecompBinAction = Action(install.installFunc, "Installing precompiled binary '$SOURCE' as '$TARGET'")
    PrecompBinBuilder = Builder(action=[PrecompBinAction],
                                emitter=[precompBinNamesEmitter, install.add_targets_to_INSTALLED_FILES],
                                single_source=False)

    env.Append(BUILDERS={'PrecompiledBinaryInstallBuilder': PrecompBinBuilder})
    Callback().register('PrePackageCollection', prePackageCollection)


def exists(env):
    return True
