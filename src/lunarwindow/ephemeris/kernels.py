"""SPICE kernel manifest and loader.

Kernels are fetched with `scripts/fetch_kernels.py` from NAIF; they are not committed.
Frame: MOON_ME (mean Earth/polar axis) from the DE440 lunar PCK — the frame LOLA products use.
"""

from __future__ import annotations

from pathlib import Path

import spiceypy as spice

from lunarwindow.config import settings

NAIF = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels"

KERNELS: dict[str, str] = {
    # leapseconds
    "naif0012.tls": f"{NAIF}/lsk/naif0012.tls",
    # planetary constants (radii etc.)
    "pck00011.tpc": f"{NAIF}/pck/pck00011.tpc",
    # planetary ephemeris (Sun, Earth, Moon barycentres) 1550–2650
    "de440.bsp": f"{NAIF}/spk/planets/de440.bsp",
    # lunar orientation (DE440-consistent) and frame definitions
    "moon_pa_de440_200625.bpc": f"{NAIF}/pck/moon_pa_de440_200625.bpc",
    "moon_de440_250416.tf": f"{NAIF}/fk/satellites/moon_de440_250416.tf",
}


def kernel_paths(directory: Path | None = None) -> list[Path]:
    d = directory or settings.kernels_dir
    return [d / name for name in KERNELS]


def kernels_present(directory: Path | None = None) -> bool:
    return all(p.exists() for p in kernel_paths(directory))


def load(directory: Path | None = None) -> None:
    """Furnish all kernels. Idempotent enough for tests (clears first)."""
    if not kernels_present(directory):
        missing = [p.name for p in kernel_paths(directory) if not p.exists()]
        raise FileNotFoundError(
            f"missing SPICE kernels {missing}; run `uv run python scripts/fetch_kernels.py`"
        )
    spice.kclear()
    for p in kernel_paths(directory):
        spice.furnsh(str(p))


def loaded_kernel_names() -> list[str]:
    n = spice.ktotal("ALL")
    return [Path(spice.kdata(i, "ALL")[0]).name for i in range(n)]
