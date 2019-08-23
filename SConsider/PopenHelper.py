# -------------------------------------------------------------------------
# Copyright (c) 2014, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import shlex
from logging import getLogger

logger = getLogger(__name__)
has_timeout_param = True
try:
    from subprocess32 import Popen, PIPE, STDOUT, TimeoutExpired
except:
    try:
        from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
    except:
        from subprocess import Popen, PIPE, STDOUT

        class TimeoutExpired(Exception):
            def __init__(self):
                pass

        has_timeout_param = False


class PopenHelper(object):
    def __init__(self, command, **kw):
        self.os_except = None
        self.returncode = None
        self.has_timeout = has_timeout_param
        _exec_using_shell = kw.get('shell', False)
        _command_list = command
        if not _exec_using_shell and not isinstance(command, list):
            _command_list = shlex.split(command)
        logger.debug("Executing command: %s with kw-args: %s", _command_list, kw)
        self.po = Popen(_command_list, **kw)

    def communicate(self, stdincontent=None, timeout=10, raise_except=False):
        _kwargs = {'input': stdincontent}
        if self.has_timeout:
            _kwargs['timeout'] = timeout
        try:
            _stdout, _stderr = self.po.communicate(**_kwargs)
        except TimeoutExpired:
            _kwargs = {'input': None}
            if self.has_timeout:
                _kwargs['timeout'] = 5
            self.po.kill()
            _stdout, _stderr = self.po.communicate(**_kwargs)
        except OSError as ex:
            self.os_except = ex
        finally:
            self.returncode = self.po.poll()
            if raise_except:
                raise
        return (_stdout, _stderr)

    def __getattr__(self, name):
        return getattr(self.po, name)
