"""Solar ephemeris approximations for Phase 4."""

from __future__ import annotations

import numpy as np

from satellite_simulator.constants import AU_M


def sun_position_eci_m(julian_date_utc: float) -> np.ndarray:
    """Low-precision geocentric Sun vector in ECI (J2000-like frame).

    Approximation follows Astronomical Almanac low-precision formula.
    """
    n_days = julian_date_utc - 2451545.0
    mean_longitude_deg = _wrap_deg(280.460 + 0.9856474 * n_days)
    mean_anomaly_deg = _wrap_deg(357.528 + 0.9856003 * n_days)
    mean_anomaly_rad = np.deg2rad(mean_anomaly_deg)

    ecliptic_longitude_deg = mean_longitude_deg + 1.915 * np.sin(mean_anomaly_rad) + 0.020 * np.sin(2.0 * mean_anomaly_rad)
    ecliptic_longitude_rad = np.deg2rad(_wrap_deg(ecliptic_longitude_deg))
    obliquity_rad = np.deg2rad(23.439 - 0.0000004 * n_days)

    distance_au = 1.00014 - 0.01671 * np.cos(mean_anomaly_rad) - 0.00014 * np.cos(2.0 * mean_anomaly_rad)

    x = distance_au * np.cos(ecliptic_longitude_rad)
    y = distance_au * np.cos(obliquity_rad) * np.sin(ecliptic_longitude_rad)
    z = distance_au * np.sin(obliquity_rad) * np.sin(ecliptic_longitude_rad)
    return AU_M * np.array([x, y, z], dtype=float)


def _wrap_deg(angle_deg: float) -> float:
    return float(angle_deg % 360.0)

