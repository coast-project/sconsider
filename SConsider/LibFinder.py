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
from SConsider.PopenHelper import PopenHelper, PIPE


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
        ldd = PopenHelper(['ldd', os.path.basename(source[0].get_abspath())],
                          stdout=PIPE,
                          cwd=os.path.dirname(source[0].get_abspath()),
                          env=getFlatENV(env))
        out, _ = ldd.communicate()
        libs = [
            j for j in re.findall(r'^.*=>\s*(not found|[^\s^\(]+)', out, re.MULTILINE)
            if functools.partial(operator.ne, 'not found')(j)
        ]
        if libnames:
            libs = [j for j in libs if functools.partial(self.__filterLibs, env, libnames=libnames)(j)]
        return libs

    def getSystemLibDirs(self, env):
        libdirs = []
        linkercmd = env.subst('$LINK')
        if not linkercmd:
            return libdirs
        cmdargs = [linkercmd, '-print-search-dirs'] + env.subst('$LINKFLAGS').split(' ')
        linker = PopenHelper(cmdargs, stdout=PIPE, env=getFlatENV(env))
        out, _ = linker.communicate()
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
        ldd = PopenHelper(['otool', '-L', os.path.basename(source[0].get_abspath())],
                          stdout=PIPE,
                          cwd=os.path.dirname(source[0].get_abspath()),
                          env=getFlatENV(env))
        out, _ = ldd.communicate()
        libs = [
            j for j in re.findall(r'^.*=>\s*(not found|[^\s^\(]+)', out, re.MULTILINE)
            if functools.partial(operator.ne, 'not found')(j)
        ]
        if libnames:
            libs = [j for j in libs if functools.partial(self.__filterLibs, env, libnames=libnames)(j)]
        return libs

    def getSystemLibDirs(self, env):
        libdirs = []
        linkercmd = env.subst('$LINK')
        cmdargs = [linkercmd, '-print-search-dirs'] + env.subst('$LINKFLAGS').split(' ')
        linker = PopenHelper(cmdargs, stdout=PIPE, env=getFlatENV(env))
        out, _ = linker.communicate()
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
        ldd = PopenHelper(['objdump', '-p', os.path.basename(source[0].get_abspath())],
                          stdout=PIPE,
                          cwd=os.path.dirname(source[0].get_abspath()),
                          env=getFlatENV(env))
        out, _ = ldd.communicate()
        deplibs = re.findall(r'DLL Name:\s*(\S*)', out, re.MULTILINE)
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
