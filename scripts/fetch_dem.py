"""Download a LOLA GDR polar-stereographic DEM tile into data/dem.

Default product: LDEM_875S_20M — LRO LOLA gridded DEM, south polar stereographic (true at the
pole, reference sphere 1737.4 km, MOON_ME frame), 87.5°S to the pole, 20 m/px. PDS3 detached
label (``.lbl``) plus 16-bit ``.img``; rasterio opens the ``.lbl`` through GDAL's PDS driver.

Sources (same product, same bytes):
  pds  https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/
  mit  https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/          (LOLA team node; upper-case names)

Usage:
  uv run python scripts/fetch_dem.py                      # LDEM_875S_20M from PDS (~115 MB)
  uv run python scripts/fetch_dem.py --source mit
  uv run python scripts/fetch_dem.py --product LDEM_875S_5M   # 5 m/px, ~1.8 GB

After download the label's PRODUCT_ID / PRODUCT_VERSION_ID / MAP_SCALE / LINES / LINE_SAMPLES
are printed and written, with the URL and SHA-256, to ``data/dem/<product>.provenance.json``
for the assurance export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from lunarwindow.config import settings
from lunarwindow.terrain.lola import DEFAULT_DEM_PRODUCT

SOURCES: dict[str, tuple[str, str]] = {
    # name: (base URL, filename case)
    "pds": (
        "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/",
        "lower",
    ),
    "mit": ("https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/", "upper"),
}

LABEL_KEYS = (
    "PRODUCT_ID",
    "PRODUCT_VERSION_ID",
    "DATA_SET_ID",
    "PRODUCT_CREATION_TIME",
    "MAP_PROJECTION_TYPE",
    "MAP_SCALE",
    "MAP_RESOLUTION",
    "A_AXIS_RADIUS",
    "MINIMUM_LATITUDE",
    "MAXIMUM_LATITUDE",
    "CENTER_LATITUDE",
    "CENTER_LONGITUDE",
    "LINES",
    "LINE_SAMPLES",
    "SCALING_FACTOR",
    "OFFSET",
    "COORDINATE_SYSTEM_NAME",
)


def _url(source: str, product: str, ext: str) -> str:
    base, case = SOURCES[source]
    name = f"{product}.{ext}"
    name = name.lower() if case == "lower" else name.upper()
    return base + name


def _download(client: httpx.Client, url: str, dest: Path) -> str:
    """Stream `url` to `dest`; return the SHA-256 hex digest."""
    h = hashlib.sha256()
    tmp = dest.with_suffix(dest.suffix + ".part")
    with client.stream("GET", url) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
                h.update(chunk)
                done += len(chunk)
                if total:
                    print(
                        f"\r  {dest.name}: {done / 1e6:8.1f} / {total / 1e6:.1f} MB",
                        end="",
                        flush=True,
                    )
        print()
    tmp.replace(dest)
    return h.hexdigest()


def parse_label(text: str) -> dict[str, str]:
    """Pull the interesting PDS3 keywords out of a detached label."""
    out: dict[str, str] = {}
    for key in LABEL_KEYS:
        m = re.search(rf"^\s*{key}\s*=\s*(.+?)\s*$", text, flags=re.MULTILINE)
        if m:
            out[key] = m.group(1).strip().strip('"')
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--product", default=DEFAULT_DEM_PRODUCT, help="LOLA GDR polar product ID")
    ap.add_argument("--source", choices=sorted(SOURCES), default="pds")
    ap.add_argument("--dest", type=Path, default=settings.dem_dir)
    ap.add_argument("--force", action="store_true", help="re-download even if files exist")
    args = ap.parse_args(argv)

    product = args.product.upper()
    args.dest.mkdir(parents=True, exist_ok=True)
    lbl = args.dest / f"{product.lower()}.lbl"
    img = args.dest / f"{product.lower()}.img"

    prov: dict[str, object] = {
        "product": product,
        "source": args.source,
        "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "files": {},
    }
    with httpx.Client(timeout=httpx.Timeout(60.0, read=600.0), follow_redirects=True) as c:
        for ext, dest in (("lbl", lbl), ("img", img)):
            url = _url(args.source, product, ext)
            if dest.exists() and dest.stat().st_size > 0 and not args.force:
                print(f"have {dest}")
                digest = hashlib.sha256(dest.read_bytes()).hexdigest() if ext == "lbl" else None
            else:
                print(f"fetching {url}")
                digest = _download(c, url, dest)
            files = prov["files"]
            assert isinstance(files, dict)
            files[dest.name] = {"url": url, "bytes": dest.stat().st_size, "sha256": digest}

    meta = parse_label(lbl.read_text(errors="replace"))
    prov["label"] = meta
    print("label:")
    for k, v in meta.items():
        print(f"  {k:24s} {v}")
    if meta.get("MAP_PROJECTION_TYPE", "").upper().replace('"', "") not in {
        "POLAR STEREOGRAPHIC",
        "POLAR_STEREOGRAPHIC",
    }:
        print("warning: label is not a polar stereographic product", file=sys.stderr)

    out = args.dest / f"{product.lower()}.provenance.json"
    out.write_text(json.dumps(prov, indent=2) + "\n")
    print(f"wrote {out}")
    print(f"open with: LolaDem.open({str(lbl)!r})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
