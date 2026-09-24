"""Site × date-window comparison: the core product query."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np

from lunarwindow import METHOD_VERSION
from lunarwindow.comms import dte
from lunarwindow.ephemeris import geometry as geo
from lunarwindow.illumination import solar
from lunarwindow.terrain.horizon import HorizonMask, flat_horizon


@dataclass
class SiteResult:
    site: str
    lat_deg: float
    lon_deg: float
    start: str
    end: str
    step_s: float
    illumination: dict[str, float]
    dte: dict[str, float]
    mean_relative_power_vertical: float
    horizon_source: str
    method_version: str = METHOD_VERSION


def evaluate(
    site: geo.Site,
    start: datetime,
    end: datetime,
    *,
    step_s: float = 3600.0,
    horizon: HorizonMask | None = None,
    dte_margin_deg: float = 0.0,
) -> SiteResult:
    """Evaluate one site over one window. Kernels must be loaded."""
    hz = horizon or flat_horizon()
    ets = geo.et_range(start, end, step_s)

    s_az, s_el, s_d = geo.sun_az_el(site, ets)
    frac = solar.illumination_fraction(s_az, s_el, geo.sun_angular_radius_deg(s_d), hz)
    power = solar.solar_power_relative(frac, s_el, "vertical")

    e_az, e_el, _ = geo.earth_az_el(site, ets)
    vis = dte.visible(e_az, e_el, hz, dte_margin_deg)

    return SiteResult(
        site=site.name,
        lat_deg=site.lat_deg,
        lon_deg=site.lon_deg,
        start=start.isoformat(),
        end=end.isoformat(),
        step_s=step_s,
        illumination=solar.summarise(frac, step_s),
        dte=dte.summarise(vis, step_s),
        mean_relative_power_vertical=float(np.mean(power)),
        horizon_source="flat" if horizon is None else "dem",
    )


def compare(sites: list[geo.Site], start: datetime, end: datetime, **kw) -> list[dict]:
    return [asdict(evaluate(s, start, end, **kw)) for s in sites]
