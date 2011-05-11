"""site_scons.ServerExtensions

Collection of slightly extended or tailored *Servers mainly used for testing

"""
#-----------------------------------------------------------------------------------------------------
# Copyright (c) 2009, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or modify it under the terms of
# the license that is included with this library/application in the file license.txt.
#-----------------------------------------------------------------------------------------------------
import socket, os
from SocketServer import BaseServer, TCPServer, BaseRequestHandler
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL, crypto
from smtpd import SMTPServer
## creating an SSL enabled HTTPServer
## see http://code.activestate.com/recipes/442473/

class SecureHTTPServer(HTTPServer):
    allow_reuse_address = True
    def __init__(self, server_address, HandlerClass, certFile=None, keyFile=None, caChainFile=None, sslContextMethod=SSL.SSLv23_METHOD):
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(sslContextMethod)
        if keyFile:
            ctx.use_privatekey_file (keyFile)
        if certFile:
            ctx.use_certificate_file(certFile)
        if certFile and keyFile:
            ctx.check_privatekey()
        ctx.set_timeout(60)
        if caChainFile:
            ctx.load_verify_locations(caChainFile)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,self.socket_type))
        self.server_bind()
        self.server_activate()
        import sys, OpenSSL
        if sys.version_info >= (2,7) and float(OpenSSL.__version__) <= 0.12:
            # beginning with python 2.7, shutdown does not take an argument anymore
            # as pyopenssl <= 0.12 is currently not aware of this, we must catch it here
            self.shutdown_request = self.shutdown_request_fix

    def shutdown_request_fix(self, request):
        """Called to shutdown and close an individual request."""
        try: request.shutdown()
        except: pass

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
        self.log_file=logfile

    def process_message(self, peer, mailfrom, rcpttos, data):
        self.message("Incoming mail")
        for recipient in rcpttos:
            self.message("Capturing mail to %s" % recipient)
            count = self.RECIPIENT_COUNTER.get(recipient, 0) + 1
            self.RECIPIENT_COUNTER[recipient] = count
            filename = os.path.join(self.path, "%s.%s" % (recipient, count))
            filename = filename.replace("<", "").replace(">", "")
            f = file(filename, "w")
            f.write(data + "\n")
            f.close()
            self.message("Mail to %s saved" % recipient)
        self.message("Incoming mail dispatched")

    def message(self, text):
        if self.log_file is not None:
            f = file(os.path.join(self.path,self.log_file), "a")
            f.write(text + "\n")
            f.close()
        else:
            print text
