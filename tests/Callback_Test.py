# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import unittest
import Callback


class CallbackTest(unittest.TestCase):

    def setUp(self):
        Callback.addCallbackFeature(__name__)
        self.result = None

    def testCallbackSimple(self):
        def blub():
            self.result = True

        registerCallback('blub', blub)
        runCallback('blub')
        self.assertEqual(True, self.result)

    def testCallbackDefaults(self):
        def blub(**kw):
            self.result = kw

        registerCallback('blub', blub, foo='bar')
        runCallback('blub')
        self.assertEqual({'foo': 'bar'}, self.result)

    def testCallbackOverrides(self):
        def blub(**kw):
            self.result = kw

        registerCallback('blub', blub, foo='bar', bar='foo')
        runCallback('blub', foo='blub')
        self.assertEqual({'foo': 'blub', 'bar': 'foo'}, self.result)
