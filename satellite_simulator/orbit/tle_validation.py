"""TLE validation utilities (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class TLERecord:
    name: str
    line1: str
    line2: str


@dataclass(frozen=True)
class SGP4PropagationResult:
    t_s: np.ndarray
    r_eci_m: np.ndarray
    v_eci_mps: np.ndarray
    epoch_jd_utc: float


@dataclass(frozen=True)
class TLEValidationMetrics:
    rms_position_error_m: float
    mean_position_error_m: float
    max_position_error_m: float
    final_position_error_m: float
    rms_velocity_error_mps: float
    max_radial_error_m: float
    max_along_track_error_m: float
    max_cross_track_error_m: float
    radial_error_m: np.ndarray
    along_track_error_m: np.ndarray
    cross_track_error_m: np.ndarray
    position_error_norm_m: np.ndarray
    velocity_error_norm_mps: np.ndarray


def sgp4_available() -> bool:
    try:
        import sgp4  # noqa: F401
    except ImportError:
        return False
    return True


def load_tle_file(tle_path: Path) -> list[TLERecord]:
    """Load one or more TLE records from text file."""
    lines = [line.strip() for line in tle_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records: list[TLERecord] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("1 ") and (i + 1) < len(lines) and lines[i + 1].startswith("2 "):
            name = f"SAT-{len(records) + 1}"
            line1 = lines[i]
            line2 = lines[i + 1]
            i += 2
        elif (i + 2) < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            name = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]
            i += 3
        else:
            i += 1
            continue
        records.append(TLERecord(name=name, line1=line1, line2=line2))
    if not records:
        raise ValueError(f"No valid TLE records found in: {tle_path}")
    return records


def propagate_tle_with_sgp4(tle: TLERecord, t_eval_s: np.ndarray) -> SGP4PropagationResult:
    """Propagate TLE with SGP4 and return ECI states in SI units."""
    try:
        from sgp4.api import SGP4_ERRORS, Satrec
    except ImportError as exc:
        raise RuntimeError("`sgp4` package is not installed. Install it to run Phase 7.") from exc

    sat = Satrec.twoline2rv(tle.line1, tle.line2)
    epoch_jd = float(sat.jdsatepoch + sat.jdsatepochF)
    r_km = np.zeros((len(t_eval_s), 3), dtype=float)
    v_km_s = np.zeros((len(t_eval_s), 3), dtype=float)
    for idx, dt_s in enumerate(t_eval_s):
        jd_total = epoch_jd + float(dt_s) / 86400.0
        jd_int = np.floor(jd_total)
        fr = jd_total - jd_int
        err_code, r_i_km, v_i_km_s = sat.sgp4(jd_int, fr)
        if err_code != 0:
            err_msg = SGP4_ERRORS.get(err_code, f"Unknown SGP4 error code {err_code}")
            raise RuntimeError(f"SGP4 propagation failed at t={dt_s:.3f} s: {err_msg}")
        r_km[idx, :] = r_i_km
        v_km_s[idx, :] = v_i_km_s
    return SGP4PropagationResult(
        t_s=t_eval_s.copy(),
        r_eci_m=r_km * 1_000.0,
        v_eci_mps=v_km_s * 1_000.0,
        epoch_jd_utc=epoch_jd,
    )


def validate_against_tle(
    r_model_eci_m: np.ndarray,
    v_model_eci_mps: np.ndarray,
    r_ref_eci_m: np.ndarray,
    v_ref_eci_mps: np.ndarray,
) -> TLEValidationMetrics:
    """Compute validation metrics model-vs-SGP4 and RTN decomposition."""
    dr = r_model_eci_m - r_ref_eci_m
    dv = v_model_eci_mps - v_ref_eci_mps
    position_norm = np.linalg.norm(dr, axis=1)
    velocity_norm = np.linalg.norm(dv, axis=1)

    radial = np.zeros(len(dr), dtype=float)
    along = np.zeros(len(dr), dtype=float)
    cross = np.zeros(len(dr), dtype=float)
    for i in range(len(dr)):
        r_ref = r_ref_eci_m[i]
        v_ref = v_ref_eci_mps[i]
        r_hat = _safe_unit(r_ref)
        h_hat = _safe_unit(np.cross(r_ref, v_ref))
        t_hat = _safe_unit(np.cross(h_hat, r_hat))
        radial[i] = float(np.dot(dr[i], r_hat))
        along[i] = float(np.dot(dr[i], t_hat))
        cross[i] = float(np.dot(dr[i], h_hat))

    return TLEValidationMetrics(
        rms_position_error_m=float(np.sqrt(np.mean(position_norm**2))),
        mean_position_error_m=float(np.mean(position_norm)),
        max_position_error_m=float(np.max(position_norm)),
        final_position_error_m=float(position_norm[-1]),
        rms_velocity_error_mps=float(np.sqrt(np.mean(velocity_norm**2))),
        max_radial_error_m=float(np.max(np.abs(radial))),
        max_along_track_error_m=float(np.max(np.abs(along))),
        max_cross_track_error_m=float(np.max(np.abs(cross))),
        radial_error_m=radial,
        along_track_error_m=along,
        cross_track_error_m=cross,
        position_error_norm_m=position_norm,
        velocity_error_norm_mps=velocity_norm,
    )


def _safe_unit(vec: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(vec)
    if n < 1e-12:
        return np.zeros_like(vec)
    return vec / n

