import unittest
import SomeUtils
import time
import os
from maintenance import ChangeImportLines

testCopyrightHeader = """
/*
 * Copyright (c) 2003 SYNLOGIC
 * All Rights Reserved
 */

fsdfds
"""

testCopyrightHeader2 = """
/* Copyright (c) 2003 SYNLOGIC
 * All Rights Reserved */
fsdfds
"""

testCopyrightHeaderFromToDate = """
/*
 * Copyright (c) 1998-2001 itopia
 * All Rights Reserved
 * hmm what is this

 * $Id$ */


fsdfds
"""

testCopyrightHeader3 = """/*
 * Copyright (c) 2000 itopia
 * All Rights Reserved
 *
 * $Id$
 */

fsdfds
"""

testHeader2007 = """/*
 * Copyright (c) 2007, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
 * All rights reserved.
 *
 * This library/application is free software; you can redistribute and/or modify it under the terms of
 * the license that is included with this library/application in the file license.txt.
 */

fsdfds
"""

testHeaderWhichFailed = """/*
 * Copyright (c) IFS institute for software at HSR Rapperswil, Switzerland
 * Dominik Wild, Marcel Huber
 * Created on: Jul 31, 2009
 */

#ifndef ALLOCATORNEWDELETE_H_
"""

testHeaderWhichFailedExpected = """/*
 * Copyright (c) 2007, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
 * All rights reserved.
 *
 * This library/application is free software; you can redistribute and/or modify it under the terms of
 * the license that is included with this library/application in the file license.txt.
 */

#ifndef ALLOCATORNEWDELETE_H_
"""

testHeaderWhichFailed2 = """/*
 * Copyright (c) 2000 itopia
 * All Rights Reserved
 *
 * initialization of multithreading library
 */

//--- interface include ---------------------------------------------------------
#include "config_mtfoundation.h"
"""

testHeaderWhichFailed2Expected = """/*
 * Copyright (c) 2007, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
 * All rights reserved.
 *
 * This library/application is free software; you can redistribute and/or modify it under the terms of
 * the license that is included with this library/application in the file license.txt.
 */

//--- interface include ---------------------------------------------------------
#include "config_mtfoundation.h"
"""

#result = SomeUtils.multiple_replace([ChangeImportLines.copyReplace], testHeaderWhichFailed)


