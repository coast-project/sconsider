"""SConsider.site_tools.sunc++

SConsider-specific sunc++ tool initialization
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

import os.path
import SCons

# use the package installer tool lslpp to figure out where cppc and what
# version of it is installed


def get_cppc(env):
    cxx = env.get('CXX', None)
    if cxx:
        cppcPath = os.path.dirname(cxx)
    else:
        cppcPath = None

    cppcVersion = None

    pkginfo = env.subst('$PKGINFO')
    pkgchk = env.subst('$PKGCHK')

    def look_pkg_db(pkginfo=pkginfo, pkgchk=pkgchk):
        version = None
        path = None
        for package in ['SPROcpl']:
            cmd = "%s -l %s 2>/dev/null | grep '^ *VERSION:'" % (pkginfo, package)
            line = os.popen(cmd).readline()
            if line:
                version = line.split()[-1]
                cmd = r"%s -l %s 2>/dev/null | grep '^Pathname:.*/bin/CC$' | grep -v '/SC[0-9]*\.[0-9]*/'" % (
                    pkgchk, package)
                line = os.popen(cmd).readline()
                if line:
                    path = os.path.dirname(line.split()[-1])
                    break

        return path, version

    path, version = look_pkg_db()
    if path and version:
        cppcPath, cppcVersion = path, version

    return (cppcPath, 'CC', 'CC', cppcVersion)


def generate(env):
    """Add Builders and construction variables for SunPRO C++."""
    path, cxx, shcxx, version = get_cppc(env)
    if path:
        cxx = os.path.join(path, cxx)
        shcxx = os.path.join(path, shcxx)

    SCons.Tool.Tool('c++')(env)

    env['CXX'] = cxx
    env['SHCXX'] = shcxx
    env['CXXVERSION'] = version
    env['SHCXXFLAGS'] = SCons.Util.CLVar('$CXXFLAGS -KPIC')
    env['SHOBJPREFIX'] = 'so_'
    env['SHOBJSUFFIX'] = '.o'

    env.AppendUnique(CXXFLAGS='-mt')

    # ensure we have getBitwidth() available
    if 'setupBuildTools' not in env['TOOLS']:
        raise SCons.Errors.UserError('setupBuildTools is required for\
 initialization')

    def bwopt(bitwidth):
        bitwoption = '-xtarget=native'
        if bitwidth == '32':
            # when compiling 32bit, -xtarget=native is all we need, otherwise
            # native64 must be specified
            bitwidth = ''
        return bitwoption + bitwidth

    env.AppendUnique(CXXFLAGS=bwopt(env.getBitwidth()))
    env.AppendUnique(CXXFLAGS='-library=stlport4')

    if not SCons.Script.GetOption('no-largefilesupport'):
        env.AppendUnique(CPPDEFINES=['_LARGEFILE64_SOURCE'])

    buildmode = env.getBuildCfg()
    if buildmode == 'debug':
        pass
    elif buildmode == 'optimized':
        env.AppendUnique(CXXFLAGS=['-fast', '-xbinopt=prepare'])
    elif buildmode == 'profile':
        env.AppendUnique(CXXFLAGS=['-xpg'])

    warnlevel = SCons.Script.GetOption('warnlevel')
    if warnlevel == 'medium' or warnlevel == 'full':
        env.AppendUnique(CXXFLAGS=['+w', '-xport64=implicit'])
    if warnlevel == 'full':
        env.AppendUnique(CXXFLAGS=[])


def exists(env):
    path, cxx, shcxx, version = get_cppc(env)
    if path and cxx:
        cppc = os.path.join(path, cxx)
        if os.path.exists(cppc):
            return cppc
    return None
