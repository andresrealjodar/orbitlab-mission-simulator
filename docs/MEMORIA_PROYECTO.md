# Project Memory

## 1) Identification
- Project: `Satellite Simulator`
- Type: Modular orbital and attitude dynamics simulator for a 3U CubeSat
- Current status: `Phases 0-7 completed`
- Memory start date: `2026-05-10`

## 2) Purpose of This Memory
This document records, from phase 0 to the final phase, what is implemented, why it is implemented, how it is validated, and what technical decisions are made.  
It remains a living document throughout the entire project.

## 3) General Objective
Build a numerical, modular, and verifiable simulator of a CubeSat in LEO that evolves from a basic Keplerian model to a higher-fidelity model with orbital perturbations, rotational dynamics, attitude control, and validation against real TLE data.

## 4) Specific Objectives
1. Implement translational dynamics with robust numerical integration.
2. Incorporate progressive physical perturbations (`J2`, drag, Sun/Moon, SRP).
3. Incorporate attitude dynamics with quaternions and PD control.
4. Validate each phase with quantitative metrics.
5. Maintain a clean and extensible architecture.

## 5) Scope and Non-Scope (Current Version)
- Current scope:
  - Two-body orbital simulation (Earth-satellite).
  - Orbital simulation with `J2` perturbation.
  - Orbital simulation with `J2` + atmospheric drag.
  - Orbital simulation with `J2` + drag + third body (Sun/Moon) + SRP.
  - Rigid-body attitude simulation with quaternions.
  - Gravity-gradient torque coupled to propagated orbit.
  - PD attitude control with LVLH reference (nadir pointing).
  - Reaction wheel actuators with per-axis torque saturation.
  - Integration using `solve_ivp(DOP853)`.
  - Quantitative comparison between phase models.
  - Reporting of period, invariant conservation, `RAAN` drift, relative decay, perturbation magnitudes, and attitude/control metrics.
  - Output plots.
- Current non-scope:
  - Production-grade JPL/Skyfield precision ephemerides.
  - Production ADCS sensor model with noise/bias.
  - Production orbital estimation with filters and parameter fitting.

## 6) Methodological Approach
Incremental phase-based development is used.

Reason:
1. It allows baseline physics validation before introducing complexity.
2. It reduces hidden-error risk.
3. It supports academic defense (each phase has evidence).
4. It maintains clear traceability between decision, implementation, and result.

## 7) Adopted Software Architecture
Main structure:

