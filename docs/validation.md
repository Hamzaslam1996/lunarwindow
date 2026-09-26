# Validation targets

The engine is not credible until it reproduces published numbers. Targets (add exact figures and
citations as they are extracted from the papers):

1. **Shackleton crater rim ("Connecting Ridge") worst-case lunar-day average illumination** —
   NASA Glenn review (Fincannon, NTRS 20070034951) reports ≈0.71 for the worst lunar day using the
   radar DEM; later LOLA-based studies (Mazarico et al. 2011; Gläser et al. 2014) give per-site
   values. Reproduce within a stated tolerance and explain differences (DEM, observer height).
2. **Pole geometry sanity** — Sun elevation at the exact pole stays within ±~1.6°; Earth
   elevation librates within ±~7–8° (tests/test_geometry_kernels.py).
3. **NASA SVS "Illumination at the Moon's South Pole, 2023 to 2030"** — qualitative agreement of
   lit/dark timing at the pole for a chosen month.
4. **ESA/Astrium ICAT Connecting Ridge study (De Rosa et al. 2012)** — longest continuous
   illumination period at 2 m height for a chosen year.

Record each reproduction in `docs/validation_log.md` with commit hash, DEM, settings and residuals.
