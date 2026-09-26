# Method note (draft)

Working title: *Fast, auditable illumination and Earth-visibility assessment for lunar polar landing sites*

1. Problem — polar lighting/comms constraints; expert-only tools; what planners need
2. Geometry — SPICE DE440, MOON_ME, site vector on 1737.4 km sphere + DEM elevation + lander height; ENU frame; LT+S
3. Terrain horizon — DEM (LOLA polar stereographic), ray-marched skyline per azimuth, sphere-curvature correction, resolution effects.
   Grid → true azimuth: the raster is polar stereographic, so "up" is not north; `terrain/lola.py`
   derives the local north/east directions from the CRS numerically (for the standard products this
   is `true = grid − longitude`) and resamples the skyline onto a regular true-azimuth grid.
   Simplifications: constant pixel size along a ray (stereographic scale factor 2/(1+sin|φ|) = 1.0005
   at 87.5°S, ignored); local vertical = radial of the 1737.4 km sphere at the site; bilinear DEM
   sampling; nodata pixels are not filled.
4. Illumination — straight-edge solar-disc fraction; power models; period summaries
5. DTE visibility — Earth elevation vs skyline + antenna margin; windows/gaps
6. Comparison and ranking — metrics, user weights
7. Assurance export — provenance fields, reproducibility
8. Validation — reproduction of published figures (targets in docs/validation.md, protocol in
   ADR 0004, results in docs/validation_log.md). First entry: Fincannon 2007 Shackleton-rim
   worst lunar day 0.71 — reproduced to −0.015 at the LOLA crest with a 10 m observer, −0.20 at
   2 m, −0.48 at the paper's printed coordinates; the gap is dominated by site placement and
   observer height, then DEM generation and disc model.
   Worst-case lunar day metric: `illumination.solar.worst_window` (anchored and sliding synodic
   windows).
9. Limitations — spherical local vertical vs geoid, limb darkening, skyline curvature across the
   disc, DEM artefacts, no relay-satellite comms, no thermal model
10. Reproducibility — commit, commands, kernel and DEM versions
