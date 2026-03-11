from __future__ import annotations

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.analysis import generate_price_aware_memo, generate_ticker_research
from app.db import Base, engine, get_db
from app.models import AnalysisRun, Portfolio, User, Watchlist, WatchlistTicker
from app.schemas import (
    AnalysisRunCreate,
    AnalysisRunOut,
    PortfolioCreate,
    PortfolioOut,
    TickerResearchCreate,
    TickerResearchOut,
    UserCreate,
    UserOut,
    WatchlistCreate,
    WatchlistOut,
)
from app.settings import settings

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup() -> None:
    # MVP: create tables automatically. Replace with Alembic migrations soon.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "app": settings.app_name, "env": settings.environment}


@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        return existing

    user = User(email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{user_id}/watchlists", response_model=list[WatchlistOut])
def list_watchlists(user_id: int, db: Session = Depends(get_db)) -> list[WatchlistOut]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [
        WatchlistOut(id=w.id, user_id=w.user_id, name=w.name, tickers=[t.symbol for t in w.tickers])
        for w in user.watchlists
    ]


@app.post("/users/{user_id}/watchlists", response_model=WatchlistOut)
def create_watchlist(user_id: int, payload: WatchlistCreate, db: Session = Depends(get_db)) -> WatchlistOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wl = Watchlist(user_id=user_id, name=payload.name)
    db.add(wl)
    db.flush()

    for symbol in payload.tickers:
        s = symbol.strip().upper()
        if not s:
            continue
        db.add(WatchlistTicker(watchlist_id=wl.id, symbol=s))

    db.commit()
    db.refresh(wl)
    return WatchlistOut(
        id=wl.id,
        user_id=wl.user_id,
        name=wl.name,
        tickers=[t.symbol for t in wl.tickers],
    )


@app.get("/users/{user_id}/portfolios", response_model=list[PortfolioOut])
def list_portfolios(user_id: int, db: Session = Depends(get_db)) -> list[Portfolio]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return list(user.portfolios)


@app.post("/users/{user_id}/portfolios", response_model=PortfolioOut)
def create_portfolio(user_id: int, payload: PortfolioCreate, db: Session = Depends(get_db)) -> Portfolio:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    p = Portfolio(user_id=user_id, name=payload.name, starting_cash=payload.starting_cash, cash=payload.starting_cash)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _run_analysis_job(*, analysis_run_id: int) -> None:
    # NOTE: In-process background task for MVP. Later: queue + dedicated worker.
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        run = db.get(AnalysisRun, analysis_run_id)
        if not run:
            return

        run.status = "running"
        db.commit()

        tickers = run.tickers
        portfolio = db.get(Portfolio, run.portfolio_id)
        memo = generate_price_aware_memo(
            db=db,
            tickers=tickers,
            starting_cash=portfolio.cash if portfolio else None,
        )

        run.memo_markdown = memo
        run.status = "succeeded"
        db.commit()
    except Exception as e:  # noqa: BLE001 (MVP: capture errors)
        run = db.get(AnalysisRun, analysis_run_id)
        if run:
            run.status = "failed"
            run.error = str(e)
            db.commit()
    finally:
        db.close()


@app.post("/analysis-runs", response_model=AnalysisRunOut)
def create_analysis_run(
    payload: AnalysisRunCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalysisRunOut:
    portfolio = db.get(Portfolio, payload.portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers: list[str] = []
    watchlist_name = "AdHoc"

    if payload.watchlist_id is not None:
        wl = db.get(Watchlist, payload.watchlist_id)
        if not wl or wl.user_id != portfolio.user_id:
            raise HTTPException(status_code=404, detail="Watchlist not found for this user")
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
    db.commit()
    db.refresh(run)

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
def list_analysis_runs(portfolio_id: int, db: Session = Depends(get_db)) -> list[AnalysisRunOut]:
    portfolio = db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.portfolio_id == portfolio_id)
        .order_by(AnalysisRun.id.desc())
        .limit(20)
        .all()
    )
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
def get_analysis_run(run_id: int, db: Session = Depends(get_db)) -> AnalysisRunOut:
    run = db.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    return AnalysisRunOut(
        id=run.id,
        portfolio_id=run.portfolio_id,
        status=run.status,
        tickers=run.tickers,
        memo_markdown=run.memo_markdown,
        error=run.error,
    )


@app.post("/ticker-research", response_model=TickerResearchOut)
def create_ticker_research(payload: TickerResearchCreate, db: Session = Depends(get_db)) -> TickerResearchOut:
    """On-demand deep-dive research for a single ticker. Runs synchronously."""
    ticker = payload.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    report = generate_ticker_research(db=db, ticker=ticker)
    return TickerResearchOut(ticker=ticker, report_markdown=report)

