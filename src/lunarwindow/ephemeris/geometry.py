"""Sun and Earth positions as seen from a point on the lunar surface.

All vectors are expressed in the MOON_ME body-fixed frame. A site is (lat, lon, elevation) where
elevation is height above the 1737.4 km reference sphere (LOLA convention). The local topocentric
frame is East-North-Up at the site.

Requires SPICE kernels to be furnished (see `kernels.load`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
import spiceypy as spice

from lunarwindow.config import settings

FRAME = "MOON_ME"
ABCORR = "LT+S"  # light-time + stellar aberration: what an observer at the site actually sees


@dataclass(frozen=True)
class Site:
    name: str
    lat_deg: float
    lon_deg: float  # east-positive, 0–360 or -180–180 both accepted
    elev_m: float = 0.0  # height above reference sphere (from DEM)
    height_m: float = settings.lander_height_m  # observer height above terrain

    @property
    def radius_km(self) -> float:
        return settings.moon_radius_km + (self.elev_m + self.height_m) / 1000.0

    def position_me(self) -> np.ndarray:
        """Site position vector in MOON_ME, km."""
        lat = np.radians(self.lat_deg)
        lon = np.radians(self.lon_deg)
        r = self.radius_km
        return np.array(
            [r * np.cos(lat) * np.cos(lon), r * np.cos(lat) * np.sin(lon), r * np.sin(lat)]
        )

    def enu_basis(self) -> np.ndarray:
        """Rows: unit East, North, Up vectors in MOON_ME (spherical local vertical)."""
        lat = np.radians(self.lat_deg)
        lon = np.radians(self.lon_deg)
        east = np.array([-np.sin(lon), np.cos(lon), 0.0])
        north = np.array([-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)])
        up = np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
        return np.vstack([east, north, up])


def et_from_datetime(t: datetime) -> float:
    if t.tzinfo is None:
        t = t.replace(tzinfo=UTC)
    return float(spice.str2et(t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")))


def et_range(start: datetime, end: datetime, step_s: float) -> np.ndarray:
    e0, e1 = et_from_datetime(start), et_from_datetime(end)
    n = int(np.floor((e1 - e0) / step_s)) + 1
    return e0 + step_s * np.arange(n)


def target_vectors_me(target: str, ets: np.ndarray) -> np.ndarray:
    """Moon-centre → target vectors in MOON_ME, km, shape (n, 3)."""
    out = np.empty((len(ets), 3))
    for i, et in enumerate(ets):
        pos, _ = spice.spkpos(target, float(et), FRAME, ABCORR, "MOON")
        out[i] = pos
    return out


def az_el_dist(
    site: Site, target: str, ets: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Azimuth (deg, from North through East), elevation (deg, above local spherical
    horizontal) and distance (km) of `target` from `site` at each ET."""
    tv = target_vectors_me(target, ets) - site.position_me()
    enu = tv @ site.enu_basis().T  # (n,3): east, north, up components
    dist = np.linalg.norm(enu, axis=1)
    el = np.degrees(np.arcsin(enu[:, 2] / dist))
    az = np.degrees(np.arctan2(enu[:, 0], enu[:, 1])) % 360.0
    return az, el, dist


def sun_az_el(site: Site, ets: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return az_el_dist(site, "SUN", ets)


def earth_az_el(site: Site, ets: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return az_el_dist(site, "EARTH", ets)


def sun_angular_radius_deg(dist_km: np.ndarray) -> np.ndarray:
    """Apparent solar angular radius given Sun–site distance (km)."""
    r_sun_km = 695_700.0
    return np.degrees(np.arcsin(r_sun_km / dist_km))
