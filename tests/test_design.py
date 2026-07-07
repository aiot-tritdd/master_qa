import qa.design as design
from qa.design import build_prompt, parse_cases, extract_sections, build_cases


def test_module_is_code_blind():
    # 1a KHÔNG được biết tới gitnexus (ranh giới thép)
    import inspect
    src = inspect.getsource(design)
    assert "gitnexus" not in src


def test_prompt_contains_spec_and_asks_json():
    p = build_prompt("YÊU CẦU: customer phải sync sang ticket")
    assert "YÊU CẦU: customer phải sync sang ticket" in p
    assert "json" in p.lower()


def test_extract_sections_finds_circled_and_bracket():
    md = "## 2. Yêu cầu\n### ① Company\n### 【A】 Cancel payment"
    secs = extract_sections(md)
    assert any("Company" in s for s in secs)
    assert any("A" in s for s in secs)


def test_parse_cases_reads_json_block():
    raw = '```json\n[{"id":"TC-01","screen":"S","pri":"High","title":"T",' \
          '"pre":"P","steps":"1","expect":"E","spec_section":"①"}]\n```'
    cases = parse_cases(raw)
    assert len(cases) == 1
    assert cases[0].id == "TC-01"
    assert cases[0].expect == "E"


def test_build_cases_uses_llm(monkeypatch):
    fake = '```json\n[{"id":"TC-01","screen":"S","pri":"High","title":"T",' \
           '"pre":"P","steps":"1","expect":"E","spec_section":"①"}]\n```'
    monkeypatch.setattr(design.llm, "call", lambda *a, **k: fake)
    cases = build_cases("spec")
    assert cases[0].expect == "E"
