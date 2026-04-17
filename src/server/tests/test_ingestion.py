from __future__ import annotations

import os
import tempfile

import pytest


@pytest.fixture()
def temp_db(monkeypatch):
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp.name}")
    # Reload modules so they pick up the new env var.
    import importlib

    import src.server.config as config_mod
    import src.server.database as db_mod
    import src.server.models as models_mod
    import src.server.crud as crud_mod
    import src.server.services.ingest as ingest_mod
    import src.server.services.sync as sync_mod

    importlib.reload(config_mod)
    importlib.reload(db_mod)
    importlib.reload(models_mod)
    importlib.reload(crud_mod)
    importlib.reload(ingest_mod)
    importlib.reload(sync_mod)

    yield db_mod
    os.unlink(tmp.name)


def test_ingest_runs(temp_db):
    import src.server.services.ingest as ingest_mod

    db_mod = temp_db
    db_mod.init_db()
    with db_mod.SessionLocal() as db:
        result = ingest_mod.ingest_all(db)

    assert result["sources"] == 3
    assert result["events"] > 0


def test_ingest_creates_alerts_and_metrics(temp_db):
    import src.server.crud as crud_mod
    import src.server.services.ingest as ingest_mod

    db_mod = temp_db
    db_mod.init_db()
    with db_mod.SessionLocal() as db:
        ingest_mod.ingest_all(db)
        events, total = crud_mod.list_events(db, page=1, limit=100)
        summary = crud_mod.summary_metrics(db)

    assert total > 0
    assert summary["sources"] == 3
    assert summary["total_events"] == total
