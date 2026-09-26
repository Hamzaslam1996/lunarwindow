import numpy as np

from lunarwindow.terrain.horizon import compute_horizon, flat_horizon


def test_flat_dem_gives_zero_or_negative_skyline():
    dem = np.zeros((201, 201))
    hz = compute_horizon(dem, pixel_m=20.0, row=100, col=100, height_m=2.0, max_range_m=2000)
    # observer 2 m above flat ground: skyline is slightly below 0 (looking down at the plane)
    assert (hz.elevations_deg <= 0.0).all()
    assert hz.elevations_deg.max() > -1.0


def test_wall_to_the_north_raises_skyline_by_expected_angle():
    dem = np.zeros((201, 201))
    dem[:80, :] = 100.0  # 100 m plateau starting 20 rows (=400 m) north of the observer
    hz = compute_horizon(dem, pixel_m=20.0, row=100, col=100, height_m=0.0, max_range_m=4000)
    # plateau reaches full height at row 79 → 21 rows × 20 m = 420 m from the observer
    expected = np.degrees(np.arctan2(100.0, 420.0))  # ≈ 13.39°
    north = hz.elevation_at(0.0)
    assert abs(north - expected) < 0.05
    assert hz.elevation_at(180.0) <= 0.0  # south is flat


def test_curvature_lowers_distant_terrain():
    dem = np.zeros((401, 401))
    dem[:, 390:] = 50.0  # 50 m rise ~58 km east at 200 m pixels
    hz = compute_horizon(dem, pixel_m=200.0, row=200, col=200, height_m=0.0, max_range_m=80_000)
    east = hz.elevation_at(90.0)
    # flat-earth angle ≈ atan(50/38000)=0.075°; sphere drop at 38 km ≈ 415 m → well below 0
    assert east < 0.0


def test_elevation_at_wraps_periodically():
    hz = flat_horizon(n_az=36, elevation_deg=1.5)
    assert np.allclose(hz.elevation_at([0.0, 359.9, 720.0, -10.0]), 1.5)
