"""LOLA polar DEM access.

Loads an LRO LOLA GDR polar-stereographic tile (PDS3 ``.LBL``/``.IMG`` pair or a GeoTIFF
derived from one) with rasterio, converts lunar latitude/longitude to pixel coordinates, and
rotates *grid* azimuths (0 = up the raster, 90 = right) into *true* azimuths (0 = lunar north,
90 = east) so that horizon masks computed on the grid can be compared with SPICE Sun/Earth
azimuths.

Conventions
-----------
* Elevations are metres above the 1737.4 km reference sphere (LOLA convention). PDS LDEM labels
  store ``SCALING_FACTOR``/``OFFSET`` such that ``raw * scale + offset`` is a *radius*; this
  module returns heights, subtracting the reference radius when the offset makes that necessary.
* Pixel coordinates are (row, col) floats in the array-index convention used by
  :func:`lunarwindow.terrain.horizon.compute_horizon`; integer values are pixel centres.
* Azimuth rotation is derived numerically from the raster's CRS, so it is correct for any polar
  projection and any ``lon_0`` rather than assuming the standard south-polar stereographic form.
  For the standard LOLA south-polar products (``+lon_0=0``) the rotation reduces to
  ``true = grid - longitude``.

Limitations (documented in ``docs/method.md``)
* The horizon ray-march treats the pixel size as constant; the polar stereographic scale factor
  ``2 / (1 + sin|lat|)`` is 1.0005 at 87.5°S, i.e. a 0.05 % range error, ignored.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine
from rasterio.warp import transform as warp_transform
from scipy.ndimage import map_coordinates

from lunarwindow.config import settings
from lunarwindow.terrain.horizon import HorizonMask, compute_horizon

log = logging.getLogger(__name__)

#: Canonical Phase-1 product: LOLA GDR, south polar stereographic, 87.5°S–90°S, 20 m/px.
DEFAULT_DEM_PRODUCT = "LDEM_875S_20M"

ValueMode = Literal["auto", "height_m", "radius_m", "radius_km"]

#: Lunar geographic CRS on the LOLA reference sphere (MOON_ME, east-positive longitude).
LUNAR_LONLAT_PROJ4 = "+proj=longlat +R={r} +no_defs"
#: South polar stereographic, true at the pole, on the LOLA reference sphere. Used as a
#: fallback when a raster carries no CRS (some converted products lose it).
SOUTH_POLAR_STEREO_PROJ4 = (
    "+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R={r} +units=m +no_defs"
)


def lunar_lonlat_crs(radius_m: float | None = None) -> CRS:
    r = settings.moon_radius_km * 1000.0 if radius_m is None else radius_m
    return CRS.from_proj4(LUNAR_LONLAT_PROJ4.format(r=f"{r:.1f}"))


def south_polar_stereo_crs(radius_m: float | None = None) -> CRS:
    r = settings.moon_radius_km * 1000.0 if radius_m is None else radius_m
    return CRS.from_proj4(SOUTH_POLAR_STEREO_PROJ4.format(r=f"{r:.1f}"))


def _to_height_m(raw: np.ndarray, scale: float, offset: float, mode: ValueMode) -> np.ndarray:
    """Convert raw raster values to metres above the reference sphere."""
    r_m = settings.moon_radius_km * 1000.0
    vals = raw.astype(np.float64) * scale + offset
    if mode == "auto":
        finite = vals[np.isfinite(vals)]
        med = float(np.median(finite)) if finite.size else 0.0
        if med > 1.0e6:  # radius in metres (PDS LDEM: OFFSET = 1737400)
            mode = "radius_m"
        elif 1000.0 < med < 3000.0:  # radius in kilometres
            mode = "radius_km"
        else:
            mode = "height_m"
    if mode == "radius_m":
        vals -= r_m
    elif mode == "radius_km":
        vals = (vals - settings.moon_radius_km) * 1000.0
    return vals.astype(np.float32)


@dataclass(frozen=True)
class LolaDem:
    """An in-memory LOLA polar DEM tile with georeferencing."""

    path: Path
    data: np.ndarray  # (rows, cols) float32, metres above the reference sphere; NaN = nodata
    transform: Affine  # pixel (col, row) → map (x, y); rasterio convention (edge-referenced)
    crs: CRS
    pixel_m: float
    product_id: str
    nodata_fraction: float = 0.0

    # ------------------------------------------------------------------ construction
    @classmethod
    def open(
        cls,
        path: str | Path,
        *,
        band: int = 1,
        values: ValueMode = "auto",
        crs: CRS | None = None,
    ) -> LolaDem:
        """Load a DEM. `path` may be a PDS3 ``.LBL`` (GDAL PDS driver) or a GeoTIFF.

        `crs` overrides the raster's CRS; if the raster has none and no override is given, the
        standard south-polar stereographic CRS on the 1737.4 km sphere is assumed and logged.
        """
        p = Path(path)
        with rasterio.open(p) as src:
            raw = src.read(band, masked=True)
            scale = float(src.scales[band - 1]) if src.scales else 1.0
            offset = float(src.offsets[band - 1]) if src.offsets else 0.0
            tfm = src.transform
            src_crs = crs or src.crs
            tags = src.tags()
            product_id = str(tags.get("PRODUCT_ID", p.stem)).strip('"')
        if src_crs is None or not str(src_crs):
            log.warning("%s carries no CRS; assuming south polar stereographic (lon_0=0)", p)
            src_crs = south_polar_stereo_crs()
        px, py = abs(tfm.a), abs(tfm.e)
        if not np.isclose(px, py, rtol=1e-6):
            raise ValueError(f"non-square pixels ({px} × {py} m) are not supported")
        heights = _to_height_m(np.ma.filled(raw, np.nan), scale, offset, values)
        heights = np.where(np.ma.getmaskarray(raw), np.nan, heights).astype(np.float32)
        nodata_fraction = float(np.isnan(heights).mean())
        return cls(
            path=p,
            data=heights,
            transform=tfm,
            crs=src_crs,
            pixel_m=float(px),
            product_id=product_id,
            nodata_fraction=nodata_fraction,
        )

    @property
    def shape(self) -> tuple[int, int]:
        return self.data.shape[0], self.data.shape[1]

    # ------------------------------------------------------------------ coordinates
    def lonlat_to_xy(self, lon_deg: np.ndarray | float, lat_deg: np.ndarray | float) -> tuple:
        """Lunar lon/lat (deg, east-positive) → projected x, y (m) in the DEM's CRS."""
        lon = np.atleast_1d(np.asarray(lon_deg, dtype=float))
        lat = np.atleast_1d(np.asarray(lat_deg, dtype=float))
        xs, ys = warp_transform(lunar_lonlat_crs(), self.crs, lon.tolist(), lat.tolist())
        return np.asarray(xs), np.asarray(ys)

    def xy_to_lonlat(self, x: np.ndarray | float, y: np.ndarray | float) -> tuple:
        xs = np.atleast_1d(np.asarray(x, dtype=float))
        ys = np.atleast_1d(np.asarray(y, dtype=float))
        lon, lat = warp_transform(self.crs, lunar_lonlat_crs(), xs.tolist(), ys.tolist())
        return np.asarray(lon) % 360.0, np.asarray(lat)

    def xy_to_rowcol(self, x: np.ndarray | float, y: np.ndarray | float) -> tuple:
        """Projected x, y → fractional (row, col); integers address pixel centres."""
        inv = ~self.transform
        xs = np.asarray(x, dtype=float)
        ys = np.asarray(y, dtype=float)
        col = inv.a * xs + inv.b * ys + inv.c - 0.5
        row = inv.d * xs + inv.e * ys + inv.f - 0.5
        return row, col

    def rowcol_to_xy(self, row: np.ndarray | float, col: np.ndarray | float) -> tuple:
        t = self.transform
        r = np.asarray(row, dtype=float) + 0.5
        c = np.asarray(col, dtype=float) + 0.5
        return t.a * c + t.b * r + t.c, t.d * c + t.e * r + t.f

    def lonlat_to_rowcol(self, lon_deg: np.ndarray | float, lat_deg: np.ndarray | float) -> tuple:
        x, y = self.lonlat_to_xy(lon_deg, lat_deg)
        return self.xy_to_rowcol(x, y)

    def rowcol_to_lonlat(self, row: np.ndarray | float, col: np.ndarray | float) -> tuple:
        x, y = self.rowcol_to_xy(row, col)
        return self.xy_to_lonlat(x, y)

    def contains(self, row: float, col: float, margin_px: float = 0.0) -> bool:
        nr, nc = self.shape
        return bool(
            margin_px <= row <= nr - 1 - margin_px and margin_px <= col <= nc - 1 - margin_px
        )

    def elevation_at(self, lon_deg: np.ndarray | float, lat_deg: np.ndarray | float) -> np.ndarray:
        """Bilinear height (m) at lunar lon/lat. NaN outside the tile."""
        row, col = self.lonlat_to_rowcol(lon_deg, lat_deg)
        return map_coordinates(
            self.data,
            [np.atleast_1d(row), np.atleast_1d(col)],
            order=1,
            mode="constant",
            cval=np.nan,
        )

    # ------------------------------------------------------------------ azimuths
    def _local_north_east(self, lon_deg: float, lat_deg: float) -> tuple[np.ndarray, np.ndarray]:
        """Unit vectors of lunar north and east in (drow, dcol) grid space at a point.

        Derived numerically from the CRS so the result holds for any polar projection. Exactly
        at the pole north is undefined; we step 1e-4° off the pole along `lon_deg`.
        """
        lat = max(min(lat_deg, 90.0 - 1e-4), -90.0 + 1e-4)
        d = 1e-4  # degrees; ~3 m on the Moon
        r0, c0 = self.lonlat_to_rowcol(lon_deg, lat)
        r_n, c_n = self.lonlat_to_rowcol(lon_deg, lat + d)
        r_e, c_e = self.lonlat_to_rowcol(lon_deg + d, lat)
        north = np.array([float(r_n[0] - r0[0]), float(c_n[0] - c0[0])])
        east = np.array([float(r_e[0] - r0[0]), float(c_e[0] - c0[0])])
        return north / np.linalg.norm(north), east / np.linalg.norm(east)

    def north_grid_azimuth_deg(self, lon_deg: float, lat_deg: float) -> float:
        """Grid azimuth (0 = up the raster, clockwise) in which lunar north points."""
        north, _ = self._local_north_east(lon_deg, lat_deg)
        return float(np.degrees(np.arctan2(north[1], -north[0])) % 360.0)

    def grid_to_true_azimuth(
        self, grid_az_deg: np.ndarray | float, lon_deg: float, lat_deg: float
    ) -> np.ndarray:
        """Rotate grid azimuths (0 = -row, 90 = +col) into true azimuths (0 = N, 90 = E)."""
        north, east = self._local_north_east(lon_deg, lat_deg)
        g = np.radians(np.asarray(grid_az_deg, dtype=float))
        d_row, d_col = -np.cos(g), np.sin(g)
        n = d_row * north[0] + d_col * north[1]
        e = d_row * east[0] + d_col * east[1]
        return np.degrees(np.arctan2(e, n)) % 360.0

    def true_to_grid_azimuth(
        self, true_az_deg: np.ndarray | float, lon_deg: float, lat_deg: float
    ) -> np.ndarray:
        """Inverse of :meth:`grid_to_true_azimuth`."""
        north, east = self._local_north_east(lon_deg, lat_deg)
        t = np.radians(np.asarray(true_az_deg, dtype=float))
        vec = np.cos(t)[..., None] * north + np.sin(t)[..., None] * east  # (…, 2) as (drow, dcol)
        return np.degrees(np.arctan2(vec[..., 1], -vec[..., 0])) % 360.0

    # ------------------------------------------------------------------ horizon
    def horizon(
        self,
        lon_deg: float,
        lat_deg: float,
        *,
        height_m: float | None = None,
        n_az: int = 360,
        max_range_m: float = 100_000.0,
        step_m: float | None = None,
    ) -> HorizonMask:
        """Skyline from (lon, lat) with azimuths expressed as *true* lunar azimuths.

        Runs :func:`compute_horizon` on the grid, rotates each ray's azimuth to true azimuth,
        and resamples the (periodic) skyline onto a regular 0–360° grid.
        """
        row, col = self.lonlat_to_rowcol(lon_deg, lat_deg)
        r, c = float(row[0]), float(col[0])
        if not self.contains(r, c):
            raise ValueError(
                f"({lat_deg}, {lon_deg}) → pixel ({r:.1f}, {c:.1f}) is outside {self.path.name}"
            )
        if np.isnan(self.data).any():
            log.warning(
                "%s has nodata pixels (%.2f%%); rays through them are unreliable",
                self.path.name,
                100 * self.nodata_fraction,
            )
        grid = compute_horizon(
            self.data,
            self.pixel_m,
            r,
            c,
            height_m=height_m,
            n_az=n_az,
            max_range_m=max_range_m,
            step_m=step_m,
        )
        true_az = self.grid_to_true_azimuth(grid.azimuths_deg, lon_deg, lat_deg)
        target = np.linspace(0.0, 360.0, n_az, endpoint=False)
        return HorizonMask(target, resample_periodic(true_az, grid.elevations_deg, target))


def resample_periodic(
    az_deg: np.ndarray, values: np.ndarray, target_az_deg: np.ndarray
) -> np.ndarray:
    """Linearly interpolate a periodic (360°) series sampled at unsorted azimuths."""
    order = np.argsort(az_deg)
    a = np.asarray(az_deg, dtype=float)[order] % 360.0
    v = np.asarray(values, dtype=float)[order]
    a_ext = np.concatenate([a[-1:] - 360.0, a, a[:1] + 360.0])
    v_ext = np.concatenate([v[-1:], v, v[:1]])
    return np.interp(np.asarray(target_az_deg, dtype=float) % 360.0, a_ext, v_ext)


def default_dem_path(product: str = DEFAULT_DEM_PRODUCT) -> Path:
    """Where `scripts/fetch_dem.py` puts the PDS label for `product`."""
    return settings.dem_dir / f"{product.lower()}.lbl"
