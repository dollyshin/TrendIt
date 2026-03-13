# List available recipes (default when you run `just`)
default:
    @just --list

# ── Setup ─────────────────────────────────────────────────────────────────────

# Configure git to use the committed hooks directory
install-hooks:
    git config core.hooksPath scripts/hooks
    chmod +x scripts/hooks/pre-commit scripts/hooks/pre-push
    @echo "hooks installed"

# ── Services ──────────────────────────────────────────────────────────────────

# Start all services (db + api + web) in the background
up:
    docker compose up -d

# Stop all services and remove containers
down:
    docker compose down

# Rebuild all Docker images
build:
    docker compose build

# Restart all running services
restart:
    docker compose restart

# Show running service status
ps:
    docker compose ps

# Tail logs for all services — optionally pass a service name (e.g. just logs api)
logs service="":
    docker compose logs -f {{service}}

# ── Testing ───────────────────────────────────────────────────────────────────

# Run the backend test suite in Docker
test:
    docker compose --profile test run --rm --build test

# Run Alembic migrations inside the running API container
migrate:
    docker compose exec api alembic upgrade head

# ── Code quality ──────────────────────────────────────────────────────────────

# Lint Python (ruff) and TypeScript/JSX (eslint) — requires: pip install ruff
lint:
    ruff check api/app api/tests
    cd web && npm run lint

# Format and auto-fix Python — requires: pip install ruff
fmt:
    ruff format api/app api/tests
    ruff check --fix api/app api/tests

# ── Shells ────────────────────────────────────────────────────────────────────

# Open a psql shell in the database container
db-shell:
    docker compose exec db psql -U trendit -d trendit

# Open a bash shell in the API container
api-shell:
    docker compose exec api bash
