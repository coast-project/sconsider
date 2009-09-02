"""SCons.Tool.suncc

Tool-specific initialization for Sun Solaris (Forte) CC and cc.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.
"""

import SCons.Util
import SCons.Tool
import setupBuildTools

def generate( env ):
    """
    Add Builders and construction variables for Forte C and C++ compilers
    to an Environment.
    """

    SCons.Tool.Tool( 'cc' )( env )

    env['CXX'] = 'CC'
    env['SHCCFLAGS'] = SCons.Util.CLVar( '$CCFLAGS -KPIC' )
    env['SHOBJPREFIX'] = 'so_'
    env['SHOBJSUFFIX'] = '.o'

    setupBuildTools.registerCallback( 'MT_OPTIONS', lambda env: env.AppendUnique( CFLAGS = '-mt' ) )
    def bwopt( bitwidth ):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    setupBuildTools.registerCallback( 'BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique( CFLAGS = bwopt( bitwidth ) ) )
    setupBuildTools.registerCallback( 'LARGEFILE_OPTIONS', lambda env: env.AppendUnique( CPPDEFINES = ['_LARGEFILE64_SOURCE'] ) )

    setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CFLAGS = ['-fast'] ) )
    setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CFLAGS = ['-xbinopt=prepare'] ) )

    setupBuildTools.registerCallback( 'PROFILE_OPTIONS', lambda env: env.AppendUnique( CFLAGS = ['-xpg'] ) )

    def setupWarnings( env, warnlevel ):
        if warnlevel == 'medium' or warnlevel == 'full':
            env.AppendUnique( CFLAGS = ['+w', '-xport64=implicit'] )
        if warnlevel == 'full':
            env.AppendUnique( CFLAGS = [] )

    setupBuildTools.registerCallback( 'WARN_OPTIONS', setupWarnings )

def exists( env ):
    return env.Detect( 'CC' )

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
