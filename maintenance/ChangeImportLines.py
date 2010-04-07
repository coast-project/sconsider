import os, pdb, re, time, sys
from SomeUtils import *
from xmlrpclib import datetime

excludelist = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules']

reCpp=re.compile(r'\.(cpp|C)$')
reHeader=re.compile(r'\.(hp*|ip*)$')
reLibPy=re.compile(r'\w+Lib\.py$')
reScons=re.compile(r'SConscript$')
reShell=re.compile(r'\.sh$')
reAny=re.compile(r'\.any$')
reMake=re.compile(r'Makefile.*$')
reHtml=re.compile(r'\.html?$')

# within .h
##define ATTFlowController_H_ID "itopia, ($Id$)"
strReHidOnly=r"define\s+\w+_H_ID"
strReHID=re.compile(r"(^\s*#[ \t]*"+strReHidOnly+".*\s*$\s+)",re.M)
hidReplace=(strReHID, "\n")

# within .cpp
# remove #ident from c++ source files
#if defined(__GNUG__) || defined(__SUNPRO_CC)
    #ident "@(#) $Id$ (c) itopia"
#else
    #define AnythingPerfTest_H_ID "@(#) $Id$ (c) itopia"
#    static char static_c_rcs_id[] = "@(#) $Id$ (c) itopia";
#    static char static_h_rcs_id[] = AnythingPerfTest_H_ID;
#endif
# or
#static char static_c_rcs_id[] = "itopia, ($Id$)";
#static char static_h_rcs_id[] = ATTFlowController_H_ID;
##ifdef __GNUG__
##define USE(name1,name2) static void use##name1() { if(!name1 && !name2) { use##name1(); } }
#USE(static_h_rcs_id, static_c_rcs_id)
##undef USE
##endif
# or
#static char static_c_rcs_id[] = "itopia, ($Id$)";
##ifdef __GNUG__
##pragma implementation
##define USE1(name) static void use##name() { if(!name) { use##name(); } }
#USE1(static_c_rcs_id)
##undef USE1
##endif
strReStaticRcsId=r"[ \t]*static[ \t]+char[ \t]+.*rcs_id"
strReIdentOld=re.compile(r"((^(\s*#if.*$\s+))((^([ \t]*#[ \t]*(pragma\s+(nomargins|implementation|interface)|define\s+(USE|\w+_H_ID)|undef\s+USE|ident)|[ \t]*#[ \t]*e(?!ndif)\w*|[ \t]*USE|"+strReStaticRcsId+").*$\s+)+)([ \t]*#endif\s*$\s+))",re.M)
identoldReplace=(strReIdentOld, "\n")

strReRCSId=re.compile(r"(^([ \t]*/\*\s*RCS\s*Id\s*\*/\s*$\s)|("+strReStaticRcsId+".*$\s))",re.M)
rcsidReplace=(strReRCSId, "")

#ifdef __370__
    #pragma nomargins
#endif
#ifdef __GNUG__
    #pragma implementation
#endif
strRePragma=re.compile(r"(^[ \t]*#if.*$\s*#\s*pragma\s+(nomargins|implementation|interface)\s*$\s+#endif\s*$\s)",re.M)
pragmaReplace=(strRePragma, "")

#--------------------------------------------------------------------
# Copyright (c) 1999 itopia
# All Rights Reserved
#
# $RCSfile$: Main configuration for StressServer
#
#--------------------------------------------------------------------
strReCopyrightAnyShell = re.compile(r"(^(\s*(#[-#]{2}).*$\s)^([ \t]*#[^#-]?.*$\s)+^([ \t]*#[-#]{2}.*$\s)\s*)",re.M)

headerTemplateAnyShell="""#-----------------------------------------------------------------------------------------------------
# Copyright (c) 2005, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or modify it under the terms of
# the license that is included with this library/application in the file license.txt.
#-----------------------------------------------------------------------------------------------------

"""

#/*
# * Copyright (c) 2003 SYNLOGIC
# * All Rights Reserved
# */
strReCopyright = re.compile(r"^(\s*/\*(([^*])|(\*[^/]))*\*/\s*$\s+)",re.M)
# the following regex can only be used with re.X flag
#strReCopyright =r"""
#        (                    ## use whole comment as one group
#           /\*               ##  Leading "/*"
#           (                 ##  Followed by any number of
#              ([^*])         ##  non star characters
#              |              ##  or
#              (\*[^/])       ##  star-nonslash
#           )*
#           \*/               ##  with a trailing "/*"
#        )                    ## close commment group
#"""

headerTemplateC="""/*
 * Copyright (c) 1980, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
 * All rights reserved.
 *
 * This library/application is free software; you can redistribute and/or modify it under the terms of
 * the license that is included with this library/application in the file license.txt.
 */

"""
replacementFromDate=time.mktime(time.strptime('20050101000000','%Y%m%d%H%M%S'))
reCopyYear=re.compile(r"(Copyright \(c\) )(\d{4})?(, Peter Sommerlad)?")

