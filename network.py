# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
import socket
import select
import sys

NB_CONNEXIONS = 4

################################################################################
#                          NETWORK SERVER CONTROLLER                           #
################################################################################

class NetworkServerController:

    def __init__(self, model, port):
        self.model = model
        self.port = port
        # init listen socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.port))
        self.sock.listen(NB_CONNEXIONS)
        #list of socket
        self.sockList = [self.sock]

    # send model to all client
    def sendModel(self, model):
        for sock in sockList:
            if sock != self.sock:
                self.sock.sendto(model, sock)
    # time event
    def tick(self, dt):
        read_list, _, _ = select.select(self.sockList, [], [])
        for sock in read_list:
            # socket server (new client connection)
            if sock == self.sock:
                sclient, addr = self.sock.accept()
                self.sockList.append(sclient)
                print('Connected by', addr)
            # socket client (new client message)
            else:
                while True:
                    # TODO: treat data
                    data = sock.recv(1500)
                    print(data)
                    if data == b'' or data == b'\n' :
                        print('Disconnected by')
                        self.sockList.remove(sock)
                        sock.close()
                        break
        return True

################################################################################
#                          NETWORK CLIENT CONTROLLER                           #
################################################################################

class NetworkClientController:

    def __init__(self, model, host, port, nickname):
        self.model = model
        self.host = host
        self.port = port
        self.nickname = nickname
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connexion to server
        try :
            self.sock.connect((host, port))
        except :
            print('Unable to connect')
            sys.exit()

    # keyboard events
    def keyboard_quit(self):
        print("=> event \"quit\"")
        return False

    def keyboard_move_character(self, direction):
        print("=> event \"keyboard move direction\" {}".format(DIRECTIONS_STR[direction]))
        # ...
        return True

    def keyboard_drop_bomb(self):
        print("=> event \"keyboard drop bomb\"")
        # ...
        return True

    # time event
    def tick(self, dt):
        # ...
        return True
