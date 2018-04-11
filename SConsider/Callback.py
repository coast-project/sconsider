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

import inspect
import pprint
from logging import getLogger
from SConsider.singleton import SingletonDecorator
logger = getLogger(__name__)


@SingletonDecorator
class Callback(object):
    def __init__(self):
        self.callbacks = {}

    def register(self, signalname, func, **kw):
        if callable(func):
            self.callbacks.setdefault(signalname, []).append((func, kw))

    def run(self, signalname, **overrides):
        frame = inspect.currentframe().f_back
        filename = inspect.getfile(frame.f_code)
        lineno = frame.f_lineno
        logger.info("running %s callback from %s:%s", signalname, filename, lineno)
        for func, kw in self.callbacks.get(signalname, []):
            kw.update(overrides)
            logger.debug("  calling %s.%s with args %s", func.__module__, func.func_name, pprint.pformat(kw))
            func(**kw)
