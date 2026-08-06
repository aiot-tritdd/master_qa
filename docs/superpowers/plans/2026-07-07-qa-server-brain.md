# QA-Server Brain — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bổ sung "bộ não QA senior" (suggest 1a/1b · impact · stale · coverage · viewer + tài-liệu-sống) cắm vào pipeline testcase-evidence, sinh `tcs.json` (schema sếp) + `trace.json` từ spec độc lập.

**Architecture:** Bộ não = các module Python trong `qa/` + slash-command `.claude/commands/testcase-*.md`. Bước `suggest` tách 2 module có tường thép: `qa/design.py` (MÙ CODE — viết kỳ vọng chỉ từ spec) → `qa/bind.py` (dùng GitNexus điền seam + truy vết, cấm sửa kỳ vọng). Viewer = `api/` (FastAPI) + `web/` (Next.js) đọc file. Không đụng script của sếp.

**Tech Stack:** Python 3.13 (stdlib `html.parser`, `subprocess`, `dataclasses`, `json`, PyYAML), pytest; GitNexus CLI; `claude -p` (qua `qa/llm.py`); FastAPI + Next.js 14 (đã có).

## Global Constraints

- Repo: `/Users/tritdd/Work/master_qa` — **NO git remote, never push**. Chạy trong venv: `source venv/bin/activate`.
- **Ranh giới thép #1:** `qa/design.py` **CẤM** import `qa.gitnexus` và **CẤM** đọc file repo — chỉ nhận `spec_md: str`. Kỳ vọng (`expect`) chỉ từ spec.
- **Ranh giới thép #2:** `qa/bind.py` **CẤM** sửa `title`/`expect`/`steps` của case (assert bằng nhau, lệch → raise).
- **KHÔNG** sửa file/script của sếp. `tcs.json` giữ đúng schema sếp; truy vết để ở **sidecar `trace.json`**.
- `tcs.json` schema (mỗi tc): `id, screen, pri(High|Medium|Low), result(PASS|FAIL|未実施), title, pre, steps, expect, actual, note, before, after`. `meta{project,module,issue,tester,date,env}`, `shots_dir`.
- Docs/comment/UI tiếng Việt; code identifier tiếng Anh.
- Chạy 1 lần đầu: `git checkout -b qa-brain` (không làm trên `phase1-mvp`).
- Test dùng `python -m pytest`; LLM/GitNexus **luôn monkeypatch** trong unit test (không gọi thật).

---

## Task 1: HTML → specs.md ingest (`qa/specmd.py`)

**Files:**
- Create: `qa/specmd.py`, `tests/test_specmd.py`

**Interfaces:**
- Produces:
  - `html_to_markdown(html: str) -> str` — bóc tag HTML → text có cấu trúc (heading `#`, `-` list), bỏ script/style.
  - `ingest(folder: Path) -> Path` — đọc `<folder>/specs.html` → ghi `<folder>/specs.md` (nếu chưa có) → trả path.

- [ ] **Step 1: Write the failing test** `tests/test_specmd.py`

```python
from qa.specmd import html_to_markdown


def test_strips_tags_and_keeps_text():
    html = "<h1>Tiêu đề</h1><p>Đoạn văn</p><script>bad()</script>"
    md = html_to_markdown(html)
    assert "Tiêu đề" in md
    assert "Đoạn văn" in md
    assert "bad()" not in md
    assert "<" not in md


def test_heading_becomes_hash():
    md = html_to_markdown("<h2>Yêu cầu</h2>")
    assert md.strip().startswith("#")
    assert "Yêu cầu" in md


def test_list_items_become_dashes():
    md = html_to_markdown("<ul><li>một</li><li>hai</li></ul>")
    assert "- một" in md
    assert "- hai" in md
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_specmd.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.specmd'`

- [ ] **Step 3: Implement `qa/specmd.py`**

