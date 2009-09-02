"""SCons.Tool.sunc++

Tool-specific initialization for C++ on SunOS / Solaris.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""


import os.path

import SCons
import setupBuildTools

# use the package installer tool lslpp to figure out where cppc and what
# version of it is installed
def get_cppc( env ):
    cxx = env.get( 'CXX', None )
    if cxx:
        cppcPath = os.path.dirname( cxx )
    else:
        cppcPath = None

    cppcVersion = None

    pkginfo = env.subst( '$PKGINFO' )
    pkgchk = env.subst( '$PKGCHK' )

    def look_pkg_db( pkginfo = pkginfo, pkgchk = pkgchk ):
        version = None
        path = None
        for package in ['SPROcpl']:
            cmd = "%s -l %s 2>/dev/null | grep '^ *VERSION:'" % ( pkginfo, package )
            line = os.popen( cmd ).readline()
            if line:
                version = line.split()[-1]
                cmd = "%s -l %s 2>/dev/null | grep '^Pathname:.*/bin/CC$' | grep -v '/SC[0-9]*\.[0-9]*/'" % ( pkgchk, package )
                line = os.popen( cmd ).readline()
                if line:
                    path = os.path.dirname( line.split()[-1] )
                    break

        return path, version

    path, version = look_pkg_db()
    if path and version:
        cppcPath, cppcVersion = path, version

    return ( cppcPath, 'CC', 'CC', cppcVersion )

def generate( env ):
    """Add Builders and construction variables for SunPRO C++."""
    path, cxx, shcxx, version = get_cppc( env )
    if path:
        cxx = os.path.join( path, cxx )
        shcxx = os.path.join( path, shcxx )

    SCons.Tool.Tool( 'c++' )( env )

    env['CXX'] = cxx
    env['SHCXX'] = shcxx
    env['CXXVERSION'] = version
    env['SHCXXFLAGS'] = SCons.Util.CLVar( '$CXXFLAGS -KPIC' )
    env['SHOBJPREFIX'] = 'so_'
    env['SHOBJSUFFIX'] = '.o'

    setupBuildTools.registerCallback( 'MT_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = '-mt' ) )
    def bwopt( bitwidth ):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    setupBuildTools.registerCallback( 'BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique( CXXFLAGS = bwopt( bitwidth ) ) )
    setupBuildTools.registerCallback( 'STL_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = '-library=stlport4' ) )

    def iostreamOpt( env, usestdiostream ):
        ## iostream library means "classic", but we want to use the std
        if usestdiostream:
            env.AppendUnique( CXXFLAGS = '-library=no%iostream' )
    setupBuildTools.registerCallback( 'IOSTREAM_OPTIONS', iostreamOpt )
    setupBuildTools.registerCallback( 'LARGEFILE_OPTIONS', lambda env: env.AppendUnique( CPPDEFINES = ['_LARGEFILE64_SOURCE'] ) )

    setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-fast'] ) )
    setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-xbinopt=prepare'] ) )

    setupBuildTools.registerCallback( 'PROFILE_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-xpg'] ) )

    def setupWarnings( env, warnlevel ):
        if warnlevel == 'medium' or warnlevel == 'full':
            env.AppendUnique( CXXFLAGS = ['+w', '-xport64=implicit'] )
        if warnlevel == 'full':
            env.AppendUnique( CXXFLAGS = [] )

    setupBuildTools.registerCallback( 'WARN_OPTIONS', setupWarnings )

def exists( env ):
    path, cxx, shcxx, version = get_cppc( env )
    if path and cxx:
        cppc = os.path.join( path, cxx )
        if os.path.exists( cppc ):
            return cppc
    return None

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
