from enum import Enum, IntEnum
from dataclasses import dataclass
import struct
import numpy as np

class MessageType(Enum):
    MT_GameControl = 0
    MT_Init = 1
    MT_PlaneInfo = 2
    MT_Damage = 3
    MT_SimState = 4
    MT_VP = 5
    MT_CMD = 6

    
@dataclass
class Vector3D:
    X:float
    Y:float
    Z:float
    
@dataclass
class Rotation3D:
    Roll:float
    Pitch:float
    Yaw:float
    
@dataclass
class GameControl:
    Type:MessageType
    command:np.int8_t
    
@dataclass
class Init:
    Type:MessageType
    Plane1Location:Vector3D
    Plane1Rotation:Rotation3D
    Plane2Location:Vector3D
    Plane2Rotation:Rotation3D
    
@dataclass
class PlaneInfo:
    Type:MessageType
    PlaneID:np.int8_t
    Position:Vector3D
    Rotation:Rotation3D
    Health:float
    
@dataclass
class DamageInfo:
    Type:MessageType
    PlaneID_Attacker:np.int8_t
    PlaneID_Victim:np.int8_t
    DamageAmount:float
    
@dataclass
class VP:
	Type:MessageType
	PlaneID:np.int8_t
	VP:Vector3D

@dataclass
class CMD:
    Type:MessageType
    PlaneID:np.int8_t
    RollCMD:np.float
    PitchCMD:np.float
    YawCMD:np.float
    ThrottleCMD:np.float