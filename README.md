# ForecastLens

> **Live prediction-market intelligence with calibration, bias, and mispricing signals.**

ForecastLens is a premium analytics terminal for prediction markets. It unifies Polymarket, Kalshi, and Metaculus into a single normalized feed, then grades every event with calibration, drift, cross-market divergence, and an explainable confidence-adjusted signal. Traders, analysts, journalists, and forecasters get one trustworthy surface to explore probabilities, compare platforms, and spot mispricings.

![ForecastLens dashboard](public/logo.svg)

---

## Highlights

- **Unified market ingestion** across Polymarket, Kalshi, and Metaculus with a single canonical schema.
- **Calibration engine** that computes Brier score, absolute calibration error, and signed bias by source, category, and probability bucket.
- **Cross-market intelligence** including divergence, odds drift, and a composite edge score with severity-ranked alerts.
- **Confidence-adjusted signals** with human-readable explanations of *why* every event is flagged.
- **Narrative insights generator** that writes concise, judge-friendly bullets describing the most interesting findings of the day.
- **Searchable public API** with nine documented endpoints, copy-ready cURL examples, and an in-page Try-It panel.
- **Premium dark UI** inspired by financial terminals: glassmorphism cards, subtle gradients, responsive charts, rich tooltips, and skeleton states throughout.
- **Zero-setup demo** — works offline immediately with bundled sample data. No API keys required.

---

## Tech stack

| Layer     | Tools                                                                 |
|-----------|-----------------------------------------------------------------------|
| Frontend  | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Recharts, TanStack Query, Zustand, Lucide |
| Backend   | FastAPI, Pydantic, SQLAlchemy 2, SQLite, APScheduler, Python 3.11     |
| Packaging | Single Docker container, docker-compose, pnpm, pytest                 |

The entire project (frontend + backend + database) ships as **one Docker container**.

---

## Quick start

### 1. Docker (recommended, one command)

```bash
docker build -t app .
docker run -p 3000:3000 app
```

