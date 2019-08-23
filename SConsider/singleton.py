"""SConsider.singleton.

Helper decorator to mark a class as a singleton class
"""

# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2016, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------


class SingletonDecorator:
    """Decorator class inspired by http://python-3-patterns-idioms-
    test.readthedocs.io/en/latest/Singleton.html."""
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)
        return self.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)
