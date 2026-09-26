"""End-to-end smoke test of scripts/plot_horizon.py on a synthetic DEM (no real data needed)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from tests.test_lola import N, _write

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "plot_horizon.py"


def test_plot_horizon_script_writes_png_and_json(tmp_path: Path):
    data = np.zeros((N, N))
    data[:, 300:] = 200.0  # plateau "north" of a site at lon 90°
    dem = tmp_path / "synthetic.tif"
    _write(dem, data)
    out = tmp_path / "figures"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--dem",
        str(dem),
        "--lat",
        "-89.95",
        "--lon",
        "90",
        "--name",
        "Synthetic Test Site",
        "--height",
        "0",
        "--n-az",
        "90",
        "--range-km",
        "6",
        "--out",
        str(out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    png = out / "synthetic_test_site_horizon.png"
    js = out / "synthetic_test_site_horizon.json"
    assert png.exists() and png.stat().st_size > 10_000
    rec = json.loads(js.read_text())
    assert rec["dem"]["product_id"] == "SYNTHETIC_875S_20M"
    assert rec["horizon"]["n_az"] == 90
    assert abs(rec["horizon"]["max_elevation_azimuth_deg"] - 0.0) < 1e-9  # plateau is due north
    assert rec["horizon"]["max_elevation_deg"] > 20.0
    assert "not for flight-critical" in rec["notice"]


def test_plot_horizon_script_missing_dem(tmp_path: Path):
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--dem", str(tmp_path / "nope.lbl"), "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode != 0
    assert "fetch_dem.py" in res.stderr
