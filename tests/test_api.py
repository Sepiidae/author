"""End-to-end API tests using an in-memory SQLite database.

The DATABASE_URL override must happen *before* app.database is imported (the
engine/session are built at import time).
"""
import os

os.environ["BOOK_AUTHOR_CONFIG"] = "config.yaml"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["AI_API_KEY"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

ADMIN = {"email": "admin@example.com", "password": "changeme123"}


def _auth(payload):
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_first_user_is_admin_and_login():
    token = _auth(ADMIN)
    me = client.get("/auth/me", headers=_headers(token)).json()
    assert me["email"] == ADMIN["email"]
    assert me["is_admin"] is True
    # second user is not admin
    r2 = client.post("/auth/register", json={"email": "b@example.com", "password": "changeme123"})
    assert r2.status_code == 201
    me2 = client.get("/auth/me", headers=_headers(r2.json()["access_token"])).json()
    assert me2["is_admin"] is False


def test_duplicate_registration_conflicts():
    client.post("/auth/register", json={"email": "dup@example.com", "password": "changeme123"})
    r = client.post("/auth/register", json={"email": "dup@example.com", "password": "changeme123"})
    assert r.status_code == 409


def test_bad_login():
    r = client.post("/auth/login", json={"email": "nope@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_unauthenticated_is_rejected():
    assert client.get("/content/universes").status_code == 401


def test_full_content_flow():
    token = _auth(ADMIN)
    h = _headers(token)

    # universe
    r = client.post("/content/universes", headers=h, json={"title": "U", "description": "d"})
    assert r.status_code == 201
    universe_id = r.json()["id"]

    # series
    r = client.post("/content/series", headers=h, params={"universe_id": universe_id},
                    json={"title": "S"})
    assert r.status_code == 201
    series_id = r.json()["id"]

    # book
    r = client.post("/content/books", headers=h, params={"series_id": series_id},
                    json={"title": "B"})
    assert r.status_code == 201
    book_id = r.json()["id"]

    # character (universe-level)
    r = client.post("/items/characters", headers=h, params={"universe_id": universe_id},
                    json={"name": "Hero", "description": "brave"})
    assert r.status_code == 201
    char_id = r.json()["id"]

    # background
    r = client.post("/items/backgrounds", headers=h, params={"universe_id": universe_id},
                    json={"title": "World", "body": "markdown body"})
    assert r.status_code == 201
    bg_id = r.json()["id"]

    # chapter
    r = client.post("/items/chapters", headers=h, params={"book_id": book_id},
                    json={"title": "Ch 1", "body": "# Chapter one"})
    assert r.status_code == 201
    chapter_id = r.json()["id"]

    # idea linked to the character
    r = client.post("/items/ideas", headers=h, params={"universe_id": universe_id},
                    json={"title": "plot twist", "body": "x",
                          "targets": [{"target_type": "character", "target_id": char_id}]})
    assert r.status_code == 201
    idea_id = r.json()["id"]
    links = client.get(f"/items/ideas/{idea_id}/links", headers=h).json()
    assert len(links) == 1
    assert links[0].target_type == "character"

    # export to markdown
    r = client.get(f"/export/books/{book_id}?fmt=md", headers=h)
    assert r.status_code == 200
    assert "Chapter one" in r.text


def test_idea_target_validation():
    token = _auth(ADMIN)
    h = _headers(token)
    r = client.post("/content/universes", headers=h, json={"title": "U"})
    universe_id = r.json()["id"]
    r = client.post("/items/ideas", headers=h, params={"universe_id": universe_id},
                    json={"title": "i", "targets": [{"target_type": "bogus", "target_id": "x"}]})
    assert r.status_code == 400


def test_api_token_generation_and_use():
    token = _auth(ADMIN)
    r = client.post("/auth/tokens", headers=_headers(token), params={"name": "cli"})
    assert r.status_code == 201
    raw = r.json()["token"]
    assert raw.startswith("ba_")
    # the generated bearer token works
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {raw}"}).json()
    assert me["email"] == ADMIN["email"]
    # listing hides the raw secret
    listed = client.get("/auth/tokens", headers=_headers(token)).json()
    assert listed[0]["prefix"].startswith("ba_")
    assert "token" not in listed[0] or "token" in listed[0] and listed[0].get("token") is None
