# Security-gom Track (`/testcase-security`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây type-track thứ 3 (`/testcase-security`) quét security có hệ thống (Injection/XSS · IDOR · Client-bypass · Error-disclosure) cho các màn 1 TestCase, oracle = bất biến an ninh phổ quát, code-blind.

**Architecture:** Khuôn giống a11y track. `security_lib.js` = **payload banks + oracle helpers thuần + probe** (không tự gọi HTTP — nhận result do driver fetch, để driver lo auth per-app). `build_security_report.py` in xlsx (khuôn `build_a11y_report.py`, tách Chi tiết/Cách fix + File ảnh). `build_bug_report.py` thêm `bug_type:"Security"`. Command `testcase-security.md` điều phối. Live-verify sau khi build.

**Tech Stack:** Node `playwright` + `pw_lib` (`getPage`,`shot`) + `pw_api` (`withApi`) · Python `openpyxl` · test = `node --test` + plain-python (KHÔNG pytest).

## Global Constraints

- **Oracle = bất biến an ninh PHỔ QUÁT, KHÔNG phải SPEC, KHÔNG phải code.** `specs.md` chỉ chọn màn (scope).
- **Mù code runtime:** không đọc code sản phẩm / GitNexus / `knowledge/system/**`. Chỉ quan sát response + DOM + trạng thái browser.
- **Verdict = `PASS` / `FAIL` / `未実施` — KHÔNG BAO GIỜ `SPEC-GAP`** (bất biến an ninh luôn định nghĩa kỳ vọng).
- **Data test tạo ra prefix `AIOT-TEST-SEC-*`** (để `/testcase-cleanup` quét). XSS marker = `window.__SEC_XSS`.
- **KHÔNG viết lại helper:** tái dùng `pw_lib`/`pw_api`. KHÔNG viết `.py` phụ trợ ngoài file plan nêu. KHÔNG `claude -p`.
- **Base dir mọi file:** `.claude/skills-scripts/testcase-evidence/` (gọi tắt `<E>/`). Repo root = `/Users/tritdd/Work/ThreeSides/master_qa`.
- **security_lib KHÔNG tự gọi HTTP** — probe IDOR/bypass/error nhận `{status, body}` do driver fetch; chỉ `probeInjection` cần `page`.
- Commit message kết bằng: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## File Structure

- Create `<E>/security_lib.js` — payload banks, oracle helpers (`isServerError`/`hasStackLeak`/`looksLikeData`/`xssFired`), probes (`probeInjection`/`probeIDOR`/`probeBypass`/`probeErrorDisclosure`), `finding()` normalizer.
- Create `<E>/security_lib.test.js` — node:test cho helpers + probeInjection trên fixture setContent.
- Create `<E>/build_security_report.py` — `security.results.json` → `<Case>.security.xlsx` (Findings + Đã quét).
- Create `<E>/test_build_security_report.py` — cột/tách/coverage/empty.
- Modify `<E>/build_bug_report.py:380,383` — thêm `"Security"` vào tuple + nâng nrows floor.
- Create `<E>/test_bug_report_security_type.py` — bug_type "Security" render được.
- Create `.claude/commands/testcase-security.md` — quy trình track.
- Modify `docs/STATE.md`, `docs/ROADMAP.md`, `docs/BUG-LOG.md`, `README.md`, `CLAUDE.md` — đăng ký track.

---

### Task 1: Payload banks + oracle helpers thuần (security_lib.js phần lõi)

**Files:**
- Create: `.claude/skills-scripts/testcase-evidence/security_lib.js`
- Test: `.claude/skills-scripts/testcase-evidence/security_lib.test.js`

**Interfaces:**
- Produces: `PAYLOADS` (object: `xss[]`,`sqli[]`,`template[]`,`csv[]`); `isServerError(status)→bool`; `hasStackLeak(body)→{leak:bool,kind:string,snippet:string}`; `looksLikeData(body)→bool`. Tất cả THUẦN (không browser/không network).

- [ ] **Step 1: Write the failing test**

