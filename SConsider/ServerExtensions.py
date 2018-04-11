"""SConsider.ServerExtensions.

Collection of slightly extended or tailored *Servers mainly used for
testing
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2011, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import socket
import os
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL
from smtpd import SMTPServer
from logging import getLogger
logger = getLogger(__name__)


# creating an SSL enabled HTTPServer
# see http://code.activestate.com/recipes/442473/
class SecureHTTPServer(HTTPServer):
    allow_reuse_address = True

    def __init__(self,
                 server_address,
                 HandlerClass,
                 certFile=None,
                 keyFile=None,
                 caChainFile=None,
                 sslContextMethod=SSL.SSLv23_METHOD,
                 ciphers="ALL"):
        HTTPServer.__init__(self, server_address, HandlerClass, False)
        ctx = SSL.Context(sslContextMethod)
        if keyFile:
            ctx.use_privatekey_file(keyFile)
        if certFile:
            ctx.use_certificate_file(certFile)
        if certFile and keyFile:
            ctx.check_privatekey()
        if ciphers:
            ctx.set_cipher_list(ciphers)
        ctx.set_timeout(60)
        if caChainFile:
            ctx.load_verify_locations(caChainFile)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family, self.socket_type))
        self.server_bind()
        self.server_activate()
        import sys
        import OpenSSL
        if sys.version_info >= (2, 7):
            pyOpensslVersion = tuple(int(t) for t in OpenSSL.__version__.split('.'))
            noMemoryViewsBelow = (0, 12)

            if pyOpensslVersion < noMemoryViewsBelow:
                raise SystemError("""Please upgrade your pyopenssl version to at least 0.12
 as python2.7 is neither interface nor memory view compatible with older pyopenssl versions
Checkout sources and install: bzr branch lp:pyopenssl pyopenssl/
Check https://launchpad.net/pyopenssl for updates

Hint: Check your system for already installed python OpenSSL modules and rename/delete to use the newly installed one
 - known locations (ubuntu): /usr/[lib|share]/pyshared/python2.7/OpenSSL and /usr/lib/python2.7/dist-packages/OpenSSL

Aborting!""")

    # request is of type OpenSSL.SSL.Connection
    def shutdown_request(self, request):
        # (Pdb) inspect.getargspec(OpenSSL.SSL.Connection.shutdown)
        # *** TypeError: <method 'shutdown' of 'OpenSSL.SSL.Connection' objects> is not a Python function
        # it doesn't work for C functions! see http://bugs.python.org/issue1748064
        # only with python 2.7 this function gets called!
        request.shutdown()

    def process_request(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except:
            pass

        try:
            self.shutdown_request(request)
        except:
            pass
        finally:
            try:
                self.close_request(request)
            except:
                pass

    def handle_error(self, request, client_address):
        pass


class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)


class SMTPFileSinkServer(SMTPServer):

    RECIPIENT_COUNTER = {}

    def __init__(self, localaddr, remoteaddr, path, logfile=None):
        SMTPServer.__init__(self, localaddr, remoteaddr)
        self.path = path
        self.log_file = logfile

    def process_message(self, peer, mailfrom, rcpttos, data):
        self.message("Incoming mail")
        for recipient in rcpttos:
            self.message("Capturing mail to %s" % recipient)
            count = self.RECIPIENT_COUNTER.get(recipient, 0) + 1
            self.RECIPIENT_COUNTER[recipient] = count
            filename = os.path.join(self.path, "%s.%s" % (recipient, count))
            filename = filename.replace("<", "").replace(">", "")
            with open(filename, "w") as f:
                f.write(data + "\n")
            self.message("Mail to %s saved" % recipient)
        self.message("Incoming mail dispatched")

    def message(self, text):
        if self.log_file is not None:
            with open(os.path.join(self.path, self.log_file), "a") as f:
                f.write(text + "\n")
        else:
            logger.info(text)
