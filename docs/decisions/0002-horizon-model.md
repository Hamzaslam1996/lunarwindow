# ADR 0002 — Horizon (skyline) model

Status: accepted (v0) · Date: 2026-09-24

Ray-march the DEM in N azimuths (default 360, step half a pixel, range 100 km) from the observer
at `height_m` above terrain; skyline = max elevation angle after subtracting the spherical
curvature drop. Local vertical is the radial of the reference sphere (not the geoid). Limitation:
skyline treated as straight across the solar disc. Alternative (rejected for now): full
visibility raster rendering; heavier, no planning benefit at this stage.