Tạo `<E>/security_lib.test.js`:
```js
const { test } = require('node:test');
const assert = require('node:assert');
const { PAYLOADS, isServerError, hasStackLeak, looksLikeData } = require('./security_lib');

test('PAYLOADS có đủ 4 họ, XSS dùng marker window.__SEC_XSS', () => {
  for (const k of ['xss', 'sqli', 'template', 'csv']) {
    assert.ok(Array.isArray(PAYLOADS[k]) && PAYLOADS[k].length >= 3, `${k} phải có ≥3 payload`);
  }
  assert.ok(PAYLOADS.xss.some(p => p.includes('__SEC_XSS')), 'XSS phải bơm marker __SEC_XSS');
});

test('isServerError chỉ true cho 5xx', () => {
  assert.equal(isServerError(500), true);
  assert.equal(isServerError(503), true);
  assert.equal(isServerError(404), false);
  assert.equal(isServerError(200), false);
});

test('hasStackLeak bắt traceback/SQL/exception, bỏ qua body sạch', () => {
  assert.equal(hasStackLeak('Traceback (most recent call last):\n  File "x.py"').leak, true);
  assert.equal(hasStackLeak('django.db.utils.IntegrityError: null value').leak, true);
  assert.equal(hasStackLeak('SQLSTATE[23000]: Integrity constraint').leak, true);
  assert.equal(hasStackLeak('{"error":"not found"}').leak, false);
  assert.equal(hasStackLeak('').leak, false);
});

test('looksLikeData: object/array có field giống record thật → true; lỗi/rỗng → false', () => {
  assert.equal(looksLikeData({ id: 5, name: 'KH khác', email: 'a@b.c' }), true);
  assert.equal(looksLikeData([{ id: 1 }, { id: 2 }]), true);
  assert.equal(looksLikeData({ error: 'forbidden' }), false);
  assert.equal(looksLikeData({}), false);
  assert.equal(looksLikeData('Not Found'), false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd <E> && node --test security_lib.test.js`
Expected: FAIL — `Cannot find module './security_lib'`.

- [ ] **Step 3: Write minimal implementation**

Tạo `<E>/security_lib.js`:
```js
// security_lib.js — bất biến an ninh PHỔ QUÁT (black-box, mù code). Oracle helpers THUẦN + probe.
// KHÔNG tự gọi HTTP: probe IDOR/bypass/error nhận {status,body} do driver fetch (driver lo auth per-app).
// XSS marker = window.__SEC_XSS (bơm rồi đọc lại — chỉ quan sát browser, không đọc code).

const PAYLOADS = {
  xss: [
    '<img src=x onerror="window.__SEC_XSS=1">',
    '<svg onload="window.__SEC_XSS=1">',
    '"><script>window.__SEC_XSS=1</script>',
  ],
  sqli: ["' OR '1'='1", "'; DROP TABLE x;--", '" OR ""="'],
  template: ['${{7*7}}', '{{7*7}}', '#{7*7}'],
  csv: ['=2+2', '+2+2', '-2+2', '@SUM(1+1)'],
};

function isServerError(status) {
  return typeof status === 'number' && status >= 500 && status < 600;
}

// hasStackLeak: dấu hiệu lộ stack/SQL/traceback ra client (bất biến: KHÔNG được lộ).
const LEAK_PATTERNS = [
  [/Traceback \(most recent call last\)/, 'python-traceback'],
  [/\b(django\.\w+\.\w+Error|IntegrityError|OperationalError|ProgrammingError)\b/, 'django-exception'],
  [/SQLSTATE\[|SQL syntax|psql:|pg_query|near "/i, 'sql-error'],
  [/\b(NoMethodError|ActiveRecord::|RuntimeError|StandardError)\b/, 'ruby-exception'],
  [/ at .+\(.+:\d+:\d+\)/, 'js-stack'],
];
function hasStackLeak(body) {
  const s = typeof body === 'string' ? body : JSON.stringify(body || '');
  for (const [re, kind] of LEAK_PATTERNS) {
    const m = re.exec(s);
    if (m) return { leak: true, kind, snippet: s.slice(Math.max(0, m.index - 10), m.index + 80) };
  }
  return { leak: false, kind: '', snippet: '' };
}

// looksLikeData: body TRÔNG NHƯ record thật (object/array có field định danh) → IDOR có thể lộ data.
const DATA_KEYS = ['id', 'name', 'email', 'customer', 'uid', 'phone', 'code', 'title'];
function looksLikeData(body) {
  const recordLike = (o) =>
    o && typeof o === 'object' && !('error' in o) && Object.keys(o).some(k => DATA_KEYS.includes(k.toLowerCase()));
  if (Array.isArray(body)) return body.length > 0 && body.some(recordLike);
  return recordLike(body);
}

module.exports = { PAYLOADS, isServerError, hasStackLeak, looksLikeData };
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd <E> && node --test security_lib.test.js`
Expected: PASS — 4 tests.

- [ ] **Step 5: Commit**

```bash
cd <repo> && git add .claude/skills-scripts/testcase-evidence/security_lib.js .claude/skills-scripts/testcase-evidence/security_lib.test.js
git commit -m "security: payload banks + oracle helpers thuần (security_lib lõi)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Probes + finding normalizer (security_lib.js phần probe)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/security_lib.js`
- Test: `.claude/skills-scripts/testcase-evidence/security_lib.test.js`

