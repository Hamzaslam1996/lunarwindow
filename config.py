"""Runtime settings. Nothing secret; paths only."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    kernels_dir: Path = Path("data/kernels")
    dem_dir: Path = Path("data/dem")
    moon_radius_km: float = 1737.4  # IAU mean radius; LOLA DEMs are referenced to this sphere
    sun_angular_radius_deg: float = 0.2665  # at 1 AU; refined per-epoch in illumination.solar
    lander_height_m: float = 2.0  # height of solar array / antenna above local terrain


settings = Settings()
