# Project Logbook

## How to Use This Logbook
Each entry must answer:
1. What was done.
2. Why it was done.
3. Result and evidence.
4. Next step.

Recommended date format: `YYYY-MM-DD`.

---

## 2026-05-10 - Entry 001 - Phase 0 closed
Phase: `0 - Definition and architecture`

What was done:
1. The final simulator objective was established.
2. A modular architecture was chosen (`orbit`, `attitude`, `environment`, `visualization`, `data`).
3. A phase-based roadmap was defined (0 to 7).
4. The baseline 3U CubeSat LEO scenario was selected.

Why:
1. A scalable and academically defensible base was needed.
2. Traceability was prioritized from the start.

Result:
1. Conceptual structure closed.
2. Progressive technical plan defined.

Evidence:
1. Folder structure created in the repository.
2. Project memory initialized.

Next step:
1. Implement Phase 1 (2-body) with numerical validation.

---

## 2026-05-10 - Entry 002 - Phase 1 implemented
Phase: `1 - Keplerian Orbit`

What was done:
1. Implemented Kepler->ECI conversion and orbital utilities.
2. Implemented 2-body propagator with `DOP853`.
3. Implemented console validation summary.
4. Implemented figures: 3D orbit, altitude vs time, invariants.
5. Created root entry point `main.py`.

Why:
1. A physically correct baseline was needed before introducing perturbations.
2. `DOP853` was chosen for precision.
3. Invariants were included for numerical quality control.

Result:
1. End-to-end executable simulation.
2. Plot outputs saved in `outputs/`.
3. Period error and drifts within a low range.

Evidence:
1. `outputs/orbit_3d.png`
2. `outputs/altitude_vs_time.png`
3. `outputs/invariants.png`
4. Numerical summary shown in console.

Next step:
1. Start Phase 2 with `J2` coupling.

---

## 2026-05-10 - Entry 003 - Memory and logbook system
Phase: `Cross-cutting (project management)`

What was done:
1. Created `docs/MEMORIA_PROYECTO.md`.
2. Created this logbook `docs/BITACORA_PROYECTO.md`.
3. Created reusable template for phase records.

Why:
1. The project requires continuous evidence of "what" and "why".
2. It simplifies final writing of the university project memory.

Result:
1. Formal traceability enabled for the full project lifecycle.

Next step:
1. Update this logbook at the close of each phase.

---

## 2026-05-10 - Entry 004 - Phase 2 implemented
Phase: `2 - J2 Perturbation`

What was done:
1. Generalized propagator to accept additional acceleration models.
2. Coupled `J2` perturbation acceleration.
3. Ran two comparable simulations:
   - Kepler 2-body
   - Kepler + J2
4. Implemented `RAAN` computation from ECI states.
5. Added comparative and nodal precession plots.

Why:
1. `J2` is the main perturbation in LEO.
2. `RAAN` precession demonstrates real orbital behavior.
3. Direct comparison validates the impact of `J2`.

Result:
1. RAAN drift in pure Kepler is nearly zero.
2. RAAN drift with J2 is clearly visible.
3. Simulated RAAN rate is very close to secular theory.

Evidence:
1. `outputs/orbit_3d_kepler_vs_j2.png`
2. `outputs/altitude_kepler_vs_j2.png`
3. `outputs/raan_vs_time.png`
4. Console numerical summary:
   - Simulated RAAN: `0.936052 deg/day`
   - Theoretical RAAN: `0.932416 deg/day`
   - Absolute error: `0.003636 deg/day`

Next step:
1. Start Phase 3 with atmospheric drag model.

---

## 2026-05-10 - Entry 005 - Phase 3 implemented
Phase: `3 - Atmospheric drag`

What was done:
1. Updated atmosphere model to layered exponential version (0-1000+ km).
2. Implemented drag acceleration in ECI with co-rotating atmosphere.
3. Ran three comparative cases:
   - Kepler
   - Kepler + J2
   - Kepler + J2 + Drag
4. Added new plots for J2 vs J2+drag comparison.

Why:
1. In LEO, drag defines part of orbital decay.
2. Layered model improves realism over single simple exponential model.
3. Comparative analysis clearly separates atmospheric effect.

Result:
1. Mean in-orbit drag acceleration: `0.416870 um/s^2`.
2. Additional decay due to drag (vs J2 case): `38.355348 m` in 10 orbits.
3. Final position difference J2 vs J2+drag: `2010.222 m`.

Evidence:
1. `outputs/orbit_3d_j2_vs_j2_drag.png`
2. `outputs/altitude_j2_vs_j2_drag.png`
3. `outputs/raan_j2_vs_j2_drag.png`
4. Phase 3 numerical summary in console.

Next step:
1. Start Phase 4: Sun/Moon and SRP perturbations.

