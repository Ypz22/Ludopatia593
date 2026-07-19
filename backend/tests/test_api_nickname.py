"""Integración: nickname único en registro, /me y ranking; partido en apuestas."""
from __future__ import annotations

import uuid


def _email():
    return f"n-{uuid.uuid4().hex[:8]}@test.com"


def test_register_requires_nickname(client):
    r = client.post("/v1/auth/register",
                    json={"email": _email(), "password": "Supersecret1!"})
    assert r.status_code == 422  # falta nickname


def test_register_rejects_short_or_invalid_nickname(client):
    assert client.post("/v1/auth/register", json={
        "email": _email(), "nickname": "ab", "password": "Supersecret1!"}).status_code == 422
    assert client.post("/v1/auth/register", json={
        "email": _email(), "nickname": "bad/name!", "password": "Supersecret1!"}).status_code == 422


def test_nickname_must_be_unique(client):
    nick = f"Nick{uuid.uuid4().hex[:6]}"
    assert client.post("/v1/auth/register", json={
        "email": _email(), "nickname": nick, "password": "Supersecret1!"}).status_code == 201
    # otro email, mismo nickname (aunque cambie mayúsculas) -> 409
    r = client.post("/v1/auth/register", json={
        "email": _email(), "nickname": nick.upper(), "password": "Supersecret1!"})
    assert r.status_code == 409


def test_me_exposes_nickname(client):
    nick = f"Me{uuid.uuid4().hex[:6]}"
    email = _email()
    client.post("/v1/auth/register",
                json={"email": email, "nickname": nick, "password": "Supersecret1!"})
    tok = client.post("/v1/auth/login",
                      json={"email": email, "password": "Supersecret1!"}).json()["access_token"]
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {tok}"}).json()
    assert me["nickname"] == nick


def test_leaderboard_shows_nickname_not_email(client):
    nick = f"Rank{uuid.uuid4().hex[:6]}"
    email = _email()
    client.post("/v1/auth/register",
                json={"email": email, "nickname": nick, "password": "Supersecret1!"})
    rows = client.get("/v1/leaderboard").json()
    names = [r["name"] for r in rows]
    assert nick in names
    # no se filtra el correo en claro
    assert all("@test.com" not in (r["name"] or "") for r in rows)


def test_admin_nickname_is_admin(client, admin_headers):
    me = client.get("/v1/auth/me", headers=admin_headers).json()
    assert me["nickname"] == "Admin"


def test_password_must_be_complex(client):
    weak = [
        "alllowercase1!",   # sin mayúscula
        "NoNumber!!!!",     # sin número
        "NoSpecial123",     # sin caracter especial
        "Ab1!",             # muy corta
    ]
    for pw in weak:
        r = client.post("/v1/auth/register", json={
            "email": _email(), "nickname": f"W{uuid.uuid4().hex[:6]}", "password": pw})
        assert r.status_code == 422, f"debía rechazar '{pw}'"
    # una contraseña que cumple todo -> 201
    ok = client.post("/v1/auth/register", json={
        "email": _email(), "nickname": f"Ok{uuid.uuid4().hex[:6]}", "password": "Valid1Pass!"})
    assert ok.status_code == 201


def test_bets_list_includes_match(client, user_headers, scheduled_fixture_id):
    client.post("/v1/bets", headers=user_headers, json={
        "fixture_id": scheduled_fixture_id, "market": "1x2", "selection": "home",
        "stake_points": 100, "idempotency_key": "match-col-1"})
    bets = client.get("/v1/bets", headers=user_headers).json()
    assert bets
    b = bets[0]
    assert b["home_team"] and b["away_team"]
