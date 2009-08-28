"""SCons.Tool.g++

Tool-specific initialization for g++.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

import os.path
import re, pdb
import subprocess

import SCons.Tool
import SCons.Util
import setupBuildTools

compilers = ['g++']

def generate(env):
    """Add Builders and construction variables for g++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    SCons.Tool.Tool('c++')(env)

    if env.get('_CXXPREPEND_'):
        compilers.insert(0, env.get('_CXXPREPEND_'))
    env['CXX'] = env.Detect(compilers)

    # platform specific settings
    if env['PLATFORM'] == 'aix':
        env['SHCXXFLAGS'] = SCons.Util.CLVar('$CXXFLAGS -mminimal-toc')
        env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1
        env['SHOBJSUFFIX'] = '$OBJSUFFIX'
    elif env['PLATFORM'] == 'hpux':
        env['SHOBJSUFFIX'] = '.pic.o'
    elif env['PLATFORM'] == 'sunos':
        env['SHOBJSUFFIX'] = '.pic.o'
    # determine compiler version
    if env['CXX']:
        #pipe = SCons.Action._subproc(env, [env['CXX'], '-dumpversion'],
        pipe = SCons.Action._subproc(env, [env['CXX'], '--version'],
                                     stdin = 'devnull',
                                     stderr = 'devnull',
                                     stdout = subprocess.PIPE)
        if pipe.wait() != 0: return
        # -dumpversion was added in GCC 3.0.  As long as we're supporting
        # GCC versions older than that, we should use --version and a
        # regular expression.
        #line = pipe.stdout.read().strip()
        #if line:
        #    env['CXXVERSION'] = line
        line = pipe.stdout.readline()
        match = re.search(r'(\s+)([0-9]+(\.[0-9]+)+)', line)
        if match:
            env['CXXVERSION'] = match.group(2)

        ## own extension
        tFile = os.path.join(SCons.Script.Dir('.').abspath, '.x1y2')
        outFile = os.path.join(SCons.Script.Dir('.').abspath, '.gugus')
        try:
            outf = open(tFile,'w')
            outf.write('#include <cstdlib>\nint main(){}')
            outf.close()
        except: pass
        pipe = SCons.Action._subproc(env, [env['CXX'], '-v', '-xc++', tFile, '-o', outFile],
                                     stdin = 'devnull',
                                     stderr = subprocess.PIPE,
                                     stdout = subprocess.PIPE)
        pRet = pipe.wait()
        os.remove(tFile)
        os.remove(outFile)
        if pRet != 0:
            print "pipe error:",pRet
            return
        pout = pipe.stderr.read()
        reIncl = re.compile('#include <\.\.\.>.*:$\s((^ .*\s)*)', re.M)
        match = reIncl.search(pout)
        sysincludes=[]
        if match:
            for it in re.finditer("^ (.*)$", match.group(1), re.M):
                sysincludes.append(it.groups()[0])
        if sysincludes:
            env['SYSINCLUDES'] = sysincludes

    setupBuildTools.registerCallback('MT_OPTIONS', lambda env: env.AppendUnique(CPPDEFINES=['_POSIX_PTHREAD_SEMANTICS']) )
    setupBuildTools.registerCallback('MT_OPTIONS', lambda env: env.AppendUnique(CPPDEFINES=['_REENTRANT']) )
    setupBuildTools.registerCallback('DEBUG_OPTIONS', lambda env: env.AppendUnique(CXXFLAGS=['-g']) )
    setupBuildTools.registerCallback('BITWIDTH_OPTIONS', lambda env, bitwidth: env.AppendUnique(CCFLAGS='-m'+bitwidth) )
    setupBuildTools.registerCallback('LARGEFILE_OPTIONS', lambda env: env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE']) )

def exists(env):
    if env.get('_CXXPREPEND_'):
        compilers.insert(0, env.get('_CXXPREPEND_'))
    return env.Detect(compilers)
