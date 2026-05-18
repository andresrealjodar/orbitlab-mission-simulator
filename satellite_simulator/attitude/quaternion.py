"""Quaternion math utilities."""

import numpy as np


def normalize(q: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(q)
    if n == 0.0:
        raise ValueError("Cannot normalize zero quaternion.")
    return q / n


def conjugate(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


def multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array(
        [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ],
        dtype=float,
    )


def derivative_body_rates(q_bi: np.ndarray, omega_body_rad_s: np.ndarray) -> np.ndarray:
    """Quaternion derivative for body->inertial quaternion and body rates."""
    omega_quat = np.array([0.0, omega_body_rad_s[0], omega_body_rad_s[1], omega_body_rad_s[2]], dtype=float)
    return 0.5 * multiply(q_bi, omega_quat)


def dcm_body_to_inertial(q_bi: np.ndarray) -> np.ndarray:
    """Direction cosine matrix mapping body-frame vectors to inertial frame."""
    q = normalize(q_bi)
    q0, q1, q2, q3 = q
    return np.array(
        [
            [1.0 - 2.0 * (q2 * q2 + q3 * q3), 2.0 * (q1 * q2 - q0 * q3), 2.0 * (q1 * q3 + q0 * q2)],
            [2.0 * (q1 * q2 + q0 * q3), 1.0 - 2.0 * (q1 * q1 + q3 * q3), 2.0 * (q2 * q3 - q0 * q1)],
            [2.0 * (q1 * q3 - q0 * q2), 2.0 * (q2 * q3 + q0 * q1), 1.0 - 2.0 * (q1 * q1 + q2 * q2)],
        ],
        dtype=float,
    )


def dcm_inertial_to_body(q_bi: np.ndarray) -> np.ndarray:
    """Direction cosine matrix mapping inertial vectors to body frame."""
    return dcm_body_to_inertial(q_bi).T


def rotate_inertial_to_body(q_bi: np.ndarray, vec_inertial: np.ndarray) -> np.ndarray:
    """Rotate inertial vector into body coordinates."""
    return dcm_inertial_to_body(q_bi) @ vec_inertial


def rotate_body_to_inertial(q_bi: np.ndarray, vec_body: np.ndarray) -> np.ndarray:
    """Rotate body vector into inertial coordinates."""
    return dcm_body_to_inertial(q_bi) @ vec_body


def quaternion_from_dcm_body_to_inertial(dcm_bi: np.ndarray) -> np.ndarray:
    """Convert body->inertial DCM to unit quaternion [q0, q1, q2, q3]."""
    m = dcm_bi
    trace = float(np.trace(m))
    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        q0 = 0.25 * s
        q1 = (m[2, 1] - m[1, 2]) / s
        q2 = (m[0, 2] - m[2, 0]) / s
        q3 = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        q0 = (m[2, 1] - m[1, 2]) / s
        q1 = 0.25 * s
        q2 = (m[0, 1] + m[1, 0]) / s
        q3 = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        q0 = (m[0, 2] - m[2, 0]) / s
        q1 = (m[0, 1] + m[1, 0]) / s
        q2 = 0.25 * s
        q3 = (m[1, 2] + m[2, 1]) / s
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        q0 = (m[1, 0] - m[0, 1]) / s
        q1 = (m[0, 2] + m[2, 0]) / s
        q2 = (m[1, 2] + m[2, 1]) / s
        q3 = 0.25 * s
    return normalize(np.array([q0, q1, q2, q3], dtype=float))


def quaternion_error_shortest_path(q_current_bi: np.ndarray, q_desired_bi: np.ndarray) -> np.ndarray:
    """Quaternion error q_e = q_d^{-1} ⊗ q, forced to shortest-path hemisphere."""
    q_err = multiply(conjugate(normalize(q_desired_bi)), normalize(q_current_bi))
    if q_err[0] < 0.0:
        q_err = -q_err
    return normalize(q_err)
