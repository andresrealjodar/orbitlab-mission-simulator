"""Atmospheric density models."""

from __future__ import annotations

import numpy as np

# Exponential atmosphere model (Vallado-style table, 0-1000 km).
# Columns: base altitude [km], base density [kg/m^3], scale height [km]
_EXPONENTIAL_TABLE = np.array(
    [
        [0.0, 1.225, 7.249],
        [25.0, 3.899e-2, 6.349],
        [30.0, 1.774e-2, 6.682],
        [40.0, 3.972e-3, 7.554],
        [50.0, 1.057e-3, 8.382],
        [60.0, 3.206e-4, 7.714],
        [70.0, 8.770e-5, 6.549],
        [80.0, 1.905e-5, 5.799],
        [90.0, 3.396e-6, 5.382],
        [100.0, 5.297e-7, 5.877],
        [110.0, 9.661e-8, 7.263],
        [120.0, 2.438e-8, 9.473],
        [130.0, 8.484e-9, 12.636],
        [140.0, 3.845e-9, 16.149],
        [150.0, 2.070e-9, 22.523],
        [180.0, 5.464e-10, 29.740],
        [200.0, 2.789e-10, 37.105],
        [250.0, 7.248e-11, 45.546],
        [300.0, 2.418e-11, 53.628],
        [350.0, 9.518e-12, 53.298],
        [400.0, 3.725e-12, 58.515],
        [450.0, 1.585e-12, 60.828],
        [500.0, 6.967e-13, 63.822],
        [600.0, 1.454e-13, 71.835],
        [700.0, 3.614e-14, 88.667],
        [800.0, 1.170e-14, 124.640],
        [900.0, 5.245e-15, 181.050],
        [1000.0, 3.019e-15, 268.000],
    ],
    dtype=float,
)


def exponential_density_kg_m3(altitude_m: float) -> float:
    """Piecewise-exponential atmosphere density from 0 to 1000+ km."""
    altitude_km = max(0.0, altitude_m / 1_000.0)
    idx = np.searchsorted(_EXPONENTIAL_TABLE[:, 0], altitude_km, side="right") - 1
    idx = int(np.clip(idx, 0, len(_EXPONENTIAL_TABLE) - 1))
    h0_km, rho0, h_scale_km = _EXPONENTIAL_TABLE[idx]
    rho = rho0 * np.exp(-(altitude_km - h0_km) / h_scale_km)
    return float(max(rho, 0.0))

