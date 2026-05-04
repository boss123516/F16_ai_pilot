# -*- coding: utf-8 -*-
# AIAICE JSBSimWrapper.py V.0.7.3((2022.04.18))
# JSBSim FDM and Rule based AI pilot model are separated

# AIAICE JSBSimWrapper.py V.0.7.2
# #theta = root.find("alpha")#2022.01.28
# #theta = root.find("theta")#2022.01.28
# gamma = root.find("gamma")#2022.02.08
# gamma.text = str(Init_Pitch)#2022.02.08

# AIAICE JSBSimWrapper.py V.0.7.1
# #theta = root.find("alpha")#2022.01.28
# theta = root.find("theta")#2022.01.28

# AIAICE JSBSimWrapper.py V.0.7
# 1. Add intial speed paramater in def __init__()  
# 2. Add PurePursuitRun()
# Next

# AIAICE JSBSimWrapper.py V.0.6
# 1. Add locking access xml files for jsbsim

# AIPILOTDLL v1.1.2 Added 2023.02.03
# 1. class AIPilotDLL_Adv added.

import ctypes as ct
import os
import math
import struct
from xml.etree.ElementTree import parse
from filelock import Timeout, FileLock

class J_NavigationData(ct.Structure):
    _pack_ = 1
    _fields_ = [
        ("Header", ct.c_uint8 * 2), ("Counter", ct.c_uint8), ("SimTime", ct.c_double), ("AircraftModel", ct.c_uint8),("AircraftID", ct.c_uint8),
        ("Lat", ct.c_int32),("Lon", ct.c_int32),("Alt", ct.c_uint32),("phi", ct.c_int32),("theta", ct.c_int32),("psi", ct.c_int32),
        ("u", ct.c_int32),("v", ct.c_int32),("w", ct.c_int32),("p", ct.c_int32),("q", ct.c_int32),("r", ct.c_int32),
        ("Ax", ct.c_int32),("Ay", ct.c_int32),("Az", ct.c_int32),
        ("AOA", ct.c_float),("AOS", ct.c_float),("KCAS", ct.c_uint16),("KTAS", ct.c_uint16),("GNDS", ct.c_uint16),("MachNum", ct.c_uint16),
        ("VV", ct.c_float), ("Nz", ct.c_int16),("Ny", ct.c_int16),
        ("LonMode", ct.c_uint8), ("LonCtrlCmd", ct.c_float),("ElevatorPosition", ct.c_int16),("FlapCtrlCmd", ct.c_int8),
        ("FlapPosition", ct.c_int16),("LatMode", ct.c_uint8),("LatCtrlCmd", ct.c_float),("AileronPosition", ct.c_int16),
        ("DirCtrlCmd", ct.c_float),("RudderPosition", ct.c_int16),("SpeedMode", ct.c_uint8),("SpeedCtrlCmd1", ct.c_float),
        ("Engine1_N1RPM", ct.c_uint32),("Engine1_N2RPM", ct.c_uint32),("Engine1_FuelFlow", ct.c_double),("SpeedCtrlCmd2", ct.c_float),
        ("Engine2_N1RPM", ct.c_uint32),("Engine2_N2RPM", ct.c_uint32),("Engine2_FuelFlow", ct.c_double),("SpeedBrakeCtrlCmd", ct.c_int8),
        ("SpeedBrakePosition", ct.c_uint16),("Fuel", ct.c_double),("checksum", ct.c_uint8)
    ]

#Add for rule based AI pilot
class ControlValue(ct.Structure):
    _pack = 1
    _fields_ = [
        ("RollCMD", ct.c_float), ("PitchCMD", ct.c_float), ("RudderCMD", ct.c_float), ("Throttle", ct.c_float)
    ]

#Add for AIPilotDLL V1.1.2 
class oPlaneData(ct.Structure):
    _pack = 1
    _fields_ = [
        ("LocationX", ct.c_float),("LocationY", ct.c_float),("LocationZ", ct.c_float),
        ("Roll", ct.c_float), ("Pitch", ct.c_float), ("Yaw", ct.c_float),
        ("Speed", ct.c_float),("Team", ct.c_int),("Resv0", ct.c_float),("Resv1", ct.c_float),("Resv2", ct.c_float)
    ]

