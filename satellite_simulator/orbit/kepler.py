"""Keplerian utility functions and state conversions."""

from dataclasses import dataclass

import numpy as np

from satellite_simulator.constants import MU_EARTH_M3_S2


@dataclass(frozen=True)
class OrbitalElements:
    """Classical orbital elements in SI/radians."""

    semi_major_axis_m: float
    eccentricity: float
    inclination_rad: float
    raan_rad: float
    arg_perigee_rad: float
    true_anomaly_rad: float


def mean_motion_rad_s(semi_major_axis_m: float, mu: float = MU_EARTH_M3_S2) -> float:
    return np.sqrt(mu / (semi_major_axis_m**3))


def orbital_period_s(semi_major_axis_m: float, mu: float = MU_EARTH_M3_S2) -> float:
    return 2.0 * np.pi / mean_motion_rad_s(semi_major_axis_m, mu=mu)


def specific_energy_j_kg(r_eci_m: np.ndarray, v_eci_mps: np.ndarray, mu: float = MU_EARTH_M3_S2) -> float:
    r_norm = np.linalg.norm(r_eci_m)
    v_norm = np.linalg.norm(v_eci_mps)
    return 0.5 * v_norm**2 - (mu / r_norm)


def specific_angular_momentum_m2_s(r_eci_m: np.ndarray, v_eci_mps: np.ndarray) -> np.ndarray:
    return np.cross(r_eci_m, v_eci_mps)


def raan_from_state_rad(r_eci_m: np.ndarray, v_eci_mps: np.ndarray) -> float:
    """Compute right ascension of ascending node from inertial state."""
    h_vec = np.cross(r_eci_m, v_eci_mps)
    n_vec = np.cross(np.array([0.0, 0.0, 1.0], dtype=float), h_vec)
    n_norm = np.linalg.norm(n_vec)
    if n_norm < 1e-12:
        return 0.0
    return np.arctan2(n_vec[1], n_vec[0])


def inclination_from_state_rad(r_eci_m: np.ndarray, v_eci_mps: np.ndarray) -> float:
    """Compute inclination from inertial state."""
    h_vec = np.cross(r_eci_m, v_eci_mps)
    h_norm = np.linalg.norm(h_vec)
    if h_norm < 1e-12:
        return 0.0
    cos_i = np.clip(h_vec[2] / h_norm, -1.0, 1.0)
    return np.arccos(cos_i)


def raan_series_deg(states_eci: np.ndarray, unwrap: bool = True) -> np.ndarray:
    """Return RAAN time series in degrees from propagated states."""
    r = states_eci[:, :3]
    v = states_eci[:, 3:]
    raan_rad = np.array([raan_from_state_rad(ri, vi) for ri, vi in zip(r, v, strict=False)], dtype=float)
    if unwrap:
        raan_rad = np.unwrap(raan_rad)
    return np.rad2deg(raan_rad)


def keplerian_to_eci(elements: OrbitalElements, mu: float = MU_EARTH_M3_S2) -> tuple[np.ndarray, np.ndarray]:
    """Convert classical elements to inertial position/velocity vectors."""
    a = elements.semi_major_axis_m
    e = elements.eccentricity
    i = elements.inclination_rad
    raan = elements.raan_rad
    argp = elements.arg_perigee_rad
    nu = elements.true_anomaly_rad

    p = a * (1.0 - e**2)
    r_pf = (p / (1.0 + e * np.cos(nu))) * np.array([np.cos(nu), np.sin(nu), 0.0], dtype=float)
    v_pf = np.sqrt(mu / p) * np.array([-np.sin(nu), e + np.cos(nu), 0.0], dtype=float)

    dcm_eci_from_pf = _r3(raan) @ _r1(i) @ _r3(argp)
    r_eci = dcm_eci_from_pf @ r_pf
    v_eci = dcm_eci_from_pf @ v_pf
    return r_eci, v_eci


def _r1(angle_rad: float) -> np.ndarray:
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    return np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, c, -s],
            [0.0, s, c],
        ],
        dtype=float,
    )


def _r3(angle_rad: float) -> np.ndarray:
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    return np.array(
        [
            [c, -s, 0.0],
            [s, c, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
