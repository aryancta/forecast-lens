from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


@dataclass
class Settings:
    app_name: str = "ForecastLens API"
    version: str = "0.1.0"
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(BASE_DIR.parent.parent / 'forecast_lens.db').as_posix()}"
    )
    enable_live_ingest: bool = os.getenv("ENABLE_LIVE_INGEST", "false").lower() in {"1", "true", "yes"}
    cors_origins: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        origins = os.getenv("CORS_ORIGINS", "*")
        self.cors_origins = [o.strip() for o in origins.split(",") if o.strip()]


settings = Settings()
