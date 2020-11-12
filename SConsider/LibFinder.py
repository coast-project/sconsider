"""SConsider.LibFinder.

Utility to find depending libraries of a target.
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
import functools
import itertools
import operator
from SConsider.SomeUtils import getFlatENV
from SConsider.PopenHelper import ProcessRunner


def uniquelist(iterable):
    """Generates an order preserved list with unique items."""
    return list(unique(iterable))


def unique(iterable):
    """Generates an iterator over an order preserved list with unique items."""
    seen = set()
    for element in itertools.ifilterfalse(seen.__contains__, iterable):
        seen.add(element)
        yield element


class FinderFactory(object):
    @staticmethod
    def getForPlatform(platform):
        if platform == 'win32':
            return Win32Finder()
        elif platform == 'darwin':
            return MacFinder()
        return UnixFinder()


class LibFinder(object):
    def getLibs(self, env, source, libnames=None, libdirs=None):
        raise NotImplementedError()

    def getSystemLibDirs(self, env):
        raise NotImplementedError()


class UnixFinder(LibFinder):
    def __filterLibs(self, env, filename, libnames):
        basename = os.path.basename(filename)
        libNamesStr = '(' + '|'.join([re.escape(j) for j in libnames]) + ')'
        match = re.match(
            r'^' + re.escape(env.subst('$SHLIBPREFIX')) + libNamesStr + re.escape(env.subst('$SHLIBSUFFIX')),
            basename)
        return bool(match)

    @staticmethod
    def absolutify(pathOrNode):
        if hasattr(pathOrNode, 'get_abspath'):
            return pathOrNode.get_abspath()
        return pathOrNode

    def getLibs(self, env, source, libnames=None, libdirs=None):
        if libdirs:
            env.AppendENVPath('LD_LIBRARY_PATH', [self.absolutify(j) for j in libdirs])
        libs = []
        cmd = ['ldd', os.path.basename(source[0].get_abspath())]
        with ProcessRunner(cmd,
                           timeout=30,
                           seconds_to_wait=0.1,
                           cwd=os.path.dirname(source[0].get_abspath()),
                           env=getFlatENV(env)) as executor:
            for out, _ in executor:
                for (ln_lib, libpath) in re.findall(r'^\s*(.*)\s+=>\s*(not found|[^\s^\(]+)', out,
                                                    re.MULTILINE):
                    if functools.partial(operator.ne, 'not found')(libpath) and not ln_lib.startswith(os.sep):
                        libs.append(libpath)
        if libnames:
            libs = [j for j in libs if functools.partial(self.__filterLibs, env, libnames=libnames)(j)]
        return libs

    def getSystemLibDirs(self, env):
        libdirs = []
        linkercmd = env.subst('$LINK')
        if not linkercmd:
            return libdirs
        cmd = [linkercmd, '-print-search-dirs'] + env.subst('$LINKFLAGS').split(' ')
        with ProcessRunner(cmd, timeout=30, env=getFlatENV(env)) as executor:
            for out, _ in executor:
                match = re.search('^libraries.*=(.*)$', out, re.MULTILINE)
                if match:
                    libdirs.extend(
                        unique([
                            os.path.abspath(j) for j in match.group(1).split(os.pathsep)
                            if os.path.exists(os.path.abspath(j))
                        ]))
        return libdirs


class MacFinder(LibFinder):
    def __filterLibs(self, env, filename, libnames):
        basename = os.path.basename(filename)
        libNamesStr = '(' + '|'.join([re.escape(j) for j in libnames]) + ')'
        match = re.match(
            r'^' + re.escape(env.subst('$SHLIBPREFIX')) + libNamesStr + re.escape(env.subst('$SHLIBSUFFIX')),
            basename)
        return bool(match)

    @staticmethod
    def absolutify(pathOrNode):
        if hasattr(pathOrNode, 'get_abspath'):
            return pathOrNode.get_abspath()
        return pathOrNode

    def getLibs(self, env, source, libnames=None, libdirs=None):
        if libdirs:
            env.AppendENVPath('DYLD_LIBRARY_PATH', [self.absolutify(j) for j in libdirs])

        libs = []
        cmd = ['otool', '-L', os.path.basename(source[0].get_abspath())]
        with ProcessRunner(cmd,
                           timeout=30,
                           seconds_to_wait=0.1,
                           cwd=os.path.dirname(source[0].get_abspath()),
                           env=getFlatENV(env)) as executor:
            for out, _ in executor:
                for (ln_lib, libpath) in re.findall(r'^\s*(.*)\s+=>\s*(not found|[^\s^\(]+)', out,
                                                    re.MULTILINE):
                    if functools.partial(operator.ne, 'not found')(libpath) and not ln_lib.startswith(os.sep):
                        libs.append(libpath)

        if libnames:
            libs = [j for j in libs if functools.partial(self.__filterLibs, env, libnames=libnames)(j)]
        return libs

    def getSystemLibDirs(self, env):
        libdirs = []
        linkercmd = env.subst('$LINK')
        cmd = [linkercmd, '-print-search-dirs'] + env.subst('$LINKFLAGS').split(' ')

        with ProcessRunner(cmd, timeout=30, seconds_to_wait=0.1, env=getFlatENV(env)) as executor:
            for out, _ in executor:
                match = re.search('^libraries.*=(.*)$', out, re.MULTILINE)
                if match:
                    libdirs.extend(
                        unique([
                            os.path.abspath(j) for j in match.group(1).split(os.pathsep)
                            if os.path.exists(os.path.abspath(j))
                        ]))
        return libdirs


class Win32Finder(LibFinder):
    def __filterLibs(self, env, filename, libnames):
        basename = os.path.basename(filename)
        libNamesStr = '(' + '|'.join([re.escape(j) for j in libnames]) + ')'
        match = re.match(
            r'^(' + re.escape(env.subst('$LIBPREFIX')) + ')?' + libNamesStr + '.*' +
            re.escape(env.subst('$SHLIBSUFFIX')) + '$', basename)
        return bool(match)

    def __findFileInPath(self, filename, paths):
        for path in paths:
            if os.path.isfile(os.path.join(path, filename)):
                return os.path.abspath(os.path.join(path, filename))
        return None

    def getLibs(self, env, source, libnames=None, libdirs=None):
        deplibs = []
        cmd = ['objdump', '-p', os.path.basename(source[0].get_abspath())]
        with ProcessRunner(cmd,
                           timeout=30,
                           seconds_to_wait=0.1,
                           cwd=os.path.dirname(source[0].get_abspath()),
                           env=getFlatENV(env)) as executor:
            for out, _ in executor:
                deplibs.extend(re.findall(r'DLL Name:\s*(\S*)', out, re.MULTILINE))
        if not libdirs:
            libdirs = self.getSystemLibDirs(env)
        if libnames:
            deplibs = [j for j in deplibs if functools.partial(self.__filterLibs, env, libnames=libnames)(j)]
        return [
            j for j in itertools.imap(functools.partial(self.__findFileInPath, paths=libdirs), deplibs)
            if bool(j)
        ]

    def getSystemLibDirs(self, env):
        return os.environ['PATH'].split(os.pathsep)


try:
    from SCons.Tool import EmitLibSymlinks
except:
    from SCons.Util import is_List

    # copied over from scons 2.4.1
    def EmitLibSymlinks(env, symlinks, libnode, **kw):
        """Used by emitters to handle (shared/versioned) library symlinks."""
        nodes = list(set([x for x, _ in symlinks] + [libnode]))
        clean_targets = kw.get('clean_targets', [])
        if not is_List(clean_targets):
            clean_targets = [clean_targets]

        for link, linktgt in symlinks:
            env.SideEffect(link, linktgt)
            clean_list = filter(lambda x: x != linktgt, nodes)
            env.Clean(list(set([linktgt] + clean_targets)), clean_list)


# consolidated copy of SCons.Tool.VersionShLibLinkNames
# and SCons.Tool.install.versionedLibVersion as of scons 2.3.6
# adapted to accept non-patch versions too
def versionedLibVersion(dest, source, env):
    if (hasattr(source[0], 'attributes') and hasattr(source[0].attributes, 'shlibname')):
        libname = source[0].attributes.shlibname
    else:
        libname = os.path.basename(str(dest))
    shlib_suffix = env.subst('$SHLIBSUFFIX')
    version_pattern = r'(?P<version>(?P<major>[0-9]+)(\.(?P<minor>[0-9]+)(\.(?P<patch>[0-9a-zA-Z]+))?)?)'
    version = None
    versioned_re = re.compile(r'(?P<libname>.*)(?P<suffix>' + re.escape(shlib_suffix) + r')\.' +
                              version_pattern)
    result = versioned_re.search(libname)
    linknames = []
    if result:
        version = result.group('version')
        if version is not None:
            # For libfoo.so.x.y.z, linknames libfoo.so libfoo.so.x.y libfoo.so.x
            # First linkname has no version number
            linkname = result.group('libname') + result.group('suffix')
            for topdownversion in [result.group('major'), result.group('minor')]:
                if topdownversion is not None:
                    linknames.append(linkname)
                    linkname = linkname + "." + topdownversion

    return (version, linknames)