```python
from html.parser import HTMLParser
from pathlib import Path


class _Md(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self._skip = 0          # bên trong script/style
        self._prefix = ""       # prefix cho block hiện tại (#, -, …)

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in ("li",):
            self.out.append("\n- ")
        elif tag in ("p", "br", "tr", "div"):
            self.out.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag in ("h1", "h2", "h3", "h4", "p"):
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = " ".join(data.split())
        if text:
            self.out.append(text)


def html_to_markdown(html: str) -> str:
    p = _Md()
    p.feed(html)
    md = "".join(p.out)
    lines = [ln.rstrip() for ln in md.splitlines()]
    # gộp dòng trống liên tiếp
    result: list[str] = []
    for ln in lines:
        if ln == "" and result and result[-1] == "":
            continue
        result.append(ln)
    return "\n".join(result).strip() + "\n"


def ingest(folder: Path) -> Path:
    folder = Path(folder)
    md_path = folder / "specs.md"
    html_path = folder / "specs.html"
    if not html_path.exists():
        raise FileNotFoundError(f"không thấy {html_path}")
    md_path.write_text(html_to_markdown(html_path.read_text()), encoding="utf-8")
    return md_path
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_specmd.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add qa/specmd.py tests/test_specmd.py
git commit -m "feat: html->specs.md ingest (stdlib HTMLParser)"
```

---

## Task 2: Design (1a — MÙ CODE) (`qa/design.py`)

**Files:**
- Create: `qa/design.py`, `tests/test_design.py`

**Interfaces:**
- Consumes: `qa.llm.call`, `qa.llm.extract_block`.
- Produces:
  - `@dataclass Case { id, screen, pri, title, pre, steps, expect, spec_section }` (all `str`).
  - `build_prompt(spec_md: str) -> str` — pure; ép LLM trả JSON list case, chỉ dựa spec.
  - `parse_cases(raw: str) -> list[Case]` — pure; đọc khối ```json → list Case.
  - `extract_sections(spec_md: str) -> list[str]` — pure; nhặt các mục (`##`, `①-⑨`, `【A】…`).
  - `build_cases(spec_md: str) -> list[Case]` — call llm → parse.
- **RÀNG BUỘC:** module KHÔNG được `import qa.gitnexus` và không đọc file repo.

- [ ] **Step 1: Write the failing test** `tests/test_design.py`

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_design.py -v`
Expected: FAIL — `No module named 'qa.design'`

- [ ] **Step 3: Implement `qa/design.py`**

```python
import json
import re
from dataclasses import dataclass
from qa import llm  # CHỈ llm — KHÔNG gitnexus, KHÔNG đọc repo (ranh giới thép 1a)


@dataclass
class Case:
    id: str
    screen: str
    pri: str
    title: str
    pre: str
    steps: str
    expect: str
    spec_section: str


def extract_sections(spec_md: str) -> list[str]:
    secs: list[str] = []
    for line in spec_md.splitlines():
        s = line.strip()
        if re.match(r"^#{2,4}\s+\S", s) or re.match(r"^[①②③④⑤⑥⑦⑧⑨]", s) or "【" in s:
            secs.append(re.sub(r"^#{2,4}\s+", "", s))
    return secs


def build_prompt(spec_md: str) -> str:
    return f"""Bạn là QA senior. CHỈ dựa trên TÀI LIỆU SPEC dưới đây (nghiệp vụ khách đã chốt),
thiết kế bộ test case. TUYỆT ĐỐI không suy đoán từ code — bạn KHÔNG có code.

Mỗi case: happy path / biến thể quyền-điều kiện / boundary / regression / negative.
`expect` phải là hành vi ĐÚNG theo spec (kể cả thông báo nguyên văn nếu spec ghi), KHÔNG mô tả "hệ thống đang làm gì".
`spec_section` = mục trong spec mà case này truy về (vd "①Company", "【A】").
`steps`/`pre` viết bằng NGÔN NGỮ NGHIỆP VỤ (chưa cần biết URL/màn hình cụ thể).

Chỉ trả về MỘT khối ```json là mảng object, mỗi object khoá:
id (TC-01…), screen, pri (High|Medium|Low), title, pre, steps, expect, spec_section.

## SPEC
{spec_md}
"""


