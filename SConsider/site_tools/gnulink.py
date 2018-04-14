"""SConsider.site_tools.gnulink.

SConsider-specific gnulink tool initialization
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

import sys
import os
import SCons.Tool
from SCons.Errors import UserError
import SConsider.SomeUtils


def gnu_link_node_comparer(left, right):
    """Specialized implementation of file node sorting based on the fact that
    config_ files must get placed before any other object on the linker command
    line."""
    nleft = left.srcnode().get_abspath()
    nright = right.srcnode().get_abspath()
    _, lbasename = os.path.split(nleft)
    _, rbasename = os.path.split(nright)
    # l < r, -1
    # l == r, 0
    # l > r, 1
    if lbasename.startswith('config_'):
        return -1
    elif rbasename.startswith('config_'):
        return 1
    return cmp(nleft, nright)


SConsider.SomeUtils.FileNodeComparer = gnu_link_node_comparer


def generate(env):
    """Add Builders and construction variables for gnu compilers to an
    Environment."""
    defaulttoolpath = SCons.Tool.DefaultToolpath
    try:
        SCons.Tool.DefaultToolpath = []
        # load default link tool and extend afterwards
        env.Tool('gnulink')
    finally:
        SCons.Tool.DefaultToolpath = defaulttoolpath

    platf = env['PLATFORM']
    if str(platf) not in ["cygwin", "win32"]:
        env.AppendUnique(LINKFLAGS=['-nodefaultlibs'])
        env.AppendUnique(LIBS=['rt', 'm', 'gcc', 'gcc_s'])
        env.AppendUnique(LIBS=['dl', 'c'])
        env.AppendUnique(LIBS=['nsl'])
    elif str(platf) == "win32":
        env.AppendUnique(LINKFLAGS=['-Wl,--enable-auto-import'])
        env.AppendUnique(SHLINKFLAGS=['-Wl,--export-all-symbols'])
        env.AppendUnique(LIBS=['ws2_32'])
    orig_smart_link = env['SMARTLINK']

    def smart_link(source, target, env, for_signature):
        try:
            cplusplus = sys.modules['SCons.Tool.c++']
            if cplusplus.iscplusplus(source):
                env.AppendUnique(LIBS=['stdc++'])
        except:
            pass
        return orig_smart_link(source, target, env, for_signature)

    env.Replace(SMARTLINK=smart_link)

    # ensure we have getBitwidth() available
    if 'setupBuildTools' not in env['TOOLS']:
        raise UserError('setupBuildTools is required for\
 initialization')

    bitwidth = env.getBitwidth()
    env.AppendUnique(LINKFLAGS='-m' + bitwidth)

    if str(platf) not in ["cygwin", "win32"]:
        # tell linker to only succeed when all external references can be
        # resolved
        env.Append(_NONLAZYLINKFLAGS='-z defs -z now ')
        env.Append(LINKFLAGS=['$_NONLAZYLINKFLAGS'])
    if str(platf) == "sunos":
        # this lib is needed when using sun-CC or gcc on sunos systems
        env.AppendUnique(LIBS=['socket', 'resolv', 'posix4', 'aio'])

    buildmode = env.getBuildCfg()
    if buildmode in ['debug', 'profile']:
        env.AppendUnique(SHLINKFLAGS=['-ggdb3' if str(platf) == 'sunos' else '-g'])
    if buildmode == 'debug':
        env.AppendUnique(LINKFLAGS=['-v'])
        env.AppendUnique(SHLINKFLAGS=['-v'])
    elif buildmode == 'optimized':
        pass
    elif buildmode == 'coverage':
        env.AppendUnique(LINKFLAGS=['-fprofile-arcs', '-ftest-coverage'])
        env.AppendUnique(SHLINKFLAGS=['-fprofile-arcs', '-ftest-coverage'])
        env.PrependUnique(LIBS=['gcov'])
    elif buildmode == 'profile':
        env.AppendUnique(LINKFLAGS=['-pg'])
        env.AppendUnique(SHLINKFLAGS=['-pg'])
    env.AddMethod(lambda env: env.Replace(_NONLAZYLINKFLAGS=''), 'allowUnresolvedLinkSymbols')


def exists(env):
    return True
