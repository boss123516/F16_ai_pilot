# F16_ai_pilot

> Autonomous F-16 Air Combat Agent — Behavior Tree based tactical decision-making

> 📦 **Archived coursework / competition project (Jul – Dec 2025).** Built for the Korea Aerospace University autonomous air combat competition. The repository was cleaned up and documented retroactively — source code preserved as-is. See [About this project](#about-this-project).

Autonomous F-16 agent that performs 1v1 dogfight against an opponent by analyzing real-time 3D combat geometry and dynamically selecting offensive/defensive maneuvers via a Behavior Tree.

---

## 📌 Overview

```
                   ┌───────────────────────────────┐
                   │        main_engage.py          │
                   │  - Loads ownship & target DLL  │
                   │  - Runs simulation step loop   │
                   └──────────────┬────────────────┘
                                  │
          ┌───────────────────────▼──────────────────────┐
          │              DogFightEnvWrapper               │
          │         (gym.Env step/reset interface)        │
          └──────────┬───────────────────────────────────┘
                     │
      ┌──────────────▼──────────────┐    ┌────────────────────────┐
      │      DogFightEnv            │    │       CppBT.py          │
      │  - JSBSim flight physics    │◄───│  - Python wrapper for   │
      │  - GeoMathUtil (AA/AO/LOS)  │    │    C++ BT DLL           │
      │  - 60 Hz simulation tick    │    │  - Outputs Roll/Pitch/  │
      └─────────────────────────────┘    │    Rudder/Throttle CMD  │
                                         └────────────────────────┘
```

Each simulation tick (5 ms):
1. JSBSim propagates flight physics for both aircraft
2. `GeoMathUtil` computes AA, AO, LOS, distance from raw NED state vectors
3. C++ Behavior Tree inside the DLL reads the Blackboard and selects a maneuver
4. Control commands (`RollCMD`, `PitchCMD`, `RudderCMD`, `Throttle`) are returned to JSBSim

> ⚠️ **The BT logic lives inside compiled C++ DLLs** (`AIP_DCS_ownship.dll`, `AIP_DCS_target.dll`, `AIP_DCS_base.dll`). These were provided by the competition organizer and are **not included** in this repository. `CppBT.py` is the Python-side wrapper that loads and calls them via `ctypes`. The `config/Rule.xml` describes the BT node schema; the actual node implementations are in the DLLs.

---

## 📁 Project structure

```
F16_ai_pilot/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── main_engage.py          # Entry point — sets up env, runs engage loop
│   ├── main_battleViewer.py    # TacView log visualizer
│   ├── DogFightEnv.py          # Core gym.Env: JSBSim + geometry + scoring
│   ├── DogFightEnvWrapper.py   # Wrapper with logging and episode management
│   ├── CppBT.py                # ctypes wrapper for the C++ AI pilot DLL
│   ├── GeoMathUtil.py          # 3D combat geometry math (AA, AO, LOS, distance)
│   ├── FighterSim.py           # JSBSim aircraft instance manager
│   ├── JSBSimWrapper.py        # Low-level JSBSim C++ bridge
│   ├── AIACEENV_helper.py      # Utility helpers for the AIACE environment
│   ├── CommUdpThread.py        # UDP communication thread (multi-agent)
│   └── CommonTypes.py          # Shared type definitions
├── config/
│   ├── Rule.xml                # BT node schema definition
│   ├── aircraft/               # JSBSim aircraft models (F-16, F-15, FA-50)
│   ├── engine/                 # JSBSim engine data files
│   └── scripts/                # JSBSim flight initialization scripts
├── docs/
│   └── images/
└── archive/
    ├── BT_target.py            # Superseded by CppBT.py (target DLL variant)
    ├── Rule_duplicate.xml      # Identical to config/Rule.xml
    └── catch.xml               # Unused XML leftover
```

---

## 🛠 Setup & run

### Prerequisites

- Python 3.10+
- JSBSim installed and on `PATH`
- Competition DLL files in `src/`:
  - `AIP_DCS_ownship.dll` — your agent's C++ BT
  - `AIP_DCS_base.dll` — baseline opponent
  - `AIP_DCS_target.dll` — alternative target agent

### Install

```bash
pip install -r requirements.txt
```

### Run a 1v1 engage

```bash
cd src
python main_engage.py
```

Default initial conditions (edit `main_engage.py`):

```python
env_config = {
    'max_engage_time': 300,          # seconds
    'min_altitude': 300,             # meters AGL
    'ownship': [1000, 0, -7000, 0, 0,   0, 300],  # [N,E,D, R,P, Hdg, Speed]
    'target':  [6000, 0, -7000, 0, 0, 180, 300],
}
```

Output: a TacView-compatible `.acmi` log. Open it with [TacView](https://www.tacview.net/) to replay the engagement.

### Run the battle viewer

```bash
cd src
python main_battleViewer.py
```

---

## 🧭 Tactical system

The BT implements a 3-layer decision hierarchy, evaluated every 5 ms:

```
Layer 1 — Safety      altitude < 1100 ft?  →  Task_Climb (overrides everything)
Layer 2 — Situation   distance > 3000 m?   →  long-range mode (Task_Lead)
                      distance ≤ 3000 m?   →  dogfight mode (OBFM / DBFM / Head-on)
Layer 3 — Default     none of the above    →  Task_Pure
```

### Combat geometry computed each tick

| Variable | Definition | Used for |
|---|---|---|
| **AA** (Aspect Angle) | Angle from target's tail to ownship | OBFM / DBFM classification |
| **AO** (Angle-Off) | Difference between ownship and target heading vectors | Attack geometry quality |
| **LOS** (Line-of-Sight) | Angle between ownship nose and target position | Firing condition (< 1°) |
| **Distance** | 3D Euclidean range | Phase transition thresholds |

### Maneuver nodes

| Node | Type | Description |
|---|---|---|
| `Task_Lead` | Attack | Aims at target's predicted position 3 s ahead — used at long range and post-merge to cut inside the turn |
| `Task_Pure` | Attack | Continuously points nose at current target position — used for final gun solution (LOS → 0°) |
| `Task_Lag` | Attack | Trails slightly behind target's 6 o'clock — energy-conserving pursuit, forces target to exhaust energy first |
| `Task_Climb` | Defense / Safety | Hard pull-up; used both as altitude floor protection and as a low-altitude trap to induce target overshoot into the ground |
| `Task_BreakTurn` | Defense | Maximum-G snap turn when target LOS < 3° — breaks firing solution, induces Pure Pursuit overshoot |

### OBFM vs DBFM classification

```
AA < 90° AND AO < 90°  →  OBFM (offensive — ownship is in target's rear hemisphere)
AA > 90° (from target's perspective)  →  DBFM (defensive — target is in ownship's rear hemisphere)
Both LOS angles small and approximately equal  →  Head-on (LOS comparison decides who fires first)
```

### Pursuit geometry

- **Lead** — aim ahead of target's current position; used when target is turning predictably or at merge.
- **Pure** — track target's instantaneous position; most aggressive but highest energy cost.
- **Lag** — trail behind target's projected 6 o'clock; lowest G, best energy retention.

---

## 📐 GeoMathUtil — geometry implementation

`GeoMathUtil.py` contains the 3D rotation-matrix math that backs all tactical decisions. All angles are computed in the NED (North-East-Down) frame.

```python
# Each tick, the env calls:
dis, aa, hca, ata = geo.get_geometry_info_ned(ownship_ned, target_ned)

# LOS (azimuth, elevation) is computed separately:
az, el = geo._get_los_angle(ownship_ned, target_ned)
```

Key math:
- AA uses the **inverse target body frame** (`Tz_pi · Tx · Ty · Tz`) to find where ownship lies relative to target's tail axis.
- AO (`_get_heading_cross_angle`) transforms target's forward vector into ownship's body frame.
- LOS (`_get_los_angle`) projects the ownship→target NED vector into ownship's body frame; azimuth < 1° triggers the fire condition.

---

## 🗂 CppBT.py — DLL interface

`CppBT.py` bridges Python (simulation environment) and C++ (BT decision logic):

```python
AIP = AIPilot("AIP_DCS_ownship.dll")
AIP.CreateBehaviorTree(My_ID, ForceID)

# Each step:
control = AIP.Step(My_ID, My_ForceID, Tgt_ID, Tgt_ForceID, My_Navi, Tgt_Navi)
# → control.RollCMD, control.PitchCMD, control.RudderCMD, control.Throttle
```

The DLL exposes five entry points: `CreateBehaviorTree`, `ChangeData`, `Step`, `GetVP`, `Reset`, `RemoveBT`. State is passed as a packed `J_NavigationData` C struct (position, attitude, velocity, control surface positions, engine data).

---

## ⚠️ Known limitations / TODO

- DLL files not included — the actual BT node implementations are in the competition-provided binaries.
- `config/Rule.xml` currently contains only a Pure Pursuit skeleton; the full OBFM/DBFM/altitude logic tree will be updated when the C++ implementation is open-sourced.
- `GeoMathUtil` sign conventions for 3D AA and AO have known edge cases at extreme roll angles (see inline comments).
- Multi-agent UDP mode (`CommUdpThread.py`) is functional but untested in this repo's configuration.

---

## About this project

**Korea Aerospace University — Autonomous Air Combat Competition (Jul – Dec 2025)**
Department of AI Autonomous Driving Systems Engineering

Designed and implemented a rule-based autonomous F-16 dogfight agent using a Behavior Tree architecture. The tactical decision logic was derived by studying publicly available BFM (Basic Fighter Maneuvers) doctrine and validated through agent-vs-agent simulation.

**Key contributions:**
- Synthesized AA / AO / LOS geometry into a real-time Blackboard perception system
- Designed the 3-layer BT hierarchy (safety → tactical situation → maneuver execution)
- Implemented `GeoMathUtil` — full 3D rotation-matrix computation of all combat angles
- Authored Decorator nodes for OBFM/DBFM/Head-on classification
- Designed the low-altitude trap strategy and Break Turn overshoot induction logic

### Restructure log *(2026)*

Repository cleaned up retroactively — code preserved as-is:
- Collapsed `ADF_BT_Tool/DogFightEnv_final/` nesting into `src/`
- Moved aircraft/engine/script configs into `config/`
- Removed accidentally committed TurtleBot4 map files (`nav2_params.yaml`, `sex_77.pgm/.yaml`)
- Archived duplicate files (`BT_target.py`, `Rule_duplicate.xml`)
- Added README, `.gitignore`, and this documentation

## License

MIT (replace with your actual license).
