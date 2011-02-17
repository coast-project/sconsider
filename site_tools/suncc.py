"""SCons.Tool.suncc

Tool-specific initialization for Sun Solaris (Forte) CC and cc.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.
"""

import SCons.Util
import SCons.Tool

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

    env.AppendUnique( CFLAGS = '-mt' )
    def bwopt( bitwidth ):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    env.AppendUnique( CFLAGS = bwopt( env['ARCHBITS'] ) )

    if not SCons.Script.GetOption( 'no-largefilesupport' ):
        env.AppendUnique( CPPDEFINES = ['_LARGEFILE64_SOURCE'] )

    buildmode = SCons.Script.GetOption( 'buildcfg' )
    if buildmode == 'debug':
        pass
    elif buildmode == 'optimized':
        env.AppendUnique( CFLAGS = ['-fast', '-xbinopt=prepare'] )
    elif buildmode == 'profile':
        env.AppendUnique( CFLAGS = ['-xpg'] )

    warnlevel = SCons.Script.GetOption( 'warnlevel' )
    if warnlevel == 'medium' or warnlevel == 'full':
        env.AppendUnique( CFLAGS = ['+w', '-xport64=implicit'] )
    if warnlevel == 'full':
        env.AppendUnique( CFLAGS = [] )

def exists( env ):
    return env.Detect( 'CC' )

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
