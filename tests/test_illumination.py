import numpy as np

from lunarwindow.illumination.solar import (
    disc_fraction_above,
    illumination_fraction,
    solar_power_relative,
    summarise,
)
from lunarwindow.terrain.horizon import flat_horizon


def test_disc_fraction_limits_and_symmetry():
    r = 0.25
    assert disc_fraction_above(r, r) == 1.0
    assert disc_fraction_above(-r, r) == 0.0
    assert abs(disc_fraction_above(0.0, r) - 0.5) < 1e-12
    a = disc_fraction_above(0.1, r)
    b = disc_fraction_above(-0.1, r)
    assert abs((a + b) - 1.0) < 1e-12
    assert 0.5 < a < 1.0


def test_disc_fraction_monotonic():
    d = np.linspace(-0.3, 0.3, 61)
    f = disc_fraction_above(d, 0.25)
    assert (np.diff(f) >= 0).all()


def test_illumination_against_flat_and_raised_skyline():
    az = np.array([0.0, 90.0, 180.0])
    el = np.array([1.0, 0.0, -1.0])
    flat = flat_horizon()
    f = illumination_fraction(az, el, 0.25, flat)
    assert np.allclose(f, [1.0, 0.5, 0.0])
    raised = flat_horizon(elevation_deg=1.0)
    f2 = illumination_fraction(az, el, 0.25, raised)
    assert np.allclose(f2, [0.5, 0.0, 0.0])


def test_summary_longest_dark():
    frac = np.array([1, 1, 0, 0, 0, 1, 0, 0, 1], dtype=float)
    s = summarise(frac, step_s=3600)
    assert s["longest_dark_hours"] == 3.0
    assert s["total_lit_hours"] == 4.0
    assert abs(s["fraction_time_lit"] - 4 / 9) < 1e-12


def test_power_models():
    frac = np.ones(3)
    el = np.array([0.0, 30.0, 90.0])
    v = solar_power_relative(frac, el, "vertical")
    h = solar_power_relative(frac, el, "horizontal")
    assert np.allclose(v, [1.0, np.cos(np.radians(30)), 0.0], atol=1e-12)
    assert np.allclose(h, [0.0, 0.5, 1.0], atol=1e-12)
