# -*- coding: utf-8 -*
import socket, threading, sys, select, struct, time
from Queue import Queue
from os import popen
from shared import buffrify, packet

class Connection(object):
    
    pingtime = 3

    def __init__(self, socket, addr):
        self.addr, self.port = addr
        self.socket = socket
        self.id = socket.fileno()
        self.out_queue = Queue()
        self.out_buffer = ""
        self.in_queue = Queue()
        self.in_buffer = ""
        self.timestamp = time.time()
        self.timepinged = 0

client_sockets = {}
connections = {}
clientrequests = {}

host_addr = "130.236.76.135"
host_port = 442

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, struct.pack("i",1))
s.bind((host_addr, host_port))
s.setblocking(0)
s.settimeout(0)
s.listen(5)

print "Server igång på %s:%s" % (host_addr, host_port)
while True:
    try:
        acceptor = select.select([s,], [s,], [s,], 0)[0]
        if acceptor:
            newsocket, addr = s.accept()
            client_sockets[newsocket.fileno()] = newsocket
            connections[newsocket.fileno()] = Connection(newsocket, addr)

            print "new connected %s: %s, %s" % (newsocket.fileno(), newsocket, addr)
            print client_sockets

        read_list, write_list, error_list = select.select(
            client_sockets.values(),
            client_sockets.values(),
            client_sockets.values(), 0)
        to_be_removed = []

        for sock in read_list:
            # TODO: fixa in_buffern :p
            # och in_queue
            connection = connections[sock.fileno()]
            print "läsa från %s" % sock.fileno()
            read = sock.recv(1024)
            if read != "":
                connection.in_buffer += read
                can_split = buffrify.split_buffer(connection.in_buffer)
                if can_split is not None:
                    connection.in_buffer = can_split[1]
                    read = can_split[0]
                    print "lägger till %s" % read
                    sendpacket = packet.Packet.from_net(read)
                    if packet.type in clientrequests:
                        print "Ditt packet du kör request på: ", str(sendpacket)
                        clientrequests[packet.type](sendpacket)
                    for fileno, connection in connections.iteritems():
                        if sock.fileno() != fileno:
                            connection.out_queue.put("%s hälsar: %s" % \
                                    (sock.fileno(), read))
            else:
                to_be_removed.append(sock.fileno())


        for sock in write_list:
            connection = connections[sock.fileno()]

            if connection.out_buffer == "" and \
                not connection.out_queue.empty():
                connection.out_buffer = buffrify.create_pack(str(connection.out_queue.get()))
                print "ska skriva %s till.... %s" % (connection.out_buffer, sock.fileno())

            if connection.out_buffer != "":
                sent = sock.send(connection.out_buffer)
                if sent != len(connection.out_buffer):
                    connection.out_buffer = connections[sock.fileno()].out_buffer[sent:]
                else:
                    connections[sock.fileno()].out_buffer = ""

        for sock in error_list:
            print "fel på %s" % sock.fileno()

        # logics
        for fileno, connection in connections.iteritems():
            if time.time()-connection.timestamp > connection.pingtime: 
                connection.timestamp = time.time()
                if connection.timepinged == 3:
                    print "You tried to connect to klient:" , connection.socket.fileno() , \
                            "three times you will now remove that client" 
                    connection.timepinged == 0
                    to_be_removed.append(connection.socket.fileno())
                else:
                    connection.timepinged = connection.timepinged + 1
                    ping = packet.Packet("ping")
                    connection.out_queue.put(ping)

        for id in to_be_removed:
            connections[id].socket.close()
            client_sockets[id].close()
            del connections[id]
            del client_sockets[id]

    except KeyboardInterrupt:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        for sock in client_sockets.values():
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
    except socket.error:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        for sock in client_sockets.values():
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()

def pong(hax):
    print "Sätter ny timestamp"
    connection.timestamp = time.time()
    connection.timepinged = 0
clientrequests["pong"] = pong

def login(hax):
    pass
clientrequests["login"] = login