def parse_cases(raw: str) -> list[Case]:
    block = llm.extract_block(raw, "json")
    data = json.loads(block)
    return [Case(**{k: str(item.get(k, "")) for k in Case.__annotations__}) for item in data]


def build_cases(spec_md: str) -> list[Case]:
    raw = llm.call(build_prompt(spec_md))
    return parse_cases(raw)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_design.py -v`
Expected: PASS (5 tests) — chú ý `test_module_is_code_blind` xanh.

- [ ] **Step 5: Commit**

```bash
git add qa/design.py tests/test_design.py
git commit -m "feat: design 1a (code-blind case builder from spec only)"
```

---

## Task 3: Bind (1b) + tcs.json + trace.json (`qa/bind.py`)

**Files:**
- Create: `qa/bind.py`, `tests/test_bind.py`

**Interfaces:**
- Consumes: `qa.design.Case`, `qa.gitnexus.query`, `qa.gitnexus.symbol_hash`, `qa.llm`.
- Produces:
  - `@dataclass Seam { type: str, create: str, observe: str, source_symbols: list[str] }`.
  - `build_prompt(case: Case, facts: str) -> str` — pure; hỏi LLM seam cho 1 case, KÈM lệnh "không sửa expect".
  - `parse_seam(raw: str) -> Seam` — pure.
  - `to_tcs(cases: list[Case]) -> list[dict]` — pure; đổi Case → dict schema sếp (result=`未実施`, actual=`未実施`, before/after=`None`).
  - `bind_seams(cases: list[Case], flow_id: str) -> tuple[list[dict], dict]` — với mỗi case: query gitnexus → seam; assert title/expect/steps không đổi; trả `(tcs_list, trace)`.

- [ ] **Step 1: Write the failing test** `tests/test_bind.py`

```python
import qa.bind as bind
from qa.design import Case
from qa.bind import to_tcs, parse_seam, bind_seams

C = Case(id="TC-01", screen="Company", pri="High", title="T", pre="P",
         steps="tạo company", expect="Ticket +1, tên khớp", spec_section="①Company")


def test_to_tcs_matches_boss_schema():
    row = to_tcs([C])[0]
    for k in ["id","screen","pri","result","title","pre","steps","expect","actual","note","before","after"]:
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_bind.py -v`
Expected: FAIL — `No module named 'qa.bind'`

- [ ] **Step 3: Implement `qa/bind.py`**

```python
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from qa import llm, gitnexus
from qa.design import Case

_TCS_KEYS = ["id", "screen", "pri", "result", "title", "pre", "steps",
             "expect", "actual", "note", "before", "after"]


@dataclass
class Seam:
    type: str            # "ui" | "headless"
    create: str
    observe: str
    source_symbols: list[str]


def to_tcs(cases: list[Case]) -> list[dict]:
    rows = []
    for c in cases:
        rows.append({
            "id": c.id, "screen": c.screen, "pri": c.pri, "result": "未実施",
            "title": c.title, "pre": c.pre, "steps": c.steps, "expect": c.expect,
            "actual": "未実施", "note": "", "before": None, "after": None,
        })
    return rows


def build_prompt(case: Case, facts: str) -> str:
    return f"""Bạn là QA senior HIỂU hệ thống. Dưới đây là 1 test case (đã chốt kỳ vọng) và FACTS từ GitNexus.
CHỈ xác định *chỗ chạm hệ thống* để chạy được case — TUYỆT ĐỐI KHÔNG sửa/diễn giải lại `expect`.

Trả về MỘT khối ```json: {{type, create, observe, source_symbols}}
- type: "ui" nếu thao tác qua màn hình; "headless" nếu qua API/DB.
- create: chỗ/bước tạo dữ liệu (app/màn hoặc API).
- observe: chỗ quan sát kết quả (màn hoặc bảng DB/endpoint).
- source_symbols: các symbol code liên quan (để truy vết), dạng "repo:path#sym".

## CASE
title: {case.title}
steps: {case.steps}
expect: {case.expect}

## FACTS (GitNexus)
{facts}
"""


