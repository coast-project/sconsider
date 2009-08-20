from __future__ import with_statement
import os, re, pdb
from SCons.Script import Dir
import StanfordUtils

def writeSCB(registry, packagename, buildSettings, **kw):
    includeDirs = set()
    sysIncludes = set()
    for targetname, settings in buildSettings.items():
        target = registry.getPackageTarget(packagename, targetname)["plaintarget"]
        if target and target.has_builder():
            for incpath in target.env.get("CPPPATH_ORIGIN", []):
                includeDirs.add(incpath.srcnode().abspath)
            for incpath in target.env.get("SYSINCLUDES", []):
                sysIncludes.add(Dir(incpath).srcnode().abspath)
            
    inclLists = []
    inclLists.extend(sorted(includeDirs))
    inclLists.extend(sorted(sysIncludes))
    
    fname = os.path.join(Dir('.').srcnode().abspath, '.scb')
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
    StanfordUtils.registerCallback("PostCreatePackageTargets", writeSCB)

def exists(env):
   return 1