class VP(ct.Structure):
    _pack = 1
    _fields_ = [
        ("X", ct.c_double),("Y", ct.c_double),("Z", ct.c_double)
    ]

lib_path = os.path.dirname(os.path.abspath(os.path.expanduser(__file__)))

#AI Pilot Model 조종값 생성 모델 가져오기

    
class AIPilot(object):
    def __init__(self, filename="AIP_DCS_target.dll"):
        path_to_so_file = os.path.join(lib_path, filename)
        self.AIPilotDLL     = ct.cdll.LoadLibrary(path_to_so_file)

        self.AIPilotDLL.CreateBehaviorTree.argtypes = [ct.c_int, ct.c_int]  #Aircraft ID, ForceID
        self.AIPilotDLL.CreateBehaviorTree.restype  = None

        self.AIPilotDLL.ChangeData.argtypes = [ct.c_int, ct.c_int, ct.c_float, ct.c_int, ct.POINTER(J_NavigationData)]
        self.AIPilotDLL.ChangeData.restype  = oPlaneData

        self.AIPilotDLL.Step.argtypes  = [ct.POINTER(oPlaneData), ct.c_int,  ct.c_void_p, ct.c_bool,  ct.c_void_p, ct.c_void_p] #ct.POINTER(ct.c_bool), ct.POINTER(ct.c_bool)]
        self.AIPilotDLL.Step.restype   = ControlValue

        self.AIPilotDLL.GetVP.argtype = ct.POINTER(oPlaneData)
        self.AIPilotDLL.GetVP.restype = VP

        self.AIPilotDLL.Reset.argtype = None
        self.AIPilotDLL.Reset.restype = None

        self.AIPilotDLL.RemoveBT.argtype = ct.c_int
        self.AIPilotDLL.RemoveBT.restype = None

    def CreateBehaviorTree(self, My_ID, My_ForceID):
        self.AIPilotDLL.CreateBehaviorTree(My_ID, My_ForceID)

    def Step(self, My_ID, My_ForceID, Tgt_ID, Tgt_ForceID, My_Navi, Tgt_Navi):
        bLockon     = ct.c_bool()
        bLockon     = False
        bFlare      = ct.c_bool()
        bLnchMSL    = ct.c_bool()
        my_oPD      = oPlaneData()
        tgt_oPD     = oPlaneData()
        my_oPD      = self.AIPilotDLL.ChangeData(My_ID, My_ForceID, 100.0, 0, ct.POINTER(J_NavigationData)(My_Navi))
        tgt_oPD     = self.AIPilotDLL.ChangeData(Tgt_ID, Tgt_ForceID, 100.0, 0, ct.POINTER(J_NavigationData)(Tgt_Navi))
        tgt_oPD_arr = bytes()
        tgt_oPD_arr += struct.pack("fffffffifff", tgt_oPD.LocationX, tgt_oPD.LocationY, tgt_oPD.LocationZ, 
                                    tgt_oPD.Roll, tgt_oPD.Pitch, tgt_oPD.Yaw, 
                                    tgt_oPD.Speed, tgt_oPD.Team, tgt_oPD.Resv0, tgt_oPD.Resv1, tgt_oPD.Resv2)

        
        return self.AIPilotDLL.Step(my_oPD, 1, tgt_oPD_arr, bLockon, ct.byref(bFlare), ct.byref(bLnchMSL))

    def GetVP(self, My_ID, My_ForceID, My_Navi):
        my_oPD      = oPlaneData()
        my_oPD      = self.AIPilotDLL.ChangeData(My_ID, My_ForceID, 100.0, 0, ct.POINTER(J_NavigationData)(My_Navi))
        return self.AIPilotDLL.GetVP(my_oPD)

    def Reset(self):
        self.AIPilotDLL.Reset()

    def RemoveBT(self, My_ID):
        self.AIPilotDLL.RemoveBT(My_ID)
