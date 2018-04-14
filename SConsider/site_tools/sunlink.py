"""SConsider.site_tools.sunlink.

SConsider-specific sunlink tool initialization
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
import SCons.Util
import SCons.Tool
import SomeUtils


def FileNodeComparer(left, right):
    """Specialized implementation of file node sorting based on the fact that
    config_ files must get placed after any other object on the linker command
    line."""
    nleft = left.srcnode().get_abspath()
    nright = right.srcnode().get_abspath()
    ldirname, lbasename = os.path.split(nleft)
    rdirname, rbasename = os.path.split(nright)
    # l < r, -1
    # l == r, 0
    # l > r, 1
    if lbasename.startswith('config_'):
        return 1
    elif rbasename.startswith('config_'):
        return -1
    return cmp(nleft, nright)


SomeUtils.FileNodeComparer = FileNodeComparer


def sun_smart_link(source, target, env, for_signature):
    try:
        cplusplus = sys.modules['SCons.Tool.c++']
        if cplusplus.iscplusplus(source):
            env.AppendUnique(LIBS=['Crun'])
    except:
        pass
    return '$CXX'


def generate(env):
    """Add Builders and construction variables for sun compilers to an
    Environment."""
    defaulttoolpath = SCons.Tool.DefaultToolpath
    try:
        SCons.Tool.DefaultToolpath = []
        # load default sunlink tool and extend afterwards
        env.Tool('sunlink')
    finally:
        SCons.Tool.DefaultToolpath = defaulttoolpath

    env['SMARTLINK'] = sun_smart_link
    env['LINK'] = "$SMARTLINK"

    env.AppendUnique(LINKFLAGS='-mt')
    env.AppendUnique(SHLINKFLAGS='-mt')
    # do not use rpath
    env.AppendUnique(SHLINKFLAGS='-norunpath')
    env.AppendUnique(LIBS=['socket', 'resolv', 'nsl', 'posix4', 'aio'])

    def bwopt(bitwidth):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise
            # native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    # ensure we have getBitwidth() available
    if 'setupBuildTools' not in env['TOOLS']:
        raise SCons.Errors.UserError('setupBuildTools is required for\
 initialization')

    bitwidth = env.getBitwidth()
    env.AppendUnique(LINKFLAGS=bwopt(bitwidth))
    env.AppendUnique(SHLINKFLAGS=bwopt(bitwidth))
    env.AppendUnique(SHLINKFLAGS='-library=stlport4')

    buildmode = env.getBuildCfg()
    if buildmode == 'debug':
        env.AppendUnique(LINKFLAGS=['-v'])
        env.AppendUnique(SHLINKFLAGS=['-v'])
    elif buildmode == 'optimized':
        env.AppendUnique(LINKFLAGS=['-xbinopt=prepare'])
        env.AppendUnique(SHLINKFLAGS=['-xbinopt=prepare'])
    elif buildmode == 'profile':
        env.AppendUnique(LINKFLAGS=['-xpg'])
        env.AppendUnique(SHLINKFLAGS=['-xpg'])


def exists(env):
    return True
