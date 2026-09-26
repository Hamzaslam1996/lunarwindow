# Roadmap

| Phase | Dates | Deliverable |
|---|---|---|
| 1 Foundations | now → 5 Oct | Kernels fetched; kernel tests green; LOLA south-pole DEM loaded (`terrain/lola.py`); first horizon mask for Shackleton Connecting Ridge; one validation reproduction logged |
| 2 Engine | 6–27 Oct | DEM projection + true-azimuth handling; horizon cache; site × date comparison + ranking; API; method note draft; ADRs |
| 3 Product | 28 Oct – 13 Nov | Full statement; frontend (site picker on Moon basemap, date range, comparison table, sky-dome/horizon plot, timeline); assurance export; deployment; demo script |
| 4 Ship | 14–15 Nov | Clean repo, live URL, 2-min video, submission |

## Definition of "shipping grade"
- CI green on every commit (lint, types, tests incl. kernel tests)
- At least two published figures reproduced and logged in `docs/validation_log.md`
- Reproducible from a clean clone: `uv sync && python scripts/fetch_kernels.py && make api`
- Every output carries provenance; UI and exports carry the "not for flight-critical decisions" notice
- Live deployment with health check and uptime monitor
- `docs/method.md` matches the code and states limitations
