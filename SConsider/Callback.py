"""SConsider.Callback.

Provide callback function support

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

import sys


class Callback(object):

    def __init__(self):
        self.callbacks = {}

    def register(self, signalname, func, **kw):
        if callable(func):
            self.callbacks.setdefault(signalname, []).append((func, kw))

    def call(self, signalname, **overrides):
        for func, kw in self.callbacks.get(signalname, []):
            kw.update(overrides)
            func(**kw)


def addCallbackFeature(modulename):
    callback = Callback()

    def registerCallback(signalname, func, **kw):
        callback.register(signalname, func, **kw)

    def runCallback(signalname, **overrides):
        callback.call(signalname, **overrides)

    __import__(modulename)
    module = sys.modules[modulename]
    module.registerCallback = registerCallback
    module.runCallback = runCallback
