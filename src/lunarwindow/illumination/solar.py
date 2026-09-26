"""Illumination: fraction of the solar disc above the local skyline, and derived power metrics.

Model (v0): the Sun is a uniform disc of angular radius ρ; the skyline is treated as a straight
edge at the disc's azimuth. visible_fraction = area of the disc above the edge / total area.
This is the standard first-order model used in lunar polar illumination studies; limb darkening
and skyline curvature across the disc are second-order and documented as limitations.
"""

from __future__ import annotations

import numpy as np

from lunarwindow.terrain.horizon import HorizonMask

#: Mean synodic month (one "lunar day"), seconds.
SYNODIC_MONTH_S = 29.530589 * 86400.0


def window_means(frac: np.ndarray, step_s: float, window_s: float = SYNODIC_MONTH_S) -> np.ndarray:
    """Mean of `frac` over consecutive, non-overlapping windows of `window_s` seconds.

    Windows are anchored at index 0; a trailing partial window is dropped. With the default
    window this is the "lunar-day average" used in polar power studies (Fincannon 2007).
    """
    n = int(round(window_s / step_s))
    if n <= 0:
        raise ValueError("window shorter than one step")
    m = len(frac) // n
    if m == 0:
        return np.empty(0)
    return np.asarray(frac[: m * n], dtype=float).reshape(m, n).mean(axis=1)


def sliding_window_means(
    frac: np.ndarray, step_s: float, window_s: float = SYNODIC_MONTH_S
) -> np.ndarray:
    """Mean of `frac` over every window of `window_s` seconds starting at each step."""
    n = int(round(window_s / step_s))
    if n <= 0 or n > len(frac):
        return np.empty(0)
    c = np.concatenate([[0.0], np.cumsum(np.asarray(frac, dtype=float))])
    return (c[n:] - c[:-n]) / n


def worst_window(
    frac: np.ndarray, step_s: float, window_s: float = SYNODIC_MONTH_S, *, sliding: bool = False
) -> tuple[int, float]:
    """(start_index, mean) of the window with the lowest mean illumination.

    `sliding=False` uses the anchored non-overlapping windows of :func:`window_means`;
    `sliding=True` considers every start step and is therefore a lower bound on any anchoring.
    """
    n = int(round(window_s / step_s))
    means = (
        sliding_window_means(frac, step_s, window_s)
        if sliding
        else window_means(frac, step_s, window_s)
    )
    if means.size == 0:
        raise ValueError("period shorter than one window")
    i = int(np.argmin(means))
    return (i if sliding else i * n), float(means[i])


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
