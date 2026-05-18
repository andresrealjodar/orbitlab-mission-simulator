"""Perturbation models for orbital dynamics."""

import numpy as np

from satellite_simulator.constants import AU_M, J2_EARTH, MU_EARTH_M3_S2, OMEGA_EARTH_RAD_S, R_EARTH_M, SOLAR_PRESSURE_N_M2
from satellite_simulator.environment.atmosphere import exponential_density_kg_m3


def j2_acceleration_eci(r_eci_m: np.ndarray, mu: float = MU_EARTH_M3_S2, r_eq_m: float = R_EARTH_M) -> np.ndarray:
    """Earth J2 perturbation acceleration in ECI."""
    x, y, z = r_eci_m
    r2 = np.dot(r_eci_m, r_eci_m)
    r = np.sqrt(r2)
    z2_r2 = (z * z) / r2
    factor = 1.5 * J2_EARTH * mu * (r_eq_m**2) / (r**5)
    ax = factor * x * (5.0 * z2_r2 - 1.0)
    ay = factor * y * (5.0 * z2_r2 - 1.0)
    az = factor * z * (5.0 * z2_r2 - 3.0)
    return np.array([ax, ay, az], dtype=float)


def drag_acceleration_eci(
    r_eci_m: np.ndarray,
    v_eci_mps: np.ndarray,
    area_m2: float,
    mass_kg: float,
    cd: float,
    omega_earth_rad_s: float = OMEGA_EARTH_RAD_S,
    r_eq_m: float = R_EARTH_M,
) -> np.ndarray:
    """Aerodynamic drag acceleration in ECI using a co-rotating atmosphere."""
    altitude_m = np.linalg.norm(r_eci_m) - r_eq_m
    rho = exponential_density_kg_m3(altitude_m)
    omega_vec = np.array([0.0, 0.0, omega_earth_rad_s], dtype=float)
    v_atm_eci_mps = np.cross(omega_vec, r_eci_m)
    v_rel_eci_mps = v_eci_mps - v_atm_eci_mps
    v_rel = np.linalg.norm(v_rel_eci_mps)
    if v_rel < 1e-12:
        return np.zeros(3, dtype=float)
    return -0.5 * rho * cd * (area_m2 / mass_kg) * v_rel * v_rel_eci_mps


def srp_acceleration_eci(
    r_eci_m: np.ndarray,
    r_sun_eci_m: np.ndarray,
    area_m2: float,
    mass_kg: float,
    cr: float,
    include_shadow: bool = True,
) -> np.ndarray:
    """Solar radiation pressure acceleration in ECI."""
    if include_shadow and in_earth_shadow_cylindrical(r_eci_m, r_sun_eci_m):
        return np.zeros(3, dtype=float)

    sun_to_sat = r_eci_m - r_sun_eci_m
    distance = np.linalg.norm(sun_to_sat)
    if distance < 1e-6:
        return np.zeros(3, dtype=float)
    unit_sun_to_sat = sun_to_sat / distance
    pressure = SOLAR_PRESSURE_N_M2 * (AU_M / distance) ** 2
    return pressure * cr * (area_m2 / mass_kg) * unit_sun_to_sat


def third_body_acceleration_eci(r_eci_m: np.ndarray, r_body_eci_m: np.ndarray, mu_body_m3_s2: float) -> np.ndarray:
    """Third-body differential acceleration in ECI."""
    rel = r_body_eci_m - r_eci_m
    rel_norm = np.linalg.norm(rel)
    body_norm = np.linalg.norm(r_body_eci_m)
    if rel_norm < 1e-6 or body_norm < 1e-6:
        return np.zeros(3, dtype=float)
    return mu_body_m3_s2 * ((rel / rel_norm**3) - (r_body_eci_m / body_norm**3))


def in_earth_shadow_cylindrical(r_eci_m: np.ndarray, r_sun_eci_m: np.ndarray, r_earth_m: float = R_EARTH_M) -> bool:
    """Simple cylindrical eclipse test."""
    sun_dir = r_sun_eci_m / np.linalg.norm(r_sun_eci_m)
    projection = np.dot(r_eci_m, sun_dir)
    if projection > 0.0:
        return False
    perpendicular = r_eci_m - projection * sun_dir
    return np.linalg.norm(perpendicular) < r_earth_m
