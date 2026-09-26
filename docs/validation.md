# Validation targets

The engine is not credible until it reproduces published numbers. Targets (add exact figures and
citations as they are extracted from the papers):

1. **Shackleton crater rim worst-case lunar-day average illumination** — Fincannon, J. (2007),
   *Lunar South Pole Illumination: Review, Reassessment, and Power System Implications*,
   NASA/TM-2007-215025, NTRS 20070034951 (AIAA 2007-4700). Using the 2006 Goldstone radar DEM
   (40 m/px), "the main site under consideration by present lunar mission planners (on the Crater
   Shackleton rim)" has a **0.71** average illumination fraction for the worst-case lunar day
   (0.73 in the 2008 follow-up, NTRS 20080018474). Sites as stated in the paper (approximate,
   east longitude): A1 Shackleton rim ~89.8°S 213°E (1.9 km); B "connecting ridge" ~89.4°S 233°E
   (1.9 km), 13 km from A1. Observer height and analysis year are not given in the accessible
   abstract. Protocol: ADR 0004; run `scripts/validate_fincannon2007.py`; result logged in
   `docs/validation_log.md`. Later LOLA-based studies (Mazarico et al. 2011; Gläser et al. 2014)
   give per-site values with tighter tolerances — next targets.
2. **Pole geometry sanity** — Sun elevation at the exact pole stays within ±~1.6°; Earth
   elevation librates within ±~7–8° (tests/test_geometry_kernels.py).
3. **NASA SVS "Illumination at the Moon's South Pole, 2023 to 2030"** — qualitative agreement of
   lit/dark timing at the pole for a chosen month.
4. **ESA/Astrium ICAT Connecting Ridge study (De Rosa et al. 2012)** — longest continuous
   illumination period at 2 m height for a chosen year.

Record each reproduction in `docs/validation_log.md` with commit hash, DEM, settings and residuals.
