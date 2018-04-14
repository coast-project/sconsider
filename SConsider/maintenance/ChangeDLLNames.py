"""SConsider.maintenance.ChangeDLLNames.

Simple helper tool to replace old WebDisplay2 dll names with new coast shared library names

Usually it will be applied to Config.any and test configuration files using dynamic library loading
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
# pylint: skip-file
import os
import re

excludelist = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules']
list2 = []
excludelist.extend(list2)
print excludelist
libdict = {
    'renderers': 'CoastRenderers',
    'renderer': 'CoastRenderers',
    'actions': 'CoastActions',
    'stddataaccess': 'CoastStdDataAccess',
    'security': 'CoastSecurity',
    'SSL': 'CoastSSL',
    'ITOSSL': 'CoastSSL',
    'ldapdataaccess': 'CoastLDAPDataAccess',
    'ldapdataaccess2': 'CoastLDAP',
    'dataaccess': 'CoastDataAccess',
    'perftest': 'CoastPerfTest',
    'perftesttest': 'CoastPerfTestTest',
    'applog': 'CoastAppLog',
    'TKFFunctionalRenderers': 'CoastFunctionalRenderers',
    'TKFFunctionalActions': 'CoastFunctionalActions',
    'TKFHTMLRenderers': 'CoastHTMLRenderers',
    'TKFStringRenderers': 'CoastStringRenderers',
    'TKFAppAndUserRights': 'AppAndUserRights',
    'TKSAppLog': 'TKSAppLog',
    'EDICommon': 'EDICommon',
    'Queueing': 'CoastQueueing',
    'sybaseCT': 'CoastSybaseCT',
    'radiusdataaccess': 'RadiusDataAccess',
    'workerpoolmanagermodule': 'CoastWorkerPoolManager',
    'fdcore': 'fdCore',
    'dnscachemodule': 'DNSCacheModule',
    'rsamodule': 'RSAModule',
    'dataserver': 'HIKUDataServer',
    'DataServer': 'HIKUDataServer',
    'HIKUDataServer': 'KFF_DataServer',
    'DataServerPerfTest': 'HIKUDataServerPerfTest',
    'HIKUDataServerPerfTest': 'KFF_DataServerPerfTest',
    'calcserver': 'HIKUCalcServer',
    'CalcServer': 'HIKUCalcServer',
    'HIKUCalcServer': 'KFF_CalcServer',
    'HPSComm': 'HIKUHPSComm',
    'HIKUHPSComm': 'KFF_HPSMessage',
    'HPSPerfTest': 'HIKUHPSCommPerfTest',
    'HIKUHPSCommPerfTest': 'KFF_HPSMessagePerfTest',
    'SystemFunctions': 'CoastSystemFunctions',
    'wdbase': 'CoastWDBase',
    'mtfoundation': 'CoastMTFoundation',
    'regex': 'CoastRegex',
    'foundation': 'CoastFoundation',
    'testbases': 'testfwWDBase',
    'EBCDIC': 'CoastEBCDIC',
    'TestLib': 'CoastWDBaseTestTestLib',
    'compress': 'CoastCompress',
    'MySQL': 'CoastMySQL',
    'SynMySQL': 'CoastMySQL',
    'NTLMAuth': 'CoastNTLMAuth',
    'accesscontrol': 'CoastAccessControl',
    'cachehandler': 'CoastCacheHandler',
    'HTTP': 'CoastHTTP',
    'ldapdaicachehdlr': 'CoastLDAPDAICacheHandler',
    'cachehdlr': 'CoastCacheHandler',
    'CoastOracle': 'CoastOracle',
    'HIKU_common': 'HIKUCommon',
    'HIKU_ChunkHandling': 'HIKUChunkHandling',
    'BPL': 'HIKUBPL',
    'DCD': 'HIKUDCD',
    'HIKU': 'HIKUPflegeSystem',
    'PoolFiller': 'HIKUPoolFiller',
    'momsmsg': 'MomsMsg',
    'deliverer': 'HIKUDeliverer',
    'dsverifier': 'HIKUDSVerifier',
    'helloworld': 'Helloworld',
    'loki': 'lokiObjects',
    'Topic': 'HIKUTopic',
    #           '':'',
    #           '':'',
    #           '':'',
}
for dirpath, dirnames, filenames in os.walk('.'):
    dirnames[:] = [d for d in dirnames if d not in excludelist]
    reDLL = re.compile(r"^[\s]*/DLL\s*{([^}]+)}[\s]*$", re.M)
    reLibTarget = re.compile(r"^\s+LibTarget\s+:\s*\"([^\"]+)\",\s*$", re.M)
    reAny = re.compile('^.*.any$')
    reShared = re.compile('^.*.shared$')
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
                        for it in re.finditer(r"^([^#\S]+)(\"?(lib)?(\w+)(\.so)?\"?)([\s]*)$", strGroup,
                                              re.M):
                            if len(strout):
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
                        if len(strout):
                            if outstr[len(outstr) - 1] != '\n' and strout[0] != '\n':
                                outstr += '\n'
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
        if reShared.match(name):
            fname = os.path.join(dirpath, name)
            try:
                fo = open(fname)
                if fo:
                    fstr = fo.read()
                    fo.close()
                    mo = reLibTarget.search(fstr)
                    if mo:
                        outstr = mo.string[:mo.start(1)]
                        strGroup = mo.group(1)
                        strout = ''
                        for it in re.finditer(r"^lib(\w+)$", strGroup):
                            g = it.groups()
                            lname = g[0]
                            if lname in libdict:
                                kval = libdict.get(lname)
                                strout += it.string[it.start(0):it.start(1)]
                                strout += kval
                                strout += it.string[it.end(1):it.end(0)]
                            elif lname in libdict.itervalues():
                                strout += it.string[it.start(0):it.end(0)]
                            else:
                                print lname, "MISSING in file ", fname
                                strout += it.string[it.start(0):it.end(0)]
                        if len(strout):
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
