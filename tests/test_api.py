import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def c():
    with TestClient(app) as client:
        yield client


def H(user):
    return {"X-User": user}


def test_requires_user(c):
    assert c.get("/api/docs").status_code == 401


def test_sharing_and_permissions(c):
    doc = c.post("/api/docs", json={"title": "Plan"}, headers=H("alice")).json()
    url = f"/api/docs/{doc['id']}"

    assert c.get(url, headers=H("bob")).status_code == 404  # no access yet

    c.post(url + "/share", json={"username": "bob", "role": "viewer"}, headers=H("alice"))
    assert c.get(url, headers=H("bob")).json()["access"] == "viewer"
    assert c.put(url, json={"content": "<p>x</p>"}, headers=H("bob")).status_code == 403
    assert c.post(url + "/share", json={"username": "carol"}, headers=H("bob")).status_code == 403

    c.post(url + "/share", json={"username": "bob", "role": "editor"}, headers=H("alice"))
    assert c.put(url, json={"content": "<p><strong>Hi</strong></p>"}, headers=H("bob")).status_code == 200
    assert "<strong>Hi</strong>" in c.get(url, headers=H("alice")).json()["content"]  # persisted

    ids_owned = [d["id"] for d in c.get("/api/docs", headers=H("alice")).json()["owned"]]
    ids_shared = [d["id"] for d in c.get("/api/docs", headers=H("bob")).json()["shared"]]
    assert doc["id"] in ids_owned and doc["id"] in ids_shared

    c.delete(url + "/share/bob", headers=H("alice"))
    assert c.get(url, headers=H("bob")).status_code == 404


def test_content_is_sanitized(c):
    doc = c.post("/api/docs", json={}, headers=H("alice")).json()
    bad = "<p>ok</p><script>alert(1)</script><img src=x onerror=alert(1)>"
    out = c.put(f"/api/docs/{doc['id']}", json={"content": bad}, headers=H("alice")).json()["content"]
    assert "script" not in out and "onerror" not in out and "<p>ok</p>" in out


def test_upload(c):
    r = c.post("/api/upload", files={"file": ("notes.md", b"# Title\n\n- one\n- two")}, headers=H("alice"))
    assert r.status_code == 201
    assert r.json()["title"] == "notes" and "<h1>Title</h1>" in r.json()["content"]
    bad = c.post("/api/upload", files={"file": ("a.pdf", b"%PDF")}, headers=H("alice"))
    assert bad.status_code == 400


def test_rejects_empty_title(c):
    doc = c.post("/api/docs", json={"title": "A"}, headers=H("alice")).json()
    assert c.put(f"/api/docs/{doc['id']}", json={"title": "  "}, headers=H("alice")).status_code == 422

def test_cannot_share_with_yourself(c):
    doc = c.post("/api/docs", json={"title": "Solo"}, headers=H("alice")).json()
    r = c.post(f"/api/docs/{doc['id']}/share", json={"username": "alice"}, headers=H("alice"))
    assert r.status_code == 400


def test_only_owner_can_delete(c):
    doc = c.post("/api/docs", json={"title": "Mine"}, headers=H("alice")).json()
    url = f"/api/docs/{doc['id']}"
    c.post(url + "/share", json={"username": "bob", "role": "editor"}, headers=H("alice"))
    assert c.delete(url, headers=H("bob")).status_code == 403
    assert c.delete(url, headers=H("alice")).status_code == 204
