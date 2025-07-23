from typing import Dict, List

FEET_TO_METER = 0.30480
METER_TO_FEET = 3.28084
KNOT_TO_METER_SEC = 0.51444
WEZ_ANGLE_DEG = 2
WEZ_MIN_RANGE_M = 500 * FEET_TO_METER # meter (150m)
WEZ_MAX_RANGE_M = 3000 * FEET_TO_METER # meter (900m)
MAX_ENGAGE_TIME = 600
MIN_ALTITUDE = 300

obs_dict = {
        "N": 0, "E": 1, "D": 2,
        "Roll": 3, "Pitch": 4, "Yaw": 5,
        "U": 6, "V": 7, "W": 8,
        "P": 9, "Q": 10, "R": 11,
        "KCAS": 12,
        "AOA": 13, "AOS": 14,
        "ActionX": 15, "ActionX_deflection": 16,
        "ActionY": 17, "ActionY_deflection": 18,
        "ActionRud": 19, "ActionRud_deflection": 20,
        "ActionTh": 21, "ActionTh_deflection": 22,
        "Fuel": 23,
        "Ax": 24, "Ay": 25, "Az": 26,
        "KTAS": 27, "GNDS": 28, "MachNum": 29,
        "VV": 30, "Nz": 31, "Ny": 32,
        "Sim_time": 41,
        "Lat": 42, "Lon": 43, "Alt": 44,
        "Health": 45,

        # Not Used
        "E1_N2RPM": 33, "E1_FuelFlow": 34,
        "ActionTh2": 35, "ActionTh2_deflection": 36, "E2_N2RPM": 37, "E2_FuelFlow": 38,
        "SpeedBrakeCtrlCmd": 39, "SpeedBrakePoisition": 40,

        # Not in STATE 0~50
        "AA": 100, "ATA": 101, "distance": 102, "AZ": 103, "EL": 104,
        "dAA": 105, "dATA": 106, "ddistance": 107, "AB":108, "CD":109
    }
range_dict = {
        0: [0, 0], 1: [0, 0], 2:[0, 0],
        3: [-180.0, 180.0], 4: [-90.0, 90.0], 5: [0.0, 360.0],
        6: [-100.0, 500.0], 7: [-100.0, 100.0], 8: [-100.0, 100.0],
        9: [-300.0, 300.0], 10: [-150.0, 150.0], 11: [-70.0, 70.0],
        12: [0.0, 550.0], 13: [-90.0, 90.0], 14: [-90.0, 90.0],    
        15: [-1.0, 1.0], 16: [-60, 60],
        17: [-1.0, 1.0], 18: [-60, 60],
        19: [-1.0, 1.0], 20: [-60, 60],
        21: [-1.0, 1.0], 22: [0.0, 100.0],
        23: [0.0, 100.0],
        24: [-50.0, 50.0], 25: [-50.0, 50.0], 26: [-200.0, 150.0],
        27: [0.0, 500.0], 28: [0.0, 700.0], 29: [0.0, 1.5],
        30: [-100.0, 100.0], 31: [-20.0, 20.0], 32: [-20.0, 20.0],
        33: [0.0, 100.0], 34: [-1.0, 1.0], 35: [0.0, 100.0],
        36: [0.0, 100.0], 37: [0.0, 100.0], 38: [0.0, 1000.0],
        39: [-1.0, 1.0], 40: [0.0, 60.0],
        41: [0.0, 0.0], 42: [0.0, 0.0], 43: [0.0, 0.0], 44: [0.0, 10000.0],
        45: [0.0, 1.0],

        # Not in STATE 0~50
        100: [-180.0, 180.0], 101: [-180.0, 180.0], 102: [0.0, 20000.0],
        103: [-180.0, 180.0], 104: [-90.0, 90.0],
        105: [-180.0, 180.0], 106: [-180.0, 180.0], 107: [-1000.0, 1000.0]
    }

DEFAULT_OBS_LIST={
        "ownship": [
                "Roll",
                "Pitch",
                "Yaw",
                "U",
                "V",
                "W",
                "P",
                "Q",
                "R",
                "Ax",
                "Ay",
                "Az",
                "Alt",
                "Health",
                "KCAS"
            ],
        "target": [
                "Health"
            ],
        "relative": [
                "AA",
                "ATA",
                "distance",
                "AZ",
                "EL"
            ]
    }

DEFAULT_RANDOM_SCENARIO = {
    # [ N, E, D, Roll, Pitch, Initial Heading(deg), Speed(m/s), target_type ]
    # pursue
    0: [
            [1000.0, 0.0, -8100.0, 0.0, 0.0, 0.0, 250.0, 2],
            [3000.0, 0.0, -8000.0, 0.0, 0.0, 0.0, 250.0, 2],
        ],
    # lotering
    1: [
            [3000.0, 1000.0, -8000.0, 0.0, 0.0, 0.0, 250.0, 2],
            [4000.0, 0.0, -8000.0, 0.0, 0.0, 0.0, 250.0, 1],
        ],
        # neutral
    2: [
            [3000.0, 0.0, -8000.0, 0.0, 0.0, 0.0, 250.0, 2],
            [3000.0, 500.0, -8000.0, 0.0, 0.0, 180.0, 250.0, 2],
        ]
}

DEFAULT_ENV_CONFIG = {
    # observation ratio Hz
    'time_step': 10,
    # jsbsim fight model simulation ratio Hz 
    'sim_hz': 60,
    'max_engage_time': MAX_ENGAGE_TIME,
    'min_altitude': MIN_ALTITUDE,
    # Gun WEZ parameter : [angle_d(deg), min_range_m(meter), max_range_m(meter)]
    'wez' : [WEZ_ANGLE_DEG, WEZ_MIN_RANGE_M, WEZ_MAX_RANGE_M],
    # [N, E, D, Roll, Pitch, Initial Heading(deg), Speed(m/s)]
    'ownship': [1000.0, 0.0, -7000.0, 0.0, 0.0, 0.0, 300.0],
    'target': [6000.0, 0.0, -7000.0, 0.0, 0.0, 180.0, 300.0],
    'target_type': 2, # 0: fix, 1: loitering, 2: RAIP
}