def parse_seam(raw: str) -> Seam:
    data = json.loads(llm.extract_block(raw, "json"))
    return Seam(type=str(data.get("type", "ui")), create=str(data.get("create", "")),
                observe=str(data.get("observe", "")),
                source_symbols=list(data.get("source_symbols", [])))


def bind_seams(cases: list[Case], flow_id: str) -> tuple[list[dict], dict]:
    tcs = to_tcs(cases)
    frozen = {c.id: (c.title, c.expect, c.steps) for c in cases}
    trace = {"flow": flow_id,
             "generated_at": datetime.now(timezone.utc).isoformat(),
             "cases": {}}
    by_id = {c.id: c for c in cases}
    for row in tcs:
        c = by_id[row["id"]]
        facts = gitnexus.query("@threease", f"{c.title} {c.steps}")
        seam = parse_seam(llm.call(build_prompt(c, facts)))
        # ranh giới thép 1b: KHÔNG được đổi expect/title/steps
        assert (row["title"], row["expect"], row["steps"]) == frozen[row["id"]], \
            f"bind vi phạm: đã sửa expect của {row['id']}"
        row["note"] = f"[seam:{seam.type}] tạo: {seam.create} · xem: {seam.observe}"
        trace["cases"][c.id] = {
            "spec_section": c.spec_section,
            "seam": {"type": seam.type, "create": seam.create, "observe": seam.observe},
            "source_symbols": seam.source_symbols,
            "source_hash": gitnexus.symbol_hash(seam.source_symbols),
        }
    return tcs, trace
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_bind.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add qa/bind.py tests/test_bind.py
git commit -m "feat: bind 1b (seam + trace.json, expect frozen)"
```

---

## Task 4: Suggest orchestration + coverage + command (`qa/suggest.py`)

**Files:**
- Create: `qa/suggest.py`, `tests/test_suggest.py`, `.claude/commands/testcase-suggest.md`

**Interfaces:**
- Consumes: `qa.specmd.ingest`, `qa.design.build_cases`, `qa.design.extract_sections`, `qa.bind.bind_seams`.
- Produces:
  - `coverage(cases, sections) -> dict` — pure; `{section: số_case}` cho mọi section (0 nếu thiếu).
  - `suggest(folder: Path) -> dict` — chạy full: ingest (nếu có html) → build_cases → bind_seams → ghi `tcs.json` + `trace.json` → trả `{"tcs": path, "trace": path, "coverage": {...}}`.

- [ ] **Step 1: Write the failing test** `tests/test_suggest.py`

```python
import json
from pathlib import Path
import qa.suggest as suggest
from qa.suggest import coverage
from qa.design import Case


def test_coverage_counts_and_flags_gaps():
    cases = [Case("TC-01","S","High","T","P","st","E","①Company"),
             Case("TC-02","S","High","T","P","st","E","①Company")]
    cov = coverage(cases, ["①Company", "②Branch"])
    assert cov["①Company"] == 2
    assert cov["②Branch"] == 0        # lỗ hổng


def test_suggest_writes_files(tmp_path, monkeypatch):
    (tmp_path / "specs.md").write_text("## Yêu cầu\n### ①Company\nsync company")
    monkeypatch.setattr(suggest, "build_cases",
        lambda md: [Case("TC-01","Company","High","T","P","st","E","①Company")])
    monkeypatch.setattr(suggest, "bind_seams",
        lambda cases, flow_id: ([{"id":"TC-01","result":"未実施"}],
                                {"flow": flow_id, "cases": {"TC-01": {}}}))
    out = suggest.suggest(tmp_path)
    assert Path(out["tcs"]).exists()
    assert Path(out["trace"]).exists()
    assert json.loads(Path(out["tcs"]).read_text())["tcs"][0]["id"] == "TC-01"
    assert out["coverage"]["①Company"] == 1
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_suggest.py -v`
Expected: FAIL — `No module named 'qa.suggest'`

- [ ] **Step 3: Implement `qa/suggest.py`**

```python
import json
from pathlib import Path
from qa.specmd import ingest
from qa.design import build_cases, extract_sections
from qa.bind import bind_seams


