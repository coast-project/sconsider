"""SConsider.site_tools.suncc.

SConsider-specific suncc tool initialization

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

import SCons.Util
import SCons.Tool


def generate(env):
    """Add Builders and construction variables for Forte C and C++ compilers to
    an Environment."""

    SCons.Tool.Tool('cc')(env)

    env['CXX'] = 'CC'
    env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -KPIC')
    env['SHOBJPREFIX'] = 'so_'
    env['SHOBJSUFFIX'] = '.o'

    env.AppendUnique(CFLAGS='-mt')

    def bwopt(bitwidth):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise
            # native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    env.AppendUnique(CFLAGS=bwopt(env['ARCHBITS']))

    if not SCons.Script.GetOption('no-largefilesupport'):
        env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE'])

    buildmode = SCons.Script.GetOption('buildcfg')
    if buildmode == 'debug':
        pass
    elif buildmode == 'optimized':
        env.AppendUnique(CFLAGS=['-fast', '-xbinopt=prepare'])
    elif buildmode == 'profile':
        env.AppendUnique(CFLAGS=['-xpg'])

    warnlevel = SCons.Script.GetOption('warnlevel')
    if warnlevel == 'medium' or warnlevel == 'full':
        env.AppendUnique(CFLAGS=['+w', '-xport64=implicit'])
    if warnlevel == 'full':
        env.AppendUnique(CFLAGS=[])


def exists(env):
    return env.Detect('CC')

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
