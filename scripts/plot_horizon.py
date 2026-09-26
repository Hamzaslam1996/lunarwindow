"""Plot the terrain horizon mask for a site from a LOLA polar DEM.

Writes ``docs/figures/<slug>_horizon.png`` (polar sky-dome + azimuth profile) and
``docs/figures/<slug>_horizon.json`` (the mask plus provenance: DEM product, site, observer
height, ray settings, method version, code commit).

Usage:
  uv run python scripts/plot_horizon.py                          # Shackleton Connecting Ridge
  uv run python scripts/plot_horizon.py --site "Malapert"
  uv run python scripts/plot_horizon.py --lat -89.45 --lon 222.7 --name "my site"
  uv run python scripts/plot_horizon.py --dem data/dem/ldem_875s_5m.lbl --height 2 --n-az 720
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from lunarwindow import METHOD_VERSION  # noqa: E402
from lunarwindow.config import settings  # noqa: E402
from lunarwindow.sites.catalog import REFERENCE_SITES  # noqa: E402
from lunarwindow.terrain.lola import LolaDem, default_dem_path  # noqa: E402

# Chart ink (light surface). Two series: skyline (blue) and the Sun's elevation band (orange).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SKYLINE = "#2a78d6"
SUN = "#eb6834"

#: Sun's maximum elevation at the poles ≈ obliquity of the lunar spin axis to the ecliptic.
SUN_BAND_DEG = 1.54 + 0.27  # centre band + apparent solar radius → upper limb


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # noqa: BLE001 - provenance is best-effort
        return "unknown"


def pick_site(args: argparse.Namespace) -> tuple[str, float, float]:
    if args.lat is not None and args.lon is not None:
        return args.name or f"{args.lat:.3f}, {args.lon:.3f}", args.lat, args.lon
    matches = [s for s in REFERENCE_SITES if args.site.lower() in s.name.lower()]
    if len(matches) != 1:
        names = ", ".join(s.name for s in REFERENCE_SITES)
        raise SystemExit(
            f"--site {args.site!r} matched {len(matches)} sites; choose one of: {names}"
        )
    s = matches[0]
    return s.name, s.lat_deg, s.lon_deg


def render(
    out_png: Path,
    az: np.ndarray,
    el: np.ndarray,
    *,
    title: str,
    subtitle: str,
    footer: str,
) -> None:
    fig = plt.figure(figsize=(12, 6.0), facecolor=SURFACE)
    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.0, 1.6], wspace=0.25, left=0.05, right=0.98, top=0.80, bottom=0.2
    )

    # --- polar sky-dome zoomed to the horizon: sky at the centre, terrain around the rim.
    # Radius r = ZOOM_TOP - elevation, so elevation ZOOM_TOP sits at the centre and -5° at the rim.
    zoom_top = max(10.0, float(np.ceil(np.nanmax(el))) + 1.0)
    zoom_bottom = -5.0
    axp = fig.add_subplot(gs[0, 0], projection="polar", facecolor=SURFACE)
    axp.set_theta_zero_location("N")
    axp.set_theta_direction(-1)
    theta = np.radians(np.append(az, az[0] + 360.0))
    el_c = np.clip(np.append(el, el[0]), zoom_bottom, zoom_top)
    r_sky = zoom_top - el_c
    r_rim = zoom_top - zoom_bottom
    axp.fill_between(theta, r_sky, r_rim, color=SKYLINE, alpha=0.18, linewidth=0)
    axp.plot(theta, r_sky, color=SKYLINE, lw=2.0)
    axp.fill_between(
        theta, zoom_top - SUN_BAND_DEG, zoom_top + SUN_BAND_DEG, color=SUN, alpha=0.25, linewidth=0
    )
    axp.plot(theta, np.full_like(theta, zoom_top), color=MUTED, lw=1.0, ls=(0, (3, 3)))
    axp.set_rlim(0.0, r_rim)
    tick_el = [e for e in (zoom_top - 5.0, 5.0, 0.0) if 0.0 <= zoom_top - e < r_rim]
    axp.set_rticks([zoom_top - e for e in tick_el])
    axp.set_yticklabels([f"{e:g}°" for e in tick_el], color=MUTED, fontsize=8)
    axp.set_rlabel_position(22.5)
    axp.set_xticks(np.radians([0, 90, 180, 270]))
    axp.set_xticklabels(["N", "E", "S", "W"], color=INK_2, fontsize=9)
    axp.grid(color=GRID, lw=0.8)
    axp.spines["polar"].set_color(GRID)
    axp.text(
        0.5,
        -0.14,
        f"Sky dome near the horizon: zenith direction at the centre ({zoom_top:g}°), "
        f"{zoom_bottom:g}° at the rim",
        transform=axp.transAxes,
        ha="center",
        va="top",
        color=INK_2,
        fontsize=8,
        wrap=True,
    )

    # --- azimuth profile
    ax = fig.add_subplot(gs[0, 1], facecolor=SURFACE)
    lo = min(-3.0, float(np.nanmin(el)) - 0.5)
    hi = max(4.0, float(np.nanmax(el)) * 1.12 + 0.5)
    ax.fill_between(az, lo, el, color=SKYLINE, alpha=0.18, linewidth=0, label="_nolegend_")
    ax.plot(az, el, color=SKYLINE, lw=2.0, label="Terrain skyline (LOLA DEM)")
    ax.axhspan(
        -SUN_BAND_DEG,
        SUN_BAND_DEG,
        color=SUN,
        alpha=0.25,
        lw=0,
        label="Sun elevation range at the pole (±1.8°, upper limb)",
    )
    ax.axhline(0.0, color=MUTED, lw=1.0, ls=(0, (3, 3)))
    imax = int(np.argmax(el))
    ax.plot([az[imax]], [el[imax]], "o", ms=5, color=SKYLINE, mec=SURFACE, mew=1.5)
    ax.text(
        0.99,
        0.97,
        f"skyline max {el[imax]:.2f}° at azimuth {az[imax]:.0f}°",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=INK_2,
        bbox={"boxstyle": "round,pad=0.3", "fc": SURFACE, "ec": GRID, "lw": 0.8},
    )
    ax.set_xlim(0, 360)
    ax.set_xticks([0, 45, 90, 135, 180, 225, 270, 315, 360])
    ax.set_xticklabels(["0° N", "45", "90° E", "135", "180° S", "225", "270° W", "315", "360"])
    ax.set_ylim(lo, hi)
    ax.set_xlabel("True azimuth (degrees, clockwise from lunar north)", color=INK_2, fontsize=9)
    ax.set_ylabel("Elevation above local horizontal (degrees)", color=INK_2, fontsize=9)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(color=GRID, lw=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        frameon=False,
        fontsize=8,
        labelcolor=INK_2,
    )

    fig.text(0.05, 0.955, title, color=INK, fontsize=13, fontweight="bold", va="top")
    fig.text(0.05, 0.895, subtitle, color=INK_2, fontsize=9, va="top")
    fig.text(0.05, 0.03, footer, color=MUTED, fontsize=7.5)
    fig.savefig(out_png, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--site", default="Connecting Ridge", help="substring of a reference-site name")
    ap.add_argument("--lat", type=float, help="override latitude (deg)")
    ap.add_argument("--lon", type=float, help="override east longitude (deg)")
    ap.add_argument("--name", help="label for --lat/--lon sites")
    ap.add_argument("--dem", type=Path, default=default_dem_path(), help="PDS .lbl or GeoTIFF")
    ap.add_argument(
        "--height", type=float, default=settings.lander_height_m, help="observer height (m)"
    )
    ap.add_argument("--n-az", type=int, default=720)
    ap.add_argument("--range-km", type=float, default=100.0)
    ap.add_argument("--out", type=Path, default=Path("docs/figures"))
    args = ap.parse_args(argv)

    if not args.dem.exists():
        raise SystemExit(
            f"DEM not found: {args.dem}\nfetch it with: uv run python scripts/fetch_dem.py"
        )

    name, lat, lon = pick_site(args)
    dem = LolaDem.open(args.dem)
    elev = float(dem.elevation_at(lon, lat)[0])
    mask = dem.horizon(
        lon, lat, height_m=args.height, n_az=args.n_az, max_range_m=args.range_km * 1000.0
    )

    args.out.mkdir(parents=True, exist_ok=True)
    slug = slugify(name)
    out_png = args.out / f"{slug}_horizon.png"
    out_json = args.out / f"{slug}_horizon.json"
    commit = git_commit()

    title = f"Terrain horizon — {name}"
    subtitle = (
        f"{abs(lat):.3f}°{'S' if lat < 0 else 'N'}, {lon:.3f}°E · terrain {elev:,.0f} m · observer "
        f"{args.height:g} m above terrain · DEM {dem.product_id} ({dem.pixel_m:g} m/px) · "
        f"{args.n_az} azimuths, {args.range_km:g} km range"
    )
    footer = (
        f"LunarWindow method {METHOD_VERSION} · commit {commit} · {dem.path.name} · "
        f"{datetime.now(UTC):%Y-%m-%d} · spherical local vertical, bilinear DEM sampling · "
        "planning aid, not for flight-critical decisions"
    )
    render(
        out_png,
        mask.azimuths_deg,
        mask.elevations_deg,
        title=title,
        subtitle=subtitle,
        footer=footer,
    )

    record = {
        "site": {"name": name, "lat_deg": lat, "lon_deg": lon, "terrain_elev_m": elev},
        "observer_height_m": args.height,
        "dem": {
            "product_id": dem.product_id,
            "file": dem.path.name,
            "pixel_m": dem.pixel_m,
            "crs": dem.crs.to_string(),
            "nodata_fraction": dem.nodata_fraction,
        },
        "horizon": {
            "n_az": args.n_az,
            "max_range_km": args.range_km,
            "azimuth_convention": "true, degrees clockwise from lunar north",
            "azimuths_deg": [round(float(a), 4) for a in mask.azimuths_deg],
            "elevations_deg": [round(float(e), 4) for e in mask.elevations_deg],
            "max_elevation_deg": float(mask.elevations_deg.max()),
            "max_elevation_azimuth_deg": float(
                mask.azimuths_deg[int(np.argmax(mask.elevations_deg))]
            ),
        },
        "method_version": METHOD_VERSION,
        "commit": commit,
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "notice": "Planning aid; not for flight-critical decisions.",
    }
    out_json.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote {out_png}\nwrote {out_json}")
    hz = record["horizon"]
    assert isinstance(hz, dict)
    print(
        f"skyline max {hz['max_elevation_deg']:.2f}° at az {hz['max_elevation_azimuth_deg']:.0f}°"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
