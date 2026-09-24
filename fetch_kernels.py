"""Download the SPICE kernels listed in lunarwindow.ephemeris.kernels into data/kernels.

de440.bsp is ~114 MB. Run once:  uv run python scripts/fetch_kernels.py
"""

from __future__ import annotations

import sys

import httpx

from lunarwindow.config import settings
from lunarwindow.ephemeris.kernels import KERNELS


def main() -> int:
    settings.kernels_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=600, follow_redirects=True) as c:
        for name, url in KERNELS.items():
            dest = settings.kernels_dir / name
            if dest.exists() and dest.stat().st_size > 0:
                print(f"have {name}")
                continue
            print(f"fetching {name} ...", end="", flush=True)
            with c.stream("GET", url) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_bytes(1 << 20):
                        f.write(chunk)
            print(f" {dest.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