**Interfaces:**
- Consumes: `isServerError`, `hasStackLeak`, `looksLikeData` (Task 1).
- Produces:
  - `async xssFired(page)→bool` (đọc `window.__SEC_XSS===1`); `async resetXss(page)` (xoá marker).
  - `async probeInjection(page, fieldLocator, payload, submit)→{payload, fired, serverError, reflectedAsText}` — `fieldLocator`=Playwright Locator, `submit`=async closure (bấm nút gửi + trả `{status}` nếu quan sát được, hoặc `null`).
  - `probeIDOR({status, body})→{status, leak}` — leak = `status===200 && looksLikeData(body)`.
  - `probeBypass({uiBlocks, apiStatus})→{uiBlocks, apiBlocks, parityOk}` — apiBlocks = `apiStatus>=400 && apiStatus<500`; parityOk = `!uiBlocks || apiBlocks`.
  - `probeErrorDisclosure({status, body})→{disclosed, kind, snippet}` — disclosed = `isServerError(status) || hasStackLeak(body).leak`.
  - `finding({family, payloadClass, where, url, severity, observed, fix, shot})→object` (chuẩn hoá 1 phát hiện).

- [ ] **Step 1: Write the failing test** (append vào `security_lib.test.js`)

```js
const { chromium } = require('playwright');
const {
  xssFired, resetXss, probeInjection, probeIDOR, probeBypass, probeErrorDisclosure, finding,
} = require('./security_lib');

test('probeInjection: XSS bơm vào ô CÓ execute → fired=true; ô escaped → fired=false', async () => {
  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    // trang "dễ dính": echo input vào innerHTML (XSS sống)
    await page.setContent('<input id="f"><button id="b">go</button><div id="out"></div>'
      + '<script>document.getElementById("b").onclick=()=>{'
      + 'document.getElementById("out").innerHTML=document.getElementById("f").value;};</script>');
    const submit = async () => { await page.click('#b'); await page.waitForTimeout(50); return null; };
    const r = await probeInjection(page, page.locator('#f'), '<img src=x onerror="window.__SEC_XSS=1">', submit);
    assert.equal(r.fired, true, 'trang echo innerHTML phải làm XSS fired');

    // trang "an toàn": echo vào textContent (escaped)
    await page.setContent('<input id="f2"><button id="b2">go</button><div id="out2"></div>'
      + '<script>document.getElementById("b2").onclick=()=>{'
      + 'document.getElementById("out2").textContent=document.getElementById("f2").value;};</script>');
    const submit2 = async () => { await page.click('#b2'); await page.waitForTimeout(50); return null; };
    const r2 = await probeInjection(page, page.locator('#f2'), '<img src=x onerror="window.__SEC_XSS=1">', submit2);
    assert.equal(r2.fired, false, 'trang textContent KHÔNG được để XSS fired');
  } finally {
    await browser.close();
  }
});

test('probeIDOR: 200+data → leak; 403 → không leak', () => {
  assert.equal(probeIDOR({ status: 200, body: { id: 9, name: 'người khác' } }).leak, true);
  assert.equal(probeIDOR({ status: 403, body: { error: 'forbidden' } }).leak, false);
  assert.equal(probeIDOR({ status: 404, body: 'Not Found' }).leak, false);
});

test('probeBypass: UI chặn mà API KHÔNG chặn → parityOk=false (FAIL)', () => {
  assert.equal(probeBypass({ uiBlocks: true, apiStatus: 200 }).parityOk, false);
  assert.equal(probeBypass({ uiBlocks: true, apiStatus: 403 }).parityOk, true);
  assert.equal(probeBypass({ uiBlocks: false, apiStatus: 200 }).parityOk, true);
});

test('probeErrorDisclosure: 500 hoặc stack leak → disclosed', () => {
  assert.equal(probeErrorDisclosure({ status: 500, body: 'x' }).disclosed, true);
  assert.equal(probeErrorDisclosure({ status: 200, body: 'Traceback (most recent call last):' }).disclosed, true);
  assert.equal(probeErrorDisclosure({ status: 404, body: '{"detail":"not found"}' }).disclosed, false);
});

test('finding chuẩn hoá đủ field', () => {
  const f = finding({ family: 'xss', payloadClass: 'xss', where: 'ô Tên', url: '/coupons/new/',
    severity: 'High', observed: 'payload execute', fix: 'escape output', shot: 'shots/x.png' });
  assert.equal(f.family, 'xss'); assert.equal(f.severity, 'High'); assert.equal(f.shot, 'shots/x.png');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd <E> && node --test security_lib.test.js`
