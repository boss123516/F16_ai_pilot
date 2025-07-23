import numpy as np
import time
import copy
import pymap3d as pm
from typing import Type, Tuple, Dict, List
import os
import gym
import sys
import datetime

from GeoMathUtil import GeometryInfo
import FighterSim
import JSBSimWrapper

FEET_TO_METER = 0.30480
METER_TO_FEET = 3.28084

def normalize(x, min, max):
    y = 0
    if x > max:
        y = 1
    elif x < min:
        y = -1
        
    d = max-min
    m = (max+min) / 2
    y = (x - m) / d + 1/2

    return y

def print_holdon(x, y):
    sys.stdout.write("\033[2F")
    sys.stdout.write("\033[K]")
    print("ownship:", x)
    sys.stdout.write("\033[K]")
    print("target:", y)

class DogFight_BaseEnv(gym.Env):
    def __init__(self, env_config:dict, AIP_ownship, AIP_target):
        print("JSBSIM ENV:",os.getcwd())
        self.battle_space_id = JSBSimWrapper.create_battleSpace()
        self.num_action = 4
        self.num_observation = 12
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, 
                                                shape=[self.num_observation], dtype=np.float32)
        _low = -1 * np.ones(self.num_action)
        _low[3:] = 0
        self.action_space = gym.spaces.Box(low=_low, high=np.ones(int(self.num_action)),
                                           shape=[int(self.num_action)], dtype=np.float32)
        
        self._sim_hz = 60
        self._delta_t = 1/self._sim_hz
        
        self._geo_info = GeometryInfo()
        
        # Create ownship
        self._sim = None
        self._target_sim = None
        self._sim = FighterSim.JSBSim(
                    [
                        1, 1,
                        env_config['ownship'][0], env_config['ownship'][1], env_config['ownship'][2],
                        env_config['ownship'][3], env_config['ownship'][4], env_config['ownship'][5],
                        env_config['ownship'][6]
                ],
                AIP_ownship,
                self._sim_hz, self.battle_space_id
            ) 
        self._target_sim = FighterSim.JSBSim(
                    [
                        1, 2,
                        env_config['target'][0], env_config['target'][1], env_config['target'][2],
                        env_config['target'][3], env_config['target'][4], env_config['target'][5],
                        env_config['target'][6]
                ],
                AIP_target,
                self._sim_hz, self.battle_space_id
            )  
                    
        # Set Max engagement time
        self._max_engage_time = env_config['max_engage_time']
        self._min_altitude = env_config['min_altitude']
        
        #Set default WEZ parameter
        self._wez_angle_deg = 2
        self._wez_min_range_m = 500 * FEET_TO_METER
        self._wez_max_range_m = 3000 * FEET_TO_METER
        
        self.ownship_log = []
        self.target_log = []
        self.info = {"end_condition":0}
        self.ownship_damage = 0
        self.target_damage = 0
        self.num_engage = 0
        self.current_timestep = 0

    def __del__(self):
        print("JSBSimdf_Base destory")

    def reset(self):
        #Remove objects in same battle space
        JSBSimWrapper.Reset(self.battle_space_id)
        #ownship reset
        self._ownship_state = self._sim.reset()
        self._target_state = self._target_sim.reset()
        self.pre_obs = self.get_observation()
        
        self.info = {"end_condition":0}
        self.num_engage += 1
        self.current_timestep = 0
        return np.array(self.pre_obs)

    def step(self, action=np.array([0,0,0,0]))-> Tuple[np.ndarray, float, bool, Dict]:
        
        self._sim.step_behavior(self._target_sim.get_model())             
        if np.isnan(self._sim.get_state()).any() == True:
            self.info["end_condition"] = 'Ownship FDM output Fall'                
            return np.array(self.pre_obs), 0, True, self.info       
        
        self._target_sim.step_behavior(self._sim.get_model())
        if np.isnan(self._target_sim.get_state()).any() == True:
            self.info["end_condition"] = 'Target FDM output Fall'                    
            return np.array(self.pre_obs), 0, True, self.info      
            
        self.update_damage()
            
        # update state
        self._ownship_state = self._sim.get_state()
        self._target_state = self._target_sim.get_state()
            
        #Get observation
        self.cur_obs = self.get_observation()
        #For validating input actions
        if np.isnan(self.cur_obs).all() == True:
            self.info["end_condition"] = 'FDM output Fall'            
            assert np.isnan(self.cur_obs).all() == True, 'FDM Output Fail'
            return np.array(self.pre_obs), 0, True, self.info
        
        #Check done conditions
        reward = 0
        done = self.get_done()
        self.ownship_log.append([
                         self._ownship_state[42], self._ownship_state[43], self._ownship_state[44],
                         self._ownship_state[3], self._ownship_state[4], self._ownship_state[5]
                         ])
        self.target_log.append([
                         self._target_state[42], self._target_state[43], self._target_state[44],
                         self._target_state[3], self._target_state[4], self._target_state[5]
                         ])
        self.pre_obs = copy.deepcopy(self.cur_obs)
        self.current_timestep += 1
        return np.array(self.cur_obs), reward, done, self.info

    def get_observation(self):
        observation = np.zeros(self.num_observation)
        observation[0] = self._ownship_state[0]
        observation[1] = self._ownship_state[1]
        observation[2] = self._ownship_state[2]
        observation[3] = self._target_state[0]
        observation[4] = self._target_state[1]
        observation[5] = self._target_state[2]
        observation[6] = normalize(self._ownship_state[3], -180, 180)
        observation[7] = normalize(self._ownship_state[4], -90, 90)
        observation[8] = normalize(self._ownship_state[5], 0, 360)
        observation[9] = normalize(self._target_state[3], -180, 180)
        observation[10] = normalize(self._target_state[4], -90, 90)
        observation[11] = normalize(self._target_state[5], 0, 360)

        return np.array(observation)
     
    def get_reward(self):
        reward = 0
        #Get reward
        if self._sim._health > 0:
            reward = 1
            
        if self._target_sim._health < 1:
            reward = 1
            
        return reward
        
    def get_done(self):
        done = False
        
        #if FDM update fail
        if self._sim.fdm_update_success == False or self._target_sim.fdm_update_success == False:            
            self.info["end_condition"] = 'FDM Update Fail'            
            done = True
        
        #if ownship altitude < 300 meter (1,000ft)           
        elif self._ownship_state[44] < self._min_altitude: # meter            
            self.info["end_condition"] = 'ownship altitude below min'
            done = True

        #if target altitude < 300 meter (1,000ft)           
        elif self._target_state[44] < self._min_altitude: # meter            
            self.info["end_condition"] = 'target altitude below min'
            done = True
        
        # if simtime over 5 min
        elif self._ownship_state[41] > self._max_engage_time: # sec            
            self.info["end_condition"] = 'max time out'            
            done = True

        elif self._ownship_state[45] <= 0 :
            self.info["end_condition"] = 'sim health = {} target health = {}'.format(
                self._ownship_state[45], self._target_state[45])
            done = True

        elif self._target_state[45] <= 0:
            self.info["end_condition"] = 'sim health = {} target health = {}'.format(
                self._ownship_state[45], self._target_state[45])
            done = True
        
        #if fuel is empty
        elif self._ownship_state[23] == 0 or self._target_state[23] == 0:
            self.info["end_condition"] = 'fuel fail! sim fuel = {} target fuel = {}'.format(
                self._ownship_state[23], self._target_state[23])
            done = True
            
        return done

    # Calculate damage every step
    def update_damage(self):
        #Get distance(meter), both antena angle(degree)
        sim_state = self._sim.get_state()
        target_sim_state = self._target_sim.get_state()
        dis_m = self._geo_info._get_distance(sim_state, target_sim_state)
        ownship_ata_deg = self._geo_info._get_antenna_train_angle(sim_state, target_sim_state, False)
        target_ata_deg = self._geo_info._get_antenna_train_angle(target_sim_state, sim_state, False)
        
        #Follow with ADT conditions
        max_range_m = self._wez_max_range_m
        min_range_m = self._wez_min_range_m
        base_range_m = max_range_m - min_range_m
        half_wez_angel_deg = self._wez_angle_deg / 2 #2 * ATA angle = WEZ angle 2022.01.27 
        
        target_damage = 0.0
        ownship_damage = 0.0
                
        if base_range_m != 0:
            #Check distance in WEZ range
            if dis_m >= min_range_m and dis_m <= max_range_m:
                #Check Target in ownship's gun WEZ angle
                if half_wez_angel_deg >= abs(ownship_ata_deg):
                    target_damage = ((max_range_m - dis_m) / base_range_m)* 0.0166666 # delta_t

                #Check Ownship in Target's gun WEZ angle
                if half_wez_angel_deg >= abs(target_ata_deg):
                    ownship_damage = ((max_range_m - dis_m) / base_range_m) * 0.0166666 # delta_t
        
        # print("Distance : ", dis_m, "LOS : ", ownship_ata_deg, " OwnshipDamage : ", ownship_damage)
        #Discount ownship health
        self.ownship_damage = ownship_damage
        self._sim.deduct_health(ownship_damage)
        self.target_damage = target_damage
        self._target_sim.deduct_health(target_damage)

    def change_init_position(self, flight='ownship',
                    init_n=0, init_e=0, init_d=-8000, 
                    init_roll=0, init_pitch=0, init_heading=0, init_speed=250,
                    target_type=2):
        if flight =='ownship':
            _f = self._sim
        else:
            _f = self._target_sim
        self._target_type = target_type
        
        _f._init_pos_n = init_n
        _f._init_pos_e = init_e
        _f._init_pos_d = init_d
        _f._init_roll = init_roll
        _f._init_pitch = init_pitch
        _f._init_heading = init_heading
        _f._init_speed = init_speed
        lla = pm.ned2geodetic(_f._init_pos_n, _f._init_pos_e, _f._init_pos_d, _f._origin_lat, _f._origin_lon, _f._origin_alt )
        _f._init_pos_lat = lla[0]
        _f._init_pos_lon = lla[1]
        _f._init_pos_alt = lla[2]
        
    def add_random_init_position(self, flight='ownship', radius=500.0, r_roll=5, r_pitch=5, r_heading=5):
        if flight =='ownship':
            _f = self._sim
        else:
            _f = self._target_sim
        
        sign = np.array([-1,1])
        rand_n = np.random.choice(sign, size=1) * np.random.randint(0, radius)
        rand_e = np.random.choice(sign, size=1) * np.random.randint(0, radius)
        rand_d = np.random.choice(sign, size=1) * np.random.randint(0, radius)
        rand_r = np.random.choice(sign, size=1) * np.random.randint(0, r_roll)
        rand_p = np.random.choice(sign, size=1) * np.random.randint(0, r_pitch)
        rand_h = np.random.choice(sign, size=1) * np.random.randint(0, r_heading)
        
        _f._init_pos_n += float(rand_n)
        _f._init_pos_e += float(rand_e)
        _f._init_pos_d += float(rand_d)
        _f._init_roll += float(rand_r)
        _f._init_pitch += float(rand_p)
        _f._init_heading += float(rand_h)

        if _f._init_roll > 180:
            _f._init_roll -= 360        
        if _f._init_roll < -180:
            _f._init_roll += 360
        if _f._init_pitch > 180:
            _f._init_pitch -= 360
        if _f._init_pitch < -180:
            _f._init_pitch += 360
        if _f._init_heading > 360:
            _f._init_heading -= 360
        if _f._init_heading < 0:
            _f._init_heading += 360
        
        lla = pm.ned2geodetic(_f._init_pos_n, _f._init_pos_e, _f._init_pos_d, _f._origin_lat, _f._origin_lon, _f._origin_alt )
        _f._init_pos_lat = lla[0]
        _f._init_pos_lon = lla[1]
        _f._init_pos_alt = lla[2]

    def get_ownship_sim(self):
        if self._sim != None:
            return self._sim
        return None
    
    def get_target_sim(self):
        if self._target_sim != None:
            return self._target_sim
        return None
    
    def get_ownship_action(self):
        return np.array(self._sim.action, dtype=np.float32)
    
    def get_target_action(self):
        return np.array(self._target_sim.action, dtype=np.float32)
    
    def get_ownship_VP(self):
        return np.array(self._sim.VP, dtype=np.float32)
    
    def get_target_VP(self):
        return np.array(self._target_sim.VP, dtype=np.float32)
    
    def get_ownship_state(self)->np.ndarray:
        return self._ownship_state
    
    def get_target_state(self)->np.ndarray:
        return self._target_state
    
    def get_damage(self):
        return self.ownship_damage, self.target_damage
    
    def get_ownship_state_for_udp(self)->List:
        return [
            self._ownship_state[0], self._ownship_state[1], -self._ownship_state[2],
            self._ownship_state[3], self._ownship_state[4], self._ownship_state[5], self._ownship_state[45]
            ]
    
    def get_target_state_for_udp(self)->List:
        return [
            self._target_state[0], self._target_state[1], -self._target_state[2],
            self._target_state[3], self._target_state[4], self._target_state[5], self._target_state[45]
            ]
        
    def make_tacviewLog(self):
        
        ownship_filename = "{}_{}_{}_{}_{}_{}_ownship_(F-16)[Blue].csv".format(datetime.datetime.today().year, 
                                                    datetime.datetime.today().month,
                                                    datetime.datetime.today().day,
                                                    datetime.datetime.today().hour,
                                                    datetime.datetime.today().minute,
                                                    datetime.datetime.today().second)
        
        target_filename = "{}_{}_{}_{}_{}_{}_target_(F-16)[Red].csv".format(datetime.datetime.today().year, 
                                                    datetime.datetime.today().month,
                                                    datetime.datetime.today().day,
                                                    datetime.datetime.today().hour,
                                                    datetime.datetime.today().minute,
                                                    datetime.datetime.today().second)
        
        logpath = os.path.join("logs", ownship_filename)
            
        with open(logpath, "w") as f:
            # Header
            f.write("Time,Longitude,Latitude,Altitude,Roll (deg),Pitch (deg),Yaw (deg)\n")
            
            #dt = 0.01666667
            dt = 0.0167
            step = 0
            for i in self.ownship_log:
                time = np.floor(dt*step* 10000) / 10000
                f.write(f"{time},{i[1]},{i[0]},{i[2]},{i[3]},{i[4]},{i[5]}\n")
                step += 1
                
        logpath = os.path.join("logs", target_filename)
        with open(logpath, "w") as f:
            # Header
            f.write("Time,Longitude,Latitude,Altitude,Roll (deg),Pitch (deg),Yaw (deg)\n")
            
            #dt = 0.01666667
            dt = 0.0167
            step = 0
            for i in self.target_log:
                time = np.floor(dt*step* 10000) / 10000
                f.write(f"{time},{i[1]},{i[0]},{i[2]},{i[3]},{i[4]},{i[5]}\n")
                step += 1

    def render(self):
        pass
    
    def display(self):
        pass

    def close(self):
        pass