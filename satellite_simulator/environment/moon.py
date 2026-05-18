"""Lunar ephemeris approximations for Phase 4."""

from __future__ import annotations

import numpy as np


def moon_position_eci_m(julian_date_utc: float) -> np.ndarray:
    """Low-precision geocentric Moon vector in ECI (J2000-like frame).

    Approximation follows a reduced Astronomical Almanac-style model.
    """
    d_days = julian_date_utc - 2451545.0
    mean_longitude_deg = _wrap_deg(218.316 + 13.176396 * d_days)
    mean_anomaly_deg = _wrap_deg(134.963 + 13.064993 * d_days)
    argument_latitude_deg = _wrap_deg(93.272 + 13.229350 * d_days)

    mean_anomaly_rad = np.deg2rad(mean_anomaly_deg)
    argument_latitude_rad = np.deg2rad(argument_latitude_deg)
    ecliptic_longitude_rad = np.deg2rad(_wrap_deg(mean_longitude_deg + 6.289 * np.sin(mean_anomaly_rad)))
    ecliptic_latitude_rad = np.deg2rad(5.128 * np.sin(argument_latitude_rad))
    distance_km = 385001.0 - 20905.0 * np.cos(mean_anomaly_rad)

    n_days = d_days
    obliquity_rad = np.deg2rad(23.439 - 0.0000004 * n_days)

    x_ecl = distance_km * np.cos(ecliptic_latitude_rad) * np.cos(ecliptic_longitude_rad)
    y_ecl = distance_km * np.cos(ecliptic_latitude_rad) * np.sin(ecliptic_longitude_rad)
    z_ecl = distance_km * np.sin(ecliptic_latitude_rad)

    x_eci = x_ecl
    y_eci = y_ecl * np.cos(obliquity_rad) - z_ecl * np.sin(obliquity_rad)
    z_eci = y_ecl * np.sin(obliquity_rad) + z_ecl * np.cos(obliquity_rad)

    return 1_000.0 * np.array([x_eci, y_eci, z_eci], dtype=float)


def _wrap_deg(angle_deg: float) -> float:
    return float(angle_deg % 360.0)

