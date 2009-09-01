"""SCons.Tool.sunlink

Tool-specific initialization for the Sun Solaris (Forte) linker.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.
"""

#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009 The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import sys, os
import SCons.Util
import SCons.Tool
import SomeUtils
import setupBuildTools

def FileNodeComparer(left, right):
    """Specialized implementation of file node sorting
    based on the fact that config_ files must get placed
    after any other object on the linker command line"""
    nleft = left.srcnode().abspath
    nright = right.srcnode().abspath
    ldirname, lbasename = os.path.split(nleft)
    rdirname, rbasename = os.path.split(nright)
    # l < r, -1
    # l == r, 0
    # l > r, 1
    if lbasename.startswith('config_'): return 1
    elif rbasename.startswith('config_'): return - 1
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
    """Add Builders and construction variables for sun compilers to an Environment."""
    defaulttoolpath = SCons.Tool.DefaultToolpath
    try:
        SCons.Tool.DefaultToolpath = []
        # load default sunlink tool and extend afterwards
        env.Tool('sunlink')
    finally:
        SCons.Tool.DefaultToolpath = defaulttoolpath

    env['SMARTLINK'] = sun_smart_link
    env['LINK'] = "$SMARTLINK"

    platf = env['PLATFORM']

    setupBuildTools.registerCallback('MT_OPTIONS', lambda env: env.AppendUnique(LINKFLAGS='-mt') )
    # do not use rpath
    setupBuildTools.registerCallback('RPATH_OPTIONS', lambda env: env.AppendUnique(LINKFLAGS='-norunpath') )
    setupBuildTools.registerCallback('LINKLIBS', lambda env: env.AppendUnique(LIBS=['socket', 'resolv', 'posix4', 'aio']) )

    def bwopt(bitwidth):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    setupBuildTools.registerCallback('BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique(LINKFLAGS=bwopt(bitwidth) ) )
    setupBuildTools.registerCallback('STL_OPTIONS', lambda env: env.AppendUnique(LINKFLAGS='-library=stlport4' ) )

    def iostreamOpt(env, usestdiostream):
        ## iostream library means "classic", but we want to use the std
        if usestdiostream:
            env.AppendUnique(LINKFLAGS='-library=no%iostream')
    setupBuildTools.registerCallback('IOSTREAM_OPTIONS', iostreamOpt )


def exists(env):
    return None
