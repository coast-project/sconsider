"""SConsider.site_tools.precompiledLibraryInstallBuilder.

Coast-SConsider-specific tool to find precompiled third party libraries

A specific directory and library name scheme is assumed.

The tool tries to find the 'best matching' library, with the possibility of a downgrade.

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

import os
import re
import platform
import shutil
import stat
import SCons.Action
import SCons.Builder
from logging import getLogger
logger = getLogger(__name__)


def findPlatformTargets(env, basedir, targetname, prefixes=[], suffixes=[]):
    bitwidth = env.get('ARCHBITS', '32')
    libRE = ''
    for pre in prefixes:
        if libRE:
            libRE += '|'
        libRE += re.escape(env.subst(pre))
    libRE = '(' + libRE + ')'
    # probably there are files like 'targetname64' or 'targetname_r':
    libRE += '(' + targetname + '[^.]*)'
    libSFX = ''
    for suf in suffixes:
        if libSFX:
            libSFX += '|'
        libSFX += re.escape(env.subst(suf))
    libRE += '(' + libSFX + ')(.*)'
    reLibname = re.compile(libRE)
    osStringSep = '[_-]'
    if env['PLATFORM'] in ['cygwin', 'win32']:
        if env['PLATFORM'] == 'cygwin':
            osver = tuple([int(x)
                           for x in platform.system().split('-')
                           [1].split('.')])
        else:
            osver = tuple([int(x) for x in platform.version().split('.')])
#        dirRE = platform.system() + osStringSep + '([0-9]+(\.[0-9]+)*)'
        dirRE = 'Win' + osStringSep + 'i386'
        # re for architecture (i686, sparc, amd,...) - bitwidth (32,64)
        dirRE += osStringSep + '?(.*)'
    elif env['PLATFORM'] == 'sunos':
        osver = tuple([int(x) for x in platform.release().split('.')])
        dirRE = platform.system() + osStringSep + '([0-9]+(\.[0-9]+)*)'
        # re for architecture (i686, sparc, amd,...) - bitwidth (32,64)
        dirRE += osStringSep + '?(.*)'
    else:
        import SomeUtils
        osver = tuple([int(x)
                       for x in SomeUtils.getLibCVersion(bitwidth)[1].split(
                           '.')])
        dirRE = platform.system(
        ) + osStringSep + 'glibc' + osStringSep + '([0-9]+(\.[0-9]+)*)'
        # re for architecture (i686, sparc, amd,...) - bitwidth (32,64)
        dirRE += osStringSep + '?(.*)'
    reDirname = re.compile(dirRE)
    reBits = re.compile('.*(32|64)')
    files = []
    for dirpath, dirnames, filenames in os.walk(basedir):
        dirnames[:] = [
            dir for dir in dirnames if dir not in [
                env['BUILDDIR'],
                '.git',
                '.svn',
                'CVS']]
        dirMatch = reDirname.match(os.path.split(dirpath)[1])
        if dirMatch:
            for name in filenames:
                libMatch = reLibname.match(name)
                if libMatch:
                    bits = '32'
                    reM = reBits.match(dirMatch.group(3))
                    if reM:
                        bits = reM.group(1)
                    files.append({
                        'osver':
                        tuple(
                            [int(x)
                             for x in dirMatch.group(1).split('.')]),
                        'bits': bits, 'file': libMatch.group(0),
                        'path': dirpath,
                        'linkfile': libMatch.group(0).replace(
                                      libMatch.group(4),
                                      ''),
                        'filewoext': libMatch.group(2),
                        'suffix': libMatch.group(3),
                        'libVersion': libMatch.group(4), })
    # find best matching library
    # dirmatch: (xxver[1]:'2.9', xxx[2]:'.9', arch-bits[3]:'i686-32')
    # libmatch: ([1]:'lib', sufx[2]:'.so',vers[3]:'.0.9.7')

    # filter out wrong bit sizes
    files = [entry for entry in files if entry['bits'] == bitwidth]

    # check for best matching osver entry, downgrade if non exact match
    files.sort(cmp=lambda l, r: cmp(l['osver'], r['osver']), reverse=True)
    osvermatch = None
    for entry in files:
        if entry['osver'] <= osver:
            osvermatch = entry['osver']
            break
    files = [entry for entry in files if entry['osver'] == osvermatch]
    # shorter names are sorted first to prefer libtargetname.so over
    # libtargetname64.so
    files.sort(cmp=lambda l, r: cmp(len(l['filewoext']), len(r['filewoext'])))
    return files


def findLibrary(env, basedir, libname):
    # LIBPREFIXES = [ LIBPREFIX, SHLIBPREFIX ]
    # LIBSUFFIXES = [ LIBSUFFIX, SHLIBSUFFIX ]
    files = findPlatformTargets(
        env,
        basedir,
        libname,
        env['LIBPREFIXES'],
        env['LIBSUFFIXES'])

    preferStaticLib = env.get(
        'buildSettings',
        {}).get(
        'preferStaticLib',
        False)

    staticLibs = [
        entry for entry in files
        if entry['suffix'] == env.subst(env['LIBSUFFIX'])]
    sharedLibs = [
        entry for entry in files
        if entry['suffix'] == env.subst(env['SHLIBSUFFIX'])]

    libVersion = env.get('buildSettings', {}).get('libVersion', '')
    # FIXME: libVersion on win
    if libVersion:
        sharedLibs = [
            entry for entry in sharedLibs if entry['libVersion'] == libVersion]

    if preferStaticLib:
        allLibs = staticLibs + sharedLibs
    else:
        allLibs = sharedLibs + staticLibs

    if allLibs:
        entry = allLibs[0]
        return (
            entry['path'],
            entry['file'],
            entry['linkfile'],
            (entry['suffix'] == env.subst(
                env['LIBSUFFIX'])))

    logger.warning(
        'library [%s] not available for this platform [%s] and bitwidth[%s]',
        libname,
        env['PLATFORM'],
        env.get(
            'ARCHBITS',
            '32'))
    return (None, None, None, None)


def findBinary(env, basedir, binaryname):
    files = findPlatformTargets(
        env, basedir, binaryname, [
            env['PROGPREFIX']], [
            env['PROGSUFFIX']])

    if files:
        entry = files[0]
        return (entry['path'], entry['file'], entry['linkfile'])

    logger.warning(
        'binary [%s] not available for this platform [%s] and bitwidth[%s]',
        binaryname,
        env['PLATFORM'],
        env.get(
            'ARCHBITS',
            '32'))
    return (None, None, None)


def precompBinNamesEmitter(target, source, env):
    target = []
    newsource = []
    for src in source:
        # catch misleading alias nodes with the same name as the binary to
        # search for
        if not hasattr(src, 'srcnode'):
            src = env.File(str(src))
        path, binaryname = os.path.split(src.srcnode().abspath)
        srcpath, srcfile, linkfile = findBinary(env, path, binaryname)
        if srcfile:
            if srcfile != linkfile:
                newsource.append(
                    SCons.Script.File(
                        os.path.join(
                            srcpath,
                            srcfile)))
                target.append(
                    env['BASEOUTDIR'].Dir(
                        env['RELTARGETDIR']).Dir(
                        env['BINDIR']).Dir(
                        env['VARIANTDIR']).File(linkfile))
            newsource.append(SCons.Script.File(os.path.join(srcpath, srcfile)))
            target.append(
                env['BASEOUTDIR'].Dir(
                    env['RELTARGETDIR']).Dir(
                    env['BINDIR']).Dir(
                    env['VARIANTDIR']).File(srcfile))
    return (target, newsource)


def precompLibNamesEmitter(target, source, env):
    target = []
    newsource = []
    for src in source:
        # catch misleading alias nodes with the same name as the library to
        # search for
        if not hasattr(src, 'srcnode'):
            src = env.File(str(src))
        path, libname = os.path.split(src.srcnode().abspath)
        srcpath, srcfile, linkfile, isStaticLib = findLibrary(
            env, path, libname)
        if srcfile:
            if not isStaticLib:
                if srcfile != linkfile:
                    newsource.append(
                        SCons.Script.File(
                            os.path.join(
                                srcpath,
                                srcfile)))
                    target.append(
                        env['BASEOUTDIR'].Dir(
                            env['RELTARGETDIR']).Dir(
                            env['LIBDIR']).Dir(
                            env['VARIANTDIR']).File(linkfile))
                newsource.append(
                    SCons.Script.File(
                        os.path.join(
                            srcpath,
                            srcfile)))
                target.append(
                    env['BASEOUTDIR'].Dir(
                        env['RELTARGETDIR']).Dir(
                        env['LIBDIR']).Dir(
                        env['VARIANTDIR']).File(srcfile))
            else:
                newsource.append(
                    SCons.Script.File(
                        os.path.join(
                            srcpath,
                            srcfile)))
                target.append(SCons.Script.Dir('.').File(srcfile))
    return (target, newsource)


def copyFunc(dest, source, env):
    """Install a source file or directory into a destination by copying,
    (including copying permission/mode bits)."""
    if os.path.isdir(source):
        if os.path.exists(dest):
            if not os.path.isdir(dest):
                raise SCons.Errors.UserError(
                    "cannot overwrite non-directory `%s' with a directory `%s'" %
                    (str(dest), str(source)))
        else:
            parent = os.path.split(dest)[0]
            if not os.path.exists(parent):
                os.makedirs(parent)
        shutil.copytree(source, dest)
    else:
        shutil.copy2(source, dest)
        st = os.stat(source)
        os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

    return 0


def installFunc(target, source, env):
    """Install a source file into a target using the function specified as the
    INSTALL construction variable."""
    if len(target) == len(source):
        for t, s in zip(target, source):
            if copyFunc(t.get_path(), s.get_path(), env):
                return 1
    return 0


def generate(env):
    PrecompLibAction = SCons.Action.Action(
        installFunc,
        "Installing precompiled library '$SOURCE' as '$TARGET'")
    PrecompLibBuilder = SCons.Builder.Builder(action=[PrecompLibAction],
                                              emitter=precompLibNamesEmitter,
                                              single_source=False)

    env.Append(
        BUILDERS={
            'PrecompiledLibraryInstallBuilder': PrecompLibBuilder})

    PrecompBinAction = SCons.Action.Action(
        installFunc,
        "Installing precompiled binary '$SOURCE' as '$TARGET'")
    PrecompBinBuilder = SCons.Builder.Builder(action=[PrecompBinAction],
                                              emitter=precompBinNamesEmitter,
                                              single_source=False)

    env.Append(BUILDERS={'PrecompiledBinaryInstallBuilder': PrecompBinBuilder})


def exists(env):
    return 1
