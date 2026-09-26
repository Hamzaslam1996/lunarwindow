import numpy as np

from lunarwindow.comms.dte import summarise, visible, windows
from lunarwindow.terrain.horizon import flat_horizon


def test_windows_runs():
    m = np.array([0, 1, 1, 0, 1, 0, 0, 1, 1, 1], dtype=bool)
    assert windows(m) == [(1, 3), (4, 5), (7, 10)]
    assert windows(np.zeros(0, dtype=bool)) == []
    assert windows(np.ones(3, dtype=bool)) == [(0, 3)]


def test_visible_uses_margin():
    hz = flat_horizon(elevation_deg=2.0)
    az = np.zeros(3)
    el = np.array([1.0, 2.5, 4.0])
    assert visible(az, el, hz).tolist() == [False, True, True]
    assert visible(az, el, hz, margin_deg=1.0).tolist() == [False, False, True]


def test_summary_gaps():
    m = np.array([1, 1, 0, 0, 0, 1, 1, 1, 0, 1], dtype=bool)
    s = summarise(m, step_s=3600)
    assert s["n_windows"] == 3
    assert s["longest_window_hours"] == 3.0
    assert s["longest_gap_hours"] == 3.0
