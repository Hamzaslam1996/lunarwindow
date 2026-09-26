# Data sources

## SPICE kernels (NAIF) — fetched by `scripts/fetch_kernels.py`
- `naif0012.tls` leapseconds
- `pck00011.tpc` planetary constants
- `de440.bsp` planetary/lunar ephemeris
- `moon_pa_de440_200625.bpc` + `moon_de440_220930.tf` lunar orientation and `MOON_ME` / `MOON_PA` frames

## LOLA DEMs (PDS Geosciences Node, LRO LOLA RDR) — fetched by `scripts/fetch_dem.py`

Polar stereographic gridded data records (GDR) from the LRO Lunar Orbiter Laser Altimeter,
data set `LRO-L-LOLA-3-RDR-V1.0`. Projection: polar stereographic, **true at the pole**, on the
1737.4 km reference sphere (`A_AXIS_RADIUS = 1737.4 km`), MOON_ME (mean Earth / polar axis)
frame — the same frame the ephemeris uses (ADR 0001). Heights are metres above the sphere;
the PDS3 integer products store `raw × SCALING_FACTOR (0.5) + OFFSET (1737400 m)` = radius,
which `terrain/lola.py` converts back to height.

### Canonical Phase-1 product

| Field | Value |
|---|---|
| Product ID | `LDEM_875S_20M` |
| Coverage | 87.5°S → south pole (≈ 76 km radius around the pole) |
| Pixel scale | 20 m/px (true at the pole; stereographic scale factor 1.0005 at 87.5°S) |
| Format | PDS3 detached label `ldem_875s_20m.lbl` + 16-bit `ldem_875s_20m.img` (~115 MB) |
| Source | `https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/` |
| Mirror | `https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/` (LOLA team node, upper-case names) |
| Version | Read from the label at fetch time (`PRODUCT_VERSION_ID`, `PRODUCT_CREATION_TIME`) and written to `data/dem/ldem_875s_20m.provenance.json` together with URL, byte count and SHA-256. Quote those values, not this table, in the evidence pack. |

Sibling products in the same directory, same projection: `LDEM_875S_5M` (5 m/px, ~1.8 GB),
`LDEM_875S_10M`, `LDEM_80S_20M` (80°S → pole), `LDEM_75S_240M`. Pass `--product` to the
fetch script. The hosts above are not reachable from every network; download on a machine that
can reach them and copy the `.lbl`/`.img` pair into `data/dem/`.

### Higher-fidelity alternatives (Phase 2+)
NASA PGDA "High-Resolution LOLA Topography for Lunar South Pole Sites" (Barker et al. 2021,
*Planet. Space Sci.* 203, 105119): cloud-optimised GeoTIFFs `LDEM_80S_20MPP_ADJ.TIF`,
`LDEM_83S_10MPP_ADJ.TIF`, `LDEM_87S_5MPP_ADJ.TIF` and the 5 m/px landing-site tiles
(https://pgda.gsfc.nasa.gov/products/78, /products/81, /data/LOLA_5mpp/). Same projection,
DE421-consistent MOON_ME, with self-consistent crossover adjustment — better skylines, larger
files. `LolaDem.open` reads them unchanged.

Landing page: https://pds-geosciences.wustl.edu/missions/lro/lola.htm

## Basemap (frontend)
Moon Trek WMTS layers (LOLA hillshade / LROC WAC mosaic) — https://trek.nasa.gov/moon/

## Validation references
See `docs/validation.md` for the published illumination/visibility figures the engine must reproduce.
