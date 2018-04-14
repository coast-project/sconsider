"""SConsider.

SCons build tool extension allowing automatic target finding within a
directory tree.
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
from ._version import get_versions

__author__ = "Marcel Huber <marcel.huber@hsr.ch>"
__version__ = get_versions()['version']
__date__ = get_versions().get('date')
__sconsider_root__ = os.path.dirname(__file__)
del get_versions


def called_from_scons():
    import inspect
    __scons_main_file = os.path.join('SCons', 'Script', 'Main.py')
    __scons_main_identifier = 'main'
    for i in reversed(inspect.stack()):
        if __scons_main_file in i[1] and i[3] == __scons_main_identifier:
            return True
    return False


def get_sconsider_root():
    return __sconsider_root__


if called_from_scons():
    import SConsider.Main as Main
    cloneBaseEnv = Main.cloneBaseEnv
    get_sconstruct_dir = Main.get_sconstruct_dir
    get_launch_dir = Main.get_launch_dir
    # forward include deprecated functions
    createTargets = Main.createTargets
    splitTargetname = Main.splitTargetname
    createUniqueTargetname = Main.createUniqueTargetname
    generateFulltargetname = Main.generateFulltargetname
    listFiles = Main.listFiles
    findFiles = Main.findFiles
    removeFiles = Main.removeFiles
    getfqdn = Main.getfqdn
    Main.main()
