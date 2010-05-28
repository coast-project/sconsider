"""SCons.Tool.g++

Tool-specific initialization for g++.

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

import os.path
import re, pdb
import subprocess

import SCons.Util
import SCons.Tool
import setupBuildTools

compilers = ['g++']

def generate( env ):
    """Add Builders and construction variables for g++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders( env )

    SCons.Tool.Tool( 'c++' )( env )

    if env.get( '_CXXPREPEND_' ):
        compilers.insert( 0, env.get( '_CXXPREPEND_' ) )
    env['CXX'] = env.Detect( compilers )

    # platform specific settings
    if env['PLATFORM'] == 'aix':
        env['SHCXXFLAGS'] = SCons.Util.CLVar( '$CXXFLAGS -mminimal-toc' )
        env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1
        env['SHOBJSUFFIX'] = '$OBJSUFFIX'
    elif env['PLATFORM'] == 'hpux':
        env['SHOBJSUFFIX'] = '.pic.o'
    elif env['PLATFORM'] == 'sunos':
        env['SHOBJSUFFIX'] = '.pic.o'
    # determine compiler version
    gccfss=False
    if env['CXX']:
        #pipe = SCons.Action._subproc(env, [env['CXX'], '-dumpversion'],
        pipe = SCons.Action._subproc( env, [env['CXX'], '--version'],
                                     stdin = 'devnull',
                                     stderr = 'devnull',
                                     stdout = subprocess.PIPE )
        if pipe.wait() != 0: return
        # -dumpversion was added in GCC 3.0.  As long as we're supporting
        # GCC versions older than that, we should use --version and a
        # regular expression.
        #line = pipe.stdout.read().strip()
        #if line:
        #    env['CXXVERSION'] = line
        line = pipe.stdout.readline()
        versionmatch = re.search( r'(\s+)([0-9]+(\.[0-9]+)+)', line )
        gccfssmatch = re.search( r'(\(gccfss\))', line )
        if versionmatch:
            env['CXXVERSION'] = versionmatch.group( 2 )
        if gccfssmatch:
            env['CXXFLAVOUR'] = gccfssmatch.group( 1 )
            gccfss=True

        ## own extension to detect system include paths
        tFile = os.path.join( SCons.Script.Dir( '.' ).abspath, '.x1y2' )
        outFile = os.path.join( SCons.Script.Dir( '.' ).abspath, '.gugus' )
        try:
            outf = open( tFile, 'w' )
            outf.write( '#include <cstdlib>\nint main(){}' )
            outf.close()
        except: pass
        pipe = SCons.Action._subproc( env, [env['CXX'], '-v', '-xc++', tFile, '-o', outFile, '-m'+env['ARCHBITS']],
                                     stdin = 'devnull',
                                     stderr = subprocess.PIPE,
                                     stdout = subprocess.PIPE )
        pRet = pipe.wait()
        os.remove( tFile )
        os.remove( outFile )
        if pRet != 0:
            print "pipe error:", pRet
            return
        pout = pipe.stderr.read()
        reIncl = re.compile( '#include <\.\.\.>.*:$\s((^ .*\s)*)', re.M )
        match = reIncl.search( pout )
        sysincludes = []
        if match:
            for it in re.finditer( "^ (.*)$", match.group( 1 ), re.M ):
                sysincludes.append( it.groups()[0] )
        if sysincludes:
            env.AppendUnique( SYSINCLUDES = sysincludes )

    platf = env['PLATFORM']
    setupBuildTools.registerCallback( 'MT_OPTIONS', lambda env: env.AppendUnique( CPPDEFINES = ['_POSIX_PTHREAD_SEMANTICS'] ) )
    setupBuildTools.registerCallback( 'MT_OPTIONS', lambda env: env.AppendUnique( CPPDEFINES = ['_REENTRANT'] ) )

    setupBuildTools.registerCallback( 'BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique( CCFLAGS = '-m' + bitwidth ) )
    setupBuildTools.registerCallback( 'LARGEFILE_OPTIONS', lambda env: env.AppendUnique( CPPDEFINES = ['_LARGEFILE64_SOURCE'] ) )

    if str( platf ) == "sunos":
        setupBuildTools.registerCallback( 'DEBUG_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-ggdb3'] ) )
    else:
        setupBuildTools.registerCallback( 'DEBUG_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-g'] ) )

    if str( platf ) == "sunos":
        if gccfss:
            # at least until g++ 4.3.3 (gccfss), there is a bug #100 when using optimization levels above -O1
            # -> -fast option breaks creation of correct static initialization sequence
            setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-O1'] ) )
        else:
            setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-O3'] ) )
    else:
        setupBuildTools.registerCallback( 'OPTIMIZE_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-O3'] ) )

    setupBuildTools.registerCallback( 'PROFILE_OPTIONS', lambda env: env.AppendUnique( CXXFLAGS = ['-fprofile'] ) )

    def setupWarnings( env, warnlevel ):
        if warnlevel == 'medium' or warnlevel == 'full':
            env.AppendUnique( CXXFLAGS = [
                '-Waddress',                #<! Warn about suspicious uses of memory addresses
                '-Wall',                    #<! Enable most warning messages
                '-Wdeprecated',
                '-Wendif-labels',
                '-Wno-system-headers',
                '-Woverloaded-virtual',
                '-Wpointer-arith',          #<! Warn about function pointer arithmetic
                '-Wreturn-type',
                '-Wshadow',
                '-Wundef',                  #<! Warn if an undefined macro is used in an #if directive
            ] )
        if warnlevel == 'full':
            env.AppendUnique( CXXFLAGS = [
                '-Wcast-qual',              #<! Warn about casts which discard qualifiers
                '-Wconversion',             #<! Warn for implicit type conversions that may change a value
                '-Weffc++',                 #<! Warn about violations of Effective C++ style rules
                '-Wignored-qualifiers',     #<! Warn whenever type qualifiers are ignored.
                '-Wold-style-cast',         #<! Warn if a C-style cast is used in a program
            ] )

    setupBuildTools.registerCallback( 'WARN_OPTIONS', setupWarnings )

def exists( env ):
    if env.get( '_CXXPREPEND_' ):
        compilers.insert( 0, env.get( '_CXXPREPEND_' ) )
    return env.Detect( compilers )
