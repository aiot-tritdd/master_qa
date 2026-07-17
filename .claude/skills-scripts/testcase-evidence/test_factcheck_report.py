# Chạy: python3 test_factcheck_report.py
# Kiểm factcheck_report.analyze: filler + tally = GATE; synonym/passive/vague = WARN; report sạch → 0 lỗi.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from factcheck_report import analyze, count_results  # noqa: E402


def test_filler_is_gate():
    e, w, c = analyze({"tcs": [{"result": "PASS", "note": "Moving forward, the team is committed to quality."}]})
    assert any("filler" in x for x in e), "filler phải là lỗi gate"


def test_tally_mismatch_in_summary_is_gate():
    doc = {"meta": {"summary": "2 PASS / 1 FAIL"},
           "screens": [{"result": "PASS"}, {"result": "FAIL"}, {"result": "FAIL"}]}
    e, w, c = analyze(doc)
    assert c == {"PASS": 1, "FAIL": 2}, c
    assert any("tally" in x and "PASS" in x for x in e), "2 PASS ≠ đếm 1 → gate"
    assert any("tally" in x and "FAIL" in x for x in e), "1 FAIL ≠ đếm 2 → gate"


def test_tally_correct_in_summary_passes():
    doc = {"meta": {"summary": "1 PASS / 2 FAIL"},
           "screens": [{"result": "PASS"}, {"result": "FAIL"}, {"result": "FAIL"}]}
    e, w, c = analyze(doc)
    assert not any("tally" in x for x in e), "tally khớp → không gate"


def test_tally_not_checked_outside_summary_fields():
    # số PASS/FAIL trong note thường (cross-reference case khác) KHÔNG bị gate → tránh false-positive
    doc = {"screens": [{"result": "PASS", "note": "functional case này từng 9 PASS / 8 FAIL ở TestCase-11"}]}
    e, w, c = analyze(doc)
    assert not any("tally" in x for x in e), "note thường không soi tally"


def test_vague_and_passive_are_warn_only():
    doc = {"screens": [{"result": "FAIL", "observed": "several endpoints potentially affected; a defect was discovered"}]}
    e, w, c = analyze(doc)
    assert e == [], "vague/passive chỉ warn, không gate"
    assert any("vague" in x for x in w) and any("passive" in x for x in w)


def test_clean_report_zero_errors():
    doc = {"meta": {"summary": "1 PASS"},
           "screens": [{"result": "PASS", "note": "sessionid có HttpOnly+Secure+SameSite=Lax; không cookie yếu."}]}
    e, w, c = analyze(doc)
    assert e == [] and w == [], f"report sạch phải 0 lỗi/0 warn: e={e} w={w}"


def test_count_from_actual_prefix():
    doc = {"tcs": [{"actual": "FAIL: màn thiếu nút"}, {"actual": "PASS - ok"}, {"actual": "未実施 chưa dựng được"}]}
    assert count_results(doc) == {"FAIL": 1, "PASS": 1, "未実施": 1}


def main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("✔", fn.__name__)
    print(f"\n{len(fns)} test OK")


if __name__ == "__main__":
    main()
