"""Illumination: fraction of the solar disc above the local skyline, and derived power metrics.

Model (v0): the Sun is a uniform disc of angular radius ρ; the skyline is treated as a straight
edge at the disc's azimuth. visible_fraction = area of the disc above the edge / total area.
This is the standard first-order model used in lunar polar illumination studies; limb darkening
and skyline curvature across the disc are second-order and documented as limitations.
"""

from __future__ import annotations

import numpy as np

from lunarwindow.terrain.horizon import HorizonMask


def disc_fraction_above(
    delta_deg: np.ndarray | float, radius_deg: np.ndarray | float
) -> np.ndarray:
    """Fraction of a disc of angular radius `radius_deg` whose centre is `delta_deg` above a
    straight edge. delta ≥ radius → 1; delta ≤ -radius → 0."""
    d = np.asarray(delta_deg, dtype=float)
    r = np.asarray(radius_deg, dtype=float)
    x = np.clip(d / r, -1.0, 1.0)
    # circular-segment area: (1/π)(arccos(-x) + x·sqrt(1-x²))  ... normalised to disc area
    frac = (np.arccos(-x) + x * np.sqrt(1.0 - x * x)) / np.pi
    return np.where(d >= r, 1.0, np.where(d <= -r, 0.0, frac))


def illumination_fraction(
    sun_az_deg: np.ndarray,
    sun_el_deg: np.ndarray,
    sun_radius_deg: np.ndarray | float,
    horizon: HorizonMask,
) -> np.ndarray:
    """Per-timestep visible fraction of the solar disc (0–1)."""
    skyline = horizon.elevation_at(sun_az_deg)
    return disc_fraction_above(sun_el_deg - skyline, sun_radius_deg)


def summarise(frac: np.ndarray, step_s: float) -> dict[str, float]:
    """Aggregate metrics over a period."""
    lit = frac > 0.0
    hours = step_s / 3600.0
    # longest continuous dark spell
    longest_dark = 0
    run = 0
    for v in lit:
        run = 0 if v else run + 1
        longest_dark = max(longest_dark, run)
    return {
        "mean_illumination": float(frac.mean()),
        "fraction_time_lit": float(lit.mean()),
        "longest_dark_hours": float(longest_dark * hours),
        "total_lit_hours": float(lit.sum() * hours),
        "period_hours": float(len(frac) * hours),
    }


def solar_power_relative(
    frac: np.ndarray, sun_el_deg: np.ndarray, array: str = "vertical"
) -> np.ndarray:
    """Relative solar-array power (0–1, per unit of illuminated normal-incidence power).

    'vertical'  — array normal horizontal and tracking the Sun's azimuth (typical polar lander):
                  power ∝ cos(elevation) × visible fraction.
    'horizontal'— flat array: power ∝ sin(elevation) × visible fraction.
    """
    el = np.radians(np.clip(sun_el_deg, -90, 90))
    if array == "vertical":
        geom = np.cos(el)
    elif array == "horizontal":
        geom = np.clip(np.sin(el), 0.0, None)
    else:
        raise ValueError("array must be 'vertical' or 'horizontal'")
    return frac * geom
