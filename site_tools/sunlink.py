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

import sys
import SCons.Util
import SCons.Tool

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
    SCons.Tool.DefaultToolpath = []
    # load default sunlink tool and extend afterwards
    env.Tool('sunlink')
    SCons.Tool.DefaultToolpath = defaulttoolpath

    env['SMARTLINK']   = sun_smart_link
    env['LINK']        = "$SMARTLINK"

def exists(env):
    return None