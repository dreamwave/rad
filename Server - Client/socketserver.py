# -*- coding: utf-8 -*
import socket, threading
from OpenSSL.SSL import Context, Connection, TLSv1_METHOD

class SocketServer(object):
    """This class is setting up a server that is listining to port 443
    """
    certpath = "ca/cert.pem"
    keypath = "ca/key.pem"
    BUFF = 8192

    def __init__(self, HOST='130.236.219.241', PORT = 443):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = Context(TLSv1_METHOD)
        context.use_certificate_file((self.certpath))
        context.use_privatekey_file(self.keypath) 
        conn = Connection(context,s)
        conn.bind((HOST,PORT))
        print 'Server is listening...'
        conn.listen(5)
        #self.socketclienttable is a dictionary of clients, where each client have an unique id, self.clientid
        self.socketclienttable = {} 
        self.clientid = 0
        threading.Thread(target=self.sendinput).start()
        while True:
        # Waiting for new client to accept, sslsocket is the socket that will be used for communication with this client after a client sets up a connection with the server
            sslsocket, addr = conn.accept()
            self.socketclienttable[self.clientid] = sslsocket
            self.clientid = self.clientid + 1
            threading.Thread(target=self.receive,args=(self.clientid-1,)).start()

    #Handle the clients requests
    def receive(self, id):
        sslsocket = self.socketclienttable[id]
        output = ""
        try: 
            while True:
                data = sslsocket.recv(self.BUFF)
                if data == "start":
                    while True:
                        data = sslsocket.recv(self.BUFF)
                        if data == "end":
                            print output
                            output = ""
                            break
                        output = output + data
        except KeyboardInterrupt:
            sslsocket.close()
            exit()
    
    #sends a string to a specific client 
    def send(self, socket, str):
        socket.write("start")
        totalsent =  0
        while totalsent < str.__len__():
            sent = socket.write(str[totalsent:])
            if sent == 0:
                raise RuntimeError, "socket connection broken"
            totalsent = totalsent + sent
        socket.write("end")

    #Takes input from the server and sends to all clients
    def sendinput(self):
        while True:
            input = raw_input()
            for key, value in self.socketclienttable.iteritems():
                print value
                self.send(value, input)
            print "Treading in sendinput", threading.activeCount()
        return input

server = SocketServer()
