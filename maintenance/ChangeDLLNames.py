"""site_scons.maintenance.ChangeDLLNames

Simple helper tool to replace old WebDisplay2 dll names with new coast shared library names

Usually it will be applied to Config.any and test configuration files using dynamic library loading

"""
#-----------------------------------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or modify it under the terms of
# the license that is included with this library/application in the file license.txt.
#-----------------------------------------------------------------------------------------------------
import os, re

excludelist = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules']
list2 = []
excludelist.extend(list2)
print excludelist
libdict = {'renderers':'CoastRenderers',
           'renderer':'CoastRenderers',
           'actions':'CoastActions',
           'stddataaccess':'CoastStdDataAccess',
           'security':'CoastSecurity',
           'SSL':'CoastSSL',
           'ldapdataaccess':'CoastLDAPDataAccess',
           'ldapdataaccess2':'CoastLDAP',
           'dataaccess':'CoastDataAccess',
           'perftest':'CoastPerfTest',
           'applog':'CoastAppLog',
           'TKFFunctionalRenderers':'CoastFunctionalRenderers',
           'perftesttest':'PerfTestTest',
           'radiusdataaccess':'CoastRadiusDataAccess',
           'workerpoolmanagermodule':'CoastWorkerPoolManager'}
for dirpath, dirnames, filenames in os.walk('.'):
    dirnames[:] = [d for d in dirnames if not d in excludelist]
    reDLL = re.compile(r"^[\s]*/DLL\s*{([^}]+)}[\s]*$", re.M)
    reAny = re.compile('^.*.any$')
    for name in filenames:
        if reAny.match(name):
            fname = os.path.join(dirpath, name)
            try:
                fo = open(fname)
                if fo:
                    fstr = fo.read()
                    fo.close()
                    mo = reDLL.search(fstr)
                    if mo:
                        outstr = mo.string[:mo.start(1)]
                        strGroup = mo.group(1)
                        strout = ''
                        for it in re.finditer(r"^([^#\S]+)(\"?(lib)?(\w+)(\.so)?\"?)([\s]*)$", strGroup, re.M):
                            if strout:
                                strout += '\n'
                            g = it.groups()
                            lname = g[3]
                            if lname in libdict:
                                kval = libdict.get(lname)
                                strout += it.string[it.start(0):it.start(2)]
                                strout += kval
                                strout += it.string[it.end(2):it.end(0)]
                            elif lname in libdict.itervalues():
                                strout += it.string[it.start(0):it.end(0)]
                            else:
                                print lname, "MISSING"
                                strout += it.string[it.start(0):it.end(0)]
                        if strout:
                            outstr += strout
                        else:
                            outstr += strGroup
                        outstr += mo.string[mo.end(1):]
                        if fstr != outstr:
                            print "matches in file:", fname
                            try:
                                of = open(fname, 'w+')
                                of.write(outstr)
                                of.close()
                            except:
                                pass
            except IOError:
                pass
