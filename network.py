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

    # send model to client sockets
    def sendModel(self, socket, sendMap = False):
        model_str = "MODEL "
        # if client ask for map
        if sendMap == True :
            model_str += str(self.model.map)
            #sendMap()
        # string of all characters
        for character in self.model.characters :
            model_str = self.add_character_to_str(model_str, character)
        # string of all bombs
        for bomb in self.model.bombs :
            model_str = self.add_bomb_to_str(model_str, character)
        # string of all fruits
        for fruit in self.model.fruits :
            model_str = self.add_fruit_to_str(model_str, fruit)
        model_str += "END"
        socket.send(model_str.encode())

    # transform a character object into a string
    def add_character_to_str(self, str, character):
        str_m += "CHARACTER "
        str_m += str(character.kind) + " "
        str_m += str(character.health) + " "
        str_m += str(character.immunity) + " "
        str_m += str(character.disarmed) + " "
        str_m += str(character.nickname) + " "
        str_m += str(character.pos[0]) + " " + str(character.pos[1]) + " "
        str_m += str(character.direction) + " "
        return str_m

    # transform a bomb object into string
    def add_bomb_to_str(self, str_m, bomb):
        str_m+= "BOMB "
        str_m += str(bomb.pos) + " "
        str_m += str(bomb.max_range) + " "
        str_m += str(bomb.countdown) + " "
        str_m += str(bomb.time_to_explode) + " "
        return str_m

    # transform a fruit object into string
    def add_fruit_to_str(self, str_m, fruit):
        str_m += "FRUIT "
        str_m += str(fruit.pos[0]) + " " + str(fruit.pos[1]) + " "
        str_m += str(fruit.kind) + " "
        return str_m

    # treat a received message
    def treat(self, message, socket):
        if message==b"GET":
            self.sendModel(socket)

    # time event
    def tick(self, dt):
        read_list, _, _ = select.select(self.sockList, [], [])
        for sock in read_list:
            # socket server (new client connection)
            if sock == self.sock:
                sclient, addr = self.sock.accept()
                self.sockList.append(sclient)
                print('Connection by', addr)
                # TODO: add character
            # socket client (new client message)
            else:
                while True:
                    # TODO: treat data
                    data = sock.recv(1500)
                    self.treat(data, sock)
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
            self.sock.connect((self.host, self.port))
        except :
            print('Unable to connect to {}. Please try later.'.format(host))
            sys.exit()
        self.getModel()

    # get initial Model
    def getModel(self):
        self.sock.send(b"GET")
        data = self.sock.recv(1500)
        self.treatData(data)

    # treat received data for updating the client model
    def treatData(self, data):
        data = data.decode()
        data_a = data.split(" ")
        i = 0
        # get the original model
        if data_a[i]=="MODEL":
            while data_a[i]!="END":
                # add a fruit
                if data_a[i]=="FRUIT":
                    self.model.add_fruit(int(data_a[i+3]), (int(data_a[i+1]), int(data_a[i+2])))
                    i+=3
                # add a character
                elif data_a[i]=="CHARACTER":
                    kind_c = int(data_a[i+1])
                    health_c = int(data_a[i+2])
                    immunity_c = float(data_a[i+3])
                    disarmed_c = float(data_a[i+4])
                    nickname_c = data_a[i+5]
                    position = (int(data_a[i+6]), int(data_a[i+7]))
                    direction_c = data_a[i+8]
                    self.model.add_character(nickname_c, isplayer=True, kind=kind_c, pos=position)
                    for character in self.model.characters :
                        if character.nickname == nickname_c :
                            character.immunity = immunity_c
                            character.disarmed = disarmed_c
                            character.health = health_c
                    i+=8
                # add a bomb
                elif data_a[i]=="BOMB":
                    position = (int(data_a[i+1], int(data_a[i+2])))
                    max_range_b = int(data_a[i+3])
                    countdown_b = int(data_a[i+4])
                    time_to_explode_b = float(data_a[i+5])
                    self.model.bombs.append(Bomb(self.map, position))
                    self.model.bombs[-1].countdown = countdown_b
                    self.model.bombs[-1].time_to_explode = time_to_explode_b
                    self.model.bombs[-1].max_range = max_range_b
                    i+=5
                i+=1

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
        #self.getModel()
        return True