def coverage(cases, sections) -> dict:
    counts = {s: 0 for s in sections}
    for c in cases:
        counts[c.spec_section] = counts.get(c.spec_section, 0) + 1
    return counts


def suggest(folder: Path) -> dict:
    folder = Path(folder)
    if (folder / "specs.html").exists() and not (folder / "specs.md").exists():
        ingest(folder)
    spec_md = (folder / "specs.md").read_text(encoding="utf-8")
    cases = build_cases(spec_md)
    tcs, trace = bind_seams(cases, flow_id=folder.name)
    payload = {
        "meta": {"project": "Threesides Maintenance", "module": folder.name,
                 "issue": "", "tester": "QA-Server (brain)", "date": "", "env": "Dev"},
        "shots_dir": "shots", "tcs": tcs,
    }
    tcs_path = folder / "tcs.json"
    trace_path = folder / "trace.json"
    tcs_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"tcs": str(tcs_path), "trace": str(trace_path),
            "coverage": coverage(cases, extract_sections(spec_md))}
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_suggest.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Create the command** `.claude/commands/testcase-suggest.md`

```markdown
# /testcase-suggest — Bộ não thiết kế test case (1a mù-code → 1b bind)

Sinh `tcs.json` (schema testcase-evidence) + `trace.json` từ spec ĐỘC LẬP.
Oracle = spec; 1a viết kỳ vọng khi mù code; 1b dùng GitNexus chỉ điền seam.

## Dùng
```
/testcase-suggest <folder>
```
Ví dụ: `/testcase-suggest wtf-is-this/TestCase_No.10.4`

## Chạy
```bash
source venv/bin/activate
python -c "from qa.suggest import suggest; import json; print(json.dumps(suggest('<folder>'), ensure_ascii=False, indent=2))"
```
- Nếu folder có `specs.html` mà chưa có `specs.md` → tự convert trước.
- In ra đường dẫn `tcs.json`/`trace.json` + **coverage** (section nào 0 case = lỗ hổng, báo user bổ sung).
- KHÔNG chạy test; dùng `/testcase-run` (pipeline sếp) để chạy sau.
```

- [ ] **Step 6: Commit**

```bash
git add qa/suggest.py tests/test_suggest.py .claude/commands/testcase-suggest.md
git commit -m "feat: /testcase-suggest orchestration + coverage"
```

---

## Task 5: Impact (`qa/impact.py`)

**Files:**
- Create: `qa/impact.py`, `tests/test_impact.py`, `.claude/commands/testcase-impact.md`
- Modify: `qa/gitnexus.py` (thêm `impact()`)

**Interfaces:**
- Consumes: `qa.gitnexus.run`, `trace.json`.
- Produces:
  - `qa.gitnexus.impact(repo: str, target: str, direction: str = "upstream") -> str`.
  - `qa.impact.affected(folder: Path, changed_symbols: list[str]) -> list[str]` — trả list `tc_id` mà `source_symbols` giao với `changed_symbols` (khớp theo chuỗi con).

- [ ] **Step 1: Write the failing test** `tests/test_impact.py`

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_impact.py -v`
Expected: FAIL — `No module named 'qa.impact'`

- [ ] **Step 3: Add `impact()` to `qa/gitnexus.py`**

```python
def impact(repo: str, target: str, direction: str = "upstream") -> str:
    return run(["impact", "--repo", repo, "--target", target, "--direction", direction])
```

- [ ] **Step 4: Implement `qa/impact.py`**

```python
import json
from pathlib import Path


def affected(folder: Path, changed_symbols: list[str]) -> list[str]:
    trace = json.loads((Path(folder) / "trace.json").read_text(encoding="utf-8"))
    hits: list[str] = []
    for tc_id, info in trace.get("cases", {}).items():
        syms = info.get("source_symbols", [])
        if any(ch in s or s in ch for ch in changed_symbols for s in syms):
            hits.append(tc_id)
    return sorted(hits)
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_impact.py -v`
Expected: PASS

- [ ] **Step 6: Create command** `.claude/commands/testcase-impact.md`

```markdown
# /testcase-impact — Khoanh case cần retest khi code đổi

