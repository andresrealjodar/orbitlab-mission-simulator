"""Rigid-body rotational dynamics utilities and propagators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp

from satellite_simulator.attitude.quaternion import derivative_body_rates, normalize, rotate_inertial_to_body
from satellite_simulator.constants import MU_EARTH_M3_S2


@dataclass(frozen=True)
class AttitudePropagationResult:
    """Container for propagated attitude states."""

    t_s: np.ndarray
    states_q_omega: np.ndarray

    @property
    def quaternion_bi(self) -> np.ndarray:
        return self.states_q_omega[:, :4]

    @property
    def omega_body_rad_s(self) -> np.ndarray:
        return self.states_q_omega[:, 4:]


@dataclass(frozen=True)
class RigidBodyState:
    quaternion_bi: np.ndarray  # [q0, q1, q2, q3]
    omega_rad_s: np.ndarray  # [wx, wy, wz] in body frame


TorqueModel = Callable[[float, np.ndarray, np.ndarray], np.ndarray]


def cuboid_inertia_tensor_kg_m2(mass_kg: float, size_xyz_m: tuple[float, float, float]) -> np.ndarray:
    """Inertia tensor of a homogeneous cuboid about center of mass."""
    lx, ly, lz = size_xyz_m
    i_xx = (mass_kg / 12.0) * (ly * ly + lz * lz)
    i_yy = (mass_kg / 12.0) * (lx * lx + lz * lz)
    i_zz = (mass_kg / 12.0) * (lx * lx + ly * ly)
    return np.diag([i_xx, i_yy, i_zz]).astype(float)


def gravity_gradient_torque_body_n_m(
    r_eci_m: np.ndarray,
    q_bi: np.ndarray,
    inertia_kg_m2: np.ndarray,
    mu_earth_m3_s2: float = MU_EARTH_M3_S2,
) -> np.ndarray:
    """Gravity-gradient torque in body coordinates."""
    r_norm = np.linalg.norm(r_eci_m)
    if r_norm < 1e-6:
        return np.zeros(3, dtype=float)
    r_hat_b = rotate_inertial_to_body(q_bi, r_eci_m / r_norm)
    return 3.0 * mu_earth_m3_s2 / (r_norm**3) * np.cross(r_hat_b, inertia_kg_m2 @ r_hat_b)


def euler_equation_rhs(inertia_kg_m2: np.ndarray, omega_rad_s: np.ndarray, torque_n_m: np.ndarray) -> np.ndarray:
    """Compute angular acceleration from Euler's rigid-body equation."""
    return np.linalg.solve(inertia_kg_m2, torque_n_m - np.cross(omega_rad_s, inertia_kg_m2 @ omega_rad_s))


def propagate_attitude(
    initial_state: RigidBodyState,
    inertia_kg_m2: np.ndarray,
    duration_s: float,
    output_step_s: float,
    torque_models: list[TorqueModel] | None = None,
    method: str = "DOP853",
    rtol: float = 1e-9,
    atol: float = 1e-11,
) -> AttitudePropagationResult:
    """Propagate attitude quaternion and body rates."""
    y0 = np.hstack((normalize(initial_state.quaternion_bi), initial_state.omega_rad_s)).astype(float)
    t_eval = np.arange(0.0, duration_s, output_step_s, dtype=float)
    if t_eval.size == 0 or not np.isclose(t_eval[-1], duration_s):
        t_eval = np.append(t_eval, duration_s)

    models = torque_models or []
    sol = solve_ivp(
        fun=lambda t, y: _attitude_ode(t, y, inertia_kg_m2, models),
        t_span=(0.0, duration_s),
        y0=y0,
        t_eval=t_eval,
        method=method,
        rtol=rtol,
        atol=atol,
    )
    if not sol.success:
        raise RuntimeError(f"Attitude propagation failed: {sol.message}")

    states = sol.y.T
    q = states[:, :4]
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    states[:, :4] = q
    return AttitudePropagationResult(t_s=sol.t, states_q_omega=states)


def _attitude_ode(
    t_s: float,
    state_q_omega: np.ndarray,
    inertia_kg_m2: np.ndarray,
    torque_models: list[TorqueModel],
) -> np.ndarray:
    q_bi = normalize(state_q_omega[:4])
    omega = state_q_omega[4:]
    torque = np.zeros(3, dtype=float)
    for model in torque_models:
        torque = torque + model(t_s, q_bi, omega)
    q_dot = derivative_body_rates(q_bi=q_bi, omega_body_rad_s=omega)
    omega_dot = euler_equation_rhs(inertia_kg_m2=inertia_kg_m2, omega_rad_s=omega, torque_n_m=torque)
    return np.hstack((q_dot, omega_dot))
