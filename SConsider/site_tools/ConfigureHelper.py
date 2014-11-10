"""SConsider.site_tools.ConfigureHelper.

Helper functions used when executing configure like build steps

"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import contextlib
import functools
import os
import SCons


def CheckExecutable(context, executable):
    context.Message('Checking for executable {0}... '.format(executable))
    result = context.env.WhereIs(executable)
    context.Result(bool(result))
    return result


def CheckMultipleLibs(context, libraries=None, **kw):
    if not SCons.Util.is_List(libraries):
        libraries = [libraries]

    return functools.reduce(
        lambda x, y:
            SCons.SConf.CheckLib(context, y, **kw) and x,
        libraries,
        True)


def Configure(env, *args, **kw):
    if SCons.Script.GetOption('help'):
        import SConsider
        return SConsider.Null()

    kw.setdefault('custom_tests', {})['CheckExecutable'] = CheckExecutable
    kw.setdefault('custom_tests', {})['CheckMultipleLibs'] = CheckMultipleLibs
    env.Append(LINKFLAGS='-Wl,-rpath-link=' +
               os.pathsep.join(map(str, env['LIBPATH'])))
    conf = env.Configure(*args, **kw)
    return conf


@contextlib.contextmanager
def ConfigureContext(env, *args, **kw):
    conf = Configure(env, *args, **kw)
    yield conf
    conf.Finish()


_sconf_tempdirrel = '.sconf_temp'

def prePackageCollection(env, **kw):
    env.AppendUnique(EXCLUDE_DIRS_TOPLEVEL=[_sconf_tempdirrel])


def generate(env):
    from SConsider import registerCallback
    env['CONFIGURELOG'] = env.getBaseOutDir().File("config.log").get_abspath()
    env['CONFIGUREDIR'] = env.getBaseOutDir().Dir(_sconf_tempdirrel).get_abspath()
    registerCallback('PrePackageCollection', prePackageCollection)


def exists(env):
    return True
