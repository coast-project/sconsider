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

def generate(env):
    """Add Builders and construction variables for g++ to an Environment."""

    defaulttoolpath = SCons.Tool.DefaultToolpath
    SCons.Tool.DefaultToolpath = []
    # load default tool and extend afterwards
    env.Tool('g++')
    SCons.Tool.DefaultToolpath = defaulttoolpath

    if env['CXX']:
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

def exists(env):
    return 1
