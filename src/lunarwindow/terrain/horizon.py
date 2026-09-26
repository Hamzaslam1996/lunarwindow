"""Horizon mask: the elevation angle of the terrain skyline in every azimuth from a site.

Works on any DEM given as a 2-D array in a locally-planar projection (LOLA polar stereographic
products are ideal near the poles) with a known pixel size. The observer sits `height_m` above the
terrain at (row, col). For each azimuth a ray is marched outward; the horizon elevation is the
maximum of atan2(dz, ds) along the ray, with the curvature drop of the reference sphere subtracted
so that distant terrain is correctly lowered.

This is the expensive step; results are cached per site by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import map_coordinates

from lunarwindow.config import settings


@dataclass(frozen=True)
class HorizonMask:
    azimuths_deg: np.ndarray  # (n,) 0..360 exclusive, ascending
    elevations_deg: np.ndarray  # (n,) skyline elevation angle per azimuth

    def elevation_at(self, az_deg: np.ndarray | float) -> np.ndarray:
        """Skyline elevation interpolated (periodically) at arbitrary azimuths."""
        az = np.asarray(az_deg, dtype=float) % 360.0
        a = np.concatenate([self.azimuths_deg, [360.0]])
        e = np.concatenate([self.elevations_deg, [self.elevations_deg[0]]])
        return np.interp(az, a, e)


def compute_horizon(
    dem: np.ndarray,
    pixel_m: float,
    row: float,
    col: float,
    *,
    height_m: float | None = None,
    n_az: int = 360,
    max_range_m: float = 100_000.0,
    step_m: float | None = None,
    radius_km: float | None = None,
    azimuth_convention: str = "grid",
) -> HorizonMask:
    """Compute the skyline from DEM cell (row, col).

    `azimuth_convention="grid"` means azimuth 0 = +row-decreasing (grid "north"), 90 = +col
    (grid "east"). For polar stereographic DEMs the caller must rotate azimuths into true
    lunar azimuths (see `terrain.lola.grid_to_true_azimuth`).
    """
    h = settings.lander_height_m if height_m is None else height_m
    r_km = settings.moon_radius_km if radius_km is None else radius_km
    step = pixel_m / 2.0 if step_m is None else step_m

    z0 = float(map_coordinates(dem, [[row], [col]], order=1, mode="nearest")[0]) + h
    dists = np.arange(step, max_range_m + step, step)
    curvature_drop = dists**2 / (2.0 * r_km * 1000.0)  # metres, small-angle sphere drop

    azimuths = np.linspace(0.0, 360.0, n_az, endpoint=False)
    elev = np.empty(n_az)
    for i, az in enumerate(azimuths):
        a = np.radians(az)
        drow = -np.cos(a) * dists / pixel_m
        dcol = np.sin(a) * dists / pixel_m
        rr, cc = row + drow, col + dcol
        inside = (rr >= 0) & (rr <= dem.shape[0] - 1) & (cc >= 0) & (cc <= dem.shape[1] - 1)
        if not inside.any():
            elev[i] = 0.0
            continue
        z = map_coordinates(dem, [rr[inside], cc[inside]], order=1, mode="nearest")
        dz = z - z0 - curvature_drop[inside]
        ang = np.degrees(np.arctan2(dz, dists[inside]))
        elev[i] = max(float(ang.max()), -90.0)
    return HorizonMask(azimuths, elev)


def flat_horizon(n_az: int = 360, elevation_deg: float = 0.0) -> HorizonMask:
    """A perfectly flat skyline; useful for tests and for the 'no-DEM' fallback."""
    return HorizonMask(np.linspace(0.0, 360.0, n_az, endpoint=False), np.full(n_az, elevation_deg))