Then open [http://localhost:3000](http://localhost:3000). The container boots the FastAPI backend on `:8000`, seeds the SQLite database from bundled sample data, and serves the Next.js frontend on `:3000`. The frontend rewrites `/api/backend/*` to the backend, so everything works from one port.

### 2. docker-compose

```bash
docker compose up --build
```

### 3. Local dev

```bash
# Python deps
pip install -r requirements.txt

# Node deps
pnpm install    # or npm install

# Start the backend (auto-seeds SQLite on first run)
uvicorn src.server.main:app --host 127.0.0.1 --port 8000 --reload

# In a second shell, start the frontend
pnpm dev        # or npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

> The frontend **also falls back to bundled mock data** in the browser if the backend is unreachable, so the dashboard, events list, and alerts pages remain populated even if you only run `pnpm dev`.

---

## Environment variables

All variables are optional. See [`.env.example`](.env.example).

| Variable                   | Default                                   | Purpose                                                                |
|----------------------------|-------------------------------------------|------------------------------------------------------------------------|
| `DATABASE_URL`             | `sqlite:///./forecast_lens.db`            | SQLAlchemy connection string for the backend.                          |
| `BACKEND_URL`              | `http://127.0.0.1:8000`                   | Upstream target for the Next.js `/api/backend/*` rewrite.              |
| `NEXT_PUBLIC_BACKEND_BASE` | `/api/backend`                            | Base path used by the in-browser API client.                           |
| `ENABLE_LIVE_INGEST`       | `false`                                   | Toggles live adapters (otherwise bundled samples are used).            |
| `AUTO_SEED`                | `true`                                    | Seeds the DB on startup if empty.                                      |

---

## Project layout

```
src/
├── app/                    # Next.js 14 App Router pages
│   ├── page.tsx            # Landing dashboard
│   ├── events/             # Event explorer + detail
│   ├── calibration/        # Calibration & bias analytics
│   ├── alerts/             # Mispricing alerts feed
│   ├── api/                # Public API reference (live try-it panel)
│   └── about/              # Story + methodology + sources
├── components/             # UI components (cards, charts, table, header, ...)
│   └── ui/                 # shadcn-style primitives
├── lib/                    # api client, types, formatters, mock data
├── hooks/                  # React hooks
├── store/                  # zustand stores
└── server/                 # Python FastAPI backend
    ├── main.py             # FastAPI entrypoint + CORS + startup seeding
    ├── database.py         # SQLAlchemy engine/session
    ├── models.py           # ORM models (Source, MarketEvent, OddsSnapshot, ...)
    ├── schemas.py          # Pydantic request/response models
    ├── crud.py             # Database access helpers
    ├── routes/             # /health, /events, /metrics, /alerts, /sources, /admin
    ├── services/           # ingest, normalize, scoring, sync, narrative
    ├── scripts/            # seed_db.py, recompute_metrics.py, fetch_sources.py
    ├── data/               # sample_polymarket.json, sample_kalshi.json, sample_metaculus.json
    └── tests/              # pytest coverage for scoring, normalization, ingestion, API
```

---

## API

All endpoints are unauthenticated in demo mode. The full reference lives at [`/api`](http://localhost:3000/api) in the running app.

| Method | Path                          | Summary                                         |
|--------|-------------------------------|-------------------------------------------------|
| GET    | `/api/health`                 | Service health, DB connectivity, last sync.     |
| GET    | `/api/events`                 | Filterable, paginated event list.               |
| GET    | `/api/events/{id}`            | Event detail + history + platforms + related.   |
| GET    | `/api/events/{id}/history`    | Time-series odds snapshots.                     |
| GET    | `/api/metrics/summary`        | Dashboard summary metrics.                      |
| GET    | `/api/metrics/calibration`    | Overall + per-platform + per-category calibration. |
| GET    | `/api/metrics/insights`       | Auto-generated narrative bullets.               |
| GET    | `/api/alerts`                 | Ranked mispricing alerts.                       |
| GET    | `/api/sources`                | Data source sync status.                        |
| POST   | `/api/admin/sync`             | Trigger a fresh ingestion + rescore.            |

Example:

```bash
curl 'http://localhost:3000/api/backend/events?limit=5&sort_by=edge_score'
```

---

## Scoring methodology (summary)

1. **Ingest** raw payloads into `RawEventPayload`, then normalize into `MarketEvent` records joined by canonical slug.
2. **Compute** per-event Brier score, calibration error, and bias on resolved outcomes.
3. **Aggregate** segments by source and category, and build a 10-bucket reliability curve.
4. **Drift** = mean absolute change in probability per snapshot, squashed to `[0, 1]`.
5. **Divergence** = standard deviation of the latest probability across platforms, scaled to `[0, 1]`.
6. **Adjusted probability** = `market − (0.6·categoryBias + 0.4·sourceBias)·shrink`, then pulled toward 0.5 proportional to drift and divergence. Shrinkage is logistic in sample size.
7. **Edge score** = `0.55·|adjusted − market| + 0.25·divergence + 0.20·drift`.
8. **Severity** thresholds: `low < 0.25 < medium < 0.45 < high < 0.65 < critical`.

Every score feeds into a generated explanation, so each flagged event ships with a plain-English reason.

---

## Tests

```bash
python -m pytest src/server/tests -q
```

Covers the scoring helpers, normalization layer, ingestion pipeline, and all REST endpoints. 21 tests at the time of writing.

---

## Credits

- Built for the **Zerve AI** hackathon.
- Author: **Aryan Choudhary** — [aryancta@gmail.com](mailto:aryancta@gmail.com).
- Bundled sample event data is synthetic and illustrative; live adapters for each source are wired up but disabled by default.

ForecastLens is a research prototype; nothing here is investment advice.
