# AGENTS.md

## Project Scope
- Project: `Satellite Simulator` (CubeSat 3U, LEO)
- Status: phases 0-7 implemented.
- Current runner: `satellite_simulator/main.py` (`run_phase_7`).

## Current Architecture
- `main.py` (repo root): convenience entrypoint (`python main.py`).
- `satellite_simulator/main.py`: integrated pipeline:
  - translational propagation (2-body, J2, drag, Sun/Moon, SRP),
  - attitude dynamics (quaternion rigid-body),
  - PD attitude control + reaction wheel saturation,
  - TLE/SGP4 validation.
- `satellite_simulator/constants.py`: physical constants + scenario defaults.
- `satellite_simulator/orbit/`:
  - `propagator.py`: numerical propagation core (`solve_ivp`, DOP853),
  - `kepler.py`: orbital element/state utilities,
  - `perturbations.py`: J2, drag, third-body, SRP, eclipse helper,
  - `frames.py`: ECI/LVLH DCM transforms,
  - `tle_validation.py`: TLE parsing, SGP4 propagation, error metrics.
- `satellite_simulator/attitude/`:
  - `quaternion.py`: quaternion ops + frame rotation helpers,
  - `rigid_body.py`: attitude propagator + gravity-gradient torque + inertia,
  - `controller.py`: quaternion PD control law,
  - `actuators.py`: reaction wheel saturation model.
- `satellite_simulator/environment/`:
  - `atmosphere.py`: piecewise exponential density model,
  - `sun.py`, `moon.py`: analytic ephemeris approximations,
  - `time_utils.py`: ISO UTC -> Julian Date conversion.
- `satellite_simulator/visualization/plots.py`: all plot generators.
- `satellite_simulator/data/tle/`: local TLE inputs (includes `iss_sample.tle`).
- `docs/`: memory, logbook, and phase templates.

## Important Rules
- Keep all dynamics in SI units unless explicitly stated:
  - position `m`, velocity `m/s`, torque `N m`, angles `rad` (internal).
- Preserve phase pipeline behavior; do not remove previous phase outputs.
- Avoid changing default scenario values unless required by task.
- New code should be deterministic and runnable offline (except optional installs).
- Keep compatibility with:
  - `python main.py`
  - `python -m satellite_simulator.main`

## Conventions
- Naming:
  - `_m`, `_mps`, `_rad_s`, `_deg`, `_ppm` suffixes for units.
- Data containers:
  - use `@dataclass(frozen=True)` for result structs where possible.
- Time grids:
  - include final sample `duration_s`.
- Plot outputs:
  - saved in `outputs/`, do not require GUI backend.
- TLE validation:
  - first valid TLE record in file is used by default.

## Relevant Commands
- Install deps:
  - `python -m pip install -r requirements.txt`
- Run full pipeline (phase 7):
  - `python main.py`
- Run with explicit TLE:
  - `python main.py --tle-file satellite_simulator/data/tle/iss_sample.tle`
- Quick syntax check:
  - `python -m compileall -q satellite_simulator main.py`

## Project Structure (compact)
- `main.py`
- `requirements.txt`
- `satellite_simulator/`
  - `main.py`, `constants.py`
  - `orbit/`, `attitude/`, `environment/`, `visualization/`, `data/tle/`
- `docs/`
  - `MEMORIA_PROYECTO.md`
  - `BITACORA_PROYECTO.md`
  - `PLANTILLA_REGISTRO_FASE.md`
  - `current_state.md`

## Known Technical Caveats
- SGP4 output frame is TEME; current validation treats it as ECI-like for direct comparison.
- Ephemerides are analytic approximations (not JPL/SPICE precision).
- Phase 7 currently validates against a local sample TLE by default (not auto-fetched live data).
