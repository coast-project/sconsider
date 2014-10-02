"""SConsider.site_tools.SCBWriter.

Tool to generate settings files to use with SconsBuilder plugin by
Lothar Werzinger

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

from __future__ import with_statement
import os
import re
from SCons.Script import Dir
import SConsider


def writeSCB(registry, packagename, buildSettings, **kw):
    includeDirs = set()
    sysIncludes = set()
    for targetname, settings in buildSettings.items():
        target = registry.getPackagePlaintarget(packagename, targetname)
        if target and target.has_builder():
            for incpath in target.env.get("CPPPATH", []):
                includeDirs.add(incpath.srcnode().abspath)
            for incpath in target.env.get("SYSINCLUDES", []):
                sysIncludes.add(Dir(incpath).srcnode().abspath)

    inclLists = []
    inclLists.extend(sorted(includeDirs))
    inclLists.extend(sorted(sysIncludes))

    projectdir = Dir('.').srcnode()
    while not os.path.isfile(os.path.join(projectdir.abspath, '.project')) and projectdir.abspath != Dir('#').abspath:
        projectdir = projectdir.up()

    fname = os.path.join(projectdir.abspath, '.scb')
    fstr = ""
    if os.path.isfile(fname):
        with open(fname, 'r') as of:
            fstr = of.read()

    pathstring = ""
    for x in inclLists:
        if not re.compile('CPPPATH.*' + re.escape(x)).search(fstr):
            pathstring += "CPPPATH appendunique " + x + "\n"
    if pathstring:
        with open(fname, 'a+') as of:
            of.write(pathstring)


def generate(env):
    SConsider.registerCallback("PostCreatePackageTargets", writeSCB)


def exists(env):
    return 1
