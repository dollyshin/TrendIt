# TrendIt

Investment portfolio analysis app. Users manage watchlists and portfolios and
trigger AI-powered analysis runs that fetch price data and produce research memos.

## Stack

- **Backend:** FastAPI + async SQLAlchemy 2.0 + asyncpg + FastAPI Users v13 (JWT)
- **Frontend:** Next.js 14 (TypeScript)
- **DB:** PostgreSQL 17 (Docker)
- **Tasks:** `just` — run `just` to list all commands

## Non-obvious rules

**`type_annotation_map` handles datetime timezone globally** — `Base` in
`app/db.py` maps `dt.datetime → DateTime(timezone=True)`. Never add
`DateTime(timezone=True)` inside a `mapped_column()` call; it overrides the
map instead of inheriting it.

**Test event loop scope must stay `function`** — `asyncio_default_fixture_loop_scope = function`
in `pytest.ini` is intentional. Session scope causes asyncpg "Future attached
to a different loop" errors. Each test gets a fresh `drop_all` + `create_all`.

**`pg_terminate_backend` before `drop_all` in test setup** — stale connections
from crashed test runs hold locks and cause `drop_all` to hang indefinitely.
This is why `conftest.py` terminates connections before each test fixture runs.

