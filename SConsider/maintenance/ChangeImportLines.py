"""SConsider.maintenance.ChangeImportLines.

Simple helper tool to search/replace old-style c++ file contents in
WebDisplay2 source and header files
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
# pylint: skip-file
import os
import re
import time
import sys
import subprocess

excludelist = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules']

reCpp = re.compile(r'\.(cpp|C)$')
reHeader = re.compile(r'\.(hp*|ip*)$')
rePy = re.compile(r'\.py$')
reLibPy = re.compile(r'\w+Lib\.py$')
reScons = re.compile(r'SConscript$')
reShell = re.compile(r'\.(sh|awk)$')
reAny = re.compile(r'\.(any|pem|cnf)$')
reText = re.compile(r'\.(txt|tex)$')
reSQL = re.compile(r'\.sql$')
reLdif = re.compile(r'\.ldif$')
reSconsider = re.compile(r'\.sconsider$')
reMake = re.compile(r'Makefile.*$')
reDoxy = re.compile(r'(Doxyfile|\.doxy)$')
reHtml = re.compile(r'\.html?$')

# within .h
"""#define ATTFlowController_H_ID "itopia, ($Id$)" """
strReHidOnly = r"define\s+\w+_H_ID"
strReHID = re.compile(r"(^\s*#[ \t]*" + strReHidOnly + r".*\s*$\s+)", re.M)
hidReplace = (strReHID, "\n")

# within .cpp
# remove #ident from c++ source files
"""#if defined(__GNUG__) || defined(__SUNPRO_CC)
    #ident "@(#) $Id$ (c) itopia"
#else
    #define AnythingPerfTest_H_ID "@(#) $Id$ (c) itopia"
#    static char static_c_rcs_id[] = "@(#) $Id$ (c) itopia";
#    static char static_h_rcs_id[] = AnythingPerfTest_H_ID;
#endif"""
# or
"""#static char static_c_rcs_id[] = "itopia, ($Id$)";
static char static_h_rcs_id[] = ATTFlowController_H_ID;
#ifdef __GNUG__
#define USE(name1,name2) static void use##name1() { if(!name1 && !name2) { use##name1(); } }
USE(static_h_rcs_id, static_c_rcs_id)
#undef USE
#endif"""
# or
"""#static char static_c_rcs_id[] = "itopia, ($Id$)";
#ifdef __GNUG__
#pragma implementation
#define USE1(name) static void use##name() { if(!name) { use##name(); } }
USE1(static_c_rcs_id)
#undef USE1
#endif"""
strReStaticRcsId = r"[ \t]*static[ \t]+char[ \t]+.*rcs_id"
strReIdentOld = re.compile(
    r"((^(\s*#if.*$\s+))((^([ \t]*#[ \t]*(pragma\s+(nomargins|implementation|interface)|define\s+(USE|\w+_H_ID)|undef\s+USE|ident)|[ \t]*#[ \t]*e(?!ndif)\w*|[ \t]*USE|"
    + strReStaticRcsId + r").*$\s+)+)([ \t]*#endif\s*$\s+))", re.M)
identoldReplace = (strReIdentOld, "\n")

strReRCSId = re.compile(r"(^([ \t]*/\*\s*RCS\s*Id\s*\*/\s*$\s)|(" + strReStaticRcsId + r".*$\s))", re.M)
rcsidReplace = (strReRCSId, "")
"""#ifdef __370__
    #pragma nomargins
#endif
#ifdef __GNUG__
    #pragma implementation
#endif"""
strRePragma = re.compile(
    r"(^[ \t]*#if.*$\s*#\s*pragma\s+(nomargins|implementation|interface)\s*$\s+#endif\s*$\s)", re.M)
pragmaReplace = (strRePragma, "")
"""#--------------------------------------------------------------------
# Copyright (c) 1999 itopia
# All Rights Reserved
#
# $RCSfile$: Main configuration for StressServer
#
#--------------------------------------------------------------------"""
strReCopyrightAnyShell = re.compile(
    r"(^(\s*(#[-#]{2}).*$\s)^([ \t]*#[^#-]?.*$\s)+^([ \t]*#[-#]{2}.*$\s)?\s*)", re.M)

