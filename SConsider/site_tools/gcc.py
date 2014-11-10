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
import subprocess
import SCons.Util
import SCons.Tool
from logging import getLogger
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
        # pipe = SCons.Action._subproc(env, [compiler_subject, '-dumpversion'],
        pipe = SCons.Action._subproc(env, [compiler_subject, '--version'],
                                     stdin='devnull',
                                     stderr='devnull',
                                     stdout=subprocess.PIPE)
        if pipe.wait() != 0:
            return
        # -dumpversion was added in GCC 3.0.  As long as we're supporting
        # GCC versions older than that, we should use --version and a
        # regular expression.
        # line = pipe.stdout.read().strip()
        # if line:
        #    env['CCVERSION'] = line
        line = pipe.stdout.readline()
        versionmatch = re.search(r'(\s+)([0-9]+(\.[0-9]+)+)', line)
        gccfssmatch = re.search(r'(\(gccfss\))', line)
        if versionmatch:
            env['CCVERSION'] = versionmatch.group(2)
        if gccfssmatch:
            env['CCFLAVOUR'] = gccfssmatch.group(1)

        # own extension to detect system include paths
        import time
        fName = '.code2Compile.' + str(time.time())
        tFile = os.path.join(SCons.Script.Dir('.').get_abspath(), fName)
        outFile = os.path.join(SCons.Script.Dir('.').get_abspath(), fName + '.o')
        try:
            outf = open(tFile, 'w')
            outf.write('#include <stdlib.h>\nint main(){return 0;}')
            outf.close()
        except:
            logger.error(
                "failed to create compiler input file, check folder permissions and retry",
                exc_info=True)
            return
        pipe = SCons.Action._subproc(env,
                                     [compiler_subject,
                                      '-v',
                                      '-xc',
                                      tFile,
                                      '-o',
                                      outFile,
                                      '-m' + bitwidth],
                                     stdin='devnull',
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
        pRet = pipe.wait()
        os.remove(tFile)

        def formattedStdOutAndStdErr(the_pipe, prefix_text=None):
            text_to_join = ['---- stdout ----',
                            the_pipe.stdout.read(),
                            '---- stderr ----',
                            the_pipe.stderr.read()]
            if prefix_text:
                text_to_join[:0] = [prefix_text]
            return os.linesep.join(text_to_join)
        try:
            os.remove(outFile)
        except:
            logger.error(
                formattedStdOutAndStdErr(
                    pipe,
                    prefix_text="{0} {1}, check compiler output for errors:".format(
                        outFile,
                        'could not be deleted' if os.path.exists(outFile) else 'was not created')),
                exc_info=True)
            raise SCons.Errors.UserError(
                'Build aborted, {0} compiler detection failed!'.format(
                    compiler_subject))
        if pRet != 0:
            logger.error(
                formattedStdOutAndStdErr(
                    pipe,
                    prefix_text="compile command failed with return code {0}:".format(pRet)))
            raise SCons.Errors.UserError(
                'Build aborted, {0} compiler detection failed!'.format(
                    compiler_subject))
        pout = pipe.stderr.read()
        reIncl = re.compile('#include <\.\.\.>.*:$\s((^ .*\s)*)', re.M)
        match = reIncl.search(pout)
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

    buildmode = SCons.Script.GetOption('buildcfg')
    if buildmode == 'debug':
        env.AppendUnique(CFLAGS=['-ggdb3' if str(platf) == 'sunos' else '-g'])
    elif buildmode == 'optimized':
        if str(platf) == 'sunos':
            env.AppendUnique(CFLAGS=['-O0'])
        else:
            env.AppendUnique(
                CFLAGS=[
                    '-O0',
                    '-fdefer-pop',
                    '-fmerge-constants',
                    '-fthread-jumps',
                    '-fguess-branch-probability',
                    '-fcprop-registers'])
    elif buildmode == 'profile':
        env.AppendUnique(CFLAGS=['-fprofile'])

    warnlevel = SCons.Script.GetOption('warnlevel')
    if warnlevel == 'medium' or warnlevel == 'full':
        env.AppendUnique(
            CFLAGS=[
                '-Wall',
                '-Wunused',
                '-Wno-system-headers',
                '-Wreturn-type'])
    if warnlevel == 'full':
        env.AppendUnique(CFLAGS=['-Wconversion', '-Wundef', '-Wwrite-strings'])


def exists(env):
    if env.get('_CCPREPEND_'):
        compilers.insert(0, env.get('_CCPREPEND_'))
    return env.Detect(compilers)
