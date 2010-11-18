import pdb, os, platform
import SCons.Tool
import SCons.Script
from SCons.Script import AddOption, Dir, GetOption
import SConsider

import Callback
Callback.addCallbackFeature( __name__ )

added = None
cxxCompiler = None
ccCompiler = None

def checkCompiler( env, optionvalue, envVarName ):
    if not optionvalue:
        optionvalue = os.getenv( envVarName, None )
    if optionvalue:
        dirname = os.path.dirname( optionvalue )
        if dirname:
            env.PrependENVPath( 'PATH', dirname )
        basename = os.path.basename( optionvalue )
        return basename
    return None

def generate( env, **kw ):
    """Add build tools."""
    global added
    if not added:
        added = 1
        AddOption( '--with-cxx', dest = 'whichcxx', action = 'store', nargs = 1, type = 'string', default = None, metavar = 'PATH', help = 'fully qualified path and name to gnu g++ compiler' )
        AddOption( '--with-cc', dest = 'whichcc', action = 'store', nargs = 1, type = 'string', default = None, metavar = 'PATH', help = 'fully qualified path and name to gnu gcc compiler' )
        bitchoices = ['32', '64']
        bitdefault = '32'
        AddOption( '--archbits', dest = 'archbits', action = 'store', nargs = 1, type = 'choice', choices = bitchoices, default = bitdefault, metavar = 'OPTIONS', help = 'Select target bit width (if compiler supports it), ' + str( bitchoices ) + ', default=' + bitdefault )
        buildchoices = ['debug', 'optimized', 'profile']
        builddefault = 'optimized'
        AddOption( '--build-cfg', dest = 'buildcfg', action = 'store', nargs = 1, type = 'choice', choices = buildchoices, default = builddefault, metavar = 'OPTIONS', help = 'Select build configuration, ' + str( buildchoices ) + ', default=' + builddefault )
        langchoices = ['boost', 'c++0x', 'tr1']
        langdefault = 'boost'
        AddOption( '--use-lang-features', dest = 'whichlangfeat', action = 'store', nargs = 1, type = 'choice', choices = langchoices, default = langdefault, metavar = 'OPTIONS', help = 'Select which language features, ' + str( langchoices ) + ', default=' + langdefault )
        warnchoices = ['none', 'medium', 'full']
        warndefault = 'medium'
        AddOption( '--warnlevel', dest = 'warnlevel', action = 'store', nargs = 1, type = 'choice', choices = warnchoices, default = warndefault, metavar = 'OPTIONS', help = 'Select compilation warning level, one of ' + str( warnchoices ) + ', default=' + warndefault )
        AddOption( '--no-largefilesupport', dest = 'no-largefilesupport', action = 'store_true', help = 'Disable use of std libraries iostream headers' )

    platf = env['PLATFORM']
    cxxCompiler = checkCompiler( env, GetOption( 'whichcxx' ), 'CXX' )
    ccCompiler = checkCompiler( env, GetOption( 'whichcc' ), 'CC' )
    toolchainOverride = False
    if cxxCompiler:
        toolchainOverride = True
        env['_CXXPREPEND_'] = cxxCompiler
    if ccCompiler:
        toolchainOverride = True
        env['_CCPREPEND_'] = ccCompiler

    if toolchainOverride:
        # this section is needed to select gnu toolchain on sun systems, default is sunCC
        # -> see SCons.Tool.__init__.py tool_list method for explanation
        if str( platf ) == 'sunos':
            platf = None

    # if we are within cygwin and want to build a win32 target
    if "mingw" in GetOption( 'usetools' ):
        platf = "win32"

    # select language features
    langfeature = GetOption( 'whichlangfeat' )

    if langfeature == 'c++0x':
        env.AppendUnique( CPPDEFINES = ['USE_STD0X'] )
    elif langfeature == 'tr1':
        env.AppendUnique( CPPDEFINES = ['USE_TR1'] )

    # select target architecture bits
    bitwidth = GetOption( 'archbits' )
    env['ARCHBITS'] = bitwidth

    # tool initialization, previously done in <scons>/Tool/default.py
    for t in SCons.Tool.tool_list( platf, env ):
        SCons.Tool.Tool( t )( env )

    print 'using CXX compiler and version:', env['CXX'], '(' + env.get( 'CXXVERSION', 'unknown' ) + ')'
    print 'using CC compiler and version:', env['CC'], '(' + env.get( 'CCVERSION', 'unknown' ) + ')'

    platf = env['PLATFORM']

    # tell linker to only succeed when all external references can be resolved
    ##FIXME: attention the following is a workaround
    ##  because LINKFLAGS='-z defs' would lead to a string'ified "-z defs" in the linker command line
    env.Append( LINKFLAGS = ['$_NONLAZYLINKFLAGS'] )

