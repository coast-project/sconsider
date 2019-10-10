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
import os
from locale import getpreferredencoding
import time
from threading import Timer, Thread, Event
from tempfile import NamedTemporaryFile
from logging import getLogger

logger = getLogger(__name__)
has_timeout_param = True
try:
    from subprocess32 import Popen, PIPE, STDOUT, TimeoutExpired, CalledProcessError
except:
    try:
        from subprocess import Popen, PIPE, STDOUT, TimeoutExpired, CalledProcessError
    except:
        from subprocess import Popen, PIPE, STDOUT

        # Exception classes copied over from subprocess32
        class CalledProcessError(Exception):
            """This exception is raised when a process run by check_call() or
            check_output() returns a non-zero exit status.

            The exit status will be stored in the returncode attribute;
            check_output() will also store the output in the output
            attribute.
            """
            def __init__(self, returncode, cmd, output=None):
                self.returncode = returncode
                self.cmd = cmd
                self.output = output

            def __str__(self):
                return "Command '%s' returned non-zero exit status %d" % (self.cmd, self.returncode)

        class TimeoutExpired(Exception):
            """This exception is raised when the timeout expires while waiting
            for a child process."""
            def __init__(self, cmd, timeout, output=None):
                self.cmd = cmd
                self.timeout = timeout
                self.output = output

            def __str__(self):
                return ("Command '%s' timed out after %s seconds" % (self.cmd, self.timeout))

        has_timeout_param = False


class PopenHelper(object):
    def __init__(self, command, **kw):
        self.returncode = None
        self.has_timeout = has_timeout_param
        _exec_using_shell = kw.get('shell', False)
        _command_list = command
        if not _exec_using_shell and not isinstance(command, list):
            _command_list = shlex.split(command)
        logger.debug("Executing command: %s with kw-args: %s", _command_list, kw)
        self.po = Popen(_command_list, **kw)

    def communicate(self, stdincontent=None, timeout=10):
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
            # raised if the executed program cannot be found
            logger.debug(ex)
        finally:
            self.returncode = self.po.poll()
            logger.debug("Popen returncode: %d, poll() returncode: %d", self.po.returncode, self.returncode)
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
        while self.writers:
            stream, _, _, closer = self.writers.pop()
            closer(stream)


#https://stackoverflow.com/a/54868710/542082
class ProcessRunner(object):
    def __init__(self, args, timeout=None, bufsize=-1, seconds_to_wait=0.25, **kwargs):
        """Constructor facade to subprocess.Popen that receives parameters
        which are more specifically required for the.

        Process Runner. This is a class that should be used as a context manager - and that provides an iterator
        for reading captured output from subprocess.communicate in near realtime.

        Example usage:

        exitcode = -9
        with Tee() as tee:
            tee.attach_std()
            process_runner = None
            try:
                with ProcessRunner(('ls', '-lAR', '.'), seconds_to_wait=0.25) as process_runner:
                    for out, err in process_runner:
                        tee.write(out)
                    exitcode = process_runner.returncode
            except CalledProcessError as e:
                logger.debug("non-zero exitcode: %s", e)
            except TimeoutExpired as e:
                logger.debug(e)
            except OSError as e:
                logger.debug("executable error: %s", e)
                # follow shell exit code
                exitcode = 127
            except Exception as e:
                logger.debug("process creation failure: %s", e)
            finally:
                if process_runner:
                    exitcode = process_runner.returncode

        :param args: same as subprocess.Popen
        :param timeout: same as subprocess.communicate
        :param bufsize: same as subprocess.Popen
        :param seconds_to_wait: time to wait between each readline from the temporary file
        :param kwargs: same as subprocess.Popen
        """
        self._seconds_to_wait = seconds_to_wait
        self._process_has_timed_out = False
        self._timeout = timeout
        self._has_timeout = has_timeout_param
        self._process_done = False
        self._stdout_file_handle = NamedTemporaryFile()
        self._stderr_file_handle = kwargs.pop('stderr', None)
        # DEVNULL and STDOUT will be passed through
        # redirect to err file otherwise
        if self._stderr_file_handle in (None, PIPE):
            self._stderr_file_handle = NamedTemporaryFile()
        self._stdin_handle = kwargs.pop('stdin_handle', None)
        if not self._stdin_handle is None:
            kwargs.setdefault('stdin', PIPE)

        _exec_using_shell = kwargs.get('shell', False)
        self._command_list = args
        if not _exec_using_shell and not isinstance(args, list) and not isinstance(args, tuple):
            self._command_list = shlex.split(args)
        logger.debug("Executing command: %s with kwargs: %s", self._command_list, kwargs)

        self._process = Popen(self._command_list,
                              bufsize=bufsize,
                              stdout=self._stdout_file_handle,
                              stderr=self._stderr_file_handle,
                              **kwargs)
        self._thread = Thread(target=self._run_process)
        self._thread.daemon = True

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._thread.join()
        self._stdout_file_handle.close()
        # for newer versions, DEVNULL should also be masked
        if not self._stderr_file_handle == STDOUT:
            self._stderr_file_handle.close()

    def __iter__(self):
        # read all output from stdout file that subprocess.communicate fills
        _firstiter = True
        _stderr = None
        _err = ''
        try:
            if not self._stderr_file_handle == STDOUT:
                _stderr = open(self._stderr_file_handle.name, 'r')
            with open(self._stdout_file_handle.name, 'r') as _stdout:
                # while process is alive, keep reading data
                while not self._process_done:
                    _out = _stdout.readline()
                    if _stderr:
                        _err = _stderr.readline()
                    if _out or _err:
                        yield (_out, _err)
                    else:
                        # if there is nothing to read, then please wait a tiny little bit
                        if _firstiter:
                            time.sleep(0.001)
                            _firstiter = False
                            continue
                        logger.debug("Command %s (pid: %s) has nothing to read from, sleeping for %ss",
                                     self._command_list, self._process.pid, self._seconds_to_wait)
                        time.sleep(self._seconds_to_wait)

                # catch writes to buffer after process has finished
                _out = _stdout.read()
                if _stderr:
                    _err = _stderr.read()
                if _out or _err:
                    yield (_out, _err)
        finally:
            if _stderr:
                _stderr.close()

        if self._process_has_timed_out:
            raise TimeoutExpired(self._command_list, self._timeout)

        if self._process.returncode != 0:
            raise CalledProcessError(self.returncode, self._command_list)

    def _run_process(self):
        try:
            # Start gathering information (stdout and stderr) from the opened process
            self._process.communicate(input=self._stdin_handle, timeout=self._timeout)
            # Graceful termination of the opened process
            self._process.terminate()
        except TimeoutExpired:
            # Force termination of the opened process
            self._process.terminate()
            self._process.communicate(timeout=5.0)
            self._process_has_timed_out = True

        self._process_done = True

    @property
    def returncode(self):
        return self._process.returncode
