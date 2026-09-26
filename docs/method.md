# Method note (draft)

Working title: *Fast, auditable illumination and Earth-visibility assessment for lunar polar landing sites*

1. Problem — polar lighting/comms constraints; expert-only tools; what planners need
2. Geometry — SPICE DE440, MOON_ME, site vector on 1737.4 km sphere + DEM elevation + lander height; ENU frame; LT+S
3. Terrain horizon — DEM (LOLA polar stereographic), ray-marched skyline per azimuth, sphere-curvature correction, resolution effects
4. Illumination — straight-edge solar-disc fraction; power models; period summaries
5. DTE visibility — Earth elevation vs skyline + antenna margin; windows/gaps
6. Comparison and ranking — metrics, user weights
7. Assurance export — provenance fields, reproducibility
8. Validation — reproduction of published figures (docs/validation.md)
9. Limitations — spherical local vertical vs geoid, limb darkening, skyline curvature across the
   disc, DEM artefacts, no relay-satellite comms, no thermal model
10. Reproducibility — commit, commands, kernel and DEM versions
