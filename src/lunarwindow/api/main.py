"""FastAPI entrypoint."""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from lunarwindow import METHOD_VERSION, __version__
from lunarwindow.ephemeris import kernels
from lunarwindow.ephemeris.geometry import Site
from lunarwindow.sites import compare as cmp
from lunarwindow.sites.catalog import REFERENCE_SITES

app = FastAPI(
    title="LunarWindow API",
    version=__version__,
    description=(
        "Compare lunar landing sites and dates: illumination, power potential "
        "and DTE comms windows."
    ),
)


class SiteIn(BaseModel):
    name: str
    lat_deg: float = Field(ge=-90, le=90)
    lon_deg: float = Field(ge=-180, le=360)
    elev_m: float = 0.0


class CompareIn(BaseModel):
    sites: list[SiteIn] = Field(min_length=1, max_length=20)
    start: datetime
    end: datetime
    step_s: float = Field(default=3600.0, ge=60.0, le=86400.0)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "version": __version__,
        "method_version": METHOD_VERSION,
        "kernels_present": kernels.kernels_present(),
    }


@app.get("/sites/reference")
def reference_sites() -> list[dict]:
    return [{"name": s.name, "lat_deg": s.lat_deg, "lon_deg": s.lon_deg} for s in REFERENCE_SITES]


@app.post("/compare")
def compare(body: CompareIn) -> list[dict]:
    if not kernels.kernels_present():
        raise HTTPException(503, "SPICE kernels not present on server")
    if body.end <= body.start:
        raise HTTPException(422, "end must be after start")
    kernels.load()
    sites = [Site(s.name, s.lat_deg, s.lon_deg, s.elev_m) for s in body.sites]
    return cmp.compare(sites, body.start, body.end, step_s=body.step_s)
