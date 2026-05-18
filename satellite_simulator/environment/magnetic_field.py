"""Magnetic field model placeholders."""

import numpy as np


def dipole_field_eci_t(*_: object, **__: object) -> np.ndarray:
    """Very simple placeholder dipole field vector in Tesla."""
    return np.zeros(3, dtype=float)

