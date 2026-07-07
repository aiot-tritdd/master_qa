import json
from qa.impact import affected


def test_affected_matches_source_symbols(tmp_path):
    trace = {"flow": "x", "cases": {
        "TC-01": {"source_symbols": ["backend:institute.rb#save"]},
        "TC-02": {"source_symbols": ["ticket:handlers.py#sync_customer"]},
    }}
    (tmp_path / "trace.json").write_text(json.dumps(trace))
    hits = affected(tmp_path, ["handlers.py#sync_customer"])
    assert hits == ["TC-02"]
