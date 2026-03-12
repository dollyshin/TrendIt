# List available recipes (default when you run `just`)
default:
    @just --list

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

# ── Shells ────────────────────────────────────────────────────────────────────

# Open a psql shell in the database container
db-shell:
    docker compose exec db psql -U trendit -d trendit

# Open a bash shell in the API container
api-shell:
    docker compose exec api bash