headerTemplateAnyShell = """# -------------------------------------------------------------------------
# Copyright (c) 2005, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

"""
"""#/*
# * Copyright (c) 2003 SYNLOGIC
# * All Rights Reserved
# */"""
strReCopyright = re.compile(r"^(\s*/\*(([^*])|(\*[^/]))*\*/\s*$\s+)", re.M)
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

headerTemplateC = """/*
 * Copyright (c) 1980, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
 * All rights reserved.
 *
 * This library/application is free software; you can redistribute and/or modify it under the terms of
 * the license that is included with this library/application in the file license.txt.
 */

"""
replacementFromDate = time.mktime(time.strptime('20050101000000', '%Y%m%d%H%M%S'))
reCopyYear = re.compile(r"(Copyright \(c\) )(\d{4})?(, Peter Sommerlad)?")
"""
//--- interface include --------------------------------------------------------
#include "TraceUtilsTest.h"

//--- module under test --------------------------------------------------------
#include "TraceUtils.h"

//--- test modules used --------------------------------------------------------
#include "TestSuite.h"

//--- project modules used -----------------------------------------------------
#include "PDNEMsg.h"
#include "MutterGeraet.h"
#include "Router.h"

//--- standard modules used ----------------------------------------------------
#include "Tracer.h"
#include "System.h"
#include "StringStream.h"
"""
#reIncludeCommentBloat = re.compile(r"(^[ \t]*$\s)*^//[- ]--*[ \t]*.*[ \t]*--+[ \t]*$\s+#", re.M)
reIncludeCommentBloat = re.compile(r"(^[ \t]*$\s)*^//[- ]--*[ \t]*.*[ \t]*--+[ \t]*$\s(^[ \t]*$\s)*", re.M)


def insertNewLineIfAtLeastOneWasThere(mo):
    if mo.group(1) or mo.group(2):
        return "\n"
    return ""


includeCommentBloatReplace = (reIncludeCommentBloat, lambda mo: insertNewLineIfAtLeastOneWasThere(mo))
"""
//---- TraceUtilsTest ----------------------------------------------------------------
TraceUtilsTest::TraceUtilsTest...
"""
reClassnameCommentHeader = re.compile(
    r"(^[ \t]*$\s)*^//--*[ \t]*(?P<classname>\w+)[ \t]*--+[ \t]*$\s+(?P<classline>^(class\s*(?P=classname)|(?P=classname)::))",
    re.M)
classnameCommentHeaderReplace = (reClassnameCommentHeader, lambda mo: "\n" + mo.group('classline'))

reTestsuiteHeader = re.compile(r"^// builds up a suite of testcases, add a line for each testmethod\s*", re.M)
testsuiteHeaderReplace = (reTestsuiteHeader, "")


def multiple_replace(replist, text):
    """Using a list of tuples (pattern, replacement) replace all occurrences of
    pattern (supports regex) with replacement.

    Returns the new string.
    """
    for pattern, replacement in replist:
        if not pattern or not text:
            continue
        text = re.sub(pattern, replacement, text)
    return text


def replaceRegexInFile(fname, searchReplace, multiReplFunc=multiple_replace, replacedCallback=None):
    try:
        fo = open(fname)
        if fo:
            fstr = fo.read()
            fo.close()
            if fstr:
                strout = multiReplFunc(searchReplace, fstr)
                if fstr != strout:
                    try:
                        of = open(fname, 'w+')
                        of.write(strout)
                        of.close()
                        if callable(replacedCallback):
                            replacedCallback(fname=fname, text=strout)
                        return strout
                    except:
                        pass
    except IOError:
        pass
    return None


def getCopyrightYear(text):
    crMatch = re.search(reCopyYear, text)
    if crMatch and crMatch.group(2):
        return (crMatch.group(2), crMatch)
    return (None, crMatch)


def getAuthorDate():
    # get commit date
    authdate = time.mktime(time.gmtime())
    authStr = os.environ.get('GIT_AUTHOR_DATE', '')
    if authStr:
        authdate = float(authStr.split()[0])
    return authdate


