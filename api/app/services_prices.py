from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alpha_vantage import alpha_vantage_client
from app.models import DailyPrice


def _parse_daily_adjusted(symbol: str, payload: dict[str, Any]) -> list[DailyPrice]:
    key = next((k for k in payload.keys() if "Time Series" in k), None)
    if not key:
        raise RuntimeError("Unexpected Alpha Vantage daily payload shape")
    series: dict[str, dict[str, str]] = payload[key]

    out: list[DailyPrice] = []
    for date_str, values in series.items():
        date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        out.append(
            DailyPrice(
                symbol=symbol,
                date=date,
                open=float(values.get("1. open", 0.0)),
                high=float(values.get("2. high", 0.0)),
                low=float(values.get("3. low", 0.0)),
                close=float(values.get("4. close", 0.0)),
                adjusted_close=float(values.get("5. adjusted close", values.get("4. close", 0.0))),
                volume=float(values.get("6. volume", 0.0)),
            )
        )
    # Sort ascending by date for convenience
    out.sort(key=lambda p: p.date)
    return out


def ensure_daily_prices(db: Session, symbol: str, *, min_days: int = 60) -> list[DailyPrice]:
    """Return at least `min_days` of daily prices, fetching from Alpha Vantage if needed."""
    symbol = symbol.upper()
    existing = db.scalars(
        select(DailyPrice).where(DailyPrice.symbol == symbol).order_by(DailyPrice.date.asc())
    ).all()

    if len(existing) >= min_days:
        return existing

    # Fetch from Alpha Vantage (compact: ~100 most recent trading days)
    payload = alpha_vantage_client.get_daily_adjusted(symbol=symbol, outputsize="compact")
    rows = _parse_daily_adjusted(symbol, payload)

    # Upsert naïvely: rely on unique constraint to avoid duplicates on re-fetch
    for row in rows:
        db.merge(row)
    db.commit()

    return db.scalars(
        select(DailyPrice).where(DailyPrice.symbol == symbol).order_by(DailyPrice.date.asc())
    ).all()


def latest_snapshot(db: Session, symbol: str) -> dict[str, Any]:
    """Return a simple snapshot for the analysis memo."""
    prices = ensure_daily_prices(db, symbol, min_days=60)
    if not prices:
        raise RuntimeError(f"No price data for {symbol}")

    latest = prices[-1]
    first = prices[0]

    pct_change = 0.0
    if first.adjusted_close:
        pct_change = (latest.adjusted_close / first.adjusted_close - 1.0) * 100.0

    # Simple rolling volatility proxy: last 20 days
    tail = prices[-20:] if len(prices) >= 20 else prices
    closes = [p.adjusted_close for p in tail]
    avg = sum(closes) / len(closes)
    variance = sum((c - avg) ** 2 for c in closes) / len(closes)
    vol = variance**0.5

    return {
        "symbol": symbol.upper(),
        "latest_date": latest.date.isoformat(),
        "latest_close": latest.adjusted_close,
        "period_days": (latest.date - first.date).days or 1,
        "period_pct_change": pct_change,
        "recent_volatility": vol,
    }

