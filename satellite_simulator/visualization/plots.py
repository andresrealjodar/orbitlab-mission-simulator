"""Plotting helpers for Phase 1 orbital analysis."""

from pathlib import Path

import matplotlib
import numpy as np

from satellite_simulator.constants import R_EARTH_M

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_orbit_3d(r_eci_m: np.ndarray, output_path: Path | None = None, show: bool = False) -> None:
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    r_km = r_eci_m / 1_000.0
    ax.plot(r_km[:, 0], r_km[:, 1], r_km[:, 2], linewidth=1.4, label="Orbit")

    earth_r_km = R_EARTH_M / 1_000.0
    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)
    x = earth_r_km * np.outer(np.cos(u), np.sin(v))
    y = earth_r_km * np.outer(np.sin(u), np.sin(v))
    z = earth_r_km * np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(x, y, z, color="#7aa6d8", alpha=0.55, linewidth=0)

    ax.set_title("Phase 1: Keplerian Orbit (ECI)")
    ax.set_xlabel("X [km]")
    ax.set_ylabel("Y [km]")
    ax.set_zlabel("Z [km]")
    _set_equal_3d_axes(ax, r_km)
    ax.legend(loc="upper right")
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_orbit_3d_compare(
    r_reference_eci_m: np.ndarray,
    r_j2_eci_m: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
    label_reference: str = "Kepler (2-body)",
    label_comparison: str = "Kepler + J2",
) -> None:
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    r_ref_km = r_reference_eci_m / 1_000.0
    r_j2_km = r_j2_eci_m / 1_000.0
    ax.plot(r_ref_km[:, 0], r_ref_km[:, 1], r_ref_km[:, 2], linewidth=1.2, label=label_reference)
    ax.plot(r_j2_km[:, 0], r_j2_km[:, 1], r_j2_km[:, 2], linewidth=1.2, label=label_comparison)

    earth_r_km = R_EARTH_M / 1_000.0
    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)
    x = earth_r_km * np.outer(np.cos(u), np.sin(v))
    y = earth_r_km * np.outer(np.sin(u), np.sin(v))
    z = earth_r_km * np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(x, y, z, color="#7aa6d8", alpha=0.45, linewidth=0)

    ax.set_title("Orbit Comparison in ECI")
    ax.set_xlabel("X [km]")
    ax.set_ylabel("Y [km]")
    ax.set_zlabel("Z [km]")
    points_for_scale = np.vstack((r_ref_km, r_j2_km))
    _set_equal_3d_axes(ax, points_for_scale)
    ax.legend(loc="upper right")
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_altitude_vs_time(t_s: np.ndarray, r_eci_m: np.ndarray, output_path: Path | None = None, show: bool = False) -> None:
    altitude_km = np.linalg.norm(r_eci_m, axis=1) / 1_000.0 - (R_EARTH_M / 1_000.0)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(t_s / 60.0, altitude_km, linewidth=1.4)
    ax.set_title("Altitude vs Time")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Altitude [km]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_altitude_comparison(
    t_s: np.ndarray,
    r_reference_eci_m: np.ndarray,
    r_j2_eci_m: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
    label_reference: str = "Kepler (2-body)",
    label_comparison: str = "Kepler + J2",
) -> None:
    altitude_ref_km = np.linalg.norm(r_reference_eci_m, axis=1) / 1_000.0 - (R_EARTH_M / 1_000.0)
    altitude_j2_km = np.linalg.norm(r_j2_eci_m, axis=1) / 1_000.0 - (R_EARTH_M / 1_000.0)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(t_s / 60.0, altitude_ref_km, linewidth=1.2, label=label_reference)
    ax.plot(t_s / 60.0, altitude_j2_km, linewidth=1.2, label=label_comparison)
    ax.set_title("Altitude vs Time (Comparison)")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Altitude [km]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_raan_vs_time(
    t_s: np.ndarray,
    raan_reference_deg: np.ndarray,
    raan_j2_deg: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
    label_reference: str = "Kepler (2-body)",
    label_comparison: str = "Kepler + J2",
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    time_hours = t_s / 3600.0
    ax.plot(time_hours, raan_reference_deg, linewidth=1.2, label=label_reference)
    ax.plot(time_hours, raan_j2_deg, linewidth=1.2, label=label_comparison)
    ax.set_title("RAAN vs Time")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("RAAN [deg]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_perturbation_magnitudes(
    t_s: np.ndarray,
    a_sun_mps2: np.ndarray,
    a_moon_mps2: np.ndarray,
    a_srp_mps2: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    time_hours = t_s / 3600.0
    ax.plot(time_hours, a_sun_mps2 * 1e6, linewidth=1.2, label="Sun 3-body")
    ax.plot(time_hours, a_moon_mps2 * 1e6, linewidth=1.2, label="Moon 3-body")
    ax.plot(time_hours, a_srp_mps2 * 1e6, linewidth=1.2, label="SRP")
    ax.set_title("Perturbation Accelerations")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Acceleration [um/s^2]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_quaternion_components(
    t_s: np.ndarray,
    quaternion_bi: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    time_min = t_s / 60.0
    labels = ["q0", "q1", "q2", "q3"]
    for idx, lbl in enumerate(labels):
        ax.plot(time_min, quaternion_bi[:, idx], linewidth=1.1, label=lbl)
    ax.set_title("Quaternion Components (Body -> Inertial)")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Quaternion value [-]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_body_rates(
    t_s: np.ndarray,
    omega_body_rad_s: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    time_min = t_s / 60.0
    omega_deg_s = np.rad2deg(omega_body_rad_s)
    labels = [r"$\omega_x$", r"$\omega_y$", r"$\omega_z$"]
    for idx, lbl in enumerate(labels):
        ax.plot(time_min, omega_deg_s[:, idx], linewidth=1.1, label=lbl)
    ax.set_title("Body Angular Rates")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Angular rate [deg/s]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_attitude_torques(
    t_s: np.ndarray,
    torque_gg_n_m: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    time_min = t_s / 60.0
    torque_nnm = torque_gg_n_m * 1e9
    labels = [r"$\tau_x$", r"$\tau_y$", r"$\tau_z$"]
    for idx, lbl in enumerate(labels):
        ax.plot(time_min, torque_nnm[:, idx], linewidth=1.1, label=lbl)
    ax.set_title("Gravity-Gradient Torque (Body)")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Torque [nN m]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_pointing_error_comparison(
    t_s: np.ndarray,
    error_free_deg: np.ndarray,
    error_controlled_deg: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    time_min = t_s / 60.0
    ax.plot(time_min, error_free_deg, linewidth=1.1, label="Free attitude")
    ax.plot(time_min, error_controlled_deg, linewidth=1.1, label="Controlled attitude")
    ax.set_title("Nadir Pointing Error (Body Z Axis)")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Pointing error [deg]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_control_torque_comparison(
    t_s: np.ndarray,
    commanded_torque_n_m: np.ndarray,
    applied_torque_n_m: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, axs = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
    time_min = t_s / 60.0
    labels = ["x", "y", "z"]
    for i, lbl in enumerate(labels):
        axs[i].plot(time_min, commanded_torque_n_m[:, i] * 1e3, linewidth=1.0, label=f"cmd {lbl}")
        axs[i].plot(time_min, applied_torque_n_m[:, i] * 1e3, linewidth=1.0, linestyle="--", label=f"applied {lbl}")
        axs[i].set_ylabel("mN m")
        axs[i].grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
        axs[i].legend(loc="upper right", fontsize=8)
    axs[-1].set_xlabel("Time [min]")
    fig.suptitle("Reaction Wheel Torques")
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_tle_position_velocity_error(
    t_s: np.ndarray,
    position_error_norm_m: np.ndarray,
    velocity_error_norm_mps: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, axs = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    time_hours = t_s / 3600.0
    axs[0].plot(time_hours, position_error_norm_m / 1_000.0, linewidth=1.2)
    axs[0].set_ylabel("Position error [km]")
    axs[0].grid(True, linestyle="--", linewidth=0.6, alpha=0.6)

    axs[1].plot(time_hours, velocity_error_norm_mps, linewidth=1.2)
    axs[1].set_xlabel("Time [h]")
    axs[1].set_ylabel("Velocity error [m/s]")
    axs[1].grid(True, linestyle="--", linewidth=0.6, alpha=0.6)

    fig.suptitle("Model vs SGP4 Errors")
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_tle_rtn_errors(
    t_s: np.ndarray,
    radial_error_m: np.ndarray,
    along_track_error_m: np.ndarray,
    cross_track_error_m: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    time_hours = t_s / 3600.0
    ax.plot(time_hours, radial_error_m / 1_000.0, linewidth=1.0, label="Radial")
    ax.plot(time_hours, along_track_error_m / 1_000.0, linewidth=1.0, label="Along-track")
    ax.plot(time_hours, cross_track_error_m / 1_000.0, linewidth=1.0, label="Cross-track")
    ax.set_title("RTN Position Errors vs SGP4")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Error [km]")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_conservation(
    t_s: np.ndarray,
    specific_energy_j_kg: np.ndarray,
    h_norm_m2_s: np.ndarray,
    output_path: Path | None = None,
    show: bool = False,
) -> None:
    fig, axs = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    time_min = t_s / 60.0

    axs[0].plot(time_min, specific_energy_j_kg, linewidth=1.2)
    axs[0].set_ylabel("Specific Energy [J/kg]")
    axs[0].grid(True, linestyle="--", linewidth=0.6, alpha=0.6)

    axs[1].plot(time_min, h_norm_m2_s, linewidth=1.2)
    axs[1].set_xlabel("Time [min]")
    axs[1].set_ylabel("|h| [m^2/s]")
    axs[1].grid(True, linestyle="--", linewidth=0.6, alpha=0.6)

    fig.suptitle("Two-body Invariants")
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def _set_equal_3d_axes(ax: plt.Axes, points_xyz: np.ndarray) -> None:
    x_vals = points_xyz[:, 0]
    y_vals = points_xyz[:, 1]
    z_vals = points_xyz[:, 2]
    max_range = max(
        x_vals.max() - x_vals.min(),
        y_vals.max() - y_vals.min(),
        z_vals.max() - z_vals.min(),
    ) / 2.0
    x_mid = (x_vals.max() + x_vals.min()) / 2.0
    y_mid = (y_vals.max() + y_vals.min()) / 2.0
    z_mid = (z_vals.max() + z_vals.min()) / 2.0

    ax.set_xlim(x_mid - max_range, x_mid + max_range)
    ax.set_ylim(y_mid - max_range, y_mid + max_range)
    ax.set_zlim(z_mid - max_range, z_mid + max_range)
