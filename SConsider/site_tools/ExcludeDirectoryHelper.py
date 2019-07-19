"""SConsider.site_tools.OutputDirectoryHelper.

A bunch of simple methods to access output directory values during
target creation.
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

import os
from logging import getLogger
from SCons.Script import Dir, AddOption
from SCons.Tool import DefaultToolpath
logger = getLogger(__name__)

relativeExcludeDirsList = ['CVS', '.git', '.gitmodules', '.svn', '.tox']


def prePackageCollection(env, **kw):
    """We assume no sconsider files within tool directories."""
    exclude_opt = env.GetOption('exclude')
    if exclude_opt is None:
        exclude_opt = []
    exclude_list = []
    for ex_entry in exclude_opt:
        exclude_list.extend([i.path for i in env.Glob(ex_entry)])
    exclude_list.extend(DefaultToolpath)
    for exclude_path in exclude_list:
        absolute_path = exclude_path
        if not os.path.isabs(exclude_path):
            absolute_path = Dir(exclude_path).get_abspath()
        else:
            exclude_path = os.path.relpath(exclude_path, kw.get('sconstruct_dir', Dir('#')).get_abspath())
        if not exclude_path.startswith('..'):
            first_segment = exclude_path.split(os.pathsep)[0]
            env.AppendUnique(EXCLUDE_DIRS_TOPLEVEL=[first_segment])
        env.AppendUnique(EXCLUDE_DIRS_ABS=[absolute_path])

    logger.debug("Exclude dirs rel: %s", env.relativeExcludeDirs())
    logger.debug("Exclude dirs abs: %s", env.absoluteExcludeDirs())
    logger.debug("Exclude dirs toplevel: %s", env.toplevelExcludeDirs())


def generate(env):
    from SConsider.Callback import Callback

    AddOption('--exclude',
              dest='exclude',
              action='append',
              nargs=1,
              type='string',
              default=[],
              metavar='DIR',
              help='Exclude directory from being scanned for SConscript\
 (*.sconsider) files.')

    global relativeExcludeDirsList
    env.AppendUnique(EXCLUDE_DIRS_REL=relativeExcludeDirsList)
    env.AppendUnique(EXCLUDE_DIRS_ABS=[])
    env.AppendUnique(EXCLUDE_DIRS_TOPLEVEL=relativeExcludeDirsList + [j.path for j in env.Glob('*.egg-*')])
    env.AddMethod(lambda env: env['EXCLUDE_DIRS_REL'], 'relativeExcludeDirs')
    env.AddMethod(lambda env: env['EXCLUDE_DIRS_ABS'], 'absoluteExcludeDirs')
    env.AddMethod(lambda env: env['EXCLUDE_DIRS_TOPLEVEL'], 'toplevelExcludeDirs')

    Callback().register('PrePackageCollection', prePackageCollection)


def exists(env):
    return 1
