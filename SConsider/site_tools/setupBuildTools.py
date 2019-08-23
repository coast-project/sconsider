"""SConsider.site_tools.setupBuildTools.

SConsider-specific tool chain initialization
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
import platform
from logging import getLogger
from SCons.Tool import tool_list, Tool
from SCons.Script import AddOption, GetOption
logger = getLogger(__name__)

cxxCompiler = None
ccCompiler = None


def checkCompiler(env, optionvalue, envVarName):
    if not optionvalue:
        optionvalue = os.getenv(envVarName, None)
    if optionvalue:
        dirname = os.path.dirname(optionvalue)
        if dirname:
            env.PrependENVPath('PATH', dirname)
        basename = os.path.basename(optionvalue)
        return basename
    return None


"""Extract OS specific version information into tuple to return"""


def extractOsVersion(platf):
    current_os_version = (0, 0, 0)
    if str(platf) == "cygwin":
        current_os_version = tuple([int(x) for x in platform.system().split('-')[1].split('.')])
    elif str(platf) == 'win32':
        current_os_version = tuple([int(x) for x in platform.version().split('.')])
    elif str(platf) == 'sunos':
        current_os_version = tuple([int(x) for x in platform.release().split('.')])
    elif str(platf) == 'darwin':
        current_os_version = tuple([int(x) for x in platform.release().split('.')])
    elif platform.system() == 'Linux':
        current_os_version = tuple([int(x) for x in platform.release().split('-')[0].split('.')])
    return current_os_version


def generate(env, **kw):
    """Add build tools."""
    AddOption('--with-cxx',
              dest='whichcxx',
              action='store',
              nargs=1,
              type='string',
              default=None,
              metavar='PATH',
              help='Fully qualified path and name to gnu g++ compiler')
    AddOption('--with-cc',
              dest='whichcc',
              action='store',
              nargs=1,
              type='string',
              default=None,
              metavar='PATH',
              help='Fully qualified path and name to gnu gcc compiler')
    bitchoices = ['32', '64']
    bitdefault = '32'
    AddOption('--archbits',
              dest='archbits',
              action='store',
              nargs=1,
              type='choice',
              choices=bitchoices,
              default=bitdefault,
              metavar='OPTIONS',
              help='Select target bit width (if compiler supports it), ' + str(bitchoices) + ', default=' +
              bitdefault)
    buildchoices = ['debug', 'optimized', 'profile', 'coverage']
    builddefault = 'optimized'
    AddOption('--build-cfg',
              dest='buildcfg',
              action='store',
              nargs=1,
              type='choice',
              choices=buildchoices,
              default=builddefault,
              metavar='OPTIONS',
              help='Select build configuration, ' + str(buildchoices) + ', default=' + builddefault +
              '. Use profile in conjunction with gprof and coverage in conjunction with gcov.')
    langchoices = ['c++03', 'c++11', 'c++14', 'c++17', 'c++0x', 'c++1y', 'c++1z', 'gnu++98', 'tr1']
    langdefault = 'gnu++98'
    AddOption('--use-lang-features',
              dest='whichlangfeat',
              action='store',
              nargs=1,
              type='choice',
              choices=langchoices,
              default=langdefault,
              metavar='OPTIONS',
              help='Select which language features, ' + str(langchoices) + ', default=' + langdefault + '.')
    warnchoices = ['none', 'medium', 'full']
    warndefault = 'medium'
    AddOption('--warnlevel',
              dest='warnlevel',
              action='store',
              nargs=1,
              type='choice',
              choices=warnchoices,
              default=warndefault,
              metavar='OPTIONS',
              help='Select compilation warning level, one of ' + str(warnchoices) + ', default=' +
              warndefault)
    AddOption('--no-largefilesupport',
              dest='no-largefilesupport',
              action='store_true',
              help='Disable use of std libraries iostream headers')

    cxxCompiler = checkCompiler(env, GetOption('whichcxx'), 'CXX')
    ccCompiler = checkCompiler(env, GetOption('whichcc'), 'CC')
    toolchainOverride = False
    if cxxCompiler:
        toolchainOverride = True
        env['_CXXPREPEND_'] = cxxCompiler
    if ccCompiler:
        toolchainOverride = True
        env['_CCPREPEND_'] = ccCompiler

    platf = env['PLATFORM']
    # if we are within cygwin and want to build a win32 target
    if GetOption('usetools') is not None:
        if "mingw" in GetOption('usetools'):
            platf = "win32"
    current_os_version = extractOsVersion(platf)
    env.AddMethod(lambda env: extractOsVersion(env['PLATFORM']), "getOsVersionTuple")

    # select language features
    langfeature = GetOption('whichlangfeat')

    if langfeature == 'tr1':
        env.AppendUnique(CPPDEFINES=['USE_TR1'])
    elif langfeature in langchoices:
        env.AppendUnique(CPPDEFINES=['USE_STD' + langfeature[-2:].upper()])
        env.AppendUnique(CXXFLAGS=['-std=' + langfeature])

    # select target architecture bits
    bitwidth = GetOption('archbits')
    if bitwidth is None:
        bitwidth = bitdefault
    env.AddMethod(lambda env: bitwidth, "getBitwidth")
    buildcfg = GetOption('buildcfg')
    if buildcfg is None:
        buildcfg = builddefault
    env.AddMethod(lambda env: buildcfg, "getBuildCfg")

    env.AppendUnique(CCFLAGS=['-DARCHBITS=' + str(bitwidth)])

    platf_for_tool_list = platf
    # this section is needed to select gnu toolchain on sun systems, default is sunCC
    # -> see SCons.Tool.__init__.py tool_list method for explanation
    if toolchainOverride and str(platf) == 'sunos':
        platf_for_tool_list = None

    # tool initialization, previously done in <scons>/Tool/default.py
    for t in tool_list(platf_for_tool_list, env):
        Tool(t)(env)

    logger.info('using CXX compiler and version: %s(%s)%s', env['CXX'], env.get('CXXVERSION', 'unknown'),
                '(' + langfeature + ')' if langfeature else '')
    logger.info('using CC compiler and version: %s(%s)', env['CC'], env.get('CCVERSION', 'unknown'))

    _osreldefines = ['OS_RELMAJOR', 'OS_RELMINOR', 'OS_RELMINSUB']
    for val, valname in zip(current_os_version, _osreldefines):
        env.AppendUnique(CCFLAGS=['-D' + valname + '=' + str(val)])
    logger.debug("OS-Flags: %s",
                 ', '.join([str(i) + '=' + str(j) for j, i in zip(current_os_version, _osreldefines)]))
    if str(platf) == 'sunos':
        env.AppendUnique(CCFLAGS=['-DOS_SYSV'])
        env.AppendUnique(CCFLAGS=['-DOS_SOLARIS'])
    elif str(platf) == 'darwin':
        env.AppendUnique(CCFLAGS=['-DOS_SYSV'])
    elif platform.system() == 'Linux':
        env.AppendUnique(CCFLAGS=['-DOS_SYSV'])
        env.AppendUnique(CCFLAGS=['-DOS_LINUX'])
    elif str(platf) == 'win32':
        """from scons user manual: a library build of a Windows shared library
        (.dllfile) will also build a corresponding .def file at the same
        time."""
        env.Append(WINDOWS_INSERT_DEF=1)

    env.Append(VARIANT_SUFFIX=['-' + bitwidth])
    env.Append(VARIANT_SUFFIX=['_' + buildcfg])

    if "mingw" in env["TOOLS"]:
        # mingw appends .exe if a Program target is given without extension but scons still
        # returns the target without extension. Because depending targets therefore wouldn't
        # find the target this emitter was created as a workaround.
        # => see http://scons.tigris.org/issues/show_bug.cgi?id=2712
        def appendexe(target, source, env):
            newtgt = []
            for t in target:
                newtgt.append(
                    SCons.Util.adjustixes(str(t), env.subst('$PROGPREFIX'), env.subst('$PROGSUFFIX')))
            return newtgt, source

        env["PROGEMITTER"] = appendexe

        # find and append msys' bin path in order to execute shell scripts
        # using subprocess for example
        shexe = "sh.exe"
        shpath = env.WhereIs(shexe) or SCons.Util.WhereIs(shexe)
        msysdir = os.path.dirname(shpath)
        env.PrependENVPath('PATH', msysdir)


def exists(env):
    return True
