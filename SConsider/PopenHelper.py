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
import sys
from locale import getpreferredencoding
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
            logger.debug("communicating with _kwargs: %s", _kwargs)
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
            logger.debug("Popen returncode: %d, poll() returncode: %d", self.po.returncode, self.returncode)
            if raise_except:
                raise
        return (_stdout, _stderr)

    def __getattr__(self, name):
        return getattr(self.po, name)


class Tee(object):
    def __init__(self):
        self.writers = []
        # Wrap sys.stdout into a StreamWriter to allow writing unicode.
        # https://stackoverflow.com/a/4546129/542082
        #  if not sys.stdout.isatty():
        #      sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
        self._preferred_encoding = getpreferredencoding()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def attach_file(self, writer):
        def flush(stream):
            stream.flush()
            os.fsync(stream.fileno())

        _decoder = (lambda msg: msg.decode(writer.encoding)) if writer.encoding else (lambda msg: msg)
        self.writers.append((writer, _decoder, flush, lambda stream: stream.close()))

    def attach_std(self, writer=sys.stdout):
        def flush(stream):
            stream.flush()

        _decoder = (lambda msg: msg.decode(writer.encoding)) if writer.encoding else (lambda msg: msg)
        self.writers.append((writer, _decoder, flush, lambda _: ()))

    def write(self, message):
        for writer, decoder, _, _ in self.writers:
            if not writer.closed:
                writer.write(decoder(message))

    def flush(self):
        for stream, _, flusher, _ in self.writers:
            flusher(stream)

    def close(self):
        for stream, _, _, closer in self.writers:
            closer(stream)
