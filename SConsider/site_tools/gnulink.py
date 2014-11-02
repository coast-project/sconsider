"""SConsider.site_tools.gnulink.

SConsider-specific gnulink tool initialization

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

import sys
import os
import SCons.Util
import SCons.Tool
import SomeUtils


def FileNodeComparer(left, right):
    """Specialized implementation of file node sorting based on the fact that
    config_ files must get placed before any other object on the linker command
    line."""
    nleft = left.srcnode().abspath
    nright = right.srcnode().abspath
    ldirname, lbasename = os.path.split(nleft)
    rdirname, rbasename = os.path.split(nright)
    # l < r, -1
    # l == r, 0
    # l > r, 1
    if lbasename.startswith('config_'):
        return - 1
    elif rbasename.startswith('config_'):
        return 1
    return cmp(nleft, nright)

SomeUtils.FileNodeComparer = FileNodeComparer


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

    bitwidth = env.getBitwidth() if hasattr(env, 'getBitwidth') else '32'
    env.AppendUnique(LINKFLAGS='-m' + bitwidth)

    if str(platf) not in ["cygwin", "win32"]:
        env.Append(_NONLAZYLINKFLAGS='-z defs -z now ')
    if str(platf) == "sunos":
        # this lib is needed when using sun-CC or gcc on sunos systems
        env.AppendUnique(LIBS=['socket', 'resolv', 'posix4', 'aio'])

    buildmode = SCons.Script.GetOption('buildcfg')
    if buildmode == 'debug':
        env.AppendUnique(SHLINKFLAGS=['-v'])
        env.AppendUnique(
            SHLINKFLAGS=[
                '-ggdb3' if str(platf) == 'sunos' else '-g'])
        env.AppendUnique(LINKFLAGS=['-v'])
    elif buildmode == 'optimized':
        pass
    elif buildmode == 'profile':
        env.AppendUnique(LINKFLAGS=['-fprofile'])
        env.AppendUnique(SHLINKFLAGS=['-fprofile'])


def exists(env):
    return True
