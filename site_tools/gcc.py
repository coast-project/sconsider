"""site_scons.site_tools.gcc

SConsider-specific gcc tool initialization

"""

#-----------------------------------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or modify it under the terms of
# the license that is included with this library/application in the file license.txt.
#-----------------------------------------------------------------------------------------------------

import os
import re
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
        import time
        fName = '.code2Compile.' + str(time.time())
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
    if str( platf ) == 'darwin':
        if env['ARCHBITS'] == '32':
            env.AppendUnique( CCFLAGS = ['-arch', 'i386'] )
        else:
            env.AppendUnique( CCFLAGS = ['-arch', 'x86_64'] )
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
