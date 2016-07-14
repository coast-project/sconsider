# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import LibFinder
import itertools


class TestUnique(object):
    def setup_method(self, method):
        self.names = []
        self.uniquenames = [
            'Fredi', 'Heiri', "Koebi", 'Ruedi', 'Fridolin', 'Eugen'
        ]
        size = len(self.uniquenames)
        for i in range(1, size + 1):
            selector = list(itertools.chain(
                itertools.repeat(1, i), itertools.repeat(0, size - i)))
            self.names.extend(
                [d for d, s in itertools.izip(self.uniquenames, selector) if s])

    def test_Unique(self):
        assert self.uniquenames == list(LibFinder.unique(self.names))

    def test_UniqueList(self):
        assert self.uniquenames == LibFinder.uniquelist(self.names)
