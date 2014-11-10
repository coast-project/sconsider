"""SConsider.site_tools.OutputDirectoryHelper.

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

from SCons.Script import Dir, AddOption
import os
from logging import getLogger
logger = getLogger(__name__)


relativeExcludeDirsList = ['CVS', '.git', '.gitmodules', '.svn']


def prePackageCollection(env, **kw):
    from SCons.Tool import DefaultToolpath

    """We assume no sconsider files within tool directories"""
    for exclude_path in env.GetOption('exclude') + DefaultToolpath:
        absolute_path = exclude_path
        if not os.path.isabs(exclude_path):
            absolute_path = Dir(exclude_path).get_abspath()
        else:
            exclude_path = os.path.relpath(exclude_path, Dir('#').get_abspath())
        if not exclude_path.startswith('..'):
            first_segment = exclude_path.split(os.pathsep)[0]
            env.AppendUnique(EXCLUDE_DIRS_TOPLEVEL=[first_segment])
        env.AppendUnique(EXCLUDE_DIRS_ABS=[absolute_path])


def generate(env):
    from SConsider import registerCallback

    AddOption(
        '--exclude',
        dest='exclude',
        action='append',
        nargs=1,
        type='string',
        default=[],
        metavar='DIR',
        help='Exclude directory from being scanned for SConscript\
 (*.sconsider) files.')

    env.AppendUnique(EXCLUDE_DIRS_REL=relativeExcludeDirsList)
    env.AppendUnique(EXCLUDE_DIRS_ABS=[])
    env.AppendUnique(EXCLUDE_DIRS_TOPLEVEL=relativeExcludeDirsList)
    env.AddMethod(lambda env: env['EXCLUDE_DIRS_REL'], 'relativeExcludeDirs')
    env.AddMethod(lambda env: env['EXCLUDE_DIRS_ABS'], 'absoluteExcludeDirs')
    env.AddMethod(lambda env: env['EXCLUDE_DIRS_TOPLEVEL'], 'toplevelExcludeDirs')

    registerCallback('PrePackageCollection', prePackageCollection)


def exists(env):
    return 1
