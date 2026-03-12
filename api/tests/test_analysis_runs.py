import pytest
from unittest.mock import AsyncMock, patch
from tests.conftest import register_and_login


async def _create_user_with_portfolio(client):
    headers = await register_and_login(client)
    me = (await client.get("/users/me", headers=headers)).json()
    user_id = me["id"]
    portfolio = (
        await client.post(
            f"/users/{user_id}/portfolios", json={}, headers=headers
        )
    ).json()
    return headers, user_id, portfolio


async def test_create_analysis_run_with_tickers(client):
    headers, user_id, portfolio = await _create_user_with_portfolio(client)
    portfolio_id = portfolio["id"]

    with patch("app.main._run_analysis_job", new_callable=AsyncMock):
        response = await client.post(
            "/analysis-runs",
            json={"portfolio_id": portfolio_id, "tickers": ["AAPL", "GOOGL"]},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert set(data["tickers"]) == {"AAPL", "GOOGL"}


async def test_create_analysis_run_with_watchlist(client):
    headers, user_id, portfolio = await _create_user_with_portfolio(client)
    portfolio_id = portfolio["id"]

    watchlist = (
        await client.post(
            f"/users/{user_id}/watchlists",
            json={"name": "My Watchlist", "tickers": ["NVDA"]},
            headers=headers,
        )
    ).json()
    watchlist_id = watchlist["id"]

    with patch("app.main._run_analysis_job", new_callable=AsyncMock):
        response = await client.post(
            "/analysis-runs",
            json={"portfolio_id": portfolio_id, "watchlist_id": watchlist_id},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "NVDA" in data["tickers"]


async def test_create_analysis_run_empty_tickers(client):
    headers, user_id, portfolio = await _create_user_with_portfolio(client)
    portfolio_id = portfolio["id"]

    with patch("app.main._run_analysis_job", new_callable=AsyncMock):
        response = await client.post(
            "/analysis-runs",
            json={"portfolio_id": portfolio_id, "tickers": []},
            headers=headers,
        )

    assert response.status_code == 400


async def test_get_analysis_run(client):
    headers, user_id, portfolio = await _create_user_with_portfolio(client)
    portfolio_id = portfolio["id"]

    with patch("app.main._run_analysis_job", new_callable=AsyncMock):
        created = (
            await client.post(
                "/analysis-runs",
                json={"portfolio_id": portfolio_id, "tickers": ["AAPL", "GOOGL"]},
                headers=headers,
            )
        ).json()

    run_id = created["id"]
    response = await client.get(f"/analysis-runs/{run_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["portfolio_id"] == portfolio_id
    assert set(data["tickers"]) == {"AAPL", "GOOGL"}


async def test_get_analysis_run_other_user_forbidden(client):
    headers_a = await register_and_login(client, email="a@test.com", password="password123")
    me_a = (await client.get("/users/me", headers=headers_a)).json()
    user_a_id = me_a["id"]

    portfolio_a = (
        await client.post(
            f"/users/{user_a_id}/portfolios", json={}, headers=headers_a
        )
    ).json()
    portfolio_a_id = portfolio_a["id"]

    with patch("app.main._run_analysis_job", new_callable=AsyncMock):
        created = (
            await client.post(
                "/analysis-runs",
                json={"portfolio_id": portfolio_a_id, "tickers": ["AAPL"]},
                headers=headers_a,
            )
        ).json()

    run_id = created["id"]

    headers_b = await register_and_login(client, email="b@test.com", password="password123")
    response = await client.get(f"/analysis-runs/{run_id}", headers=headers_b)
    assert response.status_code == 403


async def test_list_analysis_runs(client):
    headers, user_id, portfolio = await _create_user_with_portfolio(client)
    portfolio_id = portfolio["id"]

    with patch("app.main._run_analysis_job", new_callable=AsyncMock):
        await client.post(
            "/analysis-runs",
            json={"portfolio_id": portfolio_id, "tickers": ["AAPL"]},
            headers=headers,
        )
        await client.post(
            "/analysis-runs",
            json={"portfolio_id": portfolio_id, "tickers": ["MSFT"]},
            headers=headers,
        )

    response = await client.get(
        f"/portfolios/{portfolio_id}/analysis-runs", headers=headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_create_analysis_run_requires_auth(client):
    response = await client.post(
        "/analysis-runs",
        json={"portfolio_id": 1, "tickers": ["AAPL"]},
    )
    assert response.status_code == 401
