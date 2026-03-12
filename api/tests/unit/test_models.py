import pytest
from app.models import AnalysisRun


def test_tickers_parses_csv():
    run = AnalysisRun(tickers_csv="AAPL,MSFT,GOOGL")
    assert run.tickers == ["AAPL", "MSFT", "GOOGL"]


def test_tickers_normalizes_whitespace_and_case():
    run = AnalysisRun(tickers_csv=" aapl , msft ")
    assert run.tickers == ["AAPL", "MSFT"]


def test_tickers_empty_string():
    run = AnalysisRun(tickers_csv="")
    assert run.tickers == []


def test_tickers_none():
    run = AnalysisRun(tickers_csv=None)
    assert run.tickers == []
