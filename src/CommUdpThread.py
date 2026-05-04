import socket
import struct
import threading
from typing import Tuple
import queue
import time
import select

PLANEINFO_STRUCT_FORMAT = '<Ibfffffff' #(messageType, planeID, X, Y, Z, Roll, Pitch, Yaw, Health)
DAMAGEINFO_STRUCT_FORMAT = '<Ibbf'
GAMECONTROL_STRUCT_FORMAT = '<Ib'
INIT_STRUCT_FORMAT = '<Iffffffffffff'
SIMSTATE_STRUCT_FORMAT = '<Ib'
VP_STRUCT_FORMAT = '<Ibfff'
CMD_STRUCT_FORMAT = '<Ibffff'

class CommUDP(threading.Thread):
    def __init__(self, viewerIP:str, viewerPORT:int, 
                 command_event:threading.Event, init_event:threading.Event, 
                 out_q:queue.Queue):
        super().__init__(daemon=True)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._viewer_IP = viewerIP
        self._viewer_PORT = viewerPORT
        self._bufsize = 100
        #self._socket.bind(('', self._viewer_PORT))
        
        # timeout = 0.5
        # self._socket.settimeout(timeout)
        
        self._command_event = command_event
        self._init_event = init_event
        self.out_q = out_q
        
    def __del__(self):
        self._socket.close()
        
    def send_planeInfo(self, flight_state:dict):
        
        packet = struct.pack(PLANEINFO_STRUCT_FORMAT, 2, flight_state[0]
                            , flight_state[1], flight_state[2], flight_state[3]
                            , flight_state[4], flight_state[5], flight_state[6]
                            , flight_state[7])
        
        self._socket.sendto(packet, (self._viewer_IP, self._viewer_PORT))
        # print("send plane info")
        
    def send_damageInfo(self, type:int, damage:float):
        if type == 1: # attacker: ownship
            packet = struct.pack(DAMAGEINFO_STRUCT_FORMAT, 3, 0, 1, damage)
        else:
            packet = struct.pack(DAMAGEINFO_STRUCT_FORMAT, 3, 1, 0, damage)            
        self._socket.sendto(packet, (self._viewer_IP, self._viewer_PORT))
        # print("send damage info")
        
    def send_simState(self):
        packet = struct.pack(SIMSTATE_STRUCT_FORMAT, 4, 1)
        self._socket.sendto(packet, (self._viewer_IP, self._viewer_PORT))
        # print("send sim state")        
        
    def send_VP(self, planeID, VP):
        packet = struct.pack(VP_STRUCT_FORMAT, 5, planeID, VP[0], VP[1], VP[2])
        self._socket.sendto(packet, (self._viewer_IP, self._viewer_PORT))
        #print("send simstate")
        #print("x: ", VP[0], "y: ", VP[1], "z: ", VP[2])
        
    def send_CMD(self, planeID, CMD):
        packet = struct.pack(CMD_STRUCT_FORMAT, 6, planeID, CMD[0], CMD[1], CMD[2], CMD[3])
        self._socket.sendto(packet, (self._viewer_IP, self._viewer_PORT))
        #print("Roll: ", CMD[0], "Pitch: ", CMD[1], "Yaw: ", CMD[2], "Throttle: ", CMD[3])
        
    def run(self): # receive packet
        while True:
            # print("wait for message")
            readable, _, _ = select.select([self._socket], [], [], 0.5)
            if readable:
                data, addr = self._socket.recvfrom(self._bufsize)
                messageType = struct.unpack('I', data[:4])
                if len(data) > 0:
                    if messageType[0] == 0:                        
                        print("receive Game Control")
                        if data[4] == 0:
                            self._command_event.set() # set True
                            print("Start!")
                        elif data[4] == 1:
                            self._command_event.clear() # set False
                            print("Stop!")
                        
                    elif messageType[0] == 1:
                        print("receive Init State!")
                        init_state = struct.unpack(INIT_STRUCT_FORMAT, data)
                        self.out_q.put((time.time(), init_state[1:]))
                        self._init_event.set()