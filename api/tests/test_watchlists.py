import pytest
from tests.conftest import register_and_login


async def test_create_watchlist(client):
    headers = await register_and_login(client)
    me = (await client.get("/users/me", headers=headers)).json()
    user_id = me["id"]

    response = await client.post(
        f"/users/{user_id}/watchlists",
        json={"name": "Tech", "tickers": ["AAPL", "MSFT"]},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tech"
    assert "AAPL" in data["tickers"]
    assert "MSFT" in data["tickers"]


async def test_list_watchlists_returns_own(client):
    headers = await register_and_login(client)
    me = (await client.get("/users/me", headers=headers)).json()
    user_id = me["id"]

    await client.post(
        f"/users/{user_id}/watchlists",
        json={"name": "Tech", "tickers": ["AAPL"]},
        headers=headers,
    )

    response = await client.get(f"/users/{user_id}/watchlists", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_list_watchlists_other_user_forbidden(client):
    headers_a = await register_and_login(client, email="a@test.com", password="password123")
    headers_b = await register_and_login(client, email="b@test.com", password="password123")

    me_b = (await client.get("/users/me", headers=headers_b)).json()
    user_b_id = me_b["id"]

    response = await client.get(f"/users/{user_b_id}/watchlists", headers=headers_a)
    assert response.status_code == 403


async def test_create_watchlist_requires_auth(client):
    response = await client.post(
        "/users/1/watchlists",
        json={"name": "Tech", "tickers": ["AAPL"]},
    )
    assert response.status_code == 401
