"""Reference sites. Coordinates are approximate centroids from public NASA/LRO literature and
are for development only — the product must let users enter their own and must cite sources
per site in the evidence pack.

Artemis III candidate regions (NASA, Aug 2022 / Oct 2024 updates) and CLPS targets.
"""

from __future__ import annotations

from lunarwindow.ephemeris.geometry import Site

REFERENCE_SITES: list[Site] = [
    # Connecting Ridge between Shackleton and de Gerlache (Gläser et al. 2014 "CR1", ~1.9 km).
    Site("Shackleton Connecting Ridge", -89.45, 222.7),
    Site("Peak near Shackleton", -89.68, 196.0),
    Site("Malapert Massif", -85.99, 357.0),
    Site("Nobile Rim 1", -85.2, 36.0),
    Site("Haworth", -87.5, 354.0),
    Site("de Gerlache Rim 2", -88.3, 292.0),
    Site("Mons Mouton (Leibnitz Beta)", -84.6, 327.0),
]
