from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analysis import generate_price_aware_memo, generate_ticker_research
from app.db import async_session_factory, get_db
from app.models import AnalysisRun, Portfolio, User, Watchlist, WatchlistTicker
from app.schemas import (
    AnalysisRunCreate,
    AnalysisRunOut,
    PortfolioCreate,
    PortfolioOut,
    TickerResearchCreate,
    TickerResearchOut,
    UserCreate,
    UserRead,
    UserUpdate,
    WatchlistCreate,
    WatchlistOut,
)
from app.settings import settings
from app.users import auth_backend, current_active_user, fastapi_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


# ── Auth & user routes (FastAPI Users) ────────────────────────────────────────

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"ok": True, "app": settings.app_name, "env": settings.environment}


# ── Watchlists ────────────────────────────────────────────────────────────────

@app.get("/users/{user_id}/watchlists", response_model=list[WatchlistOut])
async def list_watchlists(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> list[WatchlistOut]:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == user_id)
        .options(selectinload(Watchlist.tickers))
    )
    watchlists = result.scalars().all()
    return [
        WatchlistOut(id=w.id, user_id=w.user_id, name=w.name, tickers=[t.symbol for t in w.tickers])
        for w in watchlists
    ]


@app.post("/users/{user_id}/watchlists", response_model=WatchlistOut)
async def create_watchlist(
    user_id: int,
    payload: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> WatchlistOut:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    wl = Watchlist(user_id=user_id, name=payload.name)
    db.add(wl)
    await db.flush()

    for symbol in payload.tickers:
        s = symbol.strip().upper()
        if not s:
            continue
        db.add(WatchlistTicker(watchlist_id=wl.id, symbol=s))

    await db.commit()

    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == wl.id)
        .options(selectinload(Watchlist.tickers))
    )
    wl = result.scalar_one()
    return WatchlistOut(
        id=wl.id,
        user_id=wl.user_id,
        name=wl.name,
        tickers=[t.symbol for t in wl.tickers],
    )


# ── Portfolios ────────────────────────────────────────────────────────────────

@app.get("/users/{user_id}/portfolios", response_model=list[PortfolioOut])
async def list_portfolios(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> list[PortfolioOut]:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
    return list(result.scalars().all())


@app.post("/users/{user_id}/portfolios", response_model=PortfolioOut)
async def create_portfolio(
    user_id: int,
    payload: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> Portfolio:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    p = Portfolio(user_id=user_id, name=payload.name, starting_cash=payload.starting_cash, cash=payload.starting_cash)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


# ── Analysis runs ─────────────────────────────────────────────────────────────

async def _run_analysis_job(*, analysis_run_id: int) -> None:
    # NOTE: In-process background task for MVP. Later: queue + dedicated worker.
    async with async_session_factory() as db:
        run = await db.get(AnalysisRun, analysis_run_id)
        if not run:
            return

        run.status = "running"
        await db.commit()

        try:
            tickers = run.tickers
            portfolio = await db.get(Portfolio, run.portfolio_id)
            memo = await generate_price_aware_memo(
                db=db,
                tickers=tickers,
                starting_cash=portfolio.cash if portfolio else None,
            )
            run.memo_markdown = memo
            run.status = "succeeded"
            await db.commit()
        except Exception as e:  # noqa: BLE001
            run = await db.get(AnalysisRun, analysis_run_id)
            if run:
                run.status = "failed"
                run.error = str(e)
                await db.commit()


@app.post("/analysis-runs", response_model=AnalysisRunOut)
async def create_analysis_run(
    payload: AnalysisRunCreate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> AnalysisRunOut:
    portfolio = await db.get(Portfolio, payload.portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    tickers: list[str] = []
    watchlist_name = "AdHoc"

    if payload.watchlist_id is not None:
        wl = await db.get(Watchlist, payload.watchlist_id)
        if not wl or wl.user_id != portfolio.user_id:
            raise HTTPException(status_code=404, detail="Watchlist not found for this user")
        result = await db.execute(
            select(Watchlist).where(Watchlist.id == wl.id).options(selectinload(Watchlist.tickers))
        )
        wl = result.scalar_one()
        watchlist_name = wl.name
        tickers = [t.symbol for t in wl.tickers]

    if payload.tickers is not None:
        tickers = [t.strip().upper() for t in payload.tickers if t.strip()]
        watchlist_name = "AdHoc"

    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers provided (watchlist empty or tickers not set)")

    run = AnalysisRun(
        portfolio_id=portfolio.id,
        status="queued",
        watchlist_name=watchlist_name,
        tickers_csv=",".join(tickers),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background.add_task(_run_analysis_job, analysis_run_id=run.id)

    return AnalysisRunOut(
        id=run.id,
        portfolio_id=run.portfolio_id,
        status=run.status,
        tickers=tickers,
        memo_markdown=run.memo_markdown,
        error=run.error,
    )


@app.get("/portfolios/{portfolio_id}/analysis-runs", response_model=list[AnalysisRunOut])
async def list_analysis_runs(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> list[AnalysisRunOut]:
    portfolio = await db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.portfolio_id == portfolio_id)
        .order_by(AnalysisRun.id.desc())
        .limit(20)
    )
    runs = result.scalars().all()
    return [
        AnalysisRunOut(
            id=r.id,
            portfolio_id=r.portfolio_id,
            status=r.status,
            tickers=r.tickers,
            memo_markdown=r.memo_markdown,
            error=r.error,
        )
        for r in runs
    ]


@app.get("/analysis-runs/{run_id}", response_model=AnalysisRunOut)
async def get_analysis_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> AnalysisRunOut:
    run = await db.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    portfolio = await db.get(Portfolio, run.portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return AnalysisRunOut(
        id=run.id,
        portfolio_id=run.portfolio_id,
        status=run.status,
        tickers=run.tickers,
        memo_markdown=run.memo_markdown,
        error=run.error,
    )


# ── Ticker research ───────────────────────────────────────────────────────────

@app.post("/ticker-research", response_model=TickerResearchOut)
async def create_ticker_research(
    payload: TickerResearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
) -> TickerResearchOut:
    """On-demand deep-dive research for a single ticker. Runs synchronously."""
    ticker = payload.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    report = await generate_ticker_research(db=db, ticker=ticker)
    return TickerResearchOut(ticker=ticker, report_markdown=report)
