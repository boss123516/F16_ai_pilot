# Behavior Tree Definitions

This directory contains the XML behavior tree definitions consumed by the C++
BT DLL (`AIP_DCS_ownship.dll` etc.). The DLL parses these XML files at
`CreateBehaviorTree(...)` time and dispatches each tick to the corresponding
node implementations.

The competition-provided DLL is **not** committed (binary, ~2 MB, organizer-owned).
These XML files describe the tactical logic that runs on top of it.

---

## File layout

```
config/bt/
├── BT_Tree.xml          # ★ Main integrated tactical BT (use this for engagement)
├── Rule_Lead.xml        # Single-maneuver test: Lead Pursuit only
├── Rule_Lag.xml         # Single-maneuver test: Lag Pursuit only
├── Rule_Pure.xml        # Single-maneuver test: Pure Pursuit only
├── Rule_Head.xml        # Single-maneuver test: head-on advance-and-descend
├── Rule_Of.xml          # Single-maneuver test: positional offset move
├── Rule_distance.xml    # Distance-only branching (Pure vs Climb)
└── variants/            # Parameter-tuning iterations kept for reference
    ├── BT_Tree2.xml ... BT_Tree7.xml
    ├── Rule_Lead2/3.xml, Rule_Lag2/3.xml, ...
    └── Rule_Pure2/3/4/5.xml
```

The DLL picks one file via `Rule.xml`'s `main_tree_to_execute` field — point it
at whichever tree you want to drive the agent.

---

## BT_Tree.xml — main integrated tactical tree

This is the full 3-layer hierarchy described in the top-level README
(safety → tactical situation → maneuver execution). Each tick, the perception
sequence runs first (target selection, direction vector, distance, sight,
angle-off, aspect angle) and the result lands on the Blackboard. The Fallback
that follows is the actual decision tree:

| Distance band | Default behavior | Altitude-floor override |
| --- | --- | --- |
| `> 4000 m` | `Task_Lead` (LeadTime 2.5 s, throttle 0.75–1.0) — close the gap | `< 1800 m` → `Task_Climb` (+500 m) |
| `3000–4000 m` | `Task_Lead` (LeadTime 1.5 s, throttle 1.0) — commit to the merge | same |
| `2000–3000 m` | `Task_Lag` (LagDist 100, throttle 0.75–1.0) — energy-conserving pursuit | same |
| `1500–2000 m` | `Task_Lag` (LagDist 50) — tighter trail | same |
| `< 1500 m` | **dogfight mode** (LOS-based, see below) | same |

### Dogfight branch (< 1500 m, altitude OK)

Evaluated as a Fallback:

1. If target LOS to me `< 2°` **and** my LOS to target `> 3°` → `Task_DefensiveBreak`
   — opponent has a firing solution but I don't yet. Break their tracking.
2. If both LOS angles `< 3°` (mutual near-firing) **and** mine is greater
   (i.e. I'm worse off) → `Task_DefensiveBreak`. The `DECO_LOSCompare` node
   resolves who fires first.
3. Otherwise → `Task_Pure` — clean firing geometry, go for the gun solution.

`Task_DefensiveBreak` parameters: `BreakDist=800`, `SideOffset=300`,
`KeepAltitude=true`, `MaxThrottle=true`. Tuned to force a Pure-Pursuit overshoot
without bleeding too much energy.

---

## Single-maneuver Rule_*.xml files

These exist for isolated regression testing of individual BT tasks. Each file
runs the same perception sequence as `BT_Tree.xml` but the Fallback only fires
**one task node**, regardless of geometry. Useful for:

- Verifying a single C++ task implementation in the DLL
- Replaying a controlled scenario with a fixed maneuver
- Bisecting bugs ("does the agent break in Pure mode or in Lag mode?")

| File | Single task | Notes |
| --- | --- | --- |
| `Rule_Lead.xml` | `Task_Lead` | LeadTime 2.2 s, close_dist 3000, far_dist 5000 |
| `Rule_Lag.xml`  | `Task_Lag`  | LagDist 300 |
| `Rule_Pure.xml` | `Task_Pure` | no parameters |
| `Rule_Head.xml` | `Task_AdvanceClimb` | ClimbAlt −1000, ForwardDist 1000 — descend-and-advance head-on response |
| `Rule_Of.xml`   | `Task_MoveOffset` | OffsetX 1000, OffsetZ −700, TargetAlt 1000 — positional offset move |
| `Rule_distance.xml` | distance-branched | Pure if far, Climb if close — minimal 2-branch sanity check |

---

## variants/ — parameter-tuning iterations

`BT_Tree2.xml` through `BT_Tree7.xml` and the numbered `Rule_*` variants are
snapshots from the parameter-tuning process during the competition. They
differ in:

- Distance-band thresholds (e.g. `< 1500` vs `< 2000` for entering dogfight mode)
- `LagDist` / `LeadTime` values
- Whether the dogfight-mode fallback ends in `Task_Pure` or terminates early
- Altitude-floor thresholds (1500 vs 1800 m)

Kept for reference / ablation, not for production use. `BT_Tree.xml` is the
final selected configuration.

---

## Decorator and task nodes referenced

These names must match what the C++ DLL registers. See `Rule.xml` for the node
schema (the DLL parses node names and arguments from there).

### Perception (Service-like nodes, run every tick at the top of the sequence)
- `SelectTarget` — picks the engagement target ID into the Blackboard
- `DirectionVectorUpdate` — recomputes ownship/target forward vectors
- `DistanceUpdate` — 3D Euclidean range
- `CheckSight` — has-target-in-radar predicate
- `AngleOffUpdate` — AO (heading-vector difference)
- `AspectAngleUpdate` — AA (ownship's bearing from target's tail)

### Decorators (conditions that gate Sequence children)
- `DECO_DistanceCheck` — `UpDown="Greater"|"Less"`, `Distance="<meters>"`
- `DECO_AltitudeCheck` — `UpDown=...`, `InputAlt="<meters AGL>"`
- `DECO_LOSCheck` — my LOS to target — `InputLOS="<degrees>"`
- `DECO_LOSTargetCheck` — target's LOS to me — `InputLOS_Target="<degrees>"`
- `DECO_LOSCompare` — succeeds when my LOS angle is greater than the target's

### Tasks (terminal action nodes — produce a `ControlValue`)
- `Task_Lead` — `LeadTime`, `close_dist`, `far_dist`, `min_throttle`, `max_throttle`, `slew_per_tick`, `use_smoothstep`
- `Task_Lag` — `LagDist`, `close_dist`, `far_dist`, `min_throttle`, `max_throttle`, `slew_per_tick`, `use_smoothstep`
- `Task_Pure` — (no parameters)
- `Task_Climb` — `ClimbAlt` (target gain in meters)
- `Task_DefensiveBreak` — `BreakDist`, `SideOffset`, `KeepAltitude`, `VerticalJink`, `MaxThrottle`
- `Task_AdvanceClimb` — `ClimbAlt` (signed, negative = descend), `ForwardDist`
- `Task_MoveOffset` — `OffsetX`, `OffsetY`, `OffsetZ`, `TargetAlt`, `alt_eps`
- `Task_Empty` — no-op (placeholder, used in `Rule.xml` skeleton)