def getCopyrightYear(text):
    crMatch=re.search(reCopyYear, text)
    if crMatch and crMatch.group(2):
        return (crMatch.group(2), crMatch)
    return (None,crMatch)

def getAuthorDate():
    # get commit date
    authdate=time.mktime(time.gmtime())
    authStr=os.environ.get('GIT_AUTHOR_DATE','')
    if authStr:
        authdate=float(authStr.split()[0])
    return authdate

def replaceHeaderFunc(mo, newheader, fileCopyrightYear=None):
    originalHeader=mo.group(0)
    (copyYear,matches)=getCopyrightYear(originalHeader)
    if not matches or matches.group(3):
        return originalHeader
    # get commit date
    authdate=getAuthorDate()
    # compare old and current header string to not overwrite existing data
    if authdate >= replacementFromDate:
        # get date from dict or commit author date
        if fileCopyrightYear:
            authYear=fileCopyrightYear
        else:
            authYear=time.strftime('%Y', time.gmtime(authdate))
        # assume the header is of new format when ", Peter Sommerlad" is matched
        yearHeader=re.sub(reCopyYear, lambda moSub: moSub.group(1) + authYear + moSub.group(3), newheader)
        # if string is equal already, it returns None
        return yearHeader
    return originalHeader

copyReplace=(strReCopyright, lambda mo: replaceHeaderFunc(mo,headerTemplateC))
copyReplaceAnyShell=(strReCopyrightAnyShell, lambda mo: replaceHeaderFunc(mo,headerTemplateAnyShell))

cleanNewLines=(re.compile(r"(^[ \t]*$\s)+",re.M),"\n")

cleanQuotedSpaces=[(re.compile(r"([/%])\s+"),lambda mo: mo.group(1)),
                   (re.compile(r"\s*([<>=-?])\s*"),lambda mo: mo.group(1))]
def correctQuote(mo):
    return mo.group(1) + multiple_replace(cleanQuotedSpaces, mo.group(2))

quoteCorrect=(re.compile("(_QUOTE_\s*\()([^)]+)",re.M), correctQuote)

fgReplaceFuncs=[]
#fgReplaceFuncs.append(quoteCorrect)
fgReplaceFuncs.append(copyReplace)
fgReplaceFuncs.append(copyReplaceAnyShell)
fgReplaceFuncs.append(identoldReplace)
fgReplaceFuncs.append(rcsidReplace)
fgReplaceFuncs.append(hidReplace)
fgReplaceFuncs.append(pragmaReplace)
fgReplaceFuncs.append(cleanNewLines)

fgExcludeDirs=excludelist
fgExcludeDirs.extend(['3rdparty','site_scons','scripts'])

fgExtensionReList=[reCpp, reHeader, reAny, reShell, reMake]

fgExtensionToReplaceFuncMap={
    reCpp:    [identoldReplace,
               rcsidReplace,
               pragmaReplace,
               cleanNewLines],
    reHeader: [identoldReplace,
               rcsidReplace,
               hidReplace,
               pragmaReplace,
               cleanNewLines],
    reAny:    [cleanNewLines],
    reShell:  [cleanNewLines],
    reMake:   [cleanNewLines],
}

import threading, subprocess, math

