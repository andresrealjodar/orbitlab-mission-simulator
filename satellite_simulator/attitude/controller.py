"""Attitude control laws (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from satellite_simulator.attitude.quaternion import quaternion_error_shortest_path


@dataclass(frozen=True)
class PDGains:
    kp_vec: np.ndarray
    kd_vec: np.ndarray


def quaternion_pd_torque(
    q_current_bi: np.ndarray,
    q_desired_bi: np.ndarray,
    omega_current_body_rad_s: np.ndarray,
    omega_desired_body_rad_s: np.ndarray,
    gains: PDGains,
) -> np.ndarray:
    """Quaternion PD control torque in body frame."""
    q_err = quaternion_error_shortest_path(q_current_bi=q_current_bi, q_desired_bi=q_desired_bi)
    e_vec = q_err[1:]
    omega_err = omega_current_body_rad_s - omega_desired_body_rad_s
    return -gains.kp_vec * e_vec - gains.kd_vec * omega_err

