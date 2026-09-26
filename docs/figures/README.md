# Figures

Generated outputs; each `*_horizon.png` has a sibling `*_horizon.json` carrying the mask and
its provenance (DEM product, site, observer height, ray settings, method version, commit).

Regenerate the Phase-1 horizon mask for Shackleton Connecting Ridge:

```bash
uv run python scripts/fetch_dem.py          # LDEM_875S_20M into data/dem/ (once)
uv run python scripts/plot_horizon.py       # → shackleton_connecting_ridge_horizon.{png,json}
```

Other sites: `--site "Malapert"`, or `--lat/--lon/--name`. Figures are planning aids, not for
flight-critical decisions.
