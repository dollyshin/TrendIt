# TrendIt API - pinned Python + dependencies for consistent builds
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ ./app/

# Data directory for SQLite (persisted via volume)
RUN mkdir -p /app/data

EXPOSE 8000

# Default: SQLite in /app/data (override via DATABASE_URL)
ENV DATABASE_URL=sqlite:////app/data/trendit.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
