# Data sources

## SPICE kernels (NAIF) — fetched by `scripts/fetch_kernels.py`
- `naif0012.tls` leapseconds
- `pck00011.tpc` planetary constants
- `de440.bsp` planetary/lunar ephemeris
- `moon_pa_de440_200625.bpc` + `moon_de440_220930.tf` lunar orientation and `MOON_ME` / `MOON_PA` frames

## LOLA DEMs (PDS Geosciences Node, LRO LOLA RDR)
Polar stereographic GeoTIFFs, referenced to the 1737.4 km sphere. For south-pole work use the
polar products (e.g. 5 m/px, 10 m/px, 20 m/px, 60 m/px tiles covering 85°S–90°S), and the
LOLA+SfS blended products where available for finer skyline detail.
Download manually (large) into `data/dem/` and record product ID, version and resolution in the
evidence pack. Landing page: https://pds-geosciences.wustl.edu/missions/lro/lola.htm

## Basemap (frontend)
Moon Trek WMTS layers (LOLA hillshade / LROC WAC mosaic) — https://trek.nasa.gov/moon/

## Validation references
See `docs/validation.md` for the published illumination/visibility figures the engine must reproduce.
