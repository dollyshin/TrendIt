from tests.conftest import register_and_login


async def test_register_success(client):
    response = await client.post(
        "/auth/register",
        json={"email": "user@test.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@test.com"
    assert "hashed_password" not in data


async def test_register_duplicate_email(client):
    payload = {"email": "user@test.com", "password": "password123"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400


async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={"email": "user@test.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/jwt/login",
        data={"username": "user@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "user@test.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/jwt/login",
        data={"username": "user@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 400


async def test_protected_route_requires_auth(client):
    response = await client.get("/users/1/watchlists")
    assert response.status_code == 401
