"""Direct-to-Earth (DTE) visibility windows.

Earth is visible when its centre elevation exceeds the local skyline plus an antenna mask margin.
Windows are returned as (start_index, end_index_exclusive) pairs over the ET grid.
"""

from __future__ import annotations

import numpy as np

from lunarwindow.terrain.horizon import HorizonMask


def visible(
    earth_az_deg: np.ndarray,
    earth_el_deg: np.ndarray,
    horizon: HorizonMask,
    margin_deg: float = 0.0,
) -> np.ndarray:
    return earth_el_deg > (horizon.elevation_at(earth_az_deg) + margin_deg)


def windows(mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous True runs as [start, end) index pairs."""
    if mask.size == 0:
        return []
    m = np.concatenate([[False], mask.astype(bool), [False]])
    d = np.diff(m.astype(int))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    return list(zip(starts.tolist(), ends.tolist(), strict=True))


def summarise(mask: np.ndarray, step_s: float) -> dict[str, float]:
    w = windows(mask)
    hours = step_s / 3600.0
    lengths = [(e - s) * hours for s, e in w]
    gaps = [(w[i + 1][0] - w[i][1]) * hours for i in range(len(w) - 1)]
    return {
        "fraction_time_visible": float(mask.mean()) if mask.size else 0.0,
        "n_windows": float(len(w)),
        "longest_window_hours": float(max(lengths)) if lengths else 0.0,
        "longest_gap_hours": float(max(gaps))
        if gaps
        else (0.0 if mask.all() else float(len(mask) * hours)),
    }
