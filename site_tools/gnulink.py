"""SCons.Tool.gnulink"""

import sys,pdb, os
import SCons.Util
import SCons.Tool
import SomeUtils

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
    if lbasename.startswith('config_'): return -1
    elif rbasename.startswith('config_'): return 1
    return cmp(nleft, nright)

SomeUtils.FileNodeComparer = FileNodeComparer

def generate(env):
    """Add Builders and construction variables for gnu compilers to an Environment."""
    defaulttoolpath = SCons.Tool.DefaultToolpath
    SCons.Tool.DefaultToolpath = []
    # load default sunlink tool and extend afterwards
    env.Tool('gnulink')
    SCons.Tool.DefaultToolpath = defaulttoolpath

def exists(env):
    return None
