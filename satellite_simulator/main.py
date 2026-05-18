"""Phase 7 runner: TLE/SGP4 validation on top of Phase 6 pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from satellite_simulator.attitude.actuators import ReactionWheelArray
from satellite_simulator.attitude.controller import PDGains, quaternion_pd_torque
from satellite_simulator.attitude.quaternion import quaternion_from_dcm_body_to_inertial, rotate_body_to_inertial, rotate_inertial_to_body
from satellite_simulator.attitude.rigid_body import (
    AttitudePropagationResult,
    RigidBodyState,
    cuboid_inertia_tensor_kg_m2,
    gravity_gradient_torque_body_n_m,
    propagate_attitude,
)
from satellite_simulator.constants import (
    CUBESAT_3U_CD,
    CUBESAT_3U_CR,
    CUBESAT_3U_MASS_KG,
    CUBESAT_3U_REFERENCE_AREA_M2,
    CUBESAT_3U_SIZE_M,
    J2_EARTH,
    MU_EARTH_M3_S2,
    MU_MOON_M3_S2,
    MU_SUN_M3_S2,
    R_EARTH_M,
    ScenarioConfig,
)
from satellite_simulator.environment.moon import moon_position_eci_m
from satellite_simulator.environment.sun import sun_position_eci_m
from satellite_simulator.environment.time_utils import julian_date_from_datetime_utc, parse_utc_datetime
from satellite_simulator.orbit.frames import dcm_eci_from_lvlh
from satellite_simulator.orbit.kepler import OrbitalElements, keplerian_to_eci, orbital_period_s, raan_series_deg
from satellite_simulator.orbit.perturbations import (
    drag_acceleration_eci,
    in_earth_shadow_cylindrical,
    j2_acceleration_eci,
    srp_acceleration_eci,
    third_body_acceleration_eci,
)
from satellite_simulator.orbit.propagator import PropagationResult, propagate_orbit, propagate_two_body
from satellite_simulator.orbit.tle_validation import (
    SGP4PropagationResult,
    TLEValidationMetrics,
    load_tle_file,
    propagate_tle_with_sgp4,
    sgp4_available,
    validate_against_tle,
)
from satellite_simulator.visualization.plots import (
    plot_altitude_comparison,
    plot_attitude_torques,
    plot_body_rates,
    plot_conservation,
    plot_control_torque_comparison,
    plot_orbit_3d_compare,
    plot_perturbation_magnitudes,
    plot_pointing_error_comparison,
    plot_quaternion_components,
    plot_raan_vs_time,
    plot_tle_position_velocity_error,
    plot_tle_rtn_errors,
)


def run_phase_7(show_plots: bool, output_dir: Path, tle_file: Path) -> None:
    cfg = ScenarioConfig()
    epoch_jd_utc = julian_date_from_datetime_utc(parse_utc_datetime(cfg.start_epoch_utc))
    elements = OrbitalElements(
        semi_major_axis_m=R_EARTH_M + cfg.altitude_m,
        eccentricity=cfg.eccentricity,
        inclination_rad=np.deg2rad(cfg.inclination_deg),
        raan_rad=np.deg2rad(cfg.raan_deg),
        arg_perigee_rad=np.deg2rad(cfg.arg_perigee_deg),
        true_anomaly_rad=np.deg2rad(cfg.true_anomaly_deg),
    )
    r0, v0 = keplerian_to_eci(elements)
    period_theoretical_s = orbital_period_s(elements.semi_major_axis_m)
    duration_s = cfg.num_orbits * period_theoretical_s

    result_kepler = propagate_two_body(
        r0_eci_m=r0,
        v0_eci_mps=v0,
        duration_s=duration_s,
        output_step_s=cfg.output_step_s,
        method="DOP853",
    )
    result_j2_drag = _propagate_j2_drag(r0, v0, duration_s, cfg.output_step_s)
    result_phase4 = _propagate_phase4(r0, v0, duration_s, cfg.output_step_s, epoch_jd_utc)
    orbit_metrics = _phase4_metrics(
        elements=elements,
        period_theoretical_s=period_theoretical_s,
        result_kepler=result_kepler,
        result_j2_drag=result_j2_drag,
        result_phase4=result_phase4,
        epoch_jd_utc=epoch_jd_utc,
    )

    attitude_data = _run_attitude_phase6(result_phase4)
    tle_validation = _run_tle_validation_phase7(cfg=cfg, tle_file=tle_file, output_step_s=cfg.output_step_s)
    _print_report(cfg, orbit_metrics, attitude_data, tle_validation)
    _save_plots(
        output_dir=output_dir,
        show_plots=show_plots,
        result_kepler=result_kepler,
        result_j2_drag=result_j2_drag,
        result_phase4=result_phase4,
        orbit_metrics=orbit_metrics,
        attitude_data=attitude_data,
        tle_validation=tle_validation,
    )


def _propagate_j2_drag(r0: np.ndarray, v0: np.ndarray, duration_s: float, output_step_s: float) -> PropagationResult:
    return propagate_orbit(
        r0_eci_m=r0,
        v0_eci_mps=v0,
        duration_s=duration_s,
        output_step_s=output_step_s,
        method="DOP853",
        acceleration_models=[
            lambda _t, r, _v: j2_acceleration_eci(r),
            lambda _t, r, v: drag_acceleration_eci(
                r_eci_m=r,
                v_eci_mps=v,
                area_m2=CUBESAT_3U_REFERENCE_AREA_M2,
                mass_kg=CUBESAT_3U_MASS_KG,
                cd=CUBESAT_3U_CD,
            ),
        ],
    )


def _propagate_phase4(
    r0: np.ndarray,
    v0: np.ndarray,
    duration_s: float,
    output_step_s: float,
    epoch_jd_utc: float,
) -> PropagationResult:
    return propagate_orbit(
        r0_eci_m=r0,
        v0_eci_mps=v0,
        duration_s=duration_s,
        output_step_s=output_step_s,
        method="DOP853",
        acceleration_models=[
            lambda _t, r, _v: j2_acceleration_eci(r),
            lambda _t, r, v: drag_acceleration_eci(
                r_eci_m=r,
                v_eci_mps=v,
                area_m2=CUBESAT_3U_REFERENCE_AREA_M2,
                mass_kg=CUBESAT_3U_MASS_KG,
                cd=CUBESAT_3U_CD,
            ),
            _sun_moon_srp_model(epoch_jd_utc),
        ],
    )


def _sun_moon_srp_model(epoch_jd_utc: float):
    def model(t_s: float, r_eci_m: np.ndarray, _v_eci_mps: np.ndarray) -> np.ndarray:
        jd = epoch_jd_utc + (t_s / 86400.0)
        r_sun = sun_position_eci_m(jd)
        r_moon = moon_position_eci_m(jd)
        a_sun = third_body_acceleration_eci(r_eci_m=r_eci_m, r_body_eci_m=r_sun, mu_body_m3_s2=MU_SUN_M3_S2)
        a_moon = third_body_acceleration_eci(r_eci_m=r_eci_m, r_body_eci_m=r_moon, mu_body_m3_s2=MU_MOON_M3_S2)
        a_srp = srp_acceleration_eci(
            r_eci_m=r_eci_m,
            r_sun_eci_m=r_sun,
            area_m2=CUBESAT_3U_REFERENCE_AREA_M2,
            mass_kg=CUBESAT_3U_MASS_KG,
            cr=CUBESAT_3U_CR,
            include_shadow=True,
        )
        return a_sun + a_moon + a_srp

    return model


def _run_attitude_phase6(result_phase4: PropagationResult) -> dict[str, float | np.ndarray | AttitudePropagationResult]:
    inertia_kg_m2 = cuboid_inertia_tensor_kg_m2(CUBESAT_3U_MASS_KG, CUBESAT_3U_SIZE_M)
    wheel_array = ReactionWheelArray(max_torque_n_m=np.array([1.0e-3, 1.0e-3, 1.0e-3], dtype=float))
    gains = PDGains(kp_vec=np.array([8.0e-4, 8.0e-4, 5.0e-4], dtype=float), kd_vec=np.array([2.0e-3, 2.0e-3, 1.5e-3], dtype=float))

    t_orbit = result_phase4.t_s
    r_orbit = result_phase4.r_eci_m
    v_orbit = result_phase4.v_eci_mps

    def r_interp_eci(t_s: float) -> np.ndarray:
        return np.array([np.interp(t_s, t_orbit, r_orbit[:, i]) for i in range(3)], dtype=float)

    def v_interp_eci(t_s: float) -> np.ndarray:
        return np.array([np.interp(t_s, t_orbit, v_orbit[:, i]) for i in range(3)], dtype=float)

    def desired_attitude_and_rate(t_s: float, q_current_bi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        r = r_interp_eci(t_s)
        v = v_interp_eci(t_s)
        dcm_bi_des = dcm_eci_from_lvlh(r, v)
        q_des = quaternion_from_dcm_body_to_inertial(dcm_bi_des)
        omega_lvlh_eci = np.cross(r, v) / np.dot(r, r)
        omega_des_body = rotate_inertial_to_body(q_current_bi, omega_lvlh_eci)
        return q_des, omega_des_body

    def torque_gg_model(t_s: float, q_bi: np.ndarray, _omega: np.ndarray) -> np.ndarray:
        return gravity_gradient_torque_body_n_m(r_eci_m=r_interp_eci(t_s), q_bi=q_bi, inertia_kg_m2=inertia_kg_m2)

    initial_state = RigidBodyState(
        quaternion_bi=np.array([1.0, 0.0, 0.0, 0.0], dtype=float),
        omega_rad_s=np.deg2rad(np.array([0.20, -0.10, 0.15], dtype=float)),
    )

    free_result = propagate_attitude(
        initial_state=initial_state,
        inertia_kg_m2=inertia_kg_m2,
        duration_s=float(t_orbit[-1]),
        output_step_s=float(t_orbit[1] - t_orbit[0]),
        torque_models=[torque_gg_model],
        method="DOP853",
        rtol=1e-9,
        atol=1e-11,
    )

    def controlled_torque_model(t_s: float, q_bi: np.ndarray, omega_b: np.ndarray) -> np.ndarray:
        q_des, omega_des_body = desired_attitude_and_rate(t_s, q_bi)
        torque_cmd = quaternion_pd_torque(
            q_current_bi=q_bi,
            q_desired_bi=q_des,
            omega_current_body_rad_s=omega_b,
            omega_desired_body_rad_s=omega_des_body,
            gains=gains,
        )
        torque_applied = wheel_array.apply(torque_cmd)
        return torque_gg_model(t_s, q_bi, omega_b) + torque_applied

    controlled_result = propagate_attitude(
        initial_state=initial_state,
        inertia_kg_m2=inertia_kg_m2,
        duration_s=float(t_orbit[-1]),
        output_step_s=float(t_orbit[1] - t_orbit[0]),
        torque_models=[controlled_torque_model],
        method="DOP853",
        rtol=1e-9,
        atol=1e-11,
    )

    cmd_torque_series = []
    applied_torque_series = []
    gg_torque_series = []
    pointing_error_free = []
    pointing_error_controlled = []

    for t_s, q_free, q_ctrl, w_ctrl in zip(
        controlled_result.t_s,
        free_result.quaternion_bi,
        controlled_result.quaternion_bi,
        controlled_result.omega_body_rad_s,
        strict=False,
    ):
        q_des, omega_des = desired_attitude_and_rate(t_s, q_ctrl)
        cmd = quaternion_pd_torque(
            q_current_bi=q_ctrl,
            q_desired_bi=q_des,
            omega_current_body_rad_s=w_ctrl,
            omega_desired_body_rad_s=omega_des,
            gains=gains,
        )
        applied = wheel_array.apply(cmd)
        gg = torque_gg_model(t_s, q_ctrl, w_ctrl)
        cmd_torque_series.append(cmd)
        applied_torque_series.append(applied)
        gg_torque_series.append(gg)

        r = r_interp_eci(t_s)
        nadir = -r / np.linalg.norm(r)
        zb_free = rotate_body_to_inertial(q_free, np.array([0.0, 0.0, 1.0], dtype=float))
        zb_ctrl = rotate_body_to_inertial(q_ctrl, np.array([0.0, 0.0, 1.0], dtype=float))
        err_free = np.arccos(np.clip(np.dot(zb_free, nadir), -1.0, 1.0))
        err_ctrl = np.arccos(np.clip(np.dot(zb_ctrl, nadir), -1.0, 1.0))
        pointing_error_free.append(np.rad2deg(err_free))
        pointing_error_controlled.append(np.rad2deg(err_ctrl))

    cmd_arr = np.array(cmd_torque_series, dtype=float)
    applied_arr = np.array(applied_torque_series, dtype=float)
    gg_arr = np.array(gg_torque_series, dtype=float)
    p_free = np.array(pointing_error_free, dtype=float)
    p_ctrl = np.array(pointing_error_controlled, dtype=float)

    q_norm_ctrl = np.linalg.norm(controlled_result.quaternion_bi, axis=1)
    omega_ctrl_norm_deg_s = np.rad2deg(np.linalg.norm(controlled_result.omega_body_rad_s, axis=1))
    saturation_ratio = np.abs(cmd_arr) / np.maximum(np.abs(wheel_array.max_torque_n_m), 1e-12)
    sat_events = np.any(saturation_ratio > 1.0 + 1e-9, axis=1)

    return {
        "inertia_kg_m2": inertia_kg_m2,
        "gains_kp": gains.kp_vec,
        "gains_kd": gains.kd_vec,
        "wheel_max_torque_n_m": wheel_array.max_torque_n_m,
        "free_result": free_result,
        "controlled_result": controlled_result,
        "cmd_torque_n_m": cmd_arr,
        "applied_torque_n_m": applied_arr,
        "gg_torque_n_m": gg_arr,
        "pointing_error_free_deg": p_free,
        "pointing_error_controlled_deg": p_ctrl,
        "quat_norm_max_error": float(np.max(np.abs(q_norm_ctrl - 1.0))),
        "omega_initial_deg_s": float(omega_ctrl_norm_deg_s[0]),
        "omega_final_deg_s": float(omega_ctrl_norm_deg_s[-1]),
        "omega_max_deg_s": float(np.max(omega_ctrl_norm_deg_s)),
        "nadir_err_free_mean_deg": float(np.mean(p_free)),
        "nadir_err_free_max_deg": float(np.max(p_free)),
        "nadir_err_ctrl_mean_deg": float(np.mean(p_ctrl)),
        "nadir_err_ctrl_max_deg": float(np.max(p_ctrl)),
        "nadir_err_ctrl_final_deg": float(p_ctrl[-1]),
        "nadir_err_reduction_mean_deg": float(np.mean(p_free) - np.mean(p_ctrl)),
        "torque_cmd_mean_mnm": float(np.mean(np.linalg.norm(cmd_arr, axis=1)) * 1e3),
        "torque_applied_mean_mnm": float(np.mean(np.linalg.norm(applied_arr, axis=1)) * 1e3),
        "torque_applied_max_mnm": float(np.max(np.linalg.norm(applied_arr, axis=1)) * 1e3),
        "torque_gg_mean_nnm": float(np.mean(np.linalg.norm(gg_arr, axis=1)) * 1e9),
        "torque_gg_max_nnm": float(np.max(np.linalg.norm(gg_arr, axis=1)) * 1e9),
        "saturation_event_pct": float(np.mean(sat_events.astype(float)) * 100.0),
        "saturation_ratio_max": float(np.max(saturation_ratio)),
    }


def _phase4_metrics(
    elements: OrbitalElements,
    period_theoretical_s: float,
    result_kepler: PropagationResult,
    result_j2_drag: PropagationResult,
    result_phase4: PropagationResult,
    epoch_jd_utc: float,
) -> dict[str, float | np.ndarray]:
    period_estimated_s = _estimate_period_from_state(result_kepler.t_s, result_kepler.r_eci_m, result_kepler.v_eci_mps)
    energy_rel_ppm = (
        (result_kepler.specific_energy_j_kg.max() - result_kepler.specific_energy_j_kg.min())
        / abs(result_kepler.specific_energy_j_kg.mean())
        * 1e6
    )
    h_rel_ppm = (result_kepler.h_norm_m2_s.max() - result_kepler.h_norm_m2_s.min()) / result_kepler.h_norm_m2_s.mean() * 1e6

    raan_j2_drag_deg = raan_series_deg(result_j2_drag.states_eci, unwrap=True)
    raan_phase4_deg = raan_series_deg(result_phase4.states_eci, unwrap=True)
    raan_drift_j2_drag_deg = float(raan_j2_drag_deg[-1] - raan_j2_drag_deg[0])
    raan_drift_phase4_deg = float(raan_phase4_deg[-1] - raan_phase4_deg[0])
    elapsed_days = result_phase4.t_s[-1] / 86400.0
    raan_rate_j2_drag_deg_day_sim = raan_drift_j2_drag_deg / elapsed_days
    raan_rate_phase4_deg_day_sim = raan_drift_phase4_deg / elapsed_days
    raan_rate_deg_day_theory = _j2_raan_rate_deg_day(elements)

    alt_j2_drag_m = np.linalg.norm(result_j2_drag.r_eci_m, axis=1) - R_EARTH_M
    alt_phase4_m = np.linalg.norm(result_phase4.r_eci_m, axis=1) - R_EARTH_M
    alt_decay_j2_drag_m = _orbit_mean_decay(result_j2_drag.t_s, alt_j2_drag_m, period_theoretical_s)
    alt_decay_phase4_m = _orbit_mean_decay(result_phase4.t_s, alt_phase4_m, period_theoretical_s)
    additional_decay_phase4_m = alt_decay_phase4_m - alt_decay_j2_drag_m

    a_j2_drag_m = _semi_major_axis_from_state(result_j2_drag.states_eci)
    a_phase4_m = _semi_major_axis_from_state(result_phase4.states_eci)
    sma_decay_j2_drag_m = _orbit_mean_decay(result_j2_drag.t_s, a_j2_drag_m, period_theoretical_s)
    sma_decay_phase4_m = _orbit_mean_decay(result_phase4.t_s, a_phase4_m, period_theoretical_s)

    position_delta_norm_m = np.linalg.norm(result_phase4.r_eci_m - result_j2_drag.r_eci_m, axis=1)
    perturbation_stats = _phase4_perturbation_stats(result_phase4, epoch_jd_utc)

    return {
        "period_theoretical_s": period_theoretical_s,
        "period_estimated_s": period_estimated_s,
        "period_error_s": period_estimated_s - period_theoretical_s,
        "energy_drift_ppm": energy_rel_ppm,
        "h_drift_ppm": h_rel_ppm,
        "raan_j2_drag_deg_series": raan_j2_drag_deg,
        "raan_phase4_deg_series": raan_phase4_deg,
        "raan_drift_j2_drag_deg": raan_drift_j2_drag_deg,
        "raan_drift_phase4_deg": raan_drift_phase4_deg,
        "raan_rate_j2_drag_deg_day_sim": float(raan_rate_j2_drag_deg_day_sim),
        "raan_rate_phase4_deg_day_sim": float(raan_rate_phase4_deg_day_sim),
        "raan_rate_deg_day_theory": float(raan_rate_deg_day_theory),
        "alt_decay_j2_drag_m": alt_decay_j2_drag_m,
        "alt_decay_phase4_m": alt_decay_phase4_m,
        "additional_decay_phase4_m": additional_decay_phase4_m,
        "sma_decay_j2_drag_m": sma_decay_j2_drag_m,
        "sma_decay_phase4_m": sma_decay_phase4_m,
        "max_position_delta_m": float(position_delta_norm_m.max()),
        "final_position_delta_m": float(position_delta_norm_m[-1]),
        **perturbation_stats,
    }


def _phase4_perturbation_stats(result_phase4: PropagationResult, epoch_jd_utc: float) -> dict[str, float | np.ndarray]:
    sun_norm = []
    moon_norm = []
    srp_norm = []
    eclipsed = 0
    for t_s, state in zip(result_phase4.t_s, result_phase4.states_eci, strict=False):
        jd = epoch_jd_utc + (t_s / 86400.0)
        r = state[:3]
        r_sun = sun_position_eci_m(jd)
        r_moon = moon_position_eci_m(jd)
        a_sun = third_body_acceleration_eci(r_eci_m=r, r_body_eci_m=r_sun, mu_body_m3_s2=MU_SUN_M3_S2)
        a_moon = third_body_acceleration_eci(r_eci_m=r, r_body_eci_m=r_moon, mu_body_m3_s2=MU_MOON_M3_S2)
        a_srp = srp_acceleration_eci(
            r_eci_m=r,
            r_sun_eci_m=r_sun,
            area_m2=CUBESAT_3U_REFERENCE_AREA_M2,
            mass_kg=CUBESAT_3U_MASS_KG,
            cr=CUBESAT_3U_CR,
            include_shadow=True,
        )
        sun_norm.append(np.linalg.norm(a_sun))
        moon_norm.append(np.linalg.norm(a_moon))
        srp_norm.append(np.linalg.norm(a_srp))
        if in_earth_shadow_cylindrical(r_eci_m=r, r_sun_eci_m=r_sun):
            eclipsed += 1

    sun_arr = np.array(sun_norm, dtype=float)
    moon_arr = np.array(moon_norm, dtype=float)
    srp_arr = np.array(srp_norm, dtype=float)
    eclipse_fraction = eclipsed / len(result_phase4.t_s)

    return {
        "mean_sun_accel_um_s2": float(np.mean(sun_arr) * 1e6),
        "mean_moon_accel_um_s2": float(np.mean(moon_arr) * 1e6),
        "mean_srp_accel_um_s2": float(np.mean(srp_arr) * 1e6),
        "max_sun_accel_um_s2": float(np.max(sun_arr) * 1e6),
        "max_moon_accel_um_s2": float(np.max(moon_arr) * 1e6),
        "max_srp_accel_um_s2": float(np.max(srp_arr) * 1e6),
        "eclipse_fraction_pct": float(eclipse_fraction * 100.0),
        "a_sun_norm_mps2_series": sun_arr,
        "a_moon_norm_mps2_series": moon_arr,
        "a_srp_norm_mps2_series": srp_arr,
    }


def _run_tle_validation_phase7(
    cfg: ScenarioConfig,
    tle_file: Path,
    output_step_s: float,
) -> dict[str, object] | None:
    if not sgp4_available():
        print("\n[Phase 7] `sgp4` is not available. Install the dependency to run TLE validation.")
        return None
    if not tle_file.exists():
        print(f"\n[Phase 7] TLE file not found: {tle_file}")
        return None
    try:
        tle_records = load_tle_file(tle_file)
        tle = tle_records[0]
        mean_motion_rev_day = _tle_mean_motion_rev_day(tle.line2)
        period_s = 86400.0 / mean_motion_rev_day
        duration_s = cfg.num_orbits * period_s
        t_eval = _build_time_grid(duration_s, output_step_s)
        sgp4_ref = propagate_tle_with_sgp4(tle, t_eval)
        model_result = _propagate_phase4(
            r0=sgp4_ref.r_eci_m[0],
            v0=sgp4_ref.v_eci_mps[0],
            duration_s=duration_s,
            output_step_s=output_step_s,
            epoch_jd_utc=sgp4_ref.epoch_jd_utc,
        )
        r_model_interp = _interp_vector_series(model_result.t_s, model_result.r_eci_m, sgp4_ref.t_s)
        v_model_interp = _interp_vector_series(model_result.t_s, model_result.v_eci_mps, sgp4_ref.t_s)
        metrics = validate_against_tle(
            r_model_eci_m=r_model_interp,
            v_model_eci_mps=v_model_interp,
            r_ref_eci_m=sgp4_ref.r_eci_m,
            v_ref_eci_mps=sgp4_ref.v_eci_mps,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"\n[Phase 7] TLE validation could not be completed: {exc}")
        return None

    return {
        "tle_name": tle.name,
        "tle_line1": tle.line1,
        "tle_line2": tle.line2,
        "period_s": period_s,
        "duration_s": duration_s,
        "sgp4_ref": sgp4_ref,
        "model_result": model_result,
        "metrics": metrics,
    }


def _build_time_grid(duration_s: float, output_step_s: float) -> np.ndarray:
    t = np.arange(0.0, duration_s, output_step_s, dtype=float)
    if t.size == 0 or not np.isclose(t[-1], duration_s):
        t = np.append(t, duration_s)
    return t


def _interp_vector_series(t_src: np.ndarray, vec_src: np.ndarray, t_dst: np.ndarray) -> np.ndarray:
    return np.column_stack([np.interp(t_dst, t_src, vec_src[:, i]) for i in range(3)])


def _tle_mean_motion_rev_day(line2: str) -> float:
    mm_str = line2[52:63].strip()
    return float(mm_str)


def _save_plots(
    output_dir: Path,
    show_plots: bool,
    result_kepler: PropagationResult,
    result_j2_drag: PropagationResult,
    result_phase4: PropagationResult,
    orbit_metrics: dict[str, float | np.ndarray],
    attitude_data: dict[str, float | np.ndarray | AttitudePropagationResult],
    tle_validation: dict[str, object] | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_orbit_3d_compare(
        result_j2_drag.r_eci_m,
        result_phase4.r_eci_m,
        output_path=output_dir / "orbit_3d_j2_drag_vs_phase4.png",
        show=show_plots,
        label_reference="Kepler + J2 + Drag",
        label_comparison="Phase 4",
    )
    plot_altitude_comparison(
        result_phase4.t_s,
        result_j2_drag.r_eci_m,
        result_phase4.r_eci_m,
        output_path=output_dir / "altitude_j2_drag_vs_phase4.png",
        show=show_plots,
        label_reference="Kepler + J2 + Drag",
        label_comparison="Phase 4",
    )
    plot_raan_vs_time(
        result_phase4.t_s,
        orbit_metrics["raan_j2_drag_deg_series"],
        orbit_metrics["raan_phase4_deg_series"],
        output_path=output_dir / "raan_j2_drag_vs_phase4.png",
        show=show_plots,
        label_reference="Kepler + J2 + Drag",
        label_comparison="Phase 4",
    )
    plot_perturbation_magnitudes(
        result_phase4.t_s,
        orbit_metrics["a_sun_norm_mps2_series"],
        orbit_metrics["a_moon_norm_mps2_series"],
        orbit_metrics["a_srp_norm_mps2_series"],
        output_path=output_dir / "perturbations_phase4.png",
        show=show_plots,
    )
    free_result = attitude_data["free_result"]
    controlled_result = attitude_data["controlled_result"]
    plot_quaternion_components(
        controlled_result.t_s,
        controlled_result.quaternion_bi,
        output_path=output_dir / "attitude_quaternion_components_controlled.png",
        show=show_plots,
    )
    plot_body_rates(
        controlled_result.t_s,
        controlled_result.omega_body_rad_s,
        output_path=output_dir / "attitude_body_rates_controlled.png",
        show=show_plots,
    )
    plot_attitude_torques(
        controlled_result.t_s,
        attitude_data["gg_torque_n_m"],
        output_path=output_dir / "attitude_gravity_gradient_torque.png",
        show=show_plots,
    )
    plot_pointing_error_comparison(
        controlled_result.t_s,
        attitude_data["pointing_error_free_deg"],
        attitude_data["pointing_error_controlled_deg"],
        output_path=output_dir / "attitude_pointing_error_comparison.png",
        show=show_plots,
    )
    plot_control_torque_comparison(
        controlled_result.t_s,
        attitude_data["cmd_torque_n_m"],
        attitude_data["applied_torque_n_m"],
        output_path=output_dir / "attitude_control_torque_comparison.png",
        show=show_plots,
    )
    plot_conservation(
        result_kepler.t_s,
        result_kepler.specific_energy_j_kg,
        result_kepler.h_norm_m2_s,
        output_path=output_dir / "invariants_kepler.png",
        show=show_plots,
    )
    if tle_validation is not None:
        sgp4_ref = tle_validation["sgp4_ref"]
        tle_metrics = tle_validation["metrics"]
        plot_tle_position_velocity_error(
            sgp4_ref.t_s,
            tle_metrics.position_error_norm_m,
            tle_metrics.velocity_error_norm_mps,
            output_path=output_dir / "tle_position_velocity_error.png",
            show=show_plots,
        )
        plot_tle_rtn_errors(
            sgp4_ref.t_s,
            tle_metrics.radial_error_m,
            tle_metrics.along_track_error_m,
            tle_metrics.cross_track_error_m,
            output_path=output_dir / "tle_rtn_errors.png",
            show=show_plots,
        )
    print(f"\nFigures saved to: {output_dir.resolve()}")


def _semi_major_axis_from_state(states_eci: np.ndarray) -> np.ndarray:
    r = states_eci[:, :3]
    v = states_eci[:, 3:]
    r_norm = np.linalg.norm(r, axis=1)
    v_norm = np.linalg.norm(v, axis=1)
    energy = 0.5 * v_norm**2 - (MU_EARTH_M3_S2 / r_norm)
    return -MU_EARTH_M3_S2 / (2.0 * energy)


def _orbit_mean_decay(t_s: np.ndarray, series: np.ndarray, period_s: float) -> float:
    first_mask = t_s <= period_s
    last_mask = t_s >= (t_s[-1] - period_s)
    if not np.any(first_mask) or not np.any(last_mask):
        return float(series[0] - series[-1])
    first_mean = float(np.mean(series[first_mask]))
    last_mean = float(np.mean(series[last_mask]))
    return first_mean - last_mean


def _j2_raan_rate_deg_day(elements: OrbitalElements) -> float:
    a = elements.semi_major_axis_m
    e = elements.eccentricity
    i = elements.inclination_rad
    p = a * (1.0 - e**2)
    n = np.sqrt(MU_EARTH_M3_S2 / (a**3))
    rate_rad_s = -1.5 * n * J2_EARTH * (R_EARTH_M / p) ** 2 * np.cos(i)
    return float(np.rad2deg(rate_rad_s) * 86400.0)


def _estimate_period_from_state(t_s: np.ndarray, r_eci_m: np.ndarray, v_eci_mps: np.ndarray) -> float:
    r0 = r_eci_m[0]
    h0_hat = np.cross(r_eci_m[0], v_eci_mps[0])
    h0_hat = h0_hat / np.linalg.norm(h0_hat)
    r0_norm = np.linalg.norm(r0)
    theta = np.empty_like(t_s)
    for i, ri in enumerate(r_eci_m):
        cross_term = np.cross(r0, ri)
        sin_term = np.dot(cross_term, h0_hat)
        cos_term = np.dot(r0, ri) / (r0_norm * np.linalg.norm(ri))
        theta[i] = np.arctan2(sin_term, cos_term)
    theta = np.unwrap(theta)
    rev = theta / (2.0 * np.pi)
    n_full_revs = int(np.floor(rev[-1]))
    if n_full_revs < 1:
        return float("nan")
    crossing_times = []
    for k in range(1, n_full_revs + 1):
        idx = np.searchsorted(rev, float(k))
        if idx == 0 or idx >= len(rev):
            continue
        t0, t1 = t_s[idx - 1], t_s[idx]
        r0k, r1k = rev[idx - 1], rev[idx]
        frac = (k - r0k) / (r1k - r0k)
        crossing_times.append(t0 + frac * (t1 - t0))
    if not crossing_times:
        return float("nan")
    periods = np.diff(np.array([0.0, *crossing_times], dtype=float))
    return float(periods.mean())


def _print_report(
    cfg: ScenarioConfig,
    orbit_metrics: dict[str, float | np.ndarray],
    attitude_data: dict[str, float | np.ndarray | AttitudePropagationResult],
    tle_validation: dict[str, object] | None,
) -> None:
    inertia = attitude_data["inertia_kg_m2"]
    kp = attitude_data["gains_kp"]
    kd = attitude_data["gains_kd"]
    wheel_lim = attitude_data["wheel_max_torque_n_m"]
    print("=== Satellite Simulator | Phase 7 (PD Control + TLE Validation) ===")
    print(f"Epoch UTC: {cfg.start_epoch_utc}")
    print(f"Altitude: {cfg.altitude_m / 1_000.0:.1f} km")
    print(f"Inclination: {cfg.inclination_deg:.2f} deg")
    print(f"Simulated orbits: {cfg.num_orbits}")
    print("\nTranslational baseline:")
    print(f"- Theoretical period:      {float(orbit_metrics['period_theoretical_s']):.3f} s")
    print(f"- Estimated period:        {float(orbit_metrics['period_estimated_s']):.3f} s")
    print(f"- Period error:            {float(orbit_metrics['period_error_s']):.6f} s")
    print(f"- RAAN rate (Phase 4):     {float(orbit_metrics['raan_rate_phase4_deg_day_sim']):.6f} deg/day")
    print(f"- RAAN rate theory (J2):   {float(orbit_metrics['raan_rate_deg_day_theory']):.6f} deg/day")
    print("\nAttitude control summary:")
    print(f"- Inertia diag [kg m^2]:   [{inertia[0,0]:.6f}, {inertia[1,1]:.6f}, {inertia[2,2]:.6f}]")
    print(f"- PD gains Kp [N m]:       [{kp[0]:.2e}, {kp[1]:.2e}, {kp[2]:.2e}]")
    print(f"- PD gains Kd [N m s]:     [{kd[0]:.2e}, {kd[1]:.2e}, {kd[2]:.2e}]")
    print(f"- RW limits [mN m]:        [{wheel_lim[0]*1e3:.3f}, {wheel_lim[1]*1e3:.3f}, {wheel_lim[2]*1e3:.3f}]")
    print(f"- Max |q|-1 error:         {float(attitude_data['quat_norm_max_error']):.3e}")
    print(f"- Omega initial:           {float(attitude_data['omega_initial_deg_s']):.6f} deg/s")
    print(f"- Omega final:             {float(attitude_data['omega_final_deg_s']):.6f} deg/s")
    print(f"- Omega max:               {float(attitude_data['omega_max_deg_s']):.6f} deg/s")
    print(f"- Nadir error free mean:   {float(attitude_data['nadir_err_free_mean_deg']):.6f} deg")
    print(f"- Nadir error ctrl mean:   {float(attitude_data['nadir_err_ctrl_mean_deg']):.6f} deg")
    print(f"- Nadir error ctrl final:  {float(attitude_data['nadir_err_ctrl_final_deg']):.6f} deg")
    print(f"- Mean error reduction:    {float(attitude_data['nadir_err_reduction_mean_deg']):.6f} deg")
    print(f"- GG torque mean:          {float(attitude_data['torque_gg_mean_nnm']):.6f} nN m")
    print(f"- RW torque applied mean:  {float(attitude_data['torque_applied_mean_mnm']):.6f} mN m")
    print(f"- RW torque applied max:   {float(attitude_data['torque_applied_max_mnm']):.6f} mN m")
    print(f"- RW saturation events:    {float(attitude_data['saturation_event_pct']):.3f} %")
    print(f"- RW saturation ratio max: {float(attitude_data['saturation_ratio_max']):.6f}")
    if tle_validation is None:
        print("\nPhase 7 TLE validation:")
        print("- Not executed (missing sgp4, missing TLE, or validation error).")
    else:
        tle_metrics: TLEValidationMetrics = tle_validation["metrics"]  # type: ignore[assignment]
        tle_name = str(tle_validation["tle_name"])
        duration_h = float(tle_validation["duration_s"]) / 3600.0
        print("\nPhase 7 TLE validation (Model vs SGP4):")
        print(f"- TLE target:              {tle_name}")
        print(f"- Validation duration:     {duration_h:.3f} h")
        print(f"- RMS position error:      {tle_metrics.rms_position_error_m/1_000.0:.6f} km")
        print(f"- Mean position error:     {tle_metrics.mean_position_error_m/1_000.0:.6f} km")
        print(f"- Max position error:      {tle_metrics.max_position_error_m/1_000.0:.6f} km")
        print(f"- Final position error:    {tle_metrics.final_position_error_m/1_000.0:.6f} km")
        print(f"- RMS velocity error:      {tle_metrics.rms_velocity_error_mps:.6f} m/s")
        print(f"- Max radial error:        {tle_metrics.max_radial_error_m/1_000.0:.6f} km")
        print(f"- Max along-track error:   {tle_metrics.max_along_track_error_m/1_000.0:.6f} km")
        print(f"- Max cross-track error:   {tle_metrics.max_cross_track_error_m/1_000.0:.6f} km")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 7: TLE/SGP4 validation on top of controlled dynamics.")
    parser.add_argument("--show", action="store_true", help="Display plots in interactive windows (in addition to saving files).")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Directory used to store generated plots.")
    parser.add_argument(
        "--tle-file",
        type=Path,
        default=Path("satellite_simulator/data/tle/iss_sample.tle"),
        help="Path to TLE file used for Phase 7 validation.",
    )
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()
    run_phase_7(show_plots=args.show, output_dir=args.output_dir, tle_file=args.tle_file)


if __name__ == "__main__":
    main()

