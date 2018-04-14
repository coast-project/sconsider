"""SConsider.site_tools.applelink.

SConsider-specific initialization for the Apple gnu-like linker.
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

import SCons.Tool
import SCons.Util


def generate(env):
    """Add Builders and construction variables for gnu compilers to an
    Environment."""
    defaulttoolpath = SCons.Tool.DefaultToolpath
    try:
        SCons.Tool.DefaultToolpath = []
        # load default link tool and extend afterwards
        env.Tool('applelink')
    finally:
        SCons.Tool.DefaultToolpath = defaulttoolpath

    buildmode = env.getBuildCfg()
    if buildmode == 'debug':
        env.AppendUnique(LINKFLAGS=['-g', '-v'])
    elif buildmode == 'profile':
        env.AppendUnique(LINKFLAGS=['-fprofile'])
        env.AppendUnique(SHLINKFLAGS=['-fprofile'])

    # ensure we have getBitwidth() available
    if 'setupBuildTools' not in env['TOOLS']:
        raise SCons.Errors.UserError('setupBuildTools is required for\
 initialization')

    bitwidth = env.getBitwidth()
    env.AppendUnique(LINKFLAGS='-m' + bitwidth)
    # FIXME: only append to SHLINKFLAGS if we do not require all symbols
    # resolved!
    env.Append(SHLINKFLAGS=['-undefined', 'dynamic_lookup'])

    if bitwidth == '32':
        env.Append(LINKFLAGS=['-arch', 'i386'])
    elif bitwidth == '64':
        env.Append(LINKFLAGS=['-arch', 'x86_64'])
    orig_smart_link = env['SMARTLINK']

    def smart_link(source, target, env, for_signature):
        import os
        env.Append(SHLINKFLAGS=['-install_name', os.path.basename(str(target))])
        return orig_smart_link(source, target, env, for_signature)

    env.Replace(SMARTLINK=smart_link)


def exists(env):
    return env['PLATFORM'] == 'darwin'
