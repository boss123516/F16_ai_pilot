import numpy as np

from DogFightEnvWrapper import DogFightWrapper
import CppBT

if __name__ == "__main__":
    env_config = {
        'max_engage_time': 300,
        'min_altitude': 300,
        # [N, E, D, Roll, Pitch, Initial Heading(deg), Speed(m/s)]
        'ownship': [1000.0, 0.0, -7000.0, 0.0, 0.0, 0.0, 300.0],
        'target': [6000.0, 0.0, -7000.0, 0.0, 0.0, 180.0, 300.0],
    }
    AIP_ownship = CppBT.AIPilot("AIP_DCS_ownship.dll")
    AIP_target = CppBT.AIPilot("AIP_DCS_base.dll")
    engageEnv = DogFightWrapper(env_config, AIP_ownship, AIP_target)
        
    engageEnv.reset()
    obs = None
    done = False
    reward = 0.0
    
    while not done:
        
        obs, reward, done, info = engageEnv.step()
        
    if done:
        engageEnv.make_tacviewLog()