def processFiles(theFiles, fileCopyrightDict, extensionToReplaceFuncMap, doAstyle=False):
    astyleFiles=[]
    replaceFuncs=[]
    fileCopyrightYear=None
    authdate=getAuthorDate()
    if authdate >= replacementFromDate:
        localMap={}
        for (rex,funcs) in extensionToReplaceFuncMap.iteritems():
            if rex == reCpp or rex == reHeader:
                funcs.insert(0,(strReCopyright, lambda mo: replaceHeaderFunc(mo,headerTemplateC, fileCopyrightYear)))
            else:
                funcs.insert(0,(strReCopyrightAnyShell, lambda mo: replaceHeaderFunc(mo,headerTemplateAnyShell, fileCopyrightYear)))
            localMap.setdefault(rex,funcs)
        for fname in theFiles:
            for (rex,funcs) in localMap.iteritems():
                if rex.search(fname):
                    fileCopyrightYear=fileCopyrightDict.get(fname,None)
                    strReplaced=replaceRegexInFile(fname, searchReplace=funcs)
                    if strReplaced:
                        (year,matches)=getCopyrightYear(strReplaced)
                        if year:
                            copyDate=time.mktime(time.strptime(year, "%Y"))
                            if copyDate >= replacementFromDate:
                                fileCopyrightDict.setdefault(fname,year)
                        if doAstyle and reCpp.search(fname) or reHeader.search(fname):
                            astyleFiles.append(fname)
                    break
        if astyleFiles and doAstyle:
            astyleCmd=["astyle", "--quiet", "--suffix=none", "--mode=c"]
            astyleCmd.extend(astyleFiles)
            proc = subprocess.Popen(astyleCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res = proc.wait()

class replaceThread(threading.Thread):
    def __init__(self, replaceFuncs, files, fileCopyrightDict={}, doAstyle=False):
        threading.Thread.__init__( self )
        self.files=files
        self.fileCopyrightDict=fileCopyrightDict
        self.replaceFuncs=replaceFuncs
        self.fileCopyrightYear=None
        self.doAstyle=doAstyle

    def run(self):
        if self.files:
            processFiles(self.files, self.replaceFuncs, self.fileCopyrightDict, self.doAstyle)

def readDictFromFile(fname):
    import pickle
    retDict={}
    try:
        fo = open( fname, 'rb' )
        if fo:
            retDict=pickle.load(fo)
            fo.close()
    except IOError:
        pass
    return retDict

def writeDictToFile(fname, outDict):
    import pickle
    try:
        fo = open( fname, 'wb' )
        if fo:
            retDict=pickle.dump(outDict, fo)
            fo.close()
    except IOError:
        pass

if __name__ == "__main__":
    from optparse import OptionParser
    import time

    usage = "usage: %prog [options] <file>..."
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--allfiles", action="store_true", dest="allfiles", help="process directories and files recursively and ignore command line files", default=False)
    parser.add_option("-s", "--astyle", action="store_true", dest="astyle", help="process modified files using astyle", default=False)
    parser.add_option("-x", "--fileregex", action="append", dest="fileregex", help="process only files matching regular expression, like '"+reCpp.pattern+"'", default=[])
    parser.add_option("-f", "--filepattern", action="append", dest="filepattern", help="process only files matching glob spec, like '*.cpp'", default=[])
    parser.add_option("-d", "--dictfile", action="store", dest="dictfilename",help="write processed entries to FILE", metavar="FILE")
    parser.add_option("-t", "--threadnum", action="store", dest="threadnum",help="use given number of threads to process files")

    (options, positionalArgs) = parser.parse_args()
    if not options.allfiles and len(positionalArgs) < 1:
        parser.error("incorrect number of arguments")

    extensionReList=[]
    fileCopyrightDict={}
    for fre in options.fileregex:
        extensionReList.append(re.compile(fre))
    for fpat in options.filepattern:
        extensionReList.append(re.compile(re.escape(fpat)))
    if not options.fileregex and not options.filepattern:
        extensionReList=fgExtensionReList
    if options.dictfilename:
        fileCopyrightDict=readDictFromFile(options.dictfilename)
    filesToProcess=positionalArgs
    start = time.clock()
    matchIt=lambda n: not bool(extensionReList)
    for fileRegEx in extensionReList:
        matchIt=lambda n, r=fileRegEx.search,l=matchIt: l(n) or bool(r(n))
    if options.allfiles and len(extensionReList):
        for dirpath, dirnames, filenames in os.walk('.'):
            dirnames[:] = [d for d in dirnames if not d in fgExcludeDirs]
#            newfiles = [os.path.join(dirpath, name) for name in filenames if matchIt(name)]
            newfiles = [os.path.join(dirpath, name) for name in filenames]
            filesToProcess.extend(newfiles)

    end = time.clock()
    numFiles=len(filesToProcess)
    print "Time elapsed = ", end - start, "s for nfiles:",numFiles

    start = time.clock()
    numthreads=None
    if options.threadnum:
        numthreads=int(options.threadnum)
    # check here to see why multi threading in python is not what we would expect -> http://www.dabeaz.com/python/GIL.pdf
    if False or numthreads > 0:
        replaceThreads=[]
        filesPerThread=int(math.ceil(float(numFiles)/float(numthreads)))
        nstart=0
        nend=numthreads*filesPerThread
        while nstart < numFiles:
            t=replaceThread(replaceFuncs=fgReplaceFuncs, fileCopyrightDict=fileCopyrightDict, doAstyle=options.astyle, files=filesToProcess[nstart:nend])
            t.start()
            replaceThreads.append(t)
            nstart+=filesPerThread
            nend+=filesPerThread
        for t in replaceThreads:
            t.join()
            # get dict from thread and update with current
            fileCopyrightDict.update(t.fileCopyrightDict)
    else:
        processFiles(filesToProcess, fileCopyrightDict=fileCopyrightDict, extensionToReplaceFuncMap=fgExtensionToReplaceFuncMap, doAstyle=options.astyle)
#        processFiles(filesToProcess, fgReplaceFuncs, fileCopyrightDict=fileCopyrightDict, extensionToReplaceFuncMap=fgExtensionToReplaceFuncMap, regexList=extensionReList, doAstyle=options.astyle)
    end = time.clock()
    chgElapsed=end-start
    print "Time elapsed = ", chgElapsed, "s for processing,",(chgElapsed/numFiles),"s per file"

    if options.dictfilename:
        writeDictToFile(options.dictfilename, fileCopyrightDict)