def replaceHeaderFunc(mo, newheader, fileCopyrightYear=None):
    originalHeader = mo.group(0)
    _, matches = getCopyrightYear(originalHeader)
    if not matches or matches.group(3):
        return originalHeader
    # get commit date
    authdate = getAuthorDate()
    # compare old and current header string to not overwrite existing data
    if authdate >= replacementFromDate:
        # get date from dict or commit author date
        if fileCopyrightYear:
            authYear = fileCopyrightYear
        else:
            authYear = time.strftime('%Y', time.gmtime(authdate))
        # assume the header is of new format when ", Peter Sommerlad" is
        # matched
        yearHeader = re.sub(reCopyYear, lambda moSub: moSub.group(1) + authYear + moSub.group(3), newheader)
        # if string is equal already, it returns None
        return yearHeader
    return originalHeader


copyReplace = (strReCopyright, lambda mo: replaceHeaderFunc(mo, headerTemplateC))
copyReplaceAnyShell = (strReCopyrightAnyShell, lambda mo: replaceHeaderFunc(mo, headerTemplateAnyShell))

cleanNewLines = (re.compile(r"(^[ \t]*$\s)+", re.M), "\n")
cleanDomain = (re.compile(r"(itopia|synlogic)\.(ch|loc)"), lambda mo: 'hsr.' + mo.group(2))
cleanESport = (re.compile(r"(esport|eSport)\.(ch)"), lambda mo: mo.group(1) + '.hsr.' + mo.group(2))
cleanTokens = (re.compile(
    r"\s*#(\s*(TestCases|tkf|foolabs|HSR|soplinux|itopia|hexa|Hank|scarl|bondo|bernina|zuoz|davos|ftan|surlej|hepta|penta|infoo|athla|tk\w+))+\s*$",
    re.M), "")
cleanLineEnds = (re.compile(r"([ \t]+$)", re.M), "")
cleanCompany = (re.compile(r"([^\\/])(tkf|telekurs|itopia|<em>i</em>topia|synlogic)\b",
                           re.I), lambda mo: str(mo.group(1)) + "ifs")
cleanWebDisplay = (re.compile(r"([^\\/])webdisplay2?", re.I), lambda mo: str(mo.group(1)) + "Coast")
cleanFinanzInfo = (re.compile(r"Telekurs Finanzinformationen AG"), "Institut fuer Software")
cleanTKFPath = (re.compile(r"\.\./TKF/"), "")
cleanTKFID = (re.compile(r"tkf-id"), "ifs-id")
correctKeyFile = (re.compile(r"(/(Key|Cert)File)\b"), lambda mo: str(mo.group(1)) + "Client")
cleanWD2 = (re.compile(r"(WWW[\\/]+)?webdisplay2([\\/]+)?"), lambda mo: "coast" + str(mo.group(2)))
cleanEXPORTDECL = (re.compile(r"(\s+)(EXPORTDECL_\w+[ \t]*)(.*)$",
                              re.M), lambda mo: mo.group(1) + mo.group(3))

myshellcleanlist = []
myshellcleanlist.extend([(re.compile(r"ftp-fd"), "myApp")])
myshellcleanlist.extend([(re.compile(r"Telekurs FTP-Frontdoor"), "SomeCompany myApp")])
myshellcleanlist.extend([(re.compile(r"(^(\s*# specify ALL.*$\s)^(\s*#.*$\s)+^(ALL_CONFIGS.*$\s))",
                                     re.M), "\n")])
myshellcleanlist.extend([(re.compile(r"(^\s*#?DEF_CONF.*$\s)", re.M), "\n")])
myshellcleanlist.extend([(re.compile(r"(^\s*#\s*use setConfig\.sh.*$\s)", re.M), "\n")])
myshellcleanlist.append(cleanDomain)
myshellcleanlist.append(cleanCompany)
myshellcleanlist.append(cleanWebDisplay)
myshellcleanlist.append(cleanWD2)
myshellcleanlist.append(cleanTokens)
myshellcleanlist.append(cleanLineEnds)
myshellcleanlist.append(cleanNewLines)

