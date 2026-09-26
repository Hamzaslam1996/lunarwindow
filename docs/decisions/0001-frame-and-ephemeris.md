# ADR 0001 — Reference frame and ephemeris

Status: accepted · Date: 2026-09-24

Use DE440 with the DE440-consistent lunar orientation kernel and the `MOON_ME` frame. LOLA
products are in the mean-Earth/polar-axis system, so DEM coordinates and ephemeris agree without
transformation. Apparent positions use `LT+S`. Reference sphere 1737.4 km; DEM heights added.