Expected: FAIL — `xssFired`/`probeInjection`… không export.

- [ ] **Step 3: Write minimal implementation** (append vào `security_lib.js`, TRƯỚC `module.exports`, và cập nhật exports)

```js
async function xssFired(page) {
  return await page.evaluate(() => window.__SEC_XSS === 1);
}
async function resetXss(page) {
  await page.evaluate(() => { try { delete window.__SEC_XSS; } catch (_) { window.__SEC_XSS = undefined; } });
}

// probeInjection: reset marker → điền payload → submit → quan sát fired/serverError/phản-chiếu-dạng-text.
async function probeInjection(page, fieldLocator, payload, submit) {
  await resetXss(page);
  await fieldLocator.fill(payload, { timeout: 8000 });
  let status = null;
  try { const s = await submit(); status = s && typeof s.status === 'number' ? s.status : null; } catch (_) {}
  const fired = await xssFired(page);
  const reflectedAsText = await page.evaluate((p) => document.body && document.body.innerText.includes(p), payload)
    .catch(() => false);
  return { payload, fired, serverError: isServerError(status), reflectedAsText };
}

function probeIDOR(result) {
  const { status, body } = result || {};
  return { status, leak: status === 200 && looksLikeData(body) };
}

function probeBypass({ uiBlocks, apiStatus }) {
  const apiBlocks = typeof apiStatus === 'number' && apiStatus >= 400 && apiStatus < 500;
  return { uiBlocks: !!uiBlocks, apiBlocks, parityOk: !uiBlocks || apiBlocks };
}

function probeErrorDisclosure(result) {
  const { status, body } = result || {};
  const leak = hasStackLeak(body);
  return { disclosed: isServerError(status) || leak.leak, kind: leak.kind, snippet: leak.snippet };
}

function finding({ family, payloadClass, where, url, severity, observed, fix, shot }) {
  return { family, payloadClass: payloadClass || '', where: where || '', url: url || '',
    severity: severity || 'Medium', observed: observed || '', fix: fix || '', shot: shot || '' };
}
```

Cập nhật `module.exports`:
```js
module.exports = {
  PAYLOADS, isServerError, hasStackLeak, looksLikeData,
  xssFired, resetXss, probeInjection, probeIDOR, probeBypass, probeErrorDisclosure, finding,
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd <E> && node --test security_lib.test.js`
Expected: PASS — 8 tests (4 Task1 + 4 mới… thực tế 4+5=9 test; đủ pass, fail 0).

- [ ] **Step 5: Commit**

```bash
cd <repo> && git add .claude/skills-scripts/testcase-evidence/security_lib.js .claude/skills-scripts/testcase-evidence/security_lib.test.js
git commit -m "security: probes (injection/IDOR/bypass/error) + finding normalizer

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: build_security_report.py + test

**Files:**
- Create: `.claude/skills-scripts/testcase-evidence/build_security_report.py`
- Test: `.claude/skills-scripts/testcase-evidence/test_build_security_report.py`

**Interfaces:**
- Consumes: `security.results.json` schema `{meta:{case,date,tester}, screens:[{name,app,url,result, findings:[{family,payloadClass,where,url,severity,observed,fix,shot}]}]}`.
- Produces: `<Case>.security.xlsx` — sheet "Findings" (cột: Màn·App·URL·Họ·Payload-class·Mức·Nơi·**Chi tiết (quan sát)**·**Cách fix**·**File ảnh**·Evidence) + sheet "Đã quét" (coverage: Màn·App·URL·Verdict·Số finding High).

- [ ] **Step 1: Write the failing test**

Tạo `<E>/test_build_security_report.py`:
```python
# Chạy: python3 test_build_security_report.py
import json, os, subprocess, sys, tempfile
from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "build_security_report.py")

