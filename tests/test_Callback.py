# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from Callback import Callback


class TestCallback(object):
    def setup_method(self, method):
        self.result = None

    def test_CallbackSimple(self):
        def blub():
            self.result = True

        Callback().register('blub_simple', blub)
        Callback().run('blub_simple')
        assert True is self.result

    def test_CallbackDefaults(self):
        def blub(**kw):
            self.result = kw

        Callback().register('blub_defaults', blub, foo='bar')
        Callback().run('blub_defaults')
        assert {'foo': 'bar'} == self.result

    def test_CallbackOverrides(self):
        def blub(**kw):
            self.result = kw

        Callback().register('blub_overrides', blub, foo='bar', bar='foo')
        Callback().run('blub_overrides', foo='blub')
        assert {'foo': 'blub', 'bar': 'foo'} == self.result
