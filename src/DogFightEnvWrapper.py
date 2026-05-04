import numpy as np
import time
import copy
import pymap3d as pm
from typing import Type, Tuple, Dict, List

from DogFightEnv import DogFight_BaseEnv
from DogFightEnv import normalize
from DogFightEnv import FEET_TO_METER, METER_TO_FEET

class DogFightWrapper(DogFight_BaseEnv):
    def __init__(self, env_config:dict, AIP_ownship, AIP_target):
        super().__init__(env_config, AIP_ownship, AIP_target)
        
        self.loiter_bank = 30
        self.loiter_pitch= 0
        self.isLoitering=True

    def __del__(self):
        print("JSBSimdf_Base destory")

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
            
        if done:
            print(self.info["end_condition"])
        return done