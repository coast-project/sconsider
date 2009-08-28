"""SCons.Tool.suncc

Tool-specific initialization for Sun Solaris (Forte) CC and cc.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.
"""

import SCons.Util
import SCons.Tool
import setupBuildTools

def generate(env):
    """
    Add Builders and construction variables for Forte C and C++ compilers
    to an Environment.
    """

    SCons.Tool.Tool('cc')(env)

    env['CXX']          = 'CC'
    env['SHCCFLAGS']    = SCons.Util.CLVar('$CCFLAGS -KPIC')
    env['SHOBJPREFIX']  = 'so_'
    env['SHOBJSUFFIX']  = '.o'

    setupBuildTools.registerCallback('MT_OPTIONS', lambda env: env.AppendUnique(CCFLAGS='-mt') )
    def bwopt(bitwidth):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    setupBuildTools.registerCallback('BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique(CCFLAGS=bwopt(bitwidth) ) )
    setupBuildTools.registerCallback('STL_OPTIONS', lambda env, bitwidth: env.AppendUnique(CCFLAGS='-library=stlport4' ) )
    def iostreamOpt(env, usestdiostream):
        ## iostream library means "classic", but we want to use the std
        if usestdiostream:
            env.AppendUnique(CCFLAGS='-library=no%iostream')
    setupBuildTools.registerCallback('IOSTREAM_OPTIONS', iostreamOpt )
    setupBuildTools.registerCallback('LARGEFILE_OPTIONS', lambda env: env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE']) )

def exists(env):
    return env.Detect('CC')

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
