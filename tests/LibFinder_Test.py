# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import unittest
import LibFinder
import itertools


class UniqueTest(unittest.TestCase):

    def setUp(self):
        self.names = []
        self.uniquenames = [
            'Fredi',
            'Heiri',
            "Koebi",
            'Ruedi',
            'Fridolin',
            'Eugen']
        size = len(self.uniquenames)
        for i in range(1, size + 1):
            selector = list(
                itertools.chain(
                    itertools.repeat(
                        1, i), itertools.repeat(
                        0, size - i)))
            self.names.extend(
                [d for d, s in itertools.izip(self.uniquenames, selector) if s])

    def testUnique(self):
        self.assertEqual(self.uniquenames, list(LibFinder.unique(self.names)))

    def testUniqueList(self):
        self.assertEqual(self.uniquenames, LibFinder.uniquelist(self.names))
