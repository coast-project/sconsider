"""SConsider.site_tools.gcc.

SConsider-specific gcc tool initialization
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import os
import re
from logging import getLogger
import SCons.Tool
import SCons.Util
from SConsider.PopenHelper import ProcessRunner
logger = getLogger(__name__)

compilers = ['gcc', 'cc']


def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""

    SCons.Tool.Tool('cc')(env)

    if env.get('_CCPREPEND_'):
        compilers.insert(0, env.get('_CCPREPEND_'))
    env['CC'] = compiler_subject = env.Detect(compilers) or 'gcc'
    if env['PLATFORM'] in ['cygwin', 'win32']:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS')
    else:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')
    # determine compiler version
    # ensure we have getBitwidth() available
    if 'setupBuildTools' not in env['TOOLS']:
        raise SCons.Errors.UserError('setupBuildTools is required for\
 initialization')

    bitwidth = env.getBitwidth()
    if compiler_subject:
        _cmd = [compiler_subject, '--version']
        _out = ''
        _err = ''
        with ProcessRunner(_cmd, timeout=20, seconds_to_wait=0.1) as executor:
            for out, err in executor:
                _out += out
                _err += err

        if executor.returncode != 0:
            return
        # -dumpversion was added in GCC 3.0.  As long as we're supporting
        # GCC versions older than that, we should use --version and a
        # regular expression.
        # line = pipe.stdout.read().strip()
        # if line:
        #    env['CCVERSION'] = line
        line = _out.strip()
        versionmatch = re.search(r'(\s+)([0-9]+(\.[0-9]+)+)', line)
        gccfssmatch = re.search(r'(\(gccfss\))', line)
        if versionmatch:
            env['CCVERSION'] = versionmatch.group(2)
        if gccfssmatch:
            env['CCFLAVOUR'] = gccfssmatch.group(1)

        # own extension to detect system include paths
        import time
        fName = '.code2Compile.c.' + str(time.time()) + '.' + str(os.getpid())
        tFile = os.path.join(SCons.Script.Dir('.').get_abspath(), fName)
        outFile = os.path.join(SCons.Script.Dir('.').get_abspath(), fName + '.o')
        try:
            outf = open(tFile, 'w')
            outf.write('#include <stdlib.h>\nint main(){return 0;}')
            outf.close()
        except:
            logger.error("failed to create compiler input file, check folder permissions and retry",
                         exc_info=True)
            return
        _cmd = [compiler_subject, '-v', '-xc', tFile, '-o', outFile, '-m' + bitwidth]
        _out = ''
        _err = ''
        with ProcessRunner(_cmd, timeout=20, seconds_to_wait=0.1) as executor:
            for out, err in executor:
                _out += out
                _err += err

        text_to_join = ['---- stdout ----', _out, '---- stderr ----', _err]
        build_output = os.linesep.join(text_to_join)
        logger.debug(build_output)

        try:
            for rfile in [tFile, outFile]:
                os.remove(rfile)
        except:
            logger.error("{0} {1}, check compiler output for errors:".format(
                rfile, 'could not be deleted' if os.path.exists(rfile) else 'was not created') + os.linesep +
                         build_output,
                         exc_info=True)
            raise SCons.Errors.UserError(
                'Build aborted, {0} compiler detection failed!'.format(compiler_subject))
        if executor.returncode != 0:
            logger.error("compile command failed with return code {0}:".format(proc.returncode) + os.linesep +
                         build_output)
            raise SCons.Errors.UserError(
                'Build aborted, {0} compiler detection failed!'.format(compiler_subject))
        reIncl = re.compile(r'#include <\.\.\.>.*:$\s((^ .*\s)*)', re.M)
        match = reIncl.search(_err)
        sysincludes = []
        if match:
            for it in re.finditer("^ (.*)$", match.group(1), re.M):
                sysincludes.append(it.groups()[0])
        if sysincludes:
            env.AppendUnique(SYSINCLUDES=sysincludes)

    platf = env['PLATFORM']
    env.AppendUnique(CPPDEFINES=['_POSIX_PTHREAD_SEMANTICS', '_REENTRANT'])
    env.AppendUnique(CCFLAGS='-m' + bitwidth)
    if str(platf) == 'darwin':
        if bitwidth == '32':
            env.AppendUnique(CCFLAGS=['-arch', 'i386'])
        else:
            env.AppendUnique(CCFLAGS=['-arch', 'x86_64'])

    if not SCons.Script.GetOption('no-largefilesupport'):
        env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE'])

    buildmode = env.getBuildCfg()
    if buildmode in ['debug', 'profile']:
        env.AppendUnique(CFLAGS=['-ggdb3' if str(platf) == 'sunos' else '-g'])
    if buildmode == 'debug':
        pass
    elif buildmode == 'optimized':
        env.AppendUnique(CFLAGS=['-O0'])
    elif buildmode == 'coverage':
        env.AppendUnique(CFLAGS=['-fprofile-arcs', '-ftest-coverage'])
    elif buildmode == 'profile':
        env.AppendUnique(CFLAGS=['-pg'])

    warnlevel = SCons.Script.GetOption('warnlevel')
    if warnlevel == 'medium' or warnlevel == 'full':
        env.AppendUnique(CFLAGS=['-Wall', '-Wunused', '-Wno-system-headers', '-Wreturn-type'])
    if warnlevel == 'full':
        env.AppendUnique(CFLAGS=['-Wconversion', '-Wundef', '-Wwrite-strings'])


def exists(env):
    if env.get('_CCPREPEND_'):
        compilers.insert(0, env.get('_CCPREPEND_'))
    return env.Detect(compilers)
