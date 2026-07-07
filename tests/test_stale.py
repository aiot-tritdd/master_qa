import json
import qa.stale as stale
from qa.stale import check_stale


def test_flags_when_hash_changed(tmp_path, monkeypatch):
    trace = {"cases": {"TC-01": {"source_symbols": ["backend:x"], "source_hash": "OLD"}}}
    (tmp_path / "trace.json").write_text(json.dumps(trace))
    monkeypatch.setattr(stale, "current_hash", lambda syms: "NEW")
    res = check_stale(tmp_path)
    assert res[0]["tc"] == "TC-01"
    assert res[0]["stale"] is True
    assert res[0]["new_hash"] == "NEW"


def test_not_stale_when_same(tmp_path, monkeypatch):
    trace = {"cases": {"TC-01": {"source_symbols": ["backend:x"], "source_hash": "SAME"}}}
    (tmp_path / "trace.json").write_text(json.dumps(trace))
    monkeypatch.setattr(stale, "current_hash", lambda syms: "SAME")
    assert check_stale(tmp_path)[0]["stale"] is False
