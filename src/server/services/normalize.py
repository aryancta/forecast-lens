from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def normalize_event(source_name: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw event payload from any source into our canonical schema."""
    return {
        "source_event_id": str(raw.get("id") or raw.get("event_id") or raw.get("slug")),
        "title": raw.get("title", "Untitled event"),
        "slug": raw.get("slug") or raw.get("id") or "untitled",
        "description": raw.get("description", ""),
        "category": (raw.get("category") or "other").lower(),
        "status": (raw.get("status") or "active").lower(),
        "url": raw.get("url", ""),
        "resolution_date": _parse_dt(raw.get("resolution_date")),
        "current_probability": float(raw.get("current_probability") or raw.get("probability") or 0.5),
        "outcome": raw.get("outcome"),
        "volume": float(raw.get("volume") or 0.0),
        "liquidity": float(raw.get("liquidity") or 0.0),
        "history_days": int(raw.get("history_days") or 14),
        "drift_intensity": float(raw.get("drift_intensity") or 0.05),
        "final_market_probability": raw.get("final_market_probability"),
        "source_name": source_name,
    }
