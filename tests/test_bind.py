import qa.bind as bind
from qa.design import Case
from qa.bind import to_tcs, parse_seam, bind_seams

C = Case(id="TC-01", screen="Company", pri="High", title="T", pre="P",
         steps="tạo company", expect="Ticket +1, tên khớp", spec_section="①Company")


def test_to_tcs_matches_boss_schema():
    row = to_tcs([C])[0]
    for k in ["id", "screen", "pri", "result", "title", "pre", "steps",
              "expect", "actual", "note", "before", "after"]:
        assert k in row
    assert row["result"] == "未実施"
    assert row["expect"] == "Ticket +1, tên khớp"   # nguyên văn từ case
    assert row["before"] is None


def test_parse_seam_reads_json():
    raw = '```json\n{"type":"ui","create":"Admin /companies","observe":"Ticket Institute",' \
          '"source_symbols":["backend:institute.rb"]}\n```'
    s = parse_seam(raw)
    assert s.type == "ui"
    assert s.source_symbols == ["backend:institute.rb"]


def test_bind_freezes_expect(monkeypatch):
    monkeypatch.setattr(bind.gitnexus, "query", lambda *a, **k: "FACTS")
    monkeypatch.setattr(bind.gitnexus, "symbol_hash", lambda xs: "hash123")
    monkeypatch.setattr(bind, "parse_seam", lambda raw: bind.Seam(
        type="ui", create="c", observe="o", source_symbols=["backend:x"]))
    monkeypatch.setattr(bind.llm, "call", lambda *a, **k: "{}")
    tcs, trace = bind_seams([C], flow_id="10.4")
    assert tcs[0]["expect"] == "Ticket +1, tên khớp"          # KHÔNG bị đổi
    assert trace["cases"]["TC-01"]["spec_section"] == "①Company"
    assert trace["cases"]["TC-01"]["source_hash"] == "hash123"
    assert trace["cases"]["TC-01"]["seam"]["type"] == "ui"
