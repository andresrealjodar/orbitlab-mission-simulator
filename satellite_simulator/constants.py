"""Physical constants and baseline scenario parameters."""

from dataclasses import dataclass

# Earth constants (SI units)
MU_EARTH_M3_S2 = 3.986004418e14
R_EARTH_M = 6_378_136.3
J2_EARTH = 1.08262668e-3
OMEGA_EARTH_RAD_S = 7.2921150e-5

# Other celestial constants (SI units)
MU_SUN_M3_S2 = 1.32712440018e20
MU_MOON_M3_S2 = 4.9048695e12
AU_M = 149_597_870_700.0
SOLAR_PRESSURE_N_M2 = 4.56e-6

# CubeSat 3U baseline
CUBESAT_3U_MASS_KG = 4.0
CUBESAT_3U_SIZE_M = (0.10, 0.10, 0.34)
CUBESAT_3U_REFERENCE_AREA_M2 = 0.10 * 0.34
CUBESAT_3U_CD = 2.2
CUBESAT_3U_CR = 1.3


@dataclass(frozen=True)
class ScenarioConfig:
    """Default mission profile for orbital dynamics phases."""

    altitude_m: float = 500_000.0
    inclination_deg: float = 97.0
    eccentricity: float = 0.0
    raan_deg: float = 0.0
    arg_perigee_deg: float = 0.0
    true_anomaly_deg: float = 0.0
    num_orbits: int = 10
    output_step_s: float = 20.0
    start_epoch_utc: str = "2026-01-01T00:00:00+00:00"