def _run(results, name="T.security.xlsx"):
    d = tempfile.mkdtemp()
    rp = os.path.join(d, "security.results.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)
    out = os.path.join(d, name)
    subprocess.run([sys.executable, SCRIPT, rp, out], check=True)
    return load_workbook(out)

def test_findings_columns_and_split():
    results = {"meta": {"case": "TC11", "date": "2026-07-17", "tester": "QA-sec"},
        "screens": [{"name": "② 登録", "app": "ticket", "url": "/coupons/new/", "result": "FAIL",
            "findings": [
                {"family": "serious-high", "payloadClass": "sqli", "where": "ô Tên", "url": "/coupons/new/",
                 "severity": "Medium", "observed": "500 khi nhập '; DROP", "fix": "dùng prepared statement",
                 "shot": "shots/sec-TC11__coupon-new__sqli.png"},
                {"family": "xss", "payloadClass": "xss", "where": "ô Ghi chú", "url": "/coupons/new/",
                 "severity": "High", "observed": "payload execute (window.__SEC_XSS=1)", "fix": "escape output",
                 "shot": ""},
            ]}]}
    ws = _run(results)["Findings"]
    H = [ws.cell(1, c).value for c in range(1, 12)]
    assert H[3] == "Họ", H
    assert "Chi tiết" in H[7]
    assert H[8] == "Cách fix"
    assert H[9] == "File ảnh"
    # High phải sắp TRƯỚC Medium (severity-sort)
    assert ws.cell(2, 6).value == "High", ws.cell(2, 6).value
    # Chi tiết ≠ Cách fix (tách riêng)
    assert ws.cell(2, 8).value and ws.cell(2, 9).value and ws.cell(2, 8).value != ws.cell(2, 9).value
    # File ảnh = basename (dò ngược), rỗng khi không shot
    assert ws.cell(2, 10).value in ("", None)                # High finding không shot
    assert ws.cell(3, 10).value == "sec-TC11__coupon-new__sqli.png"

def test_coverage_sheet_and_empty():
    ws = _run({"meta": {"case": "E"}, "screens": [
        {"name": "① 一覧", "app": "ticket", "url": "/coupons/", "result": "PASS", "findings": []}]})
    assert "Đã quét" in ws.sheetnames
    cov = ws["Đã quét"]
    assert cov.cell(4, 4).value == "PASS"
    fw = ws["Findings"]
    assert fw.cell(2, 1).value == "Không có finding security nào ở các màn đã quét."

def main():
    test_findings_columns_and_split()
    test_coverage_sheet_and_empty()
    print("✅ test_build_security_report PASS (2 tests)")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd <E> && python3 test_build_security_report.py`
Expected: FAIL — `build_security_report.py` chưa tồn tại (`No such file`).

- [ ] **Step 3: Write minimal implementation**

Tạo `<E>/build_security_report.py`:
```python
#!/usr/bin/env python3
"""build_security_report.py — security.results.json -> <Case>.security.xlsx (Findings + Đã quét).
Oracle = bất biến an ninh phổ quát (không phải spec). CƠ KHÍ, không reasoning."""
import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage

SEV_ORDER = {"High": 0, "Medium": 1, "Low": 2}
SEV_FILL = {"High": "C0392B", "Medium": "E67E22", "Low": "F1C40F"}
HEADERS = ["Màn", "App", "URL", "Họ", "Payload-class", "Mức", "Nơi (field/endpoint)",
           "Chi tiết (quan sát được)", "Cách fix", "File ảnh", "Evidence"]


def build(results_path, out_path):
    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)
    base = os.path.dirname(os.path.abspath(results_path))
    top = Alignment(wrap_text=True, vertical="top")
    wb = Workbook(); ws = wb.active; ws.title = "Findings"
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(1, c, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2C3E50")
    r = 2
    for scr in data.get("screens", []):
        for fdg in sorted(scr.get("findings", []), key=lambda x: SEV_ORDER.get(x.get("severity"), 9)):
            ws.cell(r, 1, scr.get("name", "")); ws.cell(r, 2, scr.get("app", "")); ws.cell(r, 3, scr.get("url", ""))
            ws.cell(r, 4, fdg.get("family", "")); ws.cell(r, 5, fdg.get("payloadClass", ""))
            mc = ws.cell(r, 6, fdg.get("severity", ""))
            mc.fill = PatternFill("solid", fgColor=SEV_FILL.get(fdg.get("severity"), "BDC3C7"))
            ws.cell(r, 7, fdg.get("where", "")).alignment = top
            ws.cell(r, 8, fdg.get("observed", "")).alignment = top   # Chi tiết (quan sát)
            ws.cell(r, 9, fdg.get("fix", "")).alignment = top        # Cách fix (tách riêng)
            shot = fdg.get("shot", "")
            ws.cell(r, 10, os.path.basename(shot) if shot else "").alignment = top
            if shot and os.path.exists(os.path.join(base, shot)):
                img = XLImage(os.path.join(base, shot)); img.width = 240; img.height = 150
                ws.add_image(img, f"K{r}")
            ws.row_dimensions[r].height = 150
            r += 1
    if r == 2:
        ws.cell(2, 1, "Không có finding security nào ở các màn đã quét.")
    for col, w in zip("ABCDEFGHIJK", (14, 9, 20, 14, 13, 8, 22, 40, 40, 30, 34)):
        ws.column_dimensions[col].width = w

    cov = wb.create_sheet("Đã quét")
    meta = data.get("meta", {})
    cov.cell(1, 1, f"SECURITY · {meta.get('case','')} · {meta.get('date','')} · {meta.get('tester','')}").font = Font(bold=True)
    for c, h in enumerate(["Màn", "App", "URL", "Verdict", "Finding High"], 1):
        cell = cov.cell(3, c, h); cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2C3E50")
    rr = 4
    for scr in data.get("screens", []):
        hi = sum(1 for x in scr.get("findings", []) if x.get("severity") == "High")
        cov.cell(rr, 1, scr.get("name", "")); cov.cell(rr, 2, scr.get("app", "")); cov.cell(rr, 3, scr.get("url", ""))
        cov.cell(rr, 4, scr.get("result", "")); cov.cell(rr, 5, hi)
        rr += 1
    for col, w in zip("ABCDE", (18, 10, 24, 10, 14)):
        cov.column_dimensions[col].width = w

    wb.save(out_path)
    print(f"✅ security report: {out_path} ({r - 2} finding)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: build_security_report.py <results.json> <out.xlsx>")
    build(sys.argv[1], sys.argv[2])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd <E> && python3 test_build_security_report.py`
Expected: PASS — `✅ test_build_security_report PASS (2 tests)`.

- [ ] **Step 5: Commit**

```bash
cd <repo> && git add .claude/skills-scripts/testcase-evidence/build_security_report.py .claude/skills-scripts/testcase-evidence/test_build_security_report.py
git commit -m "security: build_security_report.py (Findings + coverage, tách chi tiết/fix + file ảnh)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Đăng ký bug_type "Security" trong sổ bug

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/build_bug_report.py:380,383`
- Create: `.claude/skills-scripts/testcase-evidence/test_bug_report_security_type.py`

**Interfaces:**
- Consumes: cấu trúc `bug-he-thong.tcs.json` (bug object có `bug_type`).
- Produces: sổ bug chấp nhận `bug_type:"Security"` (đếm theo type không vỡ).

- [ ] **Step 1: Write the failing test**

Tạo `<E>/test_bug_report_security_type.py` (khuôn `test_bug_report_a11y_type.py` — đọc file đó trước để copy cấu trúc _run):
```python
# Chạy: python3 test_bug_report_security_type.py
import json, os, subprocess, sys, tempfile
from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "build_bug_report.py")

