"""Actuator models (reaction wheels, magnetorquers)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ReactionWheelArray:
    """Independent per-axis reaction wheel torque limits."""

    max_torque_n_m: np.ndarray  # shape (3,)

    def apply(self, commanded_torque_n_m: np.ndarray) -> np.ndarray:
        limits = np.abs(self.max_torque_n_m)
        return np.clip(commanded_torque_n_m, -limits, limits)

    def saturation_ratio(self, commanded_torque_n_m: np.ndarray) -> np.ndarray:
        limits = np.maximum(np.abs(self.max_torque_n_m), 1e-12)
        return np.abs(commanded_torque_n_m) / limits

