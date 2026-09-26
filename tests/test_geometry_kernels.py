"""Kernel-dependent sanity checks. Skipped until kernels are fetched."""

from datetime import UTC, datetime

import numpy as np
import pytest

from lunarwindow.ephemeris import geometry as geo
from tests.conftest import needs_kernels

pytestmark = needs_kernels


@pytest.mark.usefixtures("spice_loaded")
def test_sun_elevation_at_south_pole_stays_within_axial_tilt():
    # The Moon's spin axis is tilted ~1.54° to the ecliptic: at the exact pole the Sun's
    # elevation over the spherical horizon must stay within about ±1.6° all year.
    site = geo.Site("pole", -90.0, 0.0, 0.0, height_m=0.0)
    ets = geo.et_range(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 12, 31, tzinfo=UTC),
        6 * 3600,
    )
    _, el, _ = geo.sun_az_el(site, ets)
    assert el.max() < 1.7 and el.min() > -1.7


@pytest.mark.usefixtures("spice_loaded")
def test_earth_elevation_at_south_pole_librates_within_expected_band():
    # Earth as seen from the pole moves within roughly ±7° in elevation over a month (libration).
    site = geo.Site("pole", -90.0, 0.0, 0.0, height_m=0.0)
    ets = geo.et_range(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 3, 1, tzinfo=UTC), 3600)
    _, el, _ = geo.earth_az_el(site, ets)
    assert -9.0 < el.min() < 0.0 < el.max() < 9.0


@pytest.mark.usefixtures("spice_loaded")
def test_equator_subearth_point_sees_earth_near_zenith():
    site = geo.Site("subearth", 0.0, 0.0, 0.0, height_m=0.0)
    ets = geo.et_range(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 2, 1, tzinfo=UTC),
        6 * 3600,
    )
    _, el, _ = geo.earth_az_el(site, ets)
    assert np.median(el) > 80.0
