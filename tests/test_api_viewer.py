import json
from fastapi.testclient import TestClient
from api.app import app


def test_folder_endpoint_reads_tcs(tmp_path):
    (tmp_path / "tcs.json").write_text(json.dumps({"tcs": [{"id": "TC-01"}]}))
    (tmp_path / "trace.json").write_text(json.dumps({"cases": {"TC-01": {}}}))
    r = TestClient(app).get("/api/folder", params={"path": str(tmp_path)})
    assert r.status_code == 200
    body = r.json()
    assert body["tcs"]["tcs"][0]["id"] == "TC-01"
    assert "TC-01" in body["trace"]["cases"]