def test_security_bug_type_renders():
    bug = {"bug_id": "BUG-901", "id": "", "source": "TestCase-11",
           "screen": "Ticket — ② 登録", "pri": "High", "bug_type": "Security", "result": "FAIL",
           "title": "XSS: payload execute ở ô Ghi chú", "found_at": "2026-07-17", "status": "Mở",
           "fix_note": "", "retested_at": "", "pre": "-", "steps": "-", "expect": "escaped",
           "actual": "window.__SEC_XSS=1", "note": "sec", "before": None, "after": None}
    data = {"meta": {"project": "T", "module": "m", "issue": "i", "tester": "QA", "date": "2026/07/17", "env": "dev"},
            "shots_dir": ".", "tcs": [bug]}
    d = tempfile.mkdtemp()
    rp = os.path.join(d, "b.tcs.json"); out = os.path.join(d, "b.xlsx")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    subprocess.run([sys.executable, SCRIPT, rp, out], check=True)   # không raise = pass build
    wb = load_workbook(out)
    # sheet Danh sách Bug phải chứa bug Security
    found = any("Security" == c.value for s in wb.sheetnames for row in wb[s].iter_rows() for c in row)
    assert found, "bug_type Security phải xuất hiện trong sổ"
    print("✅ test_bug_report_security_type PASS")

if __name__ == "__main__":
    test_security_bug_type_renders()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd <E> && python3 test_bug_report_security_type.py`
Expected: FAIL hoặc raise — "Security" chưa trong tuple type nên đếm/vẽ theo type thiếu, hoặc assert không thấy. (Nếu build vẫn chạy nhưng đếm sai, chuyển sang Step 3.)

- [ ] **Step 3: Write minimal implementation**

Trong `<E>/build_bug_report.py` dòng 380, thêm `"Security"` vào tuple:
```python
    for i, k in enumerate(("Function", "UI", "Text", "Accessibility", "Visual", "Security")):
```
Dòng 383, nâng floor lên 6 (số loại bug_type):
```python
    nrows = max(len(services), 6)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd <E> && python3 test_bug_report_security_type.py`
Expected: PASS — `✅ test_bug_report_security_type PASS`.

Cũng chạy lại type test cũ để chắc không vỡ: `python3 test_bug_report_a11y_type.py && python3 test_bug_report_visual_type.py`
Expected: cả 2 PASS.

- [ ] **Step 5: Commit**

```bash
cd <repo> && git add .claude/skills-scripts/testcase-evidence/build_bug_report.py .claude/skills-scripts/testcase-evidence/test_bug_report_security_type.py
git commit -m "security: đăng ký bug_type Security trong sổ bug (tuple + nrows floor)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Command doc `testcase-security.md` + đăng ký track vào docs

