# ADR 0004 — Validation protocol against published illumination figures

Status: accepted · Date: 2026-09-26

## Context

CLAUDE.md requires every geometry change to reproduce at least one published number. Published
polar-illumination studies differ in DEM (radar vs LOLA), observer height, time period, "lunar
day" definition and solar-disc treatment, and often state site coordinates only to 0.1° (≈3 km
at 89.8°S). A reproduction therefore has to state its own conventions and separate "we disagree"
from "we evaluated a different point".

## Decision

1. **Lunar day** = one mean synodic month, 29.530589 d. The *anchored* worst lunar day is the
   minimum mean illumination over consecutive non-overlapping windows starting at the period
   start (`illumination.solar.window_means`); the *sliding* worst lunar day considers every
   start step and is reported alongside as a lower bound (`solar.worst_window(sliding=True)`).
   Papers rarely state their anchoring, so both bracket the published value.
2. **Period**: three full years at 1 h steps unless the paper states its own (the Sun's
   declination cycle at the poles repeats every 18.6 yr; three years capture the seasonal
   worst case without that cycle's extremes). The period used is recorded in the log.
3. **Observer height**: evaluate at the paper's stated height; if unstated, at 0 m, 2 m and 10 m
   and report all three. Height above terrain near a ridge crest moves the worst-day mean by
   several percentage points, so it is never silently assumed.
4. **Coordinates**: evaluate the stated coordinates *and* the best point within a stated search
   radius (default 1 km, 250 m grid) on our DEM. Radar-era DEMs (GSSR 2006) and the paper's
   0.1° rounding place sites hundreds of metres from the LOLA crest; the best-point value
   tests whether *a* point in the described location behaves as published, the stated-point
   value tests our literal reading of the paper. Both go in the log.
5. **Independent path**: the worst window found by the scan is re-evaluated through the product
   path `sites.compare.evaluate(..., horizon=dem.horizon(...))`, and that number is the one
   quoted as "ours". The two must agree to < 0.005 or the run is invalid.
6. **Residual and reasons**: the log records published value, ours, residual (ours − published)
   and an explicit list of candidate reasons (DEM product and resolution, observer height,
   coordinate offset, disc model, ephemeris, period/anchoring). Tolerance for "reproduced" is
   ±0.05 in worst-lunar-day mean illumination for radar-DEM references and ±0.02 for LOLA-based
   references, provisional until more references are logged.

## Consequences

`docs/validation_log.md` gains one entry per reproduction with commit, DEM, kernels, settings and
residuals; `scripts/validate_*.py` regenerate them. Tighter tolerances and per-site cited
coordinates follow once LOLA-based references (Mazarico et al. 2011, Gläser et al. 2014) are
reproduced.
