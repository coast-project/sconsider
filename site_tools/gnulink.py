"""SCons.Tool.gnulink"""

import sys, pdb, os
import SCons.Util
import SCons.Tool
import SomeUtils
import setupBuildTools

def FileNodeComparer( left, right ):
    """Specialized implementation of file node sorting
    based on the fact that config_ files must get placed
    before any other object on the linker command line"""
    nleft = left.srcnode().abspath
    nright = right.srcnode().abspath
    ldirname, lbasename = os.path.split( nleft )
    rdirname, rbasename = os.path.split( nright )
    # l < r, -1
    # l == r, 0
    # l > r, 1
    if lbasename.startswith( 'config_' ): return - 1
    elif rbasename.startswith( 'config_' ): return 1
    return cmp( nleft, nright )

SomeUtils.FileNodeComparer = FileNodeComparer

def generate( env ):
    """Add Builders and construction variables for gnu compilers to an Environment."""
    defaulttoolpath = SCons.Tool.DefaultToolpath
    try:
        SCons.Tool.DefaultToolpath = []
        # load default link tool and extend afterwards
        env.Tool( 'gnulink' )
    finally:
        SCons.Tool.DefaultToolpath = defaulttoolpath

    platf = env['PLATFORM']
    if str( platf ) not in ["cygwin", "win32"]:
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( LINKFLAGS = ['-nodefaultlibs'] ) )
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( LIBS = ['m', 'gcc', 'gcc_s'] ) )
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( LIBS = ['dl', 'c'] ) )
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( LIBS = ['nsl'] ) )
    elif str( platf ) == "win32":
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( LINKFLAGS = ['-Wl,--enable-auto-import'] ) )
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( SHLINKFLAGS = ['-Wl,--export-all-symbols'] ) )
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( LIBS = ['ws2_32'] ) )
    orig_smart_link = env['SMARTLINK']
    def smart_link(source, target, env, for_signature):
        try:
            cplusplus = sys.modules['SCons.Tool.c++']
            if cplusplus.iscplusplus( source ):
                env.AppendUnique( LIBS = ['stdc++'] )
        except:
            pass
        return orig_smart_link(source, target, env, for_signature)
    setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.Replace(SMARTLINK = smart_link))

    setupBuildTools.registerCallback( 'BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique( LINKFLAGS = '-m' + bitwidth ) )

    if str( platf ) not in ["cygwin", "win32"]:
        setupBuildTools.registerCallback( 'LAZYLINK_OPTIONS', lambda env: env.Append( _NONLAZYLINKFLAGS = '-z defs -z now --no-undefined ' ) )
    if str( platf ) == "sunos":
        # this lib is needed when using sun-CC or gcc on sunos systems
        setupBuildTools.registerCallback( 'LINKLIBS', lambda env: env.AppendUnique( LIBS = ['socket', 'resolv', 'posix4', 'aio'] ) )

    setupBuildTools.registerCallback( 'DEBUG_OPTIONS', lambda env: env.AppendUnique( LINKFLAGS = ['-v'] ) )
    setupBuildTools.registerCallback( 'DEBUG_OPTIONS', lambda env: env.AppendUnique( SHLINKFLAGS = ['-v'] ) )

    if str( platf ) == "sunos":
        setupBuildTools.registerCallback( 'DEBUG_OPTIONS', lambda env: env.AppendUnique( SHLINKFLAGS = ['-ggdb3'] ) )
    else:
        setupBuildTools.registerCallback( 'DEBUG_OPTIONS', lambda env: env.AppendUnique( SHLINKFLAGS = ['-g'] ) )

    setupBuildTools.registerCallback( 'PROFILE_OPTIONS', lambda env: env.AppendUnique( LINKFLAGS = ['-fprofile'] ) )
    setupBuildTools.registerCallback( 'PROFILE_OPTIONS', lambda env: env.AppendUnique( SHLINKFLAGS = ['-fprofile'] ) )

def exists( env ):
    return None