class CopyrightHeaderTests(unittest.TestCase):

    def testCopyrightReplaceNoAuthorDateUseCurrentDate(self):
        if 'GIT_AUTHOR_DATE' in os.environ:
            os.environ['GIT_AUTHOR_DATE'] = ''
        expected = """/*
 * Copyright (c) """ + time.strftime('%Y', time.gmtime()) + """, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
 * All rights reserved.
 *
 * This library/application is free software; you can redistribute and/or modify it under the terms of
 * the license that is included with this library/application in the file license.txt.
 */

fsdfds
"""
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testCopyrightHeader)
        self.assertEqual(expected, result)

    def testCopyrightReplaceBeforeStartYear(self):
        dateStr = str(int(time.mktime(
            time.strptime('20040101000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testCopyrightHeader)
        self.assertEqual(testCopyrightHeader, result)

    def testCopyrightReplaceUseAuthorDate(self):
        dateStr = str(int(time.mktime(
            time.strptime('20070201000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testCopyrightHeader)
        self.assertEqual(testHeader2007, result)

    def testCopyrightReplaceUseAuthorDateVariant(self):
        dateStr = str(int(time.mktime(
            time.strptime('20070201000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testCopyrightHeader2)
        self.assertEqual(testHeader2007, result)

    def testCopyrightReplaceDoNotOverwriteExistingBefore(self):
        dateStr = str(int(time.mktime(
            time.strptime('20060101000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testHeader2007)
        self.assertEqual(testHeader2007, result)

    def testCopyrightReplaceDoNotOverwriteExistingAfter(self):
        dateStr = str(int(time.mktime(
            time.strptime('20110101000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testHeader2007)
        self.assertEqual(testHeader2007, result)

    def testCopyrightReplaceVariantInput(self):
        dateStr = str(int(time.mktime(
            time.strptime('20070201000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testCopyrightHeaderFromToDate)
        self.assertEqual(testHeader2007, result)

    def testCopyrightFailedHeader(self):
        dateStr = str(int(time.mktime(
            time.strptime('20070201000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testHeaderWhichFailed)
        self.assertEqual(testHeaderWhichFailedExpected, result)

    def testCopyrightFailedHeader2(self):
        dateStr = str(int(time.mktime(
            time.strptime('20070201000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplace],
            testHeaderWhichFailed2)
        self.assertEqual(testHeaderWhichFailed2Expected, result)


testCopyrightAnything = """#--------------------------------------------------------------------
# Copyright (c) 1997 IFA Informatik
# All Rights Reserved
#
# Config: server configuration template
#
# $Id$
#--------------------------------------------------------------------

{
}
"""

testCopyrightHeaderAnyShellExpected = """# -------------------------------------------------------------------------
# Copyright (c) 2007, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

{
}
"""

testCopyrightMakefile = """# Standard Project Makefile
################################################################################
# Copyright (c) 1999-2000 itopia
# All Rights Reserved
#
# $Id$
################################################################################


# -------------------------------------------------------------------------
# Including the generated make support files
"""

testCopyrightMakefileExpected = """# Standard Project Makefile
# -------------------------------------------------------------------------
# Copyright (c) 2007, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# Including the generated make support files
"""

result = SomeUtils.multiple_replace(
    [ChangeImportLines.copyReplaceAnyShell],
    testCopyrightAnything)
result = SomeUtils.multiple_replace(
    [ChangeImportLines.copyReplaceAnyShell],
    testCopyrightMakefile)


class CopyrightHeaderAnythingShellTests(unittest.TestCase):

    def testCopyrightInAnything(self):
        dateStr = str(int(time.mktime(
            time.strptime('20070201000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplaceAnyShell],
            testCopyrightAnything)
        self.assertEqual(testCopyrightHeaderAnyShellExpected, result)

    def testCopyrightInMake(self):
        dateStr = str(int(time.mktime(
            time.strptime('20070201000000', '%Y%m%d%H%M%S')))) + ' some date x y z'
        os.environ['GIT_AUTHOR_DATE'] = dateStr
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.copyReplaceAnyShell],
            testCopyrightMakefile)
        self.assertEqual(testCopyrightMakefileExpected, result)

strIdentNew = """
bla
#if defined(__GNUG__) || defined(__SUNPRO_CC)
    #ident "@(#) $Id$ (c) itopia"
#else
    static char static_c_rcs_id[] = "@(#) $Id$ (c) itopia";
    static char static_h_rcs_id[] = AnythingPerfTest_H_ID;
#endif


fasel
"""

strIdentExpected = """
bla

fasel
"""

strIdentOld1 = """
bla
/* RCS Id */
static char static_c_rcs_id[] = "itopia, ($Id$)";
static char static_h_rcs_id[] = ATTFlowController_H_ID;
#ifdef __GNUG__
#define USE(name1,name2) static void use##name1() { if(!name1 && !name2) { use##name1(); } }
USE(static_h_rcs_id, static_c_rcs_id)
#undef USE
#endif


fasel
"""

strIdentOld1Expected = """
bla
/* RCS Id */
static char static_c_rcs_id[] = "itopia, ($Id$)";
static char static_h_rcs_id[] = ATTFlowController_H_ID;

fasel
"""

strIdentOld2 = """
bla
/* RCS Id */
static char static_c_rcs_id[] = "itopia, ($Id$)";
#ifdef __GNUG__
#pragma implementation
#define USE1(name) static void use##name() { if(!name) { use##name(); } }
USE1(static_c_rcs_id)
#undef USE1
#endif


fasel
"""

strHID = """
bla
#define ATTFlowController_H_ID "itopia, ($Id$)"

fasel
"""

strIdentFailed = """
#ifdef __GNUG__
#pragma implementation
#endif

/* RCS Id */
static char static_c_rcs_id[] = "IFA Informatik AG, ($Id$)";

#include "SecurityModule.h"
static char static_h_rcs_id[] = SecurityModule_H_ID;

#include "Anything.h"
"""

strIdentFailedExpected = """

#include "SecurityModule.h"

#include "Anything.h"
"""

identReplaceGroups = [
    ChangeImportLines.identoldReplace,
    ChangeImportLines.rcsidReplace]
#result = SomeUtils.multiple_replace([ChangeImportLines.identoldReplace], strIdentOld1)


class IdentRemoveTests(unittest.TestCase):

    def testIdentNewReplacement(self):
        result = SomeUtils.multiple_replace(identReplaceGroups, strIdentNew)
        self.assertEqual(strIdentExpected, result)

    def testIdentOldReplacementVariant1(self):
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.identoldReplace],
            strIdentOld1)
        self.assertEqual(strIdentOld1Expected, result)

    def testIdentOldReplacementVariantAll(self):
        result = SomeUtils.multiple_replace(identReplaceGroups, strIdentOld1)
        self.assertEqual(strIdentExpected, result)

    def testIdentOldReplacementVariant2(self):
        result = SomeUtils.multiple_replace(identReplaceGroups, strIdentOld2)
        self.assertEqual(strIdentExpected, result)

    def testHIDReplacement(self):
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.hidReplace],
            strHID)
        self.assertEqual(strIdentExpected, result)

    def testIdentOldReplacementFailed(self):
        result = SomeUtils.multiple_replace(identReplaceGroups, strIdentFailed)
        self.assertEqual(strIdentFailedExpected, result)

strPragmas = """
bla

#ifdef __370__
    #pragma nomargins
#endif


#ifdef __GNUG__
    #pragma implementation
#endif
fasel
"""

strPragmaExpected = """
bla

fasel
"""


class PragmaRemoveTests(unittest.TestCase):

    def testPragmaReplacement(self):
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.pragmaReplace],
            strPragmas)
        self.assertEqual(strPragmaExpected, result)

strNewLineIn1 = """
bla



fasel
"""

strNewLineIn2 = """
bla

fasel
"""

strNewLineExpected = """
bla

fasel
"""


class CleanNewLinesTests(unittest.TestCase):

    def testCleanNewLines1(self):
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.cleanNewLines],
            strNewLineIn1)
        self.assertEqual(strNewLineExpected, result)

    def testCleanNewLines2(self):
        result = SomeUtils.multiple_replace(
            [ChangeImportLines.cleanNewLines],
            strNewLineIn2)
        self.assertEqual(strNewLineExpected, result)
