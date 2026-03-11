from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services_prices import latest_snapshot


SYSTEM_PROMPT = """You are an investment analyst for a paper-trading simulation. Your role is to write a concise daily memo that:
1. Summarizes the price and volatility data for each ticker.
2. Provides brief reasoning on whether to buy, sell, or hold each position (swing/investing horizon, not day trading).
3. Stays grounded in the data provided—do not invent facts or cite sources you don't have.
4. Uses markdown formatting. Include a "## Per-ticker analysis" section with a subsection for each ticker, and a "## Summary" with overall stance and risks.
5. Clearly states this is for educational/paper-trading purposes only, not investment advice."""


async def _gather_snapshots(db: AsyncSession, tickers: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (successful snapshots, error messages for failed tickers)."""
    snapshots: list[dict[str, Any]] = []
    errors: list[str] = []
    for symbol in tickers:
        try:
            snap = await latest_snapshot(db, symbol)
            snapshots.append(snap)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{symbol}: {e}")
    return snapshots, errors


def _build_context(snapshots: list[dict[str, Any]], starting_cash: float | None) -> str:
    lines = [
        "Portfolio context:",
        f"- Starting cash: {starting_cash if starting_cash is not None else 'unknown'} USD",
        "",
        "Per-ticker data (Alpha Vantage, daily adjusted close):",
    ]
    for s in snapshots:
        lines.append(
            f"- {s['symbol']}: latest close {s['latest_date']} = {s['latest_close']:.2f}; "
            f"change over {s['period_days']} days = {s['period_pct_change']:.2f}%; "
            f"20d volatility (stddev) = {s['recent_volatility']:.4f}"
        )
    return "\n".join(lines)


async def generate_price_aware_memo(
    *,
    db: AsyncSession,
    tickers: list[str],
    starting_cash: float | None = None,
) -> str:
    """Generate a memo using Alpha Vantage data. Uses LLM if API key is set, else a simple template."""

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    snapshots, errors = await _gather_snapshots(db, tickers)

    if not snapshots:
        return (
            "# TrendIt Analysis Memo\n\n"
            f"**Generated**: {now}\n\n"
            "## Error\nNo price data could be fetched. "
            + ("Errors: " + "; ".join(errors) if errors else "Check ticker symbols and Alpha Vantage API key.")
        )

    try:
        from app.llm import get_llm_client

        client = get_llm_client()
        if client:
            context = _build_context(snapshots, starting_cash)
            user_prompt = (
                f"Write a daily analysis memo for the following watchlist. "
                f"Data as of {now} UTC.\n\n{context}"
            )
            if errors:
                user_prompt += f"\n\nNote: Some tickers failed to fetch: {'; '.join(errors)}"
            # LLM client is sync — run in thread to avoid blocking the event loop
            raw = await asyncio.to_thread(client.complete, system=SYSTEM_PROMPT, user=user_prompt)
            return f"# TrendIt Analysis Memo\n\n**Generated**: {now}\n\n{raw}"
    except Exception:  # noqa: BLE001
        pass

    # Fallback: template memo without LLM
    lines: list[str] = []
    lines.append("# TrendIt Analysis Memo")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append("")
    lines.append("## Investment style")
    lines.append("- This simulation is designed for **swing / investing** time horizons, not day trading.")
    lines.append("- Uses **daily** data and narrative analysis; it is not real-time.")
    lines.append("")
    lines.append("## Portfolio context")
    lines.append(f"- Starting cash: `{starting_cash if starting_cash is not None else 'unknown'}`")
    lines.append("")
    lines.append("## Per-ticker snapshots (Alpha Vantage)")

    for snap in snapshots:
        lines.append(f"### {snap['symbol']}")
        lines.append(f"- Latest close ({snap['latest_date']}): `{snap['latest_close']:.2f}`")
        lines.append(
            f"- Change over last {snap['period_days']} days: "
            f"`{snap['period_pct_change']:.2f}%` (adjusted close)"
        )
        lines.append(
            "- Recent volatility (20d stddev of adjusted close): "
            f"`{snap['recent_volatility']:.4f}`"
        )
        lines.append("")

    if errors:
        lines.append("## Fetch errors")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")

    lines.append("## Notes")
    lines.append(
        "- Set LLM_API_KEY and LLM_PROVIDER (openai|anthropic) in .env for AI-generated narrative. "
        "Otherwise this memo uses template output."
    )
    return "\n".join(lines)


TICKER_RESEARCH_SYSTEM_PROMPT = """You are an investment analyst for a paper-trading simulation. The user wants a deep-dive research report on a single stock ticker.

Your report must:
1. Summarize the price and volatility data provided.
2. Provide a clear conclusion: "Is this currently a good price to buy?" with a short answer (Yes / No / Neutral) and brief reasoning.
3. List key assumptions and risks.
4. Stay grounded in the data provided—do not invent facts or cite sources you don't have.
5. Use markdown. Include: ## Data summary, ## Analysis, ## Conclusion (with explicit buy/hold/avoid stance), ## Risks and assumptions.
6. State this is for educational/paper-trading only, not investment advice."""


async def generate_ticker_research(*, db: AsyncSession, ticker: str) -> str:
    """Generate an on-demand deep-dive research report for a single ticker."""
    symbol = ticker.strip().upper()
    if not symbol:
        return "# Ticker Research\n\nError: No ticker provided."

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    try:
        snap = await latest_snapshot(db, symbol)
    except Exception as e:  # noqa: BLE001
        return (
            f"# Ticker Research: {symbol}\n\n"
            f"**Generated**: {now}\n\n"
            f"## Error\nCould not fetch price data: {e}"
        )

    context = (
        f"Ticker: {snap['symbol']}\n"
        f"Latest close ({snap['latest_date']}): {snap['latest_close']:.2f}\n"
        f"Change over {snap['period_days']} days: {snap['period_pct_change']:.2f}%\n"
        f"20d volatility (stddev): {snap['recent_volatility']:.4f}"
    )

    try:
        from app.llm import get_llm_client

        client = get_llm_client()
        if client:
            user_prompt = f"Write a research report for {symbol}. Data as of {now} UTC:\n\n{context}"
            raw = await asyncio.to_thread(client.complete, system=TICKER_RESEARCH_SYSTEM_PROMPT, user=user_prompt)
            return f"# Ticker Research: {symbol}\n\n**Generated**: {now}\n\n{raw}"
    except Exception:  # noqa: BLE001
        pass

    return (
        f"# Ticker Research: {symbol}\n\n"
        f"**Generated**: {now}\n\n"
        f"## Data summary\n"
        f"- Latest close ({snap['latest_date']}): `{snap['latest_close']:.2f}`\n"
        f"- Change over {snap['period_days']} days: `{snap['period_pct_change']:.2f}%`\n"
        f"- 20d volatility: `{snap['recent_volatility']:.4f}`\n\n"
        f"## Notes\nSet LLM_API_KEY for AI-generated analysis and buy/hold conclusion."
    )
