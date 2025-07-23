from DogFightEnvWrapper import DogFightWrapper
from CommUdpThread import CommUDP
import CppBT

import threading
import queue
import time
import sys
import signal

import numpy as np

GAMECONTROL_STRUCT_FORMAT = 'Ib'
INIT_STRUCT_FORMAT = 'Iffffffffffff'
    
# _state_keys = ['X', 'Y', 'Z', 'Roll', 'Pitch', 'Yaw', 'Health']
# _init_keys = ['ownship_X', 'ownship_Y', 'ownship_Z', 'ownship_Roll', 'ownship_Pitch', 'ownship_Yaw'
#                     ,'target_X', 'target_Y', 'target_Z', 'target_Roll', 'target_Pitch', 'target_Yaw']

def handler(sig, frame):
    print("\nKey Interrupt: Ctrl+C received\n")
    sys.exit(0)

if __name__ == "__main__":
    
    signal.signal(signal.SIGINT, handler)
    env_config = {
        'max_engage_time': 300,
        'min_altitude': 300,
        # [N, E, D, Roll, Pitch, Initial Heading(deg), Speed(m/s)]
        'ownship': [1000.0, 0.0, -7000.0, 0.0, 0.0, 0.0, 300.0],
        'target': [6000.0, 0.0, -7000.0, 0.0, 0.0, 180.0, 300.0],
    }
    
    # AIP_ownship = CppBT.AIPilot("AIP_DCS_ownship.dll")
    # AIP_target = CppBT.AIPilot("AIP_DCS_target.dll")
    AIP_ownship = CppBT.AIPilot("AIP_DCS_1.dll")
    AIP_target = CppBT.AIPilot("AIP_DCS_1.dll")
    command_evt = threading.Event()
    init_evt = threading.Event()
    state_q = queue.Queue(maxsize=10)
    engageEnv = DogFightWrapper(env_config, AIP_ownship, AIP_target)
    # commBattleViewer = CommUDP('192.168.10.114', 9999, command_evt, init_evt, state_q)
    commBattleViewer = CommUDP('127.0.0.1', 9999, command_evt, init_evt, state_q)
    commBattleViewer.start()
    init_state = []
                    
    done = False
    
    while True:
            while not command_evt.is_set():
                commBattleViewer.send_simState()
                time.sleep(0.1)
                    
            try:
                if init_evt.is_set():
                    init_state = state_q.get(timeout=1.0)
                    init_state =np.array(init_state[1])
                    print(init_state)
                    engageEnv.change_init_position('ownship', 
                                                init_n=init_state[0], init_e=init_state[1], init_d=-init_state[2],
                                                init_roll=init_state[3], init_pitch=init_state[4], init_heading=init_state[5],
                                                init_speed=250)
                    
                    engageEnv.change_init_position('target', 
                                                init_n=init_state[6], init_e=init_state[7], init_d=-init_state[8],
                                                init_roll=init_state[9], init_pitch=init_state[10], init_heading=init_state[11],
                                                init_speed=250)    
                        
                    engageEnv.reset()
                    
                    obs = None
                    done = False
                    reward = 0.0
                    
                    ownship_state_for_udp = engageEnv.get_ownship_state_for_udp()            
                    target_state_for_udp = engageEnv.get_target_state_for_udp()
                        
                    print("ownship:",ownship_state_for_udp)
                    print("target:",target_state_for_udp)
                    init_evt.clear()
                    
            except queue.Empty:
                continue
            
            next_time = time.perf_counter()
            while not done and command_evt.is_set():                
                obs, reward, done, info = engageEnv.step()
                ownship_state_for_udp = engageEnv.get_ownship_state_for_udp()
                target_state_for_udp = engageEnv.get_target_state_for_udp()
                
                ownship_action = engageEnv.get_ownship_action()
                target_action = engageEnv.get_target_action()
                ownship_VP = engageEnv.get_ownship_VP()
                target_VP = engageEnv.get_target_VP()
                ownship_damage, target_damage = engageEnv.get_damage()
                
                commBattleViewer.send_planeInfo([0]+ownship_state_for_udp)
                commBattleViewer.send_VP(0, ownship_VP)
                commBattleViewer.send_CMD(0, ownship_action)
                if target_damage > 0:
                    commBattleViewer.send_damageInfo(type=1, damage=target_damage)
                
                commBattleViewer.send_planeInfo([1]+target_state_for_udp)
                commBattleViewer.send_VP(1, target_VP)
                commBattleViewer.send_CMD(1, target_action)
                if ownship_damage > 0:
                    commBattleViewer.send_damageInfo(type=2, damage=ownship_damage)
                
                next_time += 1.0/60
                sleep_time = next_time - time.perf_counter()
                
                if sleep_time >0:
                    time.sleep(sleep_time)
                else:
                    # print("Overrun by", -sleep_time * 1000, "ms")
                    next_time = time.perf_counter()
                    
            if done:
                engageEnv.make_tacviewLog()