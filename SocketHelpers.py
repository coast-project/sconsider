import socket, time, pdb
import threading, KillableThread

def sockrecv( sock, chunksize = 4096 ):
    msg = ''
    chunk = sock.recv( chunksize )
    msg = msg + chunk
    while len( chunk ) == chunksize:
        chunk = sock.recv( chunksize )
        if chunk == '':
            raise RuntimeError, \
                "socket connection broken"
        msg = msg + chunk
    return msg

class AcceptorThread( KillableThread.KillableThread ):
    def __init__( self, addr, port, callback, protocol = socket.AF_INET, backlog = 1 ):
        KillableThread.KillableThread.__init__( self )
        self.addr = addr
        self.port = port
        self.backlog = backlog
        self.protocol = protocol
        self.callback = callback
        self.__terminate = False
        #create an INET, STREAMing socket
        self.serversocket = socket.socket( self.protocol, socket.SOCK_STREAM )
        # avoid timeout until re use of address is possible
        self.serversocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

    def run( self ):
        try:
            #bind the socket to a public host,
            # and a well-known port
            self.serversocket.bind( ( self.addr, self.port ) )
            # become a server socket and limit max connects
            self.serversocket.listen( self.backlog )
            while not self.__terminate:
                print "waiting on connect..."
                ( clientsocket, address ) = self.serversocket.accept()
                print "...connected to", address
                self.callback( sock = clientsocket, addr = address )

        finally:
            self.serversocket.close()
            self.serversocket = None
            print "simpleListener terminated"

    def terminate( self ):
        self.__terminate = True
        s = socket.socket( self.protocol, socket.SOCK_STREAM )
        try:
            s.connect( ( self.addr, self.port ) )
            s.send( '__KILLED__' )
            bla = sockrecv( s )
        finally:
            s.close()
            s = None
