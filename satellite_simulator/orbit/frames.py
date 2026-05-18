"""Reference-frame transforms used across dynamics and control."""

import numpy as np


def dcm_lvlh_from_eci(r_eci_m: np.ndarray, v_eci_mps: np.ndarray) -> np.ndarray:
    """Direction cosine matrix from ECI to LVLH."""
    r_hat = _unit(r_eci_m)
    h_hat = _unit(np.cross(r_eci_m, v_eci_mps))
    z_lvlh = -r_hat
    y_lvlh = -h_hat
    x_lvlh = _unit(np.cross(y_lvlh, z_lvlh))
    return np.vstack((x_lvlh, y_lvlh, z_lvlh))


def dcm_eci_from_lvlh(r_eci_m: np.ndarray, v_eci_mps: np.ndarray) -> np.ndarray:
    """Inverse transform LVLH -> ECI."""
    return dcm_lvlh_from_eci(r_eci_m, v_eci_mps).T


def _unit(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm == 0.0:
        raise ValueError("Cannot normalize a zero vector.")
    return vec / norm

