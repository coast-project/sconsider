"""SConsider.OutputDirectoryHelper.

A bunch of simple methods to access output directory values during target
creation.

"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2014, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from SCons.Script import Dir, AddOption, GetOption
from SCons.Platform import Platform
from SCons.Errors import UserError
import platform
import os
from SomeUtils import getLibCVersion
from logging import getLogger
logger = getLogger(__name__)


def getBaseOutDir(env):
    return env['BASEOUTDIR']


def setRelativeTargetDirectory(env, fsdir):
    env['RELTARGETDIR'] = fsdir


def getRelativeTargetDirectory(env):
    return env['RELTARGETDIR']


def getRelativeBuildDirectory(env):
    return env['BUILDDIR']


def getRelativeVariantDirectory(env):
    return env['VARIANTDIR'] + ''.join(env.get('VARIANT_SUFFIX', []))


def getTargetBaseInstallDir(env):
    return getBaseOutDir(env).Dir(getRelativeTargetDirectory(env))


def getBinaryInstallDir(env):
    return getTargetBaseInstallDir(env).Dir(env['BINDIR']).Dir(
        env.getRelativeVariantDirectory())


def getLibraryInstallDir(env, withRelTarget=False):
    if withRelTarget:
        return getTargetBaseInstallDir(env).Dir(env['LIBDIR']).Dir(
            env.getRelativeVariantDirectory())
    else:
        return getBaseOutDir(env).Dir(env['LIBDIR']).Dir(
            env.getRelativeVariantDirectory())


def getScriptInstallDir(env):
    return getTargetBaseInstallDir(env).Dir(
        env['SCRIPTDIR']).Dir(
        env.getRelativeVariantDirectory())


def getLogInstallDir(env):
    return getTargetBaseInstallDir(env).Dir(
        env['LOGDIR']).Dir(
        env.getRelativeVariantDirectory())


def prepareVariantDir(env):
    variant = "Unknown-"
    myplatf = str(Platform())

    if myplatf == "posix":
        bitwidth = env.getBitwidth()
        libcver = getLibCVersion(bitwidth)
        variant = platform.system(
        ) + "_" + libcver[0] + "_" + libcver[1] + "-" + platform.machine()
    elif myplatf == "sunos":
        variant = platform.system(
        ) + "_" + platform.release() + "-" + platform.processor()
    elif myplatf == "darwin":
        import commands
        version = commands.getoutput("sw_vers -productVersion")
        cpu = commands.getoutput("arch")
        if version.startswith("10.7"):
            variant = "lion-"
        elif version.startswith("10.6"):
            variant = "snowleopard-"
        elif version.startswith("10.5"):
            variant = "leopard-"
        elif version.startswith("10.4"):
            variant = "tiger-"
        variant += cpu
    elif myplatf == "cygwin":
        variant = platform.system() + "-" + platform.machine()
    elif myplatf == "win32":
        variant = platform.system(
        ) + "_" + platform.release() + "-" + platform.machine()

    env.Append(VARIANTDIR=variant)


def verifyBaseoutDirWritable(baseoutdir):
    testfile = os.path.join(baseoutdir.get_abspath(), '.writefiletest.'+str(os.getpid()))
    try:
        if not os.path.isdir(baseoutdir.get_abspath()):
            os.makedirs(baseoutdir.get_abspath()) # test if we are able to create a file
        fp = open(testfile, 'w+')
        fp.close()
    except (os.error, IOError):
        logger.error('Output directory [{0}] not writable'.format(baseoutdir.get_abspath()), exc_info=True)
        raise UserError(
            'Build aborted, baseoutdir [' + baseoutdir.get_abspath() + '] not writable for us!')
    finally:
        os.unlink(testfile)

def prePackageCollection(env, **kw):
    _sconstruct_dir = Dir('#')
    env.AppendUnique(EXCLUDE_DIRS_REL=[env['BUILDDIR']])
    if env.getBaseOutDir() == _sconstruct_dir:
        env.AppendUnique(EXCLUDE_DIRS_TOPLEVEL=[
                env[varname] for varname in [
                                    'BINDIR',
                                    'LIBDIR',
                                    'LOGDIR',
                                    'INCDIR',
                                    ]])


def generate(env):
    from SConsider import registerCallback
    _baseout_dir_default = '#'
    _builddirrel = '.build'

    AddOption(
        '--baseoutdir',
        dest='baseoutdir',
        action='store',
        nargs=1,
        type='string',
        default=_baseout_dir_default,
        metavar='DIR',
        help='Directory to store build target files. Helps keeping your source\
     directory clean, default="' + Dir(_baseout_dir_default).get_abspath() + '"')

    # ensure we have getBitwidth() available
    if 'setupBuildTools' not in env['TOOLS']:
        raise SCons.Errors.UserError('setupBuildTools is required for\
 initialization')

    baseoutdir = Dir(GetOption('baseoutdir'))
    verifyBaseoutDirWritable(baseoutdir)
    env.Append(BASEOUTDIR=baseoutdir)
    # directory relative to BASEOUTDIR where we are going to install target specific files
    # mainly used to rebase/group test or app specific target files
    env.Append(RELTARGETDIR='')
    env.Append(LOGDIR='log')
    env.Append(BINDIR='bin')
    env.Append(LIBDIR='lib')
    env.Append(SCRIPTDIR='scripts')
    env.Append(INCDIR='include')
    env.Append(BUILDDIR=_builddirrel)

    prepareVariantDir(env)

    env.AddMethod(getBaseOutDir, 'getBaseOutDir')
    env.AddMethod(setRelativeTargetDirectory, 'setRelativeTargetDirectory')
    env.AddMethod(getRelativeTargetDirectory, 'getRelativeTargetDirectory')
    env.AddMethod(getRelativeBuildDirectory, 'getRelativeBuildDirectory')
    env.AddMethod(getRelativeVariantDirectory, 'getRelativeVariantDirectory')
    env.AddMethod(getTargetBaseInstallDir, 'getTargetBaseInstallDir')
    env.AddMethod(getBinaryInstallDir, 'getBinaryInstallDir')
    env.AddMethod(getLibraryInstallDir, 'getLibraryInstallDir')
    env.AddMethod(getScriptInstallDir, 'getScriptInstallDir')
    env.AddMethod(getLogInstallDir, 'getLogInstallDir')
    registerCallback('PrePackageCollection', prePackageCollection)


def exists(env):
    return 1