myldifcleanlist = []
myldifcleanlist.append(cleanFinanzInfo)
myldifcleanlist.extend([(re.compile(r"street:: .*"), "street: Oberseestrasse 10")])
myldifcleanlist.extend([(re.compile(r"street: .*"), "street: Oberseestrasse 10")])
myldifcleanlist.extend([(re.compile(r"postalcode: .*"), "postalcode: 8640")])
myldifcleanlist.extend([(re.compile(r"city: .*"), "city: Rapperswil")])
myldifcleanlist.append(cleanTKFID)
myldifcleanlist.append(cleanDomain)
myldifcleanlist.append(cleanCompany)

removeVersion = (re.compile(r'(^\s*/Version\s*"\$Id\$"\s*$\s)', re.M), "\n")

cleanQuotedSpaces = [(re.compile(r"([/%])\s+"), lambda mo: mo.group(1)),
                     (re.compile(r"\s*([<>=-?])\s*"), lambda mo: mo.group(1))]


def correctQuote(mo):
    return mo.group(1) + multiple_replace(cleanQuotedSpaces, mo.group(2))


quoteCorrect = (re.compile(r"(_QUOTE_\s*\()([^)]+)", re.M), correctQuote)

fgExcludeDirs = excludelist
fgExcludeDirs.extend(['3rdparty', 'site_scons', 'scripts', 'helloworld', 'recipes', 'sso'])

fgExtensionReList = [reCpp, reHeader, reAny, reShell, reMake]

fgExtensionToReplaceFuncMap = {
    reAny: [
        cleanNewLines,
        cleanWebDisplay,
        correctKeyFile,
        cleanWD2,
        cleanLineEnds,
    ],
    reShell: [],
    reLdif: [],
    reCpp: [
        rcsidReplace,
        identoldReplace,
        pragmaReplace,
        cleanNewLines,
        cleanLineEnds,
        cleanWebDisplay,
        cleanWD2,
        cleanEXPORTDECL,
        includeCommentBloatReplace,
        classnameCommentHeaderReplace,
        testsuiteHeaderReplace,
    ],
    reHeader: [
        rcsidReplace,
        identoldReplace,
        hidReplace,
        pragmaReplace,
        cleanNewLines,
        cleanLineEnds,
        cleanWebDisplay,
        cleanWD2,
        cleanEXPORTDECL,
        includeCommentBloatReplace,
        classnameCommentHeaderReplace,
    ],
    reText: [],
    reDoxy: [
        cleanWebDisplay,
        cleanWD2,
        cleanLineEnds,
    ],
    reHtml: [
        cleanWebDisplay,
    ],
    reSQL: [],
    rePy: [],
    reSconsider: [],
    reMake: [
        cleanNewLines,
    ],
}


def extendMapWithHSRSpecifics(extensionToReplaceFuncMap):
    extensionToReplaceFuncMap[reAny].extend([
        cleanDomain,
        cleanESport,
        cleanFinanzInfo,
        cleanCompany,
        removeVersion,
        cleanTKFID,
    ])
    extensionToReplaceFuncMap[reShell].extend(myshellcleanlist)
    extensionToReplaceFuncMap[reLdif].extend(myldifcleanlist)
    extensionToReplaceFuncMap[reCpp].extend([
        cleanDomain,
        cleanCompany,
    ])
    extensionToReplaceFuncMap[reHeader].extend([
        cleanDomain,
        cleanCompany,
    ])
    extensionToReplaceFuncMap[reText].extend([
        cleanDomain,
    ])
    extensionToReplaceFuncMap[reDoxy].extend([
        cleanTKFPath,
    ])
    extensionToReplaceFuncMap[reHtml].extend([
        cleanDomain,
        cleanESport,
        cleanCompany,
    ])
    #     extensionToReplaceFuncMap[reSQL].extend([cleanDomain])
    extensionToReplaceFuncMap[rePy].extend([copyReplaceAnyShell])
    extensionToReplaceFuncMap[reSconsider].extend([copyReplaceAnyShell])
    extensionToReplaceFuncMap[reMake].extend([])