#    elif str(platf) == "win32":
#        env.AppendUnique(CPPDEFINES=['WIN32', '_WIN32_WINNT=0x400'])
#        env.AppendUnique(CPPDEFINES=['_MSC_VER=$MSVC_VER'])

    # flags which influence compilation
    runCallback( 'MT_OPTIONS', env = env )
    runCallback( 'RPATH_OPTIONS', env = env )
    runCallback( 'LAZYLINK_OPTIONS', env = env )
    runCallback( 'LINKLIBS', env = env )
    runCallback( 'BITWIDTH_OPTIONS', env = env, bitwidth = bitwidth )
    runCallback( 'STL_OPTIONS', env = env )
    if not GetOption( 'no-largefilesupport' ):
        runCallback( 'LARGEFILE_OPTIONS', env = env )
    runCallback( 'WARN_OPTIONS', env = env, warnlevel = GetOption( 'warnlevel' ) )

    buildmode = GetOption( 'buildcfg' )
    if buildmode == 'debug':
        env.AppendUnique( CPPDEFINES = ['DEBUG'] )
        runCallback( 'DEBUG_OPTIONS', env = env )
        registerCallback( 'VARIANT_SUFFIX', lambda env: env.Append( VARIANT_SUFFIX = ['_dbg'] ) )
    elif buildmode == 'optimized':
        runCallback( 'OPTIMIZE_OPTIONS', env = env )
    elif buildmode == 'profile':
        runCallback( 'PROFILE_OPTIONS', env = env )

    if str( platf ) == "cygwin":
        osver = tuple( [int( x ) for x in platform.system().split( '-' )[1].split( '.' )] )
    elif str( platf ) == 'sunos':
        osver = tuple( [int( x ) for x in platform.release().split( '.' )] )
    elif str( platf ) == 'darwin':
        osver = tuple( [int( x ) for x in platform.release().split( '.' )] )
    elif platform.system() == 'Linux':
        osver = tuple( [int( x ) for x in platform.release().split( '-' )[0].split( '.' )] )
    elif str( platf ) == 'win32':
        osver = tuple( [int( x ) for x in platform.version().split( '.' )] )

    for val, valname in zip( osver, ['OS_RELMAJOR', 'OS_RELMINOR', 'OS_RELMINSUB'] ):
        env.AppendUnique( CCFLAGS = ['-D' + valname + '=' + str( val )] )

    if str( platf ) == 'sunos':
        env.AppendUnique( CCFLAGS = ['-DOS_SYSV'] )
        env.AppendUnique( CCFLAGS = ['-DOS_SOLARIS'] )
    elif str( platf ) == 'darwin':
        env.AppendUnique( CCFLAGS = ['-DOS_SYSV'] )
    elif platform.system() == 'Linux':
        env.AppendUnique( CCFLAGS = ['-DOS_SYSV'] )
        env.AppendUnique( CCFLAGS = ['-DOS_LINUX'] )

    def variantSuffix( env ):
        env.Append( VARIANT_SUFFIX = ['-' + bitwidth] )
        runCallback( 'VARIANT_SUFFIX', env = env )
    SConsider.registerCallback( 'VARIANT_SUFFIX', variantSuffix )

    if "mingw" in env["TOOLS"]:
        # mingw appends .exe if a Program target is given without extension but scons still
        # returns the target without extension. Because depending targets therefore wouldn't
        # find the target this emitter was created as a workaround.
        # => see http://scons.tigris.org/issues/show_bug.cgi?id=2712
        def appendexe(target, source, env):
            newtgt = []
            for t in target:
                newtgt.append(SCons.Util.adjustixes(str(t), env.subst('$PROGPREFIX'), env.subst('$PROGSUFFIX')))
            return newtgt, source
        env["PROGEMITTER"] = appendexe

        # find and append msys' bin path in order to execute shell scripts using subprocess.Popen
        shexe = "sh.exe"
        shpath = env.WhereIs(shexe) or SCons.Util.WhereIs(shexe)
        msysdir = os.path.dirname(shpath)
        env.PrependENVPath('PATH', msysdir)

def exists( env ):
    return 1