## Dùng
```
/testcase-impact <folder> <symbol1> [symbol2 …]
```
Ví dụ: `/testcase-impact wtf-is-this/TestCase_No.10.4 ProBackendSyncService.sync_customer_upserted`

## Chạy
```bash
source venv/bin/activate
python -c "from qa.impact import affected; print(affected('<folder>', ['<symbol>']))"
```
Kết quả = list TC → đưa vào `/testcase-retest <folder> <TC…>` của pipeline sếp.
```

- [ ] **Step 7: Commit**

```bash
git add qa/impact.py qa/gitnexus.py tests/test_impact.py .claude/commands/testcase-impact.md
git commit -m "feat: /testcase-impact (changed symbols -> affected TCs)"
```

---

## Task 6: Stale (`qa/stale.py`)

**Files:**
- Create: `qa/stale.py`, `tests/test_stale.py`, `.claude/commands/testcase-stale.md`

**Interfaces:**
- Consumes: `trace.json`, `qa.gitnexus.symbol_hash`, `qa.gitnexus.query`.
- Produces:
  - `current_hash(source_symbols: list[str]) -> str` — lấy facts hiện tại của symbol qua gitnexus rồi hash.
  - `check_stale(folder: Path) -> list[dict]` — trả `[{tc, stale: bool, old_hash, new_hash}]`.

- [ ] **Step 1: Write the failing test** `tests/test_stale.py`

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_stale.py -v`
Expected: FAIL — `No module named 'qa.stale'`

- [ ] **Step 3: Implement `qa/stale.py`**

```python
import json
from pathlib import Path
from qa import gitnexus


def current_hash(source_symbols: list[str]) -> str:
    facts = [gitnexus.query("@threease", s) for s in source_symbols]
    return gitnexus.symbol_hash(facts)


def check_stale(folder: Path) -> list[dict]:
    trace = json.loads((Path(folder) / "trace.json").read_text(encoding="utf-8"))
    out: list[dict] = []
    for tc_id, info in trace.get("cases", {}).items():
        old = info.get("source_hash", "")
        new = current_hash(info.get("source_symbols", []))
        out.append({"tc": tc_id, "stale": old != new, "old_hash": old, "new_hash": new})
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_stale.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Create command** `.claude/commands/testcase-stale.md`

```markdown
# /testcase-stale — Dò spec/case đã lệch code

## Dùng
```
/testcase-stale <folder>
```

## Chạy
```bash
source venv/bin/activate
python -c "from qa.stale import check_stale; import json; print(json.dumps(check_stale('<folder>'), ensure_ascii=False, indent=2))"
```
TC nào `stale:true` → spec/case có thể không còn khớp code → người xem lại spec.
```

- [ ] **Step 6: Commit**

```bash
git add qa/stale.py tests/test_stale.py .claude/commands/testcase-stale.md
git commit -m "feat: /testcase-stale (source_hash drift detection)"
```

---

## Task 7: System-map — tài liệu sống (SIDE) (`qa/systemmap.py`)

**Files:**
- Create: `qa/systemmap.py`, `tests/test_systemmap.py`

**Interfaces:**
- Consumes: `qa.knowledge.load/save/KnowledgeDoc`, `qa.gitnexus.symbol_hash`.
- Produces:
  - `store_path(flow_id: str) -> Path` — `knowledge/system/<flow_id>.md`.
  - `contribute(flow_id: str, body_md: str, source_symbols: list[str]) -> Path` — ghi/merge 1 mục system-map với front-matter `{flow, source_symbols, source_hash, kind: "system-map"}`. Nhãn "code đang làm gì" — KHÔNG oracle.

- [ ] **Step 1: Write the failing test** `tests/test_systemmap.py`

```python
import types
import qa.systemmap as sm


