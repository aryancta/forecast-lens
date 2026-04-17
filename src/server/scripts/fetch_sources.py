"""Manually trigger live fetch (currently uses bundled samples; live ingestion is a stretch goal).

This script demonstrates where adapter logic for Polymarket / Kalshi / Metaculus would live.
When ENABLE_LIVE_INGEST=true and the relevant API keys are set, this could call into httpx-based
adapters to pull live event data. For the hackathon demo we always fall back to bundled samples.
"""
from __future__ import annotations

import logging

from ..config import settings
from ..database import SessionLocal, init_db
from ..services.sync import run_sync


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("ENABLE_LIVE_INGEST =", settings.enable_live_ingest)
    print("Live adapters disabled — running bundled-sample sync.")
    with SessionLocal() as db:
        result = run_sync(db, force=True)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
