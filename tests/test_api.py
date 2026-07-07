from fastapi.testclient import TestClient
from api.app import app


def test_status_endpoint():
    client = TestClient(app)
    r = client.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert "doc" in body and "tests_exist" in body


def test_generate_refuses_when_not_approved(monkeypatch):
    from api import app as apimod

    def boom(_):
        raise ValueError("doc not approved")

    monkeypatch.setattr(apimod.testgen, "generate", boom)
    client = TestClient(app)
    r = client.post("/api/generate")
    assert r.status_code == 400
