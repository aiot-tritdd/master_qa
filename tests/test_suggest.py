import json
from pathlib import Path
import qa.suggest as suggest
from qa.suggest import coverage
from qa.design import Case


def test_coverage_counts_and_flags_gaps():
    cases = [Case("TC-01", "S", "High", "T", "P", "st", "E", "①Company"),
             Case("TC-02", "S", "High", "T", "P", "st", "E", "①Company")]
    cov = coverage(cases, ["①Company", "②Branch"])
    assert cov["①Company"] == 2
    assert cov["②Branch"] == 0        # lỗ hổng


def test_suggest_writes_files(tmp_path, monkeypatch):
    (tmp_path / "specs.md").write_text("## Yêu cầu\n### ①Company\nsync company")
    monkeypatch.setattr(suggest, "build_cases",
                        lambda md: [Case("TC-01", "Company", "High", "T", "P", "st", "E", "①Company")])
    monkeypatch.setattr(suggest, "bind_seams",
                        lambda cases, flow_id: ([{"id": "TC-01", "result": "未実施"}],
                                                {"flow": flow_id, "cases": {"TC-01": {}}}))
    out = suggest.suggest(tmp_path)
    assert Path(out["tcs"]).exists()
    assert Path(out["trace"]).exists()
    assert json.loads(Path(out["tcs"]).read_text())["tcs"][0]["id"] == "TC-01"
    assert out["coverage"]["①Company"] == 1
