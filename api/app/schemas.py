from __future__ import annotations

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class PortfolioCreate(BaseModel):
    name: str = "Main"
    starting_cash: float = Field(default=10000.0, ge=0)


class PortfolioOut(BaseModel):
    id: int
    user_id: int
    name: str
    starting_cash: float
    cash: float

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str = "Default"
    tickers: list[str] = Field(default_factory=list)


class WatchlistOut(BaseModel):
    id: int
    user_id: int
    name: str
    tickers: list[str]

    class Config:
        from_attributes = True


class AnalysisRunCreate(BaseModel):
    portfolio_id: int
    watchlist_id: int | None = None
    tickers: list[str] | None = None


class AnalysisRunOut(BaseModel):
    id: int
    portfolio_id: int
    status: str
    tickers: list[str]
    memo_markdown: str | None = None
    error: str | None = None

    class Config:
        from_attributes = True


class TickerResearchCreate(BaseModel):
    ticker: str


class TickerResearchOut(BaseModel):
    ticker: str
    report_markdown: str