---

## 2026-05-10 - Entry 006 - Phase 4 implemented
Phase: `4 - Sun/Moon and SRP`

What was done:
1. Implemented analytic Sun and Moon ephemerides in ECI.
2. Added absolute time handling via `Julian Date`.
3. Implemented third-body acceleration (Sun and Moon).
4. Implemented `SRP` with heliocentric distance dependence.
5. Implemented cylindrical Earth shadow for SRP.
6. Compared Phase 3 vs Phase 4 in orbit, altitude, and `RAAN`.
7. Added perturbation-magnitude plot.

Why:
1. These perturbations increase translational model fidelity.
2. They allow quantifying second-order forces relevant for CubeSats.

Result:
1. Measurable accumulated Phase 4 effect on trajectory.
2. Acceleration magnitudes in coherent order:
   - Moon > Sun > SRP (in this short scenario).
3. Final difference Phase 3 vs Phase 4: `70.849 m`.

Evidence:
1. `outputs/orbit_3d_j2_drag_vs_phase4.png`
2. `outputs/altitude_j2_drag_vs_phase4.png`
3. `outputs/raan_j2_drag_vs_phase4.png`
4. `outputs/perturbations_phase4.png`
5. Phase 4 numerical summary in console.

Next step:
1. Start Phase 5: rotational dynamics and quaternions.

---

## 2026-05-10 - Entry 007 - Phase 5 implemented
Phase: `5 - Attitude dynamics with quaternions`

What was done:
1. Completed quaternion block with kinematics and frame rotations.
2. Implemented rigid-body attitude propagator (`q + omega`).
3. Implemented cuboid inertia tensor for 3U CubeSat.
4. Implemented gravity-gradient torque coupled to Phase 4 orbit.
5. Integrated attitude metrics and plots into main flow.

Why:
1. Attitude needed robust singularity-free representation.
2. A validated rotational dynamics model was needed before PD control.

Result:
1. Stable attitude propagation with conserved quaternion norm.
2. Measurable gravity-gradient torque in nN m scale.
3. Coherent uncontrolled behavior (no nadir maintenance).

Evidence:
1. `outputs/attitude_quaternion_components.png`
2. `outputs/attitude_body_rates.png`
3. `outputs/attitude_gravity_gradient_torque.png`
4. Phase 5 numerical summary in console.

Next step:
1. Start Phase 6: PD controller and actuators.

---

## 2026-05-10 - Entry 008 - Phase 6 implemented
Phase: `6 - PD control and actuators`

What was done:
1. Implemented quaternion PD controller with shortest-path orientation error.
2. Included LVLH attitude reference for nadir pointing.
3. Included orbital angular-rate reference in control law.
4. Implemented reaction wheel model with per-axis saturation.
5. Ran two attitude scenarios:
   - Free (no control)
   - Controlled (PD + wheels)
6. Added pointing-error and control-torque plots.

Why:
1. Closing the loop was necessary to move from dynamics simulation to real pointing capability.
2. Saturation avoids assuming unlimited ideal actuators.

Result:
1. Very strong reduction of nadir pointing error.
2. Operation within wheel limits (no saturation in baseline case).
3. Numerically stable quaternion and body-rate behavior.

Evidence:
1. `outputs/attitude_pointing_error_comparison.png`
2. `outputs/attitude_control_torque_comparison.png`
3. `outputs/attitude_quaternion_components_controlled.png`
4. `outputs/attitude_body_rates_controlled.png`
5. Phase 6 numerical summary in console:
   - free mean error: `89.882869 deg`
   - controlled mean error: `0.056668 deg`
   - controlled final error: `0.000001 deg`
   - wheel saturation: `0.000 %`

Next step:
1. Start Phase 7: TLE/SGP4 validation.

---

## 2026-05-11 - Entry 009 - Phase 7 implemented
Phase: `7 - TLE/SGP4 validation`

What was done:
1. Implemented TLE file parser.
2. Implemented reference propagation with `sgp4` library.
3. Aligned in-house model propagation to the same initial TLE state.
4. Computed position/velocity error and RTN decomposition.
5. Generated external validation plots.

Why:
1. This was the key step to close the project with evidence against a standard reference.
2. It enabled objective measurement of simulator orbital accuracy.

Result:
1. External validation completed with quantitative metrics.
2. Dominant error observed in along-track (expected in TLE/SGP4 comparison).
3. Phases 0-7 closed.

Evidence:
1. `outputs/tle_position_velocity_error.png`
2. `outputs/tle_rtn_errors.png`
3. Console summary:
   - RMS position: `1.445595 km`
   - Max position: `3.401309 km`
   - RMS velocity: `1.622539 m/s`

Next step:
1. Continue with the next work block according to the updated project roadmap.