**Files:**
- Create: `.claude/commands/testcase-security.md`
- Modify: `docs/STATE.md`, `docs/ROADMAP.md`, `docs/BUG-LOG.md`, `README.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: `security_lib.js` (Task 1-2), `build_security_report.py` (Task 3), bug_type Security (Task 4).
- Produces: quy trình `/testcase-security` cho model chạy runtime.

- [ ] **Step 1: Tạo command doc** (không có test tự động — đây là doc; "test" = đọc lại khớp spec)

Tạo `.claude/commands/testcase-security.md`:
```markdown
# /testcase-security — Test Security (bất biến an ninh, black-box) một TestCase

Quét security các màn spec đang test đụng tới, theo checklist 4 họ. **Track RIÊNG**, KHÔNG trộn
PASS/FAIL functional. Oracle = **bất biến an ninh PHỔ QUÁT** (không phải spec). Mù code.

## Cách dùng
`/testcase-security wtf-is-this/TestCase-XX`

## TIẾT KIỆM TOKEN
Dùng lại `.claude/skills-scripts/testcase-evidence/`: `pw_lib` (`getPage`,`shot`), `pw_api` (`withApi`),
`security_lib` (`PAYLOADS`, `probeInjection/probeIDOR/probeBypass/probeErrorDisclosure`, `finding`),
`build_security_report.py`. KHÔNG viết lại. Setup 1 lần: `cd .claude/skills-scripts/testcase-evidence && npm i`.

## Nguyên tắc (2 tường)
- **Oracle = bất biến an ninh phổ quát.** `specs.md` chỉ chọn màn (scope), KHÔNG làm oracle.
- **Mù code.** Không đọc code / GitNexus / `knowledge/system/**`. Chỉ quan sát response + DOM + browser.

## 4 họ + oracle (FAIL khi bất biến bị phá)
| Họ | Probe | FAIL khi |
|---|---|---|
| Injection/XSS | `PAYLOADS.xss/sqli/template/csv` vào ô text → `probeInjection` | `fired` (XSS execute) / `serverError` (500) / phản chiếu chưa escaped |
| IDOR | GET id người khác/khác institute/không tồn tại → `probeIDOR` | `leak` (200 + data thật) |
| Client-bypass | quan sát UI guard (disabled/max/nút vắng) → gọi thẳng API → `probeBypass` | `!parityOk` (UI chặn mà API không) |
| Error-disclosure | input rác/param dị → `probeErrorDisclosure` | `disclosed` (500/traceback/SQL/stack) |

## Quy trình
1. **Scope:** đọc `specs.md §3` → app/màn/field. Có `tcs.json` đã chạy → tái dùng màn/URL/field.
2. **Seam màn→URL/field:** `knowledge/*.md` approved (như functional). Chưa có → dừng, nhắc `/testcase-systemdoc`.
3. **Probe** (driver inline như /testcase-run): mỗi màn × họ áp dụng được. Data GHI ra prefix **`AIOT-TEST-SEC-*`**.
   - Injection: lặp `PAYLOADS.*` vào từng ô text; `submit` = closure bấm nút gửi.
   - IDOR/Error: `withApi` (Rails target) hoặc `context.request` (Django, kèm cookie session) GET → đưa `{status,body}` vào probe.
   - Bypass: đọc guard trên DOM (disabled/max/404) → `uiBlocks`; gọi API bỏ guard → `apiStatus`.
   - Evidence: ảnh khoanh chỗ (tái dùng pattern `shotViolation` của a11y_lib) hoặc lưu request+response text.
4. **Verdict/màn:** PASS (mọi bất biến giữ) · FAIL (≥1 phá) · 未実施 (không probe được).
   ⚠️ Security **KHÔNG BAO GIỜ** `SPEC-GAP` (bất biến an ninh luôn định nghĩa kỳ vọng).
5. **Viết `<folder>/security.results.json`**: `{meta:{case,date,tester}, screens:[{name,app,url,result,
   findings:[finding(...)]}]}`. Mỗi finding critical → severity High.
6. **Build report:** `python3 .../build_security_report.py <folder>/security.results.json <folder>/<Tên>.security.xlsx`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/(màn×họ×payload-class)** → append `bug-he-thong.tcs.json`
   (`bug_type:"Security"`, `result:"FAIL"`, `pri` = High cho XSS-fired/bypass/IDOR-leak, Medium cho error-disclosure/500,
   `screen`="<App> — <Màn>", `source`=TestCase-XX, `title`="<Họ>: <hành vi>", `before:null`+`note`, `after`=ảnh).
   Build lại `bug-he-thong.xlsx`.
