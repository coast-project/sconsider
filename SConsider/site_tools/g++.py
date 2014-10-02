"""SConsider.site_tools.g++

SConsider-specific g++ tool initialization

"""

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

compilers = ['g++']


def generate(env):
    """Add Builders and construction variables for g++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    SCons.Tool.Tool('c++')(env)

    if env.get('_CXXPREPEND_'):
        compilers.insert(0, env.get('_CXXPREPEND_'))
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
        #    env['CXXVERSION'] = line
        line = pipe.stdout.readline()
        versionmatch = re.search(r'(\s+)([0-9]+(\.[0-9]+)+)', line)
        gccfssmatch = re.search(r'(\(gccfss\))', line)
        if versionmatch:
            env['CXXVERSION'] = versionmatch.group(2)
        if gccfssmatch:
            env['CXXFLAVOUR'] = gccfssmatch.group(1)
            gccfss = True

        # own extension to detect system include paths
        import time
        fName = '.code2Compile.' + str(time.time())
        tFile = os.path.join(SCons.Script.Dir('.').abspath, fName)
        outFile = os.path.join(SCons.Script.Dir('.').abspath, fName + '.o')
        try:
            outf = open(tFile, 'w')
            outf.write('#include <cstdlib>\nint main(){return 0;}')
            outf.close()
        except:
            logger.error(
                "failed to create compiler input file, check folder permissions and retry",
                exc_info=True)
            return
        pipe = SCons.Action._subproc(env,
                                     [compiler_subject,
                                      '-v',
                                      '-xc++',
                                      tFile,
                                      '-o',
                                      outFile,
                                      '-m' + env['ARCHBITS']],
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

    env.AppendUnique(CCFLAGS='-m' + env['ARCHBITS'])
    if str(platf) == 'darwin':
        if env['ARCHBITS'] == '32':
            env.AppendUnique(CCFLAGS=['-arch', 'i386'])
        else:
            env.AppendUnique(CCFLAGS=['-arch', 'x86_64'])

    if not SCons.Script.GetOption('no-largefilesupport'):
        env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE'])

    buildmode = SCons.Script.GetOption('buildcfg')
    if buildmode == 'debug':
        env.AppendUnique(
            CXXFLAGS=[
                '-ggdb3' if str(platf) == 'sunos' else '-g'])
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
    elif buildmode == 'profile':
        env.AppendUnique(CXXFLAGS=['-fprofile'])

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
