# LunarWindow — Claude Code project instructions

## What this is
Solo entry to the 2026 NASA Space Apps Challenge, challenge **"CLPS Lunar Mission Browser"**.
Hackathon: 14–15 Nov 2026. Full challenge statement: 28 Oct 2026 — re-read `docs/challenge.md` then.

Goal: an intuitive web tool that lets mission planners, educators and the public **compare lunar
south-pole landing sites and dates** — Sun and Earth positions relative to the *local terrain
horizon*, illumination fraction, solar-power potential, and direct-to-Earth (DTE) communication
windows — with an **assurance export** (assumptions, kernels, DEM, method version, commit) for mission reviews.

## Non-negotiables
- **Licence: Apache-2.0** (Space Apps terms require OSI open source). No proprietary code.
- **No commercial promotion in the submission** — pricing and business material live outside this repo.
- **Physics honesty.** State every model simplification in `docs/method.md` (spherical local
  vertical, straight-edge skyline across the solar disc, no limb darkening, DEM resolution limits).
  Results are planning aids, *not for flight-critical decisions* — say so in the UI and exports.
- **Provenance on every output:** kernel names, DEM product ID + resolution, method version,
  site coordinates + elevation source, time step, code commit.
- **Validate before feature work.** Every geometry change must keep `tests/test_geometry_kernels.py`
  green and must reproduce at least one published number (see `docs/validation.md`).
- **Large data stays out of git.** `data/kernels`, `data/dem` are gitignored. Kernels: `scripts/fetch_kernels.py`.

## Stack
- Python 3.11, `uv`, `src/` layout. SPICE via `spiceypy` (frame `MOON_ME`, DE440 + moon_pa_de440).
- Terrain: LOLA polar DEMs (GeoTIFF, polar stereographic) via `rasterio`.
- Backend: FastAPI. Precompute horizon masks per site and cache (Parquet/JSON).
- Frontend (Phase 3): `frontend/` Next.js + a Moon basemap (Moon Trek WMTS / LOLA hillshade) +
  timeline charts. Keep it simple: site list, date range, comparison table, sky-dome plot.
- Tests: pytest. Geometry tests that need kernels are auto-skipped when kernels are absent.
- Lint: ruff + mypy. `make check` before every commit.

## Package layout
```
src/lunarwindow/
  config.py         paths and physical constants
  ephemeris/        kernels.py (manifest/loader), geometry.py (site frame, Sun/Earth az-el)
  terrain/          horizon.py (skyline from DEM); lola.py (DEM loading, projection, TODO)
  illumination/     solar.py (disc fraction, illumination summary, power models)
  comms/            dte.py (Earth visibility windows)
  sites/            catalog.py (reference sites), compare.py (site × window evaluation)
  evidence/         provenance capture + assurance export (TODO Phase 3)
  api/              FastAPI routers
```

## Physics facts to respect
- Lunar axial tilt to the ecliptic ≈ 1.54°: at the poles the Sun never rises above ~1.6°.
  Terrain, not the Sun's altitude, decides illumination. The horizon mask is the product.
- Earth as seen from the pole moves ±~7° in elevation (libration); DTE gaps of days per month are normal.
- Solar disc ≈ 0.53° across → partial illumination matters; illumination is a fraction, not a boolean.
- Lander height above terrain (default 2 m) materially changes results near ridges. Expose it.
- Use light-time + stellar aberration (`LT+S`) for apparent positions.

## Working conventions
- Conventional Commits; small PRs to `main`; CI must be green.
- Scientific choices get an ADR in `docs/decisions/` — pick the conservative option when unsure.
- Keep `docs/method.md` in sync with the code; it becomes the published method note.
- Canonical development sites: Shackleton Connecting Ridge, Malapert Massif, Mons Mouton
  (Artemis III / CLPS targets; coordinates in `sites/catalog.py` are approximate and must be cited).

## Phases
1. **Foundations (→ 5 Oct):** kernels fetched, kernel tests green, LOLA DEM tile loaded, first
   horizon mask for Shackleton rim, validation against a published illumination figure.
2. **Engine (6–27 Oct):** DEM projection handling, horizon cache, site × date comparison, ranking,
   API endpoints, method note draft, ADRs.
3. **Product (28 Oct–13 Nov):** full statement; frontend; assurance export; deployment; demo script.
4. **Ship (14–15 Nov):** clean repo, live URL, 2-min video, submission.