def processFiles(theFiles, fileCopyrightDict, extensionToReplaceFuncMap, doAstyle=False):
    astyleFiles = []
    #     fileCopyrightYear = None
    authdate = getAuthorDate()
    if authdate >= replacementFromDate or True:
        localMap = {}
        for (rex, funcs) in extensionToReplaceFuncMap.iteritems():
            #             if rex == reCpp or rex == reHeader:
            #                 funcs.insert(
            #                     0,
            #                     (strReCopyright,
            #                      lambda mo: replaceHeaderFunc(
            #                          mo,
            #                          headerTemplateC,
            #                          fileCopyrightYear)))
            #             elif rex == reAny or rex == reShell:
            #                 funcs.insert(
            #                     0,
            #                     (strReCopyrightAnyShell,
            #                      lambda mo: replaceHeaderFunc(
            #                          mo,
            #                          headerTemplateAnyShell,
            #                          fileCopyrightYear)))
            localMap.setdefault(rex, funcs)
        for fname in theFiles:
            fname = os.path.normpath(fname)
            if not os.path.isfile(fname):
                continue
            didMatch = False
            didReplace = False
            for (rex, funcs) in localMap.iteritems():
                if rex.search(fname):
                    didMatch = True
                    fileCopyrightDict.get(fname, None)
                    strReplaced = replaceRegexInFile(fname, searchReplace=funcs)
                    if strReplaced:
                        didReplace = True
                        year, _ = getCopyrightYear(strReplaced)
                        if year:
                            copyDate = time.mktime(time.strptime(year, "%Y"))
                            if copyDate >= replacementFromDate:
                                fileCopyrightDict.setdefault(fname, year)
                        if doAstyle and reCpp.search(fname) or reHeader.search(fname):
                            astyleFiles.append(fname)
                    break
            if didMatch and didReplace and options.verbose:
                print('replaced in file {0}'.format(fname))

    if astyleFiles and doAstyle:
        astyleCmd = ["astyle", "--quiet", "--suffix=none", "--mode=c"]
        astyleCmd.extend(astyleFiles)
        proc = subprocess.Popen(astyleCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()


def readDictFromFile(fname):
    import pickle
    retDict = {}
    try:
        fo = open(fname, 'rb')
        if fo:
            tmpDict = pickle.load(fo)
            fo.close()
        for (fname, fdate) in tmpDict.iteritems():
            fname = os.path.normpath(fname)
            dictDate = retDict.get(fname, fdate)
            if fdate < dictDate:
                dictDate = fdate
            retDict[fname] = str(dictDate)
    except IOError:
        pass
    return retDict


def writeDictToFile(fname, outDict):
    import pickle
    try:
        fo = open(fname, 'wb')
        if fo:
            pickle.dump(outDict, fo)
            fo.close()
    except IOError:
        pass


def healDictFile(options, filesToProcess):
    oldDict = readDictFromFile(options.dictfilename)
    newDict = {}
    if oldDict:
        for df in oldDict.keys():
            for knownDir in ['webdisplay2', 'perfTest']:
                if df.startswith(knownDir):
                    newDict[os.path.join('WWW', df)] = oldDict.pop(df)

    newDict.update(oldDict)
    remainingFileList = [f for f in filesToProcess if f not in newDict.keys() and not f.startswith('TKF')]
    remainDict = {}
    for f in remainingFileList:
        Cmd = ["git", "log", "--pretty=format:%ad", "--date=short", "--reverse", "--", f]
        authorDate = 2005
        proc = subprocess.Popen(Cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            popen_out, popen_err = proc.communicate(None)
            if popen_err:
                print >> sys.stderr, popen_err
            if popen_out:
                authorDate = int(popen_out[0:4])
                if authorDate < 2005:
                    authorDate = 2005
                remainDict[f] = str(authorDate)
            proc.returncode
        except OSError as ex:
            print >> sys.stderr, ex
            for line in proc.stderr:
                print >> sys.stderr, line

    for k, v in remainDict.iteritems():
        print('{0} {1}'.format(k, v))

    writeDictToFile(options.dictfilename, newDict)
    sys.exit()


if __name__ == "__main__":
    from optparse import OptionParser

    usage = "usage: %prog [options] <file>..."
    parser = OptionParser(usage=usage)
    parser.add_option("-a",
                      "--allfiles",
                      action="store_true",
                      dest="allfiles",
                      help="process directories and files recursively and ignore command line files",
                      default=False)
    parser.add_option("-s",
                      "--astyle",
                      action="store_true",
                      dest="astyle",
                      help="process modified files using astyle",
                      default=False)
    parser.add_option("-x",
                      "--fileregex",
                      action="append",
                      dest="fileregex",
                      help="process only files matching regular expression, like '" + reCpp.pattern + "'",
                      default=[])
    parser.add_option("-f",
                      "--filepattern",
                      action="append",
                      dest="filepattern",
                      help="process only files matching glob spec, like '*.cpp'",
                      default=[])
    parser.add_option("-d",
                      "--dictfile",
                      action="store",
                      dest="dictfilename",
                      help="write processed entries to FILE",
                      metavar="FILE")
    parser.add_option("-v",
                      "--verbose",
                      action="count",
                      dest="verbose",
                      help="write messages to stderr",
                      default=0)
    parser.add_option("-i",
                      "--ifs",
                      action="store_true",
                      dest="ifs",
                      help="do hsr specific replacements",
                      default=False)
    parser.add_option("-e",
                      "--extra",
                      action="store_true",
                      dest="xtra",
                      help="try to heal a dictfile",
                      default=False)

    (options, positionalArgs) = parser.parse_args()
    if not options.allfiles and len(positionalArgs) < 1:
        sys.exit()

    extensionReList = []
    fileCopyrightDict = {}
    for fre in options.fileregex:
        extensionReList.append(re.compile(fre))
    for fpat in options.filepattern:
        extensionReList.append(re.compile(re.escape(fpat)))
    if not options.fileregex and not options.filepattern:
        extensionReList = fgExtensionReList
    if options.dictfilename:
        fileCopyrightDict = readDictFromFile(options.dictfilename)
    filesToProcess = positionalArgs
    if len(positionalArgs) and options.verbose > 1:
        print "Files to process [%s]" % (str(positionalArgs))
    start = time.clock()
    matchIt = lambda n: not bool(extensionReList)
    for fileRegEx in extensionReList:
        matchIt = lambda n, r=fileRegEx.search, l=matchIt: l(n) or bool(r(n))
    if options.allfiles and len(extensionReList):
        for dirpath, dirnames, filenames in os.walk('.'):
            dirnames[:] = [d for d in dirnames if d not in fgExcludeDirs]
            newfiles = [os.path.join(dirpath, name) for name in filenames]
            filesToProcess.extend(newfiles)

    filesToProcess = [os.path.normpath(f) for f in filesToProcess]
    if options.xtra:
        healDictFile(options, filesToProcess)

    extensionToReplaceFuncMap = fgExtensionToReplaceFuncMap
    if options.ifs:
        extendMapWithHSRSpecifics(extensionToReplaceFuncMap)
        print "Extending for ifs"
    try:
        import WD2Coast
        WD2Coast.extendReplaceFuncMap(extensionToReplaceFuncMap)
        print "Using WD2Coast extensions"
    except:
        pass
    end = time.clock()
    numFiles = len(filesToProcess)
    if options.verbose > 2:
        print "Time elapsed = %ds for %d files" % (end - start, numFiles)
    start = time.clock()
    processFiles(filesToProcess,
                 fileCopyrightDict=fileCopyrightDict,
                 extensionToReplaceFuncMap=extensionToReplaceFuncMap,
                 doAstyle=options.astyle)
    end = time.clock()
    chgElapsed = end - start
    if options.verbose > 2:
        print "Time elapsed = %ds for processing, %ds per file" % (chgElapsed, (chgElapsed / numFiles))

    if options.dictfilename:
        writeDictToFile(options.dictfilename, fileCopyrightDict)