def test_contribute_writes_doc_with_provenance(tmp_path, monkeypatch):
    # settings là frozen dataclass → thay cả reference bằng fake, không mutate instance
    monkeypatch.setattr(sm, "settings", types.SimpleNamespace(knowledge_dir=tmp_path))
    p = sm.contribute("10.4-customer", "# Flow\nBackend -> Ticket", ["backend:x", "ticket:y"])
    doc = sm.knowledge.load(p)
    assert doc.meta["kind"] == "system-map"
    assert doc.meta["flow"] == "10.4-customer"
    assert doc.meta["source_symbols"] == ["backend:x", "ticket:y"]
    assert doc.meta["source_hash"]           # có hash provenance
    assert "Backend -> Ticket" in doc.body
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_systemmap.py -v`
Expected: FAIL — `No module named 'qa.systemmap'`

- [ ] **Step 3: Implement `qa/systemmap.py`**

```python
from pathlib import Path
from qa import knowledge, gitnexus
from qa.config import settings


def store_path(flow_id: str) -> Path:
    return settings.knowledge_dir / "system" / f"{flow_id}.md"


def contribute(flow_id: str, body_md: str, source_symbols: list[str]) -> Path:
    path = store_path(flow_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = knowledge.KnowledgeDoc(
        path=path,
        meta={"kind": "system-map", "flow": flow_id,
              "note": "MÔ TẢ code đang làm gì — KHÔNG phải oracle",
              "source_symbols": source_symbols,
              "source_hash": gitnexus.symbol_hash(source_symbols)},
        body=body_md,
    )
    knowledge.save(doc)
    return path
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_systemmap.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add qa/systemmap.py tests/test_systemmap.py
git commit -m "feat: system-map store (living doc, SIDE, provenance+hash)"
```

---

## Task 8: Viewer API (`api/app.py`)

**Files:**
- Modify: `api/app.py` (thêm endpoint đọc folder + system-doc)
- Test: `tests/test_api_viewer.py`

**Interfaces:**
- Produces (JSON API viewer dùng):
  - `GET /api/folder?path=<folder>` → `{"tcs": {...}|None, "trace": {...}|None, "coverage": {...}|None}` (đọc `tcs.json`/`trace.json` trong folder).
  - `GET /api/systemdoc` → `[{flow, body, meta}]` (mọi file trong `knowledge/system/`).

- [ ] **Step 1: Write the failing test** `tests/test_api_viewer.py`

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_api_viewer.py -v`
Expected: FAIL — `404` (endpoint chưa có)

- [ ] **Step 3: Add endpoints to `api/app.py`** (thêm vào cuối, giữ nguyên phần cũ)

```python
import json
from pathlib import Path


def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


@app.get("/api/folder")
def folder(path: str):
    f = Path(path)
    return {"tcs": _read_json(f / "tcs.json"), "trace": _read_json(f / "trace.json")}


@app.get("/api/systemdoc")
def systemdoc():
    from qa import knowledge
    root = settings.knowledge_dir / "system"
    out = []
    if root.exists():
        for md in sorted(root.glob("*.md")):
            d = knowledge.load(md)
            out.append({"flow": d.meta.get("flow", md.stem), "meta": d.meta, "body": d.body})
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_api_viewer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add api/app.py tests/test_api_viewer.py
git commit -m "feat: viewer API (folder tcs/trace + system-doc)"
```

---

## Task 9: Viewer UI (`web/`)

**Files:**
- Modify: `web/lib/api.ts` (thêm fetch helpers)
- Create: `web/app/system/page.tsx` (tài liệu sống), `web/app/folder/page.tsx` (case + coverage + evidence)

**Interfaces:**
- Consumes: `GET /api/systemdoc`, `GET /api/folder?path=`.

- [ ] **Step 1: Add helpers to `web/lib/api.ts`** (thêm dưới object `api`)

```ts
export type SystemDoc = { flow: string; meta: Record<string, any>; body: string };
export const viewer = {
  systemdoc: (): Promise<SystemDoc[]> =>
    fetch(`${BASE}/api/systemdoc`, { cache: "no-store" }).then(j),
  folder: (path: string) =>
    fetch(`${BASE}/api/folder?path=${encodeURIComponent(path)}`, { cache: "no-store" }).then(j),
};
```

- [ ] **Step 2: Create `web/app/system/page.tsx`** (tài liệu hệ thống sống)

```tsx
"use client";
import { useEffect, useState } from "react";
import { viewer, SystemDoc } from "@/lib/api";

export default function SystemPage() {
  const [docs, setDocs] = useState<SystemDoc[]>([]);
  useEffect(() => { viewer.systemdoc().then(setDocs).catch(() => setDocs([])); }, []);
  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-emerald-800">🗺 Tài liệu hệ thống (sống)</h1>
      <p className="text-emerald-700/70 mb-6">Mô tả code đang làm gì — không phải oracle. Lớn dần mỗi lần QA chạy.</p>
      {docs.length === 0 && <p>Chưa có mục nào. Chạy /testcase-suggest để gieo hạt.</p>}
      {docs.map((d) => (
        <div key={d.flow} className="card p-6 mb-4">
          <h2 className="font-semibold mb-1">{d.flow}</h2>
          <p className="text-xs text-stone-500 mb-3">nguồn: {JSON.stringify(d.meta.source_symbols)} · hash {String(d.meta.source_hash)}</p>
          <pre className="whitespace-pre-wrap text-sm bg-stone-50 rounded-2xl p-5 border border-stone-200">{d.body}</pre>
        </div>
      ))}
    </main>
  );
}
```

- [ ] **Step 3: Create `web/app/folder/page.tsx`** (case + coverage + evidence)

```tsx
"use client";
import { useEffect, useState } from "react";
import { viewer } from "@/lib/api";

export default function FolderPage() {
  const [path, setPath] = useState("");
  const [data, setData] = useState<any>(null);
  const load = () => viewer.folder(path).then(setData).catch(() => setData(null));
  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-emerald-800">📋 Test folder</h1>
      <div className="flex gap-2 my-4">
        <input className="border rounded-full px-4 py-2 flex-1" placeholder="đường dẫn folder"
          value={path} onChange={(e) => setPath(e.target.value)} />
        <button className="btn bg-emerald-300" onClick={load}>Tải</button>
      </div>
      {data?.tcs?.tcs?.map((t: any) => (
        <div key={t.id} className="card p-4 mb-2">
          <b>{t.id}</b> · {t.title} — <span className="font-mono text-sm">{t.result}</span>
          <p className="text-sm text-stone-600 mt-1">expect: {t.expect}</p>
          <p className="text-xs text-stone-500">{t.note}</p>
        </div>
      ))}
    </main>
  );
}
```

- [ ] **Step 4: Verify build**

Run: `cd web && npm run build`
Expected: `✓ Compiled successfully` — routes `/system`, `/folder` xuất hiện.

- [ ] **Step 5: Commit**

```bash
git add web/lib/api.ts web/app/system/page.tsx web/app/folder/page.tsx
git commit -m "feat: viewer UI (living system doc + folder cases)"
```

---

## Self-Review

**Spec coverage:** ① suggest 1a (Task 2) · 1b bind (Task 3) · coverage (Task 4) · impact (Task 5) · stale (Task 6) · system-map SIDE (Task 7) · viewer API+UI (Task 8,9) · HTML ingest cho test (Task 1). Chạy/evidence = pipeline sếp (ngoài repo, không build lại). Tất cả mục spec §4 có task.

**Ranh giới thép:** Task 2 có `test_module_is_code_blind` (assert "gitnexus" không xuất hiện trong `qa/design.py`). Task 3 có `test_bind_freezes_expect` + assert runtime trong `bind_seams`. Đúng spec §9.

**Type consistency:** `Case` (design) dùng nguyên ở bind/suggest. `bind_seams(cases, flow_id) -> (tcs_list, trace)` khớp giữa Task 3 và Task 4. `to_tcs` keys = schema sếp (§5.1). `trace.json` keys khớp §5.2 (spec_section, seam{type,create,observe}, source_symbols, source_hash). `affected`/`check_stale` đọc đúng `trace.json`. Viewer đọc đúng `tcs.json`/`trace.json`/`knowledge/system/*.md`.

**Placeholder scan:** không có TBD/TODO; mọi step có code/lệnh thật.
