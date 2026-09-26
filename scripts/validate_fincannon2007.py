"""Validation: worst-case lunar-day average illumination at the Shackleton rim vs Fincannon 2007.

Reference: J. Fincannon, "Lunar South Pole Illumination: Review, Reassessment, and Power System
Implications", NASA/TM-2007-215025 (NTRS 20070034951), AIAA 2007-4700. Using the 2006 Goldstone
(GSSR) radar DEM (40 m/px), the "main site under consideration ... on the Crater Shackleton rim"
has, for the worst-case lunar day, an average illumination fraction of 0.71 (0.73 in the 2008
follow-up, NTRS 20080018474). The paper places the sites at (approximate, east longitude):
Site A1 Shackleton rim ~89.8°S 213°E (1.9 km), Site A2 ~89.9°S 237°E, Site A3 ~89.9°S 301°E,
Site B "connecting ridge" ~89.4°S 233°E (1.9 km), B being 13 km from A1.

This script evaluates the same sites on the LOLA LDEM_875S_20M DEM with `sites.compare.evaluate`
and reports the worst lunar-day average, plus the best point within a small neighbourhood of the
stated coordinates (the 2006 radar DEM's control differs from LOLA by hundreds of metres, and the
paper quotes coordinates to 0.1°, i.e. ~3 km).

Usage:
  uv run python scripts/validate_fincannon2007.py                    # A1, 2024-2026, 0 m and 2 m
  uv run python scripts/validate_fincannon2007.py --sites A1 B --heights 0 2 10 --years 2025
Writes docs/validation/fincannon2007.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

from lunarwindow import METHOD_VERSION
from lunarwindow.ephemeris import geometry as geo
from lunarwindow.ephemeris import kernels
from lunarwindow.illumination import solar
from lunarwindow.sites import compare
from lunarwindow.terrain.lola import LolaDem, default_dem_path

REFERENCE = {
    "citation": "Fincannon, J. (2007). Lunar South Pole Illumination: Review, Reassessment, and "
    "Power System Implications. NASA/TM-2007-215025; NTRS 20070034951; AIAA 2007-4700.",
    "dem": "2006 Goldstone Solar System Radar (GSSR) DEM, 40 m horizontal resolution, "
    "~5 m relative vertical accuracy, filtered",
    "metric": "average illumination fraction over the worst-case lunar day",
    "value": 0.71,
    "value_2008_followup": 0.73,
    "observer_height_m": "not stated in the accessible abstract; evaluated here at several heights",
    "period": "not stated in the accessible abstract; worst-case lunar day, any year",
}

SITES: dict[str, tuple[str, float, float]] = {
    # id: (name, lat_deg, lon_deg east)
    "A1": ("Fincannon Site A1 - Shackleton rim", -89.8, 213.0),
    "A2": ("Fincannon Site A2 - Shackleton rim", -89.9, 237.0),
    "A3": ("Fincannon Site A3 - Shackleton rim", -89.9, 301.0),
    "B": ("Fincannon Site B - connecting ridge", -89.4, 233.0),
}


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def illumination_series(
    dem: LolaDem, lat: float, lon: float, height_m: float, ets: np.ndarray, n_az: int
) -> tuple[np.ndarray, geo.Site]:
    hz = dem.horizon(lon, lat, height_m=height_m, n_az=n_az)
    elev = float(dem.elevation_at(lon, lat)[0])
    site = geo.Site("probe", lat, lon, elev_m=elev, height_m=height_m)
    az, el, dist = geo.sun_az_el(site, ets)
    frac = solar.illumination_fraction(az, el, geo.sun_angular_radius_deg(dist), hz)
    return frac, site


def neighbourhood(dem: LolaDem, lat: float, lon: float, radius_m: float, step_m: float):
    """(lon, lat, dx, dy) for a square grid of offsets in the DEM's projected metres."""
    x0, y0 = dem.lonlat_to_xy(lon, lat)
    offs = np.arange(-radius_m, radius_m + step_m / 2, step_m)
    out = []
    for dy in offs:
        for dx in offs:
            if dx * dx + dy * dy > radius_m * radius_m + 1e-6:
                continue
            lo, la = dem.xy_to_lonlat(x0[0] + dx, y0[0] + dy)
            out.append((float(lo[0]), float(la[0]), float(dx), float(dy)))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--sites", nargs="+", default=["A1"], choices=sorted(SITES))
    ap.add_argument("--heights", nargs="+", type=float, default=[0.0, 2.0])
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025, 2026])
    ap.add_argument("--step-h", type=float, default=1.0)
    ap.add_argument("--n-az", type=int, default=720)
    ap.add_argument("--search-radius-m", type=float, default=1000.0, help="0 disables the search")
    ap.add_argument("--search-step-m", type=float, default=250.0)
    ap.add_argument("--dem", type=Path, default=default_dem_path())
    ap.add_argument("--out", type=Path, default=Path("docs/validation/fincannon2007.json"))
    args = ap.parse_args(argv)

    kernels.load()
    dem = LolaDem.open(args.dem)
    step_s = args.step_h * 3600.0
    start = datetime(min(args.years), 1, 1, tzinfo=UTC)
    end = datetime(max(args.years) + 1, 1, 1, tzinfo=UTC)
    ets = geo.et_range(start, end, step_s)
    t0 = start

    def when(i: int) -> str:
        return (t0 + timedelta(seconds=i * step_s)).strftime("%Y-%m-%d")

    results: list[dict] = []
    for sid in args.sites:
        name, lat, lon = SITES[sid]
        for h in args.heights:
            print(f"\n== {sid} {name} ({lat}, {lon}E) observer {h:g} m ==")
            frac, site = illumination_series(dem, lat, lon, h, ets, args.n_az)
            i_anch, worst_anch = solar.worst_window(frac, step_s)
            i_slide, worst_slide = solar.worst_window(frac, step_s, sliding=True)
            n = int(round(solar.SYNODIC_MONTH_S / step_s))
            # Independent check through the product path: evaluate() over the worst window.
            w_start = t0 + timedelta(seconds=i_anch * step_s)
            w_end = t0 + timedelta(seconds=(i_anch + n - 1) * step_s)
            hz = dem.horizon(lon, lat, height_m=h, n_az=args.n_az)
            ev = compare.evaluate(
                geo.Site(name, lat, lon, elev_m=site.elev_m, height_m=h),
                w_start,
                w_end,
                step_s=step_s,
                horizon=hz,
            )
            entry = {
                "site_id": sid,
                "site": name,
                "lat_deg": lat,
                "lon_deg": lon,
                "terrain_elev_m": site.elev_m,
                "observer_height_m": h,
                "period": f"{start:%Y-%m-%d} to {end:%Y-%m-%d}",
                "step_s": step_s,
                "mean_illumination_whole_period": float(frac.mean()),
                "worst_lunar_day_anchored": {
                    "mean": worst_anch,
                    "start": when(i_anch),
                    "evaluate_mean_illumination": ev.illumination["mean_illumination"],
                    "evaluate_longest_dark_hours": ev.illumination["longest_dark_hours"],
                },
                "worst_lunar_day_sliding": {"mean": worst_slide, "start": when(i_slide)},
                "lunar_day_means": [round(float(m), 4) for m in solar.window_means(frac, step_s)],
                "residual_vs_0.71_anchored": worst_anch - REFERENCE["value"],
                "residual_vs_0.71_sliding": worst_slide - REFERENCE["value"],
                "evaluate_result": asdict(ev),
            }
            print(
                f"  whole-period mean {frac.mean():.3f} | worst lunar day (anchored) "
                f"{worst_anch:.3f} from {when(i_anch)} | worst sliding {worst_slide:.3f} "
                f"from {when(i_slide)} | evaluate() {ev.illumination['mean_illumination']:.3f}"
            )

            if args.search_radius_m > 0:
                best = None
                grid = neighbourhood(dem, lat, lon, args.search_radius_m, args.search_step_m)
                print(f"  searching {len(grid)} points within {args.search_radius_m:g} m ...")
                for lo, la, dx, dy in grid:
                    f2, _ = illumination_series(dem, la, lo, h, ets, max(180, args.n_az // 2))
                    _, w2 = solar.worst_window(f2, step_s)
                    if best is None or w2 > best["worst_lunar_day_anchored_mean"]:
                        best = {
                            "lat_deg": la,
                            "lon_deg": lo,
                            "offset_east_m": dx,
                            "offset_north_m": dy,
                            "terrain_elev_m": float(dem.elevation_at(lo, la)[0]),
                            "worst_lunar_day_anchored_mean": float(w2),
                            "mean_illumination_whole_period": float(f2.mean()),
                        }
                assert best is not None
                entry["best_within_search_radius"] = best
                entry["residual_vs_0.71_best_point"] = (
                    best["worst_lunar_day_anchored_mean"] - REFERENCE["value"]
                )
                print(
                    f"  best point within {args.search_radius_m:g} m: worst lunar day "
                    f"{best['worst_lunar_day_anchored_mean']:.3f} at ({best['lat_deg']:.4f}, "
                    f"{best['lon_deg']:.4f}) offset E {best['offset_east_m']:+.0f} m "
                    f"N {best['offset_north_m']:+.0f} m"
                )
            results.append(entry)

    record = {
        "reference": REFERENCE,
        "ours": {
            "dem": {"product_id": dem.product_id, "file": dem.path.name, "pixel_m": dem.pixel_m},
            "kernels": kernels.loaded_kernel_names(),
            "n_az": args.n_az,
            "max_range_km": 100.0,
            "disc_model": "uniform disc, straight-edge skyline, apparent radius from Sun distance",
            "aberration": geo.ABCORR,
            "frame": geo.FRAME,
            "method_version": METHOD_VERSION,
            "commit": git_commit(),
            "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1) + "\n")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