8. **Cleanup:** liệt kê id `AIOT-TEST-SEC-*` đã tạo → nhắc `/testcase-cleanup`.
9. **Báo cáo:** bảng màn × họ × verdict; liệt kê FAIL + bug đã đẩy. Mô tả **hành vi** (payload + quan sát), KHÔNG file:line.

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG.**
- [ ] Verdict chỉ dựa bất biến an ninh + quan sát (không specs làm oracle, không SPEC-GAP)?
- [ ] Mọi data test đã prefix `AIOT-TEST-SEC-*` chưa? Đã nhắc cleanup id đã tạo chưa?
- [ ] Đã dedup 1 bug/(màn×họ×payload-class) trước khi append sổ chưa?
```

- [ ] **Step 2: Đăng ký vào docs** (mỗi file thêm 1-2 dòng — đọc file trước rồi chèn cho khớp giọng)

- `README.md`: mục liệt kê track (chỗ đã ghi `/testcase-a11y`, `/testcase-visual`) → thêm dòng
  `/testcase-security` (oracle=bất biến an ninh, mù code).
- `CLAUDE.md` (master_qa): mục "Cách xài" bước 5-6 (a11y/visual) → thêm bước 7:
  `7. (tuỳ chọn) /testcase-security wtf-is-this/TestCase-XX → quét security (4 họ) → report + sổ bug. Track RIÊNG, oracle = bất biến an ninh, mù code.`
- `docs/ROADMAP.md`: bảng type-track (§3) đổi Security từ `🟡 rút thành checklist` → `✅ done (live-verify treo)`;
  lưới §2 đổi Security `🟡 làm rải rác` → `✅ /testcase-security`.
- `docs/BUG-LOG.md`: thêm 1 dòng ghi chú cạnh block "Bug Visual": 
  `> Bug Security (do /testcase-security sinh): result luôn FAIL · before=null + note lý do · dedup 1 bug/(màn×họ×payload-class).`
- `docs/STATE.md`: ghi mục "đang làm" = Security track built (live-verify treo — cần chạy `/testcase-security wtf-is-this/TestCase-11`).

- [ ] **Step 3: Chạy toàn bộ test suite (không vỡ)**

Run: `cd <E> && node --test security_lib.test.js a11y_lib.test.js visual_lib.test.js explorer.test.js && python3 test_build_security_report.py && python3 test_build_a11y_report.py && python3 test_bug_report_security_type.py && python3 test_bug_report_a11y_type.py && python3 test_bug_report_visual_type.py`
Expected: tất cả PASS, fail 0.

- [ ] **Step 4: Commit**

```bash
cd <repo> && git add .claude/commands/testcase-security.md README.md CLAUDE.md docs/ROADMAP.md docs/BUG-LOG.md docs/STATE.md
git commit -m "security: command doc /testcase-security + đăng ký track vào docs

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Live-verify (SAU khi 5 task xong — nhịp riêng, cần dev remote)

Không phải task trong plan (cần Docker/dev + tạo data thật). Sau build: chạy `/testcase-security wtf-is-this/TestCase-11`
trên ticket dev, kiểm mỗi họ probe chạy end-to-end + report + (nếu FAIL) đẩy sổ bug. Y như đã làm cho a11y/Visual.
Cleanup `AIOT-TEST-SEC-*` sau verify.

---

## Self-Review

**Spec coverage:** §2 tường thép → Global Constraints + Task5 checklist. §3 4 họ → Task1(banks/helpers)+Task2(probes)+Task5(command). §4.1 security_lib → Task1-2. §4.2 command → Task5. §4.3 report → Task3. §4.4 bug_type → Task4. §5 an toàn (AIOT-TEST-SEC + cleanup) → Global Constraints + Task5 command. §6 ngoài phạm vi → không task (đúng, YAGNI). §7 test → mỗi task có test; live-verify tách nhịp. ✅ đủ.

**Placeholder scan:** không có TBD/TODO; mọi step có code thật/lệnh thật. ✅

**Type consistency:** `finding({...})` fields (family,payloadClass,where,url,severity,observed,fix,shot) khớp giữa Task2 (định nghĩa) ↔ Task3 (report đọc `observed`→Chi tiết, `fix`→Cách fix, `shot`→File ảnh) ↔ Task5 (command mô tả). `probeBypass` dùng `{uiBlocks,apiStatus}`→`{parityOk}` nhất quán Task2↔command. results.json schema nhất quán Task3↔Task5. ✅
