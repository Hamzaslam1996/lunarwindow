"""terrain.lola on a synthetic south-polar-stereographic GeoTIFF (no real DEM needed)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from lunarwindow.config import settings
from lunarwindow.terrain import lola
from lunarwindow.terrain.lola import LolaDem, resample_periodic

R_M = settings.moon_radius_km * 1000.0
PIX = 20.0
N = 401  # pole at pixel centre (200, 200)


def ang_diff(a, b):
    """Signed smallest difference between two angles in degrees."""
    return (np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0


def _write(
    path: Path,
    data: np.ndarray,
    *,
    dtype="float32",
    scales=None,
    offsets=None,
    crs=True,
    nodata=None,
):
    half = (N / 2) * PIX  # left/top edge so that pixel (200,200) is centred on the pole
    tfm = Affine(PIX, 0.0, -half, 0.0, -PIX, half)
    profile = {
        "driver": "GTiff",
        "height": N,
        "width": N,
        "count": 1,
        "dtype": dtype,
        "transform": tfm,
        "crs": lola.south_polar_stereo_crs() if crs else None,
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype(dtype), 1)
        if scales:
            dst.scales = scales
        if offsets:
            dst.offsets = offsets
        dst.update_tags(PRODUCT_ID="SYNTHETIC_875S_20M")


@pytest.fixture
def flat_dem(tmp_path: Path) -> LolaDem:
    p = tmp_path / "flat.tif"
    _write(p, np.zeros((N, N)))
    return LolaDem.open(p)


def rho(lat_deg: float) -> float:
    """Polar stereographic radius from the south pole, true at the pole."""
    return 2 * R_M * np.tan(np.radians(90.0 + lat_deg) / 2.0)


def test_open_reads_metadata(flat_dem: LolaDem):
    assert flat_dem.pixel_m == PIX
    assert flat_dem.shape == (N, N)
    assert flat_dem.product_id == "SYNTHETIC_875S_20M"
    assert flat_dem.nodata_fraction == 0.0


def test_pole_maps_to_centre_pixel(flat_dem: LolaDem):
    row, col = flat_dem.lonlat_to_rowcol(0.0, -90.0)
    assert np.allclose([row[0], col[0]], [200.0, 200.0], atol=1e-6)


@pytest.mark.parametrize(
    ("lon", "drow", "dcol"),
    [(0.0, -1, 0), (90.0, 0, 1), (180.0, 1, 0), (270.0, 0, -1)],
)
def test_lonlat_to_rowcol_polar_geometry(flat_dem: LolaDem, lon, drow, dcol):
    lat = -89.95
    d_px = rho(lat) / PIX  # ≈ 75.8 px from the pole
    row, col = flat_dem.lonlat_to_rowcol(lon, lat)
    assert abs(row[0] - (200 + drow * d_px)) < 1e-3
    assert abs(col[0] - (200 + dcol * d_px)) < 1e-3


def test_rowcol_lonlat_roundtrip(flat_dem: LolaDem):
    lon0, lat0 = np.array([222.7, 10.0, 355.0]), np.array([-89.6, -89.9, -89.75])
    row, col = flat_dem.lonlat_to_rowcol(lon0, lat0)
    lon1, lat1 = flat_dem.rowcol_to_lonlat(row, col)
    assert np.allclose(lon1, lon0, atol=1e-8)
    assert np.allclose(lat1, lat0, atol=1e-8)


@pytest.mark.parametrize("lon", [0.0, 90.0, 222.7, 300.0])
def test_grid_to_true_azimuth_is_rotation_by_longitude(flat_dem: LolaDem, lon):
    # Standard south-polar stereographic (lon_0 = 0): +y points to lon 0, +x to lon 90.
    # Lunar north at a point is the outward radial, whose grid azimuth equals the longitude,
    # so true = grid - lon (handedness preserved: conformal, east = north + 90°).
    g = np.linspace(0.0, 360.0, 13, endpoint=False)
    t = flat_dem.grid_to_true_azimuth(g, lon, -89.9)
    assert np.abs(ang_diff(t, g - lon)).max() < 1e-3
    assert abs(ang_diff(flat_dem.north_grid_azimuth_deg(lon, -89.9), lon)) < 1e-3
    back = flat_dem.true_to_grid_azimuth(t, lon, -89.9)
    assert np.abs(ang_diff(back, g)).max() < 1e-3


def test_elevation_at_bilinear(tmp_path: Path):
    data = np.zeros((N, N))
    data[200, 200] = 100.0
    p = tmp_path / "spike.tif"
    _write(p, data)
    dem = LolaDem.open(p)
    assert dem.elevation_at(0.0, -90.0)[0] == pytest.approx(100.0)
    # half a pixel north of the pole → halfway between spike and flat neighbour
    lon, lat = dem.rowcol_to_lonlat(199.5, 200.0)
    assert dem.elevation_at(lon[0], lat[0])[0] == pytest.approx(50.0, abs=1e-3)
    assert np.isnan(dem.elevation_at(0.0, -80.0)[0])  # far outside the tile


def test_pds_scale_offset_yields_heights(tmp_path: Path):
    # PDS LDEM: int16 raw, SCALING_FACTOR 0.5, OFFSET 1737400 → radius (m). We want heights.
    raw = np.full((N, N), 246, dtype=np.int16)  # 246 * 0.5 = 123 m above the sphere
    p = tmp_path / "pds_like.tif"
    _write(p, raw, dtype="int16", scales=(0.5,), offsets=(R_M,))
    dem = LolaDem.open(p)
    assert np.allclose(dem.data, 123.0)
    dem_km = LolaDem.open(p, values="radius_m")
    assert np.allclose(dem_km.data, 123.0)


def test_int16_nodata_becomes_nan(tmp_path: Path):
    # Real PDS LDEM tiles are int16 with a NULL constant (-32768); nodata must become NaN.
    raw = np.full((N, N), 246, dtype=np.int16)
    raw[:5, :] = -32768
    p = tmp_path / "pds_nodata.tif"
    _write(p, raw, dtype="int16", scales=(0.5,), offsets=(R_M,), nodata=-32768)
    dem = LolaDem.open(p)
    assert np.isnan(dem.data[:5]).all()
    assert np.allclose(dem.data[5:], 123.0)
    assert dem.nodata_fraction == pytest.approx(5 / N)


def test_radius_km_mode(tmp_path: Path):
    p = tmp_path / "km.tif"
    _write(p, np.full((N, N), settings.moon_radius_km + 0.25), dtype="float64")
    dem = LolaDem.open(p)  # auto-detects kilometre radii
    assert np.allclose(dem.data, 250.0, atol=1e-3)


def test_missing_crs_falls_back_to_south_polar_stereo(tmp_path: Path, caplog):
    p = tmp_path / "nocrs.tif"
    _write(p, np.zeros((N, N)), crs=False)
    with caplog.at_level("WARNING"):
        dem = LolaDem.open(p)
    assert dem.crs == lola.south_polar_stereo_crs()
    row, col = dem.lonlat_to_rowcol(0.0, -90.0)
    assert np.allclose([row[0], col[0]], [200.0, 200.0], atol=1e-6)


def test_horizon_returns_true_azimuths(tmp_path: Path):
    # Observer at lon 90°: grid "right" (+col) is the outward radial, i.e. lunar NORTH.
    # A plateau to the right must therefore appear at TRUE azimuth 0, not 90.
    data = np.zeros((N, N))
    data[:, 300:] = 200.0
    p = tmp_path / "wall.tif"
    _write(p, data)
    dem = LolaDem.open(p)
    lat = -89.95
    hz = dem.horizon(90.0, lat, height_m=0.0, max_range_m=6000.0)
    assert hz.azimuths_deg[0] == 0.0 and len(hz.azimuths_deg) == 360
    row, col = dem.lonlat_to_rowcol(90.0, lat)
    # Bilinear sampling ramps from 0 at col 299 to 200 m at col 300, so the skyline peaks at
    # col 300. The ray is sampled every half pixel, so allow half a sample of slack (~0.3°).
    dist_m = (300 - col[0]) * PIX
    expected = np.degrees(np.arctan2(200.0, dist_m))
    assert abs(hz.elevation_at(0.0) - expected) < 0.5
    assert hz.elevation_at(0.0) > 20.0
    assert hz.elevation_at(90.0) <= 0.0
    assert hz.elevation_at(180.0) <= 0.0
    assert hz.elevation_at(270.0) <= 0.0


def test_horizon_outside_tile_raises(flat_dem: LolaDem):
    with pytest.raises(ValueError, match="outside"):
        flat_dem.horizon(0.0, -85.0)


def test_resample_periodic_wraps():
    az = np.array([350.0, 10.0, 170.0, 190.0])
    v = np.array([1.0, 1.0, 3.0, 3.0])
    out = resample_periodic(az, v, np.array([0.0, 180.0, 355.0, 90.0]))
    assert np.allclose(out[:3], [1.0, 3.0, 1.0])
    assert 1.0 < out[3] < 3.0


def test_default_dem_path_uses_settings():
    assert lola.default_dem_path() == settings.dem_dir / "ldem_875s_20m.lbl"
