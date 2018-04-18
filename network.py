# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
import socket
import select
import sys

# server's settings
NB_CONNEXIONS = 4

# communication constants
GET_MAP_STR = "GET MAP".encode()
GET_MODEL_STR = "GET MODEL".encode()
GET_NICKNAME_STR = "GET NICKNAME".encode()


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
        # list of socket
        self.sockList = [self.sock]
        # dict of sockname
        self.nicknames = dict()
        self.update = "NOTHING"

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
            model_str = self.add_bomb_to_str(model_str, bomb)
        # string of all fruits
        for fruit in self.model.fruits :
            model_str = self.add_fruit_to_str(model_str, fruit)
        model_str += "END"
        socket.sendall(model_str.encode())
        ack = socket.recv(1000)

    # transform a character object into a string
    def add_character_to_str(self, str_m, character):
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
        # in case of get model ask
        if message==GET_MODEL_STR:
            self.sendModel(socket)
        #if sended nickname
        else :
            message = message.decode()
            message = message.split(" ")
            if message[0]=="UPDATAMOVE":
                print("ok {}".format(message))
                nickname = self.nicknames[socket]
                direction = int(message[1])
                for cha in self.model.characters:
                    if cha.nickname == nickname:
                        print("found")
                        cha.move(nickname)
                        print("Moved")
                #self.model.move_character(nickname)
                #print("personnage moved")
                self.update += "MOVE {} {} ".format(nickname, direction)

    def broadcast(self, data):
        for s in self.sockList:
            if s != self.sock :
                try:
                    data = data.encode()
                    s.send(data)
                except:
                    s.send(data)

    def disconnectClient(self, sock):
        nickname = self.nicknames[sock]
        print('{} was disconnected.'.format(nickname))
        self.model.kill_character(nickname)
        self.sockList.remove(sock)
        # TODO: envoyer un update de mouvement
        self.nicknames.pop(sock)
        sock.close()
        self.update += "KILL {} ".format(nickname)

    # time event
    def tick(self, dt):
        self.update = ""
        read_list, _, _ = select.select(self.sockList, [], [])
        for sock in read_list:
            # socket server (new client connection)
            if sock == self.sock:
                sclient, addr = self.sock.accept()
                self.sockList.append(sclient)
                print('Connection by', addr)
                nickname = sclient.recv(1500)
                nickname = nickname.decode()
                nickname = nickname.split(" ")
                self.nicknames[sclient] = nickname[2]
                self.model.add_character(nickname[2], isplayer=True)
                sclient.send(b"ACK")
                self.sendModel(sclient)

            # socket client (new client message)
            else:
                # TODO: treat data
                try :
                    data = sock.recv(1500)
                    sock.send(b"ACK")
                    self.treat(data, sock)
                    if data == b'' or data == b'\n' :
                        self.disconnectClient(sock)
                except :
                    self.disconnectClient(sock)
        self.update += "END"
        print(self.update)
        self.broadcast(self.update)
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
        self.update = "UPDATA"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connexion to server
        try :
            self.sock.connect((self.host, self.port))
        except :
            print('Unable to connect to {}. Please try later.'.format(host))
            sys.exit()
        self.sendnickname()
        self.getModel()

    # get initial Model
    def getModel(self):
        #self.sock.sendall(GET_MODEL_STR)
        #ack = self.sock.recv(1000)
        data = self.sock.recv(1500)
        print(data)
        self.sock.send(b"ACK")
        self.treatData(data)

    def sendnickname(self):
        data = "SEND NICKNAME "
        data += self.nickname
        self.sock.sendall(data.encode())
        ack = self.sock.recv(1000)
        print("Nickname send : {}".format(self.nickname))

    def sendData(self, data):
        self.sock.sendall(data)
        ack = self.sock.recv(1000)

    # treat received data for updating the client model
    def treatData(self, data):
        if data==b'':
            print("Connection lost.")
            sys.exit()
        print("Enter in data treatment")
        data_str = data.decode()
        data_a = data_str.split(" ")
        print(data_a)
        i = 0
        while data_a[i]!="END" and data_a[i]!="ACK" and data_a[i]!="ACKEND":
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
                        i+=7
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
                        i+=4
                    i+=1
            #elif data==GET_NICKNAME_STR:
                #self.sock.sendall(self.nickname.encode())
                #ack = self.sock.recv(1000)
            elif data_a[i]=="MOVE":
                if data[i+1]!=self.nickname:
                    self.model.move_character(data_a[i+1], int(data_a[i+2]))
                i += 1
            elif data_a[i]=="KILL":
                self.model.kill_character(data_a[i+1])
                i += 1
            else :
                i+=1

    # keyboard events
    def keyboard_quit(self):
        print("=> event \"quit\"")
        return False

    def keyboard_move_character(self, direction):
        print("=> event \"keyboard move direction\" {}".format(DIRECTIONS_STR[direction]))
        self.update += "MOVE {}".format(direction)
        nickname = self.nickname
        if direction in DIRECTIONS:
            self.model.move_character(nickname, direction)
        return True

    def keyboard_drop_bomb(self):
        print("=> event \"keyboard drop bomb\"")
        # ...
        return True

    # time event
    def tick(self, dt):
        data = self.update.encode()
        print(data)
        self.sendData(data)
        #self.treatData(data)
        self.update = "UPDATA"
        new_data = self.sock.recv(1500)
        self.treatData(new_data)
        return True
