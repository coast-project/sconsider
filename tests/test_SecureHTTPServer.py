# -------------------------------------------------------------------------
# Copyright (c) 2012, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

from ServerExtensions import SecureHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import threading
import socket
import urllib
import Queue
import os


class StartStopMixin(object):
    def __init__(self, poll_interval):
        self._thread = None
        self.poll_interval = poll_interval
        self._ready = threading.Event()

    def start(self):
        self._thread = t = threading.Thread(target=self.serve_forever, args=(self.poll_interval, ))
        t.setDaemon(True)
        t.start()

    def serve_forever(self, poll_interval):
        self._ready.set()
        super(StartStopMixin, self).serve_forever(poll_interval)

    def stop(self):
        self.shutdown()
        self._thread.join()
        self._thread = None
        self._ready.clear()


class StoppableHttpServer(StartStopMixin, SecureHTTPServer):
    def __init__(self, addr, bucket, poll_interval=0.5):
        class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
            def setup(self):
                self.connection = self.request
                self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
                self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

        self.bucket = bucket
        pem_file_name = os.path.join(os.path.dirname(__file__), "server.pem")
        SecureHTTPServer.__init__(self, addr, SecureHTTPRequestHandler, pem_file_name, pem_file_name)
        StartStopMixin.__init__(self, poll_interval)

    def process_request(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except:
            # SSL.Error (GET_CLIENT_HELLO)
            pass

        try:
            self.shutdown_request(request)
        except:
            import sys
            (etype, ) = sys.exc_info()[:2]
            if etype is TypeError:
                self.bucket.put(sys.exc_info())
        finally:
            try:
                self.close_request(request)
            except:
                pass

    def handle_error(self, request, client_address):
        pass


class TestSecureHTTPServer(object):

    server_address = ('127.0.0.1', 8000)

    def setup_method(self, method):
        self.bucket = Queue.Queue()
        self.shttpd = StoppableHttpServer(self.server_address, self.bucket)
        self.shttpd.start()

    def test_StopWithoutException(self):
        try:
            import ssl
            try:
                urllib.urlopen('https://%s:%d/' % self.server_address,
                               context=ssl._create_unverified_context())
            except (TypeError, AttributeError):
                # old version does not take a context argument
                # or _create_unverified_context might not be defined in ssl
                # module
                urllib.urlopen('https://%s:%d/' % self.server_address)
            exc = self.bucket.get(block=True, timeout=1)
            exc_type, exc_obj, exc_trace = exc
            if exc_type is TypeError:
                self.fail("Python 2.7 requires no arguments for request.shutdown")
        except Queue.Empty:
            pass

    def teardown_method(self, method):
        self.shttpd.stop()
