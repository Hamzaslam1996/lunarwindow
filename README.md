# LunarWindow

**Compare lunar south-pole landing sites and dates — Sun and Earth over the local horizon,
illumination, power potential and direct-to-Earth comms windows — in seconds, with an
assurance export for mission reviews.**

Entry to the 2026 NASA Space Apps Challenge — *CLPS Lunar Mission Browser*.

## Why

Near the Moon's south pole the Sun and Earth skim the horizon. Ridges cast kilometre-long
shadows and block the line of sight to Earth for days at a time; conditions differ between
sites a few hundred metres apart and change week to week. The tools that compute this exist but
are expert-only. LunarWindow answers the planner's question directly: *"Site A on 3 March or
Site B on 12 March — which gets more sunlight and a longer window to talk to Earth?"*

## What it computes

For each site × date window:

- Sun and Earth azimuth/elevation over time (SPICE, DE440, `MOON_ME` frame)
- the **terrain horizon mask** from a LOLA DEM (the skyline elevation in every azimuth)
- **illumination fraction** (partial solar disc), longest dark spell, mean illumination
- **relative solar-array power** (vertical / horizontal array models)
- **DTE visibility windows**, longest window, longest gap
- an **assurance export** recording kernels, DEM, method version, assumptions and code commit

## Quick start

```bash
uv sync --all-extras
uv run python scripts/fetch_kernels.py     # ~120 MB from NAIF
make check                                  # lint, types, tests (kernel tests run once kernels exist)
make api                                    # http://localhost:8000/docs
```

DEMs: LOLA polar stereographic GeoTIFFs from the PDS Geosciences Node — see `docs/data.md`.

## Method and limits

See `docs/method.md`. Results are planning aids; they are **not for flight-critical decisions**.

## Licence

Apache-2.0.
