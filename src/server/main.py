from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import SessionLocal, init_db
from .routes import admin, alerts, events, health, metrics, sources
from .services.sync import run_sync


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        if os.getenv("AUTO_SEED", "true").lower() in {"1", "true", "yes"}:
            with SessionLocal() as db:
                # If empty, seed
                from .models import MarketEvent

                if db.query(MarketEvent).count() == 0:
                    logger.info("Seeding empty database with bundled samples...")
                    run_sync(db, force=True)
                else:
                    logger.info("Database already populated; skipping seed.")

    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(events.router, prefix="/api", tags=["events"])
    app.include_router(metrics.router, prefix="/api", tags=["metrics"])
    app.include_router(alerts.router, prefix="/api", tags=["alerts"])
    app.include_router(sources.router, prefix="/api", tags=["sources"])
    app.include_router(admin.router, prefix="/api", tags=["admin"])

    @app.get("/")
    def _root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.version,
            "docs": "/docs",
        }

    return app


app = create_app()
