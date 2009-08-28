"""SCons.Tool.gnulink"""

import sys, pdb, os
import SCons.Util
import SCons.Tool
import SomeUtils
import setupBuildTools

def FileNodeComparer(left, right):
    """Specialized implementation of file node sorting
    based on the fact that config_ files must get placed
    before any other object on the linker command line"""
    nleft = left.srcnode().abspath
    nright = right.srcnode().abspath
    ldirname, lbasename = os.path.split(nleft)
    rdirname, rbasename = os.path.split(nright)
    # l < r, -1
    # l == r, 0
    # l > r, 1
    if lbasename.startswith('config_'): return - 1
    elif rbasename.startswith('config_'): return 1
    return cmp(nleft, nright)

SomeUtils.FileNodeComparer = FileNodeComparer

def generate(env):
    """Add Builders and construction variables for gnu compilers to an Environment."""
    defaulttoolpath = SCons.Tool.DefaultToolpath
    try:
        SCons.Tool.DefaultToolpath = []
        # load default link tool and extend afterwards
        env.Tool('gnulink')
    finally:
        SCons.Tool.DefaultToolpath = defaulttoolpath

    platf = env['PLATFORM']
    setupBuildTools.registerCallback('LINKLIBS', lambda env: env.AppendUnique(LIBS=['m', 'dl', 'c']) )
    setupBuildTools.registerCallback('BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique(LINKFLAGS='-m'+bitwidth) )

    if not str(platf) == "cygwin":
        setupBuildTools.registerCallback('LAZYLINK_OPTIONS', lambda env: env.Append(_NONLAZYLINKFLAGS='-z defs -z now --no-undefined '))
        setupBuildTools.registerCallback('LINKLIBS', lambda env: env.AppendUnique(LIBS=['nsl']) )
    if str(platf) == "sunos":
        # this lib is needed when using sun-CC or gcc on sunos systems
        setupBuildTools.registerCallback('LINKLIBS', lambda env: env.AppendUnique(LIBS=['socket', 'resolv', 'posix4', 'aio']) )


def exists(env):
    return None