```text
satellite_simulator/
|-- main.py
|-- constants.py
|-- orbit/
|-- attitude/
|-- environment/
|-- visualization/
`-- data/tle/
```

Reason for this architecture:
1. Separation of responsibilities (orbit, attitude, environment, visualization).
2. Easier maintenance and module-level testing.
3. Scales well to advanced phases.

## 8) Baseline System Scenario
Chosen nominal scenario:
- 3U CubeSat
- Altitude: 500 km
- Inclination: 97 deg
- Circular initial orbit
- Simulation: 10 orbits

Reason:
1. It is representative of a real LEO mission.
2. It makes future inclusion of `J2` and drag meaningful.
3. It is suitable for progressive validation.

## 9) Phase Plan (Technical Roadmap)
1. Phase 0: Concept definition and architecture.
2. Phase 1: Keplerian orbit (2-body).
3. Phase 2: `J2` inclusion.
4. Phase 3: Atmospheric drag inclusion.
5. Phase 4: Sun/Moon and SRP perturbations.
6. Phase 5: Attitude dynamics (quaternions + rigid body).
7. Phase 6: PD attitude control + actuators.
8. Phase 7: TLE/SGP4 validation.

## 10) Phase Log

### Phase 0 - Project Definition (Completed)
What was done:
1. The final technical objective of the simulator was defined.
2. A professional modular architecture was selected.
3. The reference 3U CubeSat LEO scenario was defined.
4. Development phases and incremental validation were established.

Why:
1. Avoid a monolithic script that is hard to scale.
2. Ensure traceability and academic quality.
3. Prepare a base compatible with real perturbations.

Deliverables:
1. Target folder structure.
2. Phase plan and progression criteria.

Status: `Completed`

---

### Phase 1 - Keplerian Orbit (Completed)
What was implemented:
1. `satellite_simulator/orbit/kepler.py`
   - Classical orbital elements.
   - Kepler -> ECI conversion.
   - Orbital period computation.
2. `satellite_simulator/orbit/propagator.py`
   - Two-body equation.
   - Integration with `solve_ivp(method="DOP853")`.
   - Specific energy and `|h|` extraction.
3. `satellite_simulator/main.py`
   - Scenario configuration.
   - Simulation execution.
   - Console validation summary.
4. `satellite_simulator/visualization/plots.py`
   - 3D orbit.
   - Altitude vs time.
   - Invariants.
5. Root entry point `main.py` for short-command execution.

Important decisions and why:
1. `DOP853` instead of Euler:
   - Higher precision and numerical stability.
2. Validate energy and angular momentum:
   - They are strong invariants for detecting model or integration errors.
3. `Agg` backend for matplotlib:
   - Avoids GUI dependency and allows PNG generation in any environment.

Validation obtained (latest run):
1. Theoretical period: `5676.977 s`
2. Estimated period: `5676.667 s`
3. Period error: `-0.310495 s`
4. Energy drift: `0.000413 ppm`
5. `|h|` drift: `0.000206 ppm`

Interpretation:
1. Conservation is excellent for a two-body simulation.
2. The numerical baseline is suitable for introducing perturbations in Phase 2.

Status: `Completed`

---

### Phase 2 - J2 Perturbation (Completed)
What was implemented:
1. Propagator generalization to accept extra accelerations:
   - `propagate_orbit(..., acceleration_models=[...])`
2. `J2` coupling in dynamics:
   - `j2_acceleration_eci(r)`
3. Dual comparison in the same run:
   - Case A: Kepler two-body.
   - Case B: Kepler + J2.
4. `RAAN` extraction from ECI state:
   - Time series in degrees and unwrapped.
5. New figures:
   - `orbit_3d_kepler_vs_j2.png`
   - `altitude_kepler_vs_j2.png`
   - `raan_vs_time.png`

Why:
1. `J2` is the dominant perturbation in LEO.
2. Nodal precession is one of the most visible and verifiable effects.
3. Comparing against pure Kepler isolates the `J2` effect.

Validation obtained (latest run):
1. Kepler RAAN drift: `-0.000000 deg`
2. Kepler+J2 RAAN drift: `0.615040 deg`
3. Simulated RAAN rate: `0.936052 deg/day`
4. Theoretical secular RAAN rate: `0.932416 deg/day`
5. Absolute rate error: `0.003636 deg/day`

Interpretation:
1. Nodal drift appears where expected (only with `J2`).
2. Simulated rate closely matches secular theory.
3. Phase 2 is validated and ready to advance to atmospheric drag.

Status: `Completed`

---

### Phase 3 - Atmospheric Drag (Completed)
What was implemented:
1. Simplified atmosphere model replaced by layered exponential model (0-1000+ km, Vallado style).
2. Drag acceleration implemented in ECI with co-rotating atmosphere:
   - `v_rel = v_eci - (omega_earth x r_eci)`
   - `a_drag = -0.5 * rho * Cd * (A/m) * |v_rel| * v_rel`
3. New comparative run with three cases:
   - Kepler two-body
   - Kepler + J2
   - Kepler + J2 + Drag
4. New Phase 3 figures:
   - `orbit_3d_j2_vs_j2_drag.png`
   - `altitude_j2_vs_j2_drag.png`
   - `raan_j2_vs_j2_drag.png`

Why:
1. In LEO, drag directly affects orbital lifetime.
2. The layered model avoids unrealistic densities at high altitudes.
3. With/without drag comparison isolates atmospheric effect.

Validation obtained (latest run):
1. Mean drag acceleration: `0.416870 um/s^2`
2. J2 RAAN drift: `0.615040 deg`
3. J2+drag RAAN drift: `0.615044 deg`
4. Additional decay due to drag (vs J2): `38.355348 m`
5. Final position difference J2 vs J2+drag: `2010.222 m`

Interpretation:
1. Drag produces measurable additional orbital decay in only 10 orbits.
2. Nodal precession dynamics remain dominated by `J2`.
3. The base is ready for third-body and SRP perturbations.

Status: `Completed`

---

### Phase 4 - Sun/Moon and SRP (Completed)
What was implemented:
1. Analytic Sun and Moon ephemerides in ECI:
   - `environment/sun.py`
   - `environment/moon.py`
2. Absolute time handling with `Julian Date`:
   - `environment/time_utils.py`
   - scenario with `start_epoch_utc`.
3. Differential third-body acceleration:
   - Sun and Moon in `orbit/perturbations.py`
4. Solar radiation pressure (`SRP`) with Sun-distance factor.
5. Cylindrical Earth shadow to disable SRP in eclipse.
6. Comparison between:
   - Phase 3 (`J2 + drag`)
   - Phase 4 (`J2 + drag + Sun + Moon + SRP`)
7. New perturbation magnitude plot:
   - `perturbations_phase4.png`

Why:
1. Sun/Moon introduce real long-term gravitational perturbations.
2. SRP adds a relevant non-gravitational force for CubeSats.
3. Shadow model avoids applying SRP when there is no solar illumination.

Validation obtained (latest run):
1. Mean Sun acceleration (3-body): `0.309103 um/s^2`
2. Mean Moon acceleration (3-body): `0.795896 um/s^2`
3. Mean SRP acceleration: `0.052114 um/s^2`
4. Phase 3 RAAN rate: `0.936057 deg/day`
5. Phase 4 RAAN rate: `0.935761 deg/day`
6. Additional decay Phase 4 vs Phase 3: `0.056799 m` (10 orbits)
7. Final position delta Phase 3 vs Phase 4: `70.849 m`

Interpretation:
1. Third-body and SRP perturbations are smaller than `J2` in this short horizon, but measurable.
2. Accumulated effect appears in RAAN drift and trajectory separation.
3. Translational dynamics base is ready to integrate attitude in Phase 5.

Status: `Completed`

---

### Phase 5 - Attitude with Quaternions (Completed)
What was implemented:
1. Quaternion utility extension:
   - kinematic derivative with body rates,
   - body<->inertial DCM matrices,
   - vector rotation between frames.
2. Rigid-body attitude propagator:
   - state `q + omega`,
   - Euler equations for `omega_dot`,
   - integration with `solve_ivp(DOP853)`.
3. 3U CubeSat inertia model as rectangular prism:
   - diagonal tensor estimated from mass and dimensions.
4. External gravity-gradient torque:
   - coupled to Phase 4 orbital position.
5. New attitude plots:
   - `attitude_quaternion_components.png`
   - `attitude_body_rates.png`
   - `attitude_gravity_gradient_torque.png`

Why:
1. Quaternions eliminate Euler singularities.
2. Gravity-gradient is a relevant physical torque and a natural way to validate uncontrolled rotational dynamics.
3. Keeping the incremental scheme prepares Phase 6 (control) on top of a verified model.

Validation obtained (latest run):
1. Maximum quaternion norm error: `2.220e-16`
2. Initial angular-rate norm: `0.269258 deg/s`
3. Final angular-rate norm: `0.276357 deg/s`
4. Maximum angular-rate norm: `0.285517 deg/s`
5. Maximum slew from initial state: `179.990349 deg`
6. Mean nadir error with body Z axis: `89.882897 deg`
7. Mean GG torque: `43.651721 nN m`
8. Maximum GG torque: `64.885207 nN m`

Interpretation:
1. Quaternion kinematics remain numerically stable (`|q|~1`).
2. Without control, attitude does not maintain nadir pointing (expected behavior).
3. The system is ready to close the PD control loop in Phase 6.

Status: `Completed`

---

### Phase 6 - PD Control and Actuators (Completed)
What was implemented:
1. Quaternion PD controller tracking LVLH reference:
   - shortest-path quaternion error,
   - derivative term with angular-rate error.
2. Per-axis reaction wheel actuator:
   - maximum torque limit,
   - saturation evaluation.
3. Dual attitude simulation for comparison:
   - free case (no control),
   - controlled case (PD + wheels).
4. New Phase 6 figures:
   - `attitude_pointing_error_comparison.png`
   - `attitude_control_torque_comparison.png`
   - `attitude_quaternion_components_controlled.png`
   - `attitude_body_rates_controlled.png`

Why:
1. The PD loop turns rotational dynamics into useful pointing capability.
2. Actuator saturation avoids overestimating non-physical performance.
3. Free vs controlled comparison provides direct evidence of control benefit.

Validation obtained (latest run):
1. Mean nadir error without control: `89.882869 deg`
2. Mean nadir error with control: `0.056668 deg`
3. Final nadir error with control: `0.000001 deg`
4. Mean error reduction: `89.826201 deg`
5. Maximum applied RW torque: `0.564596 mN m`
6. Saturation events: `0.000 %`
7. Maximum quaternion norm error: `2.220e-16`

Interpretation:
1. PD control stabilizes and aligns the satellite toward nadir very effectively.
2. Wheels operate within limits in this scenario (no saturation).
3. The base is ready for external TLE validation in Phase 7.

Status: `Completed`

---

### Phase 7 - TLE Validation (Completed)
What was implemented:
1. TLE ingestion from file:
   - parser compatible with 2-line or 3-line TLE records.
2. Reference propagation with `SGP4`:
   - ECI states (`r`, `v`) in SI units.
3. In-house model propagation initialized at the same TLE state.
4. Quantitative model-vs-SGP4 comparison:
   - position and velocity norm errors,
   - RTN decomposition (radial, along-track, cross-track).
5. New validation figures:
   - `tle_position_velocity_error.png`
   - `tle_rtn_errors.png`

Why:
1. It closes the validation loop against a standard orbital reference.
2. It allows quantifying real simulator performance in terms of error.

Validation obtained (latest run):
1. TLE used: `ISS (ZARYA)` (local sample file).
2. Validation window: `15.483 h` (~10 ISS orbits).
3. RMS position error: `1.445595 km`
4. Maximum position error: `3.401309 km`
5. Final position error: `2.865684 km`
6. RMS velocity error: `1.622539 m/s`
7. Maximum radial error: `0.293110 km`
8. Maximum along-track error: `3.401235 km`
9. Maximum cross-track error: `0.084696 km`

Interpretation:
1. Dominant error appears in along-track, a typical behavior against SGP4/TLE.
2. External validation is completed with reproducible metrics.
3. The base project is technically closed for phases 0-7.

Status: `Completed`

## 11) Acceptance Criteria per Phase
1. Each phase must include:
   - executable implementation,
   - numerical evidence,
   - plots or tables,
   - updates to this memory and logbook.
2. No phase advances without minimum validation of the previous one.

## 12) Technical Risks and Mitigation
1. Risk: numerical instability as perturbations increase.
   - Mitigation: compare with and without perturbations, use strict tolerances.
2. Risk: drift due to incorrect reference-frame handling.
   - Mitigation: unit tests for ECI/LVLH transformations.
3. Risk: final validation difficulty.
   - Mitigation: prepare TLE comparison structure early.

## 13) How to Use This Document in the Project
For each new phase, update:
1. Corresponding phase section (`What`, `Why`, `Results`, `Status`).
2. Acceptance criteria if they change.
3. Risks and mitigations if new risks appear.
