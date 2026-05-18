# Current State (Handoff)

## 1) Project Status
- Date: `2026-05-11`
- Overall status: phases `0-7` completed.
- Active entrypoint: `python main.py` (calls `run_phase_7`).
- Last completed objective: Phase 7 TLE/SGP4 validation integrated and executed.

## 2) Implemented Features
- Translational dynamics:
  - two-body propagation,
  - J2 perturbation,
  - atmospheric drag (piecewise exponential model),
  - third-body Sun/Moon differential acceleration,
  - SRP with cylindrical Earth eclipse switch.
- Attitude dynamics:
  - rigid-body quaternion kinematics,
  - Euler rotational dynamics,
  - gravity-gradient torque.
- Attitude control:
  - quaternion PD controller,
  - LVLH/nadir reference tracking,
  - reaction wheel torque saturation.
- External validation:
  - TLE file ingestion,
  - SGP4 reference propagation,
  - model-vs-SGP4 error metrics (norm + RTN),
  - validation plots.

## 3) Existing Modules
- `satellite_simulator/main.py`: integrated phase-7 pipeline and reporting.
- `satellite_simulator/constants.py`: constants + `ScenarioConfig`.
- `satellite_simulator/orbit/`
  - `propagator.py`, `kepler.py`, `perturbations.py`, `frames.py`, `tle_validation.py`.
- `satellite_simulator/attitude/`
  - `quaternion.py`, `rigid_body.py`, `controller.py`, `actuators.py`.
- `satellite_simulator/environment/`
  - `atmosphere.py`, `sun.py`, `moon.py`, `time_utils.py`, `magnetic_field.py`.
- `satellite_simulator/visualization/plots.py`: all generated figures.
- `satellite_simulator/data/tle/iss_sample.tle`: local sample TLE.

## 4) Key Technical Decisions
- Integrator: `solve_ivp(method="DOP853")` for both orbit and attitude.
- Units: SI internally; plot/report conversions only at output.
- Progressive model layering (phase style): kept for traceability and debugging.
- Phase 7 validation strategy:
  - initialize model from SGP4 epoch state,
  - compare propagated trajectories over same time grid.

## 5) Relevant APIs / Entry Points
- Run full pipeline:
  - `python main.py`
- Run with specific TLE:
  - `python main.py --tle-file <path>`
- Core functions:
  - `run_phase_7(...)` in `satellite_simulator/main.py`
  - `propagate_orbit(...)` in `orbit/propagator.py`
  - `propagate_attitude(...)` in `attitude/rigid_body.py`
  - `propagate_tle_with_sgp4(...)` and `validate_against_tle(...)` in `orbit/tle_validation.py`

## 6) Latest Validation Snapshot
- Phase 7 run (ISS sample TLE, ~15.483 h):
  - RMS position error: `1.445595 km`
  - Max position error: `3.401309 km`
  - Final position error: `2.865684 km`
  - RMS velocity error: `1.622539 m/s`
  - Max RTN errors:
    - Radial: `0.293110 km`
    - Along-track: `3.401235 km`
    - Cross-track: `0.084696 km`

## 7) Known Bugs / Limitations
- Frame mismatch risk:
  - SGP4 states are TEME; current comparison treats them as ECI-like directly.
- Ephemerides precision:
  - Sun/Moon models are analytic approximations, not JPL/SPICE-grade.
- TLE freshness:
  - default validation uses local sample file; no automatic live TLE retrieval.
- Runner size:
  - `satellite_simulator/main.py` is monolithic and should be split for maintainability.

## 8) Open Issues
- Add explicit TEME -> ECI conversion path before strict SGP4 comparison.
- Add test suite for:
  - quaternion algebra invariants,
  - perturbation toggles,
  - TLE parser edge cases.
- Add structured configuration layer (scenario, gains, actuator limits, TLE path).

## 9) Pending Tasks
- Improve Phase 7 robustness:
  - multiple TLE records selection by satellite name/NORAD ID,
  - batch validation report export (CSV/JSON).

## 10) Recommended Next Steps
1. Refactor `satellite_simulator/main.py` into:
   - `pipelines/orbit.py`
   - `pipelines/attitude.py`
   - `pipelines/validation.py`
2. Implement TEME/ECI frame handling for stricter SGP4 comparison.
3. Add automated tests and CI smoke run (`python main.py` + compile check).
4. Define and execute the next functional block according to the updated roadmap.

## 11) Short Handoff Summary
- What was being done now:
  - closed Phase 7 by integrating TLE/SGP4 validation into the main pipeline and documenting results.
- Most relevant files:
  - `satellite_simulator/main.py`
  - `satellite_simulator/orbit/tle_validation.py`
  - `satellite_simulator/visualization/plots.py`
  - `satellite_simulator/data/tle/iss_sample.tle`
  - `README.md`, `docs/MEMORIA_PROYECTO.md`, `docs/BITACORA_PROYECTO.md`
- What should be done next:
  - refactor pipeline + improve frame rigor (TEME/ECI), then continue with the updated roadmap priorities.

