"""SCons.Tool.gcc

Tool-specific initialization for gcc.

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

import os
import re, pdb
import subprocess

import SCons.Util
import SCons.Tool

compilers = ['gcc', 'cc']

def generate( env ):
    """Add Builders and construction variables for gcc to an Environment."""

    SCons.Tool.Tool( 'cc' )( env )

    if env.get( '_CCPREPEND_' ):
        compilers.insert( 0, env.get( '_CCPREPEND_' ) )
    env['CC'] = env.Detect( compilers ) or 'gcc'
    if env['PLATFORM'] in ['cygwin', 'win32']:
        env['SHCCFLAGS'] = SCons.Util.CLVar( '$CCFLAGS' )
    else:
        env['SHCCFLAGS'] = SCons.Util.CLVar( '$CCFLAGS -fPIC' )
    # determine compiler version
    gccfss=False
    if env['CC']:
        #pipe = SCons.Action._subproc(env, [env['CC'], '-dumpversion'],
        pipe = SCons.Action._subproc( env, [env['CC'], '--version'],
                                     stdin = 'devnull',
                                     stderr = 'devnull',
                                     stdout = subprocess.PIPE )
        if pipe.wait() != 0: return
        # -dumpversion was added in GCC 3.0.  As long as we're supporting
        # GCC versions older than that, we should use --version and a
        # regular expression.
        #line = pipe.stdout.read().strip()
        #if line:
        #    env['CCVERSION'] = line
        line = pipe.stdout.readline()
        versionmatch = re.search( r'(\s+)([0-9]+(\.[0-9]+)+)', line )
        gccfssmatch = re.search( r'(\(gccfss\))', line )
        if versionmatch:
            env['CCVERSION'] = versionmatch.group( 2 )
        if gccfssmatch:
            env['CCFLAVOUR'] = gccfssmatch.group( 1 )
            gccfss=True

        ## own extension to detect system include paths
        fName = '.code2Compile'
        tFile = os.path.join( SCons.Script.Dir( '.' ).abspath, fName )
        outFile = os.path.join( SCons.Script.Dir( '.' ).abspath, fName+'.o' )
        try:
            outf = open( tFile, 'w' )
            outf.write( '#include <stdlib.h>\nint main(){return 0;}' )
            outf.close()
        except:
            print "failed to create compiler input file, check folder permissions and retry"
            return
        pipe = SCons.Action._subproc( env, [env['CC'], '-v', '-xc', tFile, '-o', outFile, '-m'+env['ARCHBITS']],
                                     stdin = 'devnull',
                                     stderr = subprocess.PIPE,
                                     stdout = subprocess.PIPE )
        pRet = pipe.wait()
        os.remove( tFile )
        try: os.remove( outFile )
        except: print outFile,"could not be deleted, check compiler output"
        if pRet != 0:
            print "---- stdout ----"
            print pipe.stdout.read()
            print "---- stderr ----"
            print pipe.stderr.read()
            print "failed to compile object, return code:", pRet
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
    env.AppendUnique( CPPDEFINES = ['_POSIX_PTHREAD_SEMANTICS', '_REENTRANT'] )
    env.AppendUnique( CCFLAGS = '-m' + env['ARCHBITS'] )
    if not SCons.Script.GetOption( 'no-largefilesupport' ):
        env.AppendUnique( CPPDEFINES = ['_LARGEFILE64_SOURCE'] )

    buildmode = SCons.Script.GetOption( 'buildcfg' )
    if buildmode == 'debug':
        env.AppendUnique( CFLAGS = [ '-ggdb3' if str( platf ) == 'sunos' else '-g'] )
    elif buildmode == 'optimized':
        if str( platf ) == 'sunos':
            env.AppendUnique( CFLAGS = ['-O0'] )
        else:
            env.AppendUnique( CFLAGS = ['-O0', '-fdefer-pop', '-fmerge-constants', '-fthread-jumps', '-fguess-branch-probability', '-fcprop-registers'] )
    elif buildmode == 'profile':
        env.AppendUnique( CFLAGS = ['-fprofile'] )

    warnlevel = SCons.Script.GetOption( 'warnlevel' )
    if warnlevel == 'medium' or warnlevel == 'full':
        env.AppendUnique( CFLAGS = ['-Wall', '-Wunused', '-Wno-system-headers', '-Wreturn-type'] )
    if warnlevel == 'full':
        env.AppendUnique( CFLAGS = ['-Wconversion', '-Wundef', '-Wwrite-strings'] )

def exists( env ):
    if env.get( '_CCPREPEND_' ):
        compilers.insert( 0, env.get( '_CCPREPEND_' ) )
    return env.Detect( compilers )
