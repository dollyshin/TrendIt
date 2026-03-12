import pytest
from tests.conftest import register_and_login


async def test_create_portfolio(client):
    headers = await register_and_login(client)
    me = (await client.get("/users/me", headers=headers)).json()
    user_id = me["id"]

    response = await client.post(
        f"/users/{user_id}/portfolios",
        json={"name": "My Portfolio", "starting_cash": 5000.0},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Portfolio"
    assert data["starting_cash"] == pytest.approx(5000.0)
    assert data["cash"] == pytest.approx(5000.0)


async def test_list_portfolios_returns_own(client):
    headers = await register_and_login(client)
    me = (await client.get("/users/me", headers=headers)).json()
    user_id = me["id"]

    await client.post(
        f"/users/{user_id}/portfolios",
        json={"name": "My Portfolio", "starting_cash": 5000.0},
        headers=headers,
    )

    response = await client.get(f"/users/{user_id}/portfolios", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_list_portfolios_other_user_forbidden(client):
    headers_a = await register_and_login(client, email="a@test.com", password="password123")
    headers_b = await register_and_login(client, email="b@test.com", password="password123")

    me_b = (await client.get("/users/me", headers=headers_b)).json()
    user_b_id = me_b["id"]

    response = await client.get(f"/users/{user_b_id}/portfolios", headers=headers_a)
    assert response.status_code == 403


async def test_create_portfolio_requires_auth(client):
    response = await client.post(
        "/users/1/portfolios",
        json={"name": "My Portfolio", "starting_cash": 5000.0},
    )
    assert response.status_code == 401
