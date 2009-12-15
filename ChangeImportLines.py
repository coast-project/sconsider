import os, pdb, re, time
from SomeUtils import *

excludelist = ['build', 'CVS', 'data', 'xml', 'doc', 'bin', 'lib', '.git', '.gitmodules']

reCpp=re.compile('^.*.cpp$')
reHeader=re.compile('^.*\.hp*$')
reLibPy=re.compile('^.*Lib\.py$')
reScons=re.compile('^SConscript$')
reShell=re.compile('^.*\.sh$')
reAny=re.compile('^.*\.any$')

# ChangePackageName
#RegexReplace(lambda d,f: reLibPy.match(f), r"string.replace\(([\w_]+),\s*'Lib',\s*''\)", lambda g,it: "StanfordUtils.getPackageName(" + g[0] + ")" )

# remove #ident from c++ source files
#if defined(__GNUG__) || defined(__SUNPRO_CC)
    #ident "@(#) $Id$ (c) itopia"
#else
    #define AnythingPerfTest_H_ID "@(#) $Id$ (c) itopia"
#    static char static_c_rcs_id[] = "@(#) $Id$ (c) itopia";
#    static char static_h_rcs_id[] = AnythingPerfTest_H_ID;
#endif
#RegexReplace(lambda d,f: reCpp.match(f) or reHeader.match(f), r"^(#if.*$\s+#ident.*$\s+#else\s+(#?\w+.*$\s+){1,2}#endif\s*$\s)", "")

#ifdef __370__
    #pragma nomargins
#endif
#ifdef __GNUG__
    #pragma implementation
#endif
#RegexReplace(lambda d,f: reCpp.match(f) or reHeader.match(f), r"^([ \t]*#if.*$\s+#pragma\s+(nomargins|implementation|interface)\s*$\s+#endif\s*$\s)", "")

#/*
# * Copyright (c) 2003 SYNLOGIC
# * All Rights Reserved
# */
newheader="""/*
 * Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
 * All rights reserved.
 *
 * This library/application is free software; you can redistribute and/or modify it under the terms of
 * the license that is included with this library/application in the file license.txt.
 */"""
startHeaderReplacementFrom=time.mktime(time.strptime('20050101000000','%Y%m%d%H%M%S'))
reCopyYear=r"(Copyright \(c\) )(\d{4})(, Peter Sommerlad)"

def replaceHeaderFunc(g, it):
    # get commit date
    commitYear=time.strftime('%Y', time.gmtime())
    comdate=0.0
    dateStr=os.environ.get('GIT_COMMITTER_DATE','')
    if dateStr:
        comdate=float(dateStr.split()[0])
        commitYear=time.strftime('%Y', time.gmtime(comdate))
    # compare old and current header string to not overwrite existing data
    chgHeader=newheader
    if comdate >= startHeaderReplacementFrom:
        needReplace=True
        if len(g[0]) == len(newheader):
            crMatch=re.search(reCopyYear, g[0])
            if crMatch:
                # first commit was in year strYear
                strYear=crMatch.group(2)
                chgHeader=g[0]
                needReplace=False
        if needReplace:
            def replaceYear(gX,itX):
                return gX[0] + commitYear + gX[2]
            # if string is equal already, it returns None
            yearHeader=DoReplaceInString(newheader, reCopyYear, replaceYear)
            if yearHeader:
                chgHeader=yearHeader
    return chgHeader

#RegexReplace(lambda d,f: reCpp.match(f) or reHeader.match(f), r"^([ \t]*//?\*.*\s+(\s*\*(?!/).*)*(\s*\*/))", replaceHeaderFunc)
RegexReplace(lambda d,f: reCpp.match(f) or reHeader.match(f), searchReplace=[(r"^(#if.*$\s+#ident.*$\s+#else\s+(#?\w+.*$\s+){1,2}#endif\s*$\s)", ""),
                                                               (r"^([ \t]*#if.*$\s+#pragma\s+(nomargins|implementation|interface)\s*$\s+#endif\s*$\s)", ""),
                                                               (r"^([ \t]*//?\*.*\s+(\s*\*(?!/).*)*(\s*\*/))", replaceHeaderFunc)
                                                               ], excludelist=excludelist)

fstr='/*\n * Copyright (c) 2003 SYNLOGIC\n * All Rights Reserved\n */\n\n#if defined(__GNUG__) || defined(__SUNPRO_CC)\n    #ident "@(#) $Id$ (c) itopia"\n#else\n    static char static_c_rcs_id[] = "@(#) $Id$ (c) itopia";\n    static char static_h_rcs_id[] = AnythingPerfTest_H_ID;\n#endif\n\nfsdfds\nfsfds\n\n'
#strout=DoReplaceInString(fstr, r"^([ \t]*//?\*.*\s+(\s*\*(?!/).*)*(\s*\*/))", newheader)
