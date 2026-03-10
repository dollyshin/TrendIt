from __future__ import annotations

from typing import Any

import httpx

from app.settings import settings


class AlphaVantageClient:
    """Thin client for Alpha Vantage price data.

    Free tier has strict rate limits (5 calls/min, 500/day). In MVP we:
    - fetch only what we need per manual analysis run
    - add a simple caching layer in the database on top of this client
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.alpha_vantage_api_key
        self.base_url = settings.alpha_vantage_base_url

    def _require_key(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "Alpha Vantage API key is not set. "
                "Set ALPHA_VANTAGE_API_KEY (or alpha_vantage_api_key in .env)."
            )

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        self._require_key()
        merged = {"apikey": self.api_key, **params}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(self.base_url, params=merged)
            resp.raise_for_status()
            data = resp.json()
        if "Error Message" in data:
            raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
        if "Note" in data:
            # Usually a rate-limit warning; surface it clearly.
            raise RuntimeError(f"Alpha Vantage note: {data['Note']}")
        return data

    def get_daily_adjusted(self, symbol: str, outputsize: str = "compact") -> dict[str, Any]:
        """Fetch daily adjusted OHLCV for a symbol."""
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": outputsize,
            "datatype": "json",
        }
        return self._get(params)

    def get_global_quote(self, symbol: str) -> dict[str, Any]:
        """Fetch the latest quote (last trade, change, etc.)."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "datatype": "json",
        }
        return self._get(params)


alpha_vantage_client = AlphaVantageClient()

