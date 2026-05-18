"""Numerical orbit propagators."""

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp

from satellite_simulator.constants import MU_EARTH_M3_S2


@dataclass(frozen=True)
class PropagationResult:
    """Container for propagated state and diagnostics."""

    t_s: np.ndarray
    states_eci: np.ndarray
    specific_energy_j_kg: np.ndarray
    h_norm_m2_s: np.ndarray

    @property
    def r_eci_m(self) -> np.ndarray:
        return self.states_eci[:, :3]

    @property
    def v_eci_mps(self) -> np.ndarray:
        return self.states_eci[:, 3:]


AccelerationModel = Callable[[float, np.ndarray, np.ndarray], np.ndarray]


def propagate_two_body(
    r0_eci_m: np.ndarray,
    v0_eci_mps: np.ndarray,
    duration_s: float,
    output_step_s: float = 20.0,
    mu: float = MU_EARTH_M3_S2,
    method: str = "DOP853",
) -> PropagationResult:
    """Propagate two-body dynamics with a high-order adaptive integrator."""
    return propagate_orbit(
        r0_eci_m=r0_eci_m,
        v0_eci_mps=v0_eci_mps,
        duration_s=duration_s,
        output_step_s=output_step_s,
        mu=mu,
        method=method,
        acceleration_models=None,
    )


def propagate_orbit(
    r0_eci_m: np.ndarray,
    v0_eci_mps: np.ndarray,
    duration_s: float,
    output_step_s: float = 20.0,
    mu: float = MU_EARTH_M3_S2,
    method: str = "DOP853",
    acceleration_models: list[AccelerationModel] | None = None,
) -> PropagationResult:
    """Propagate orbit with optional perturbing acceleration models."""
    y0 = np.hstack((r0_eci_m, v0_eci_mps))
    t_eval = np.arange(0.0, duration_s, output_step_s, dtype=float)
    if t_eval.size == 0 or not np.isclose(t_eval[-1], duration_s):
        t_eval = np.append(t_eval, duration_s)

    models = acceleration_models or []

    sol = solve_ivp(
        fun=lambda t, y: _orbit_ode(t, y, mu=mu, acceleration_models=models),
        t_span=(0.0, duration_s),
        y0=y0,
        t_eval=t_eval,
        method=method,
        rtol=1e-10,
        atol=1e-12,
    )
    if not sol.success:
        raise RuntimeError(f"Propagation failed: {sol.message}")

    states = sol.y.T
    r = states[:, :3]
    v = states[:, 3:]
    r_norm = np.linalg.norm(r, axis=1)
    v_norm = np.linalg.norm(v, axis=1)
    specific_energy = 0.5 * v_norm**2 - (mu / r_norm)
    h_norm = np.linalg.norm(np.cross(r, v), axis=1)

    return PropagationResult(
        t_s=sol.t,
        states_eci=states,
        specific_energy_j_kg=specific_energy,
        h_norm_m2_s=h_norm,
    )


def _orbit_ode(t_s: float, state: np.ndarray, mu: float, acceleration_models: list[AccelerationModel]) -> np.ndarray:
    r = state[:3]
    v = state[3:]
    r_norm = np.linalg.norm(r)
    a = -mu * r / (r_norm**3)
    for model in acceleration_models:
        a = a + model(t_s, r, v)
    return np.hstack((v, a))
