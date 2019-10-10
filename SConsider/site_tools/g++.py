"""SConsider.site_tools.g++

SConsider-specific g++ tool initialization
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

compilers = ['g++']


def generate(env):
    """Add Builders and construction variables for g++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    # save potential setting of CXXFLAGS
    current_cxxflags = env.get('CXXFLAGS')
    SCons.Tool.Tool('c++')(env)

    if env.get('_CXXPREPEND_'):
        compilers.insert(0, env.get('_CXXPREPEND_'))
    if current_cxxflags:
        env['CXXFLAGS'] = current_cxxflags
    env['CXX'] = compiler_subject = env.Detect(compilers)

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
    gccfss = False

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
        #    env['CXXVERSION'] = line
        line = _out.strip()
        versionmatch = re.search(r'(\s+)([0-9]+(\.[0-9]+)+)', line)
        gccfssmatch = re.search(r'(\(gccfss\))', line)
        if versionmatch:
            env['CXXVERSION'] = versionmatch.group(2)
        if gccfssmatch:
            env['CXXFLAVOUR'] = gccfssmatch.group(1)
            gccfss = True

        # own extension to detect system include paths
        import time
        fName = '.code2Compile.cpp.' + str(time.time()) + '.' + str(os.getpid())
        tFile = os.path.join(SCons.Script.Dir('.').get_abspath(), fName)
        outFile = os.path.join(SCons.Script.Dir('.').get_abspath(), fName + '.o')
        try:
            outf = open(tFile, 'w')
            outf.write('#include <cstdlib>\nint main(){return 0;}')
            outf.close()
        except:
            logger.error("failed to create compiler input file, check folder permissions and retry",
                         exc_info=True)
            return
        _cmd = [compiler_subject, '-v', '-xc++', tFile, '-o', outFile, '-m' + bitwidth]
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
        env.AppendUnique(CXXFLAGS=['-ggdb3' if str(platf) == 'sunos' else '-g'])
    if buildmode == 'debug':
        pass
    elif buildmode == 'optimized':
        if str(platf) == 'sunos':
            if gccfss:
                # at least until g++ 4.3.3 (gccfss), there is a bug #100 when using optimization levels above -O1
                # -> -fast option breaks creation of correct static initialization sequence
                env.AppendUnique(CXXFLAGS=['-O1'])
            else:
                env.AppendUnique(CXXFLAGS=['-O3'])
        else:
            env.AppendUnique(CXXFLAGS=['-O3'])
    elif buildmode == 'coverage':
        env.AppendUnique(CXXFLAGS=['-fprofile-arcs', '-ftest-coverage'])
    elif buildmode == 'profile':
        env.AppendUnique(CXXFLAGS=['-pg'])

    warnlevel = SCons.Script.GetOption('warnlevel')
    if warnlevel == 'medium' or warnlevel == 'full':
        env.AppendUnique(CXXFLAGS=[
            '-Waddress',  # <! Warn about suspicious uses of memory addresses
            '-Wall',  # <! Enable most warning messages
            '-Wdeprecated',
            '-Wendif-labels',
            '-Wno-system-headers',
            '-Woverloaded-virtual',
            '-Wpointer-arith',  # <! Warn about function pointer arithmetic
            '-Wreturn-type',
            '-Wshadow',
        ])
    if warnlevel == 'full':
        env.AppendUnique(CXXFLAGS=[
            '-Wcast-qual',  # <! Warn about casts which discard qualifiers
            '-Wconversion',
            # <! Warn for implicit type conversions that may change a value
            '-Weffc++',
            # <! Warn about violations of Effective C++ style rules
            '-Wignored-qualifiers',
            # <! Warn whenever type qualifiers are ignored.
            '-Wold-style-cast',
            # <! Warn if a C-style cast is used in a program
            '-Wextra',
            # <! Warn about some extra warning flags that are not enabled by -Wall.
            '-Wundef',  # <! Warn if an undefined macro is used in an #if directive
        ])


def exists(env):
    if env.get('_CXXPREPEND_'):
        compilers.insert(0, env.get('_CXXPREPEND_'))
    return env.Detect(compilers)
