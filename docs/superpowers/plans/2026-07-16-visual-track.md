# Track Visual (`/testcase-visual`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Type test thứ 3 — Visual regression (black-box) — cho master_qa: so ảnh màn với baseline người-duyệt, che vùng động, xuất report + đẩy FAIL vào sổ bug. Mask sinh tự động ở build-time authoring.

**Architecture:** `visual_lib.js` (capture-masked + detect-dynamic + compare-pixel qua pixelmatch) → command `/testcase-visual` đọc `specs.md` chọn màn, đọc `mask:` từ `knowledge/`, chụp masked, so với `baselines/<app>/<slug>.png` (commit git) → report xlsx + sổ bug. `/testcase-systemdoc`+`explorer.js` được nâng để auto-detect vùng động → emit `mask:` vào knowledge doc. Bám khuôn track a11y.

**Tech Stack:** Node + Playwright (mask screenshot sẵn) + `pixelmatch@^5` + `pngjs@^7` · Python 3 + openpyxl · test JS = `node:test`, test Python = plain assert.

## Global Constraints

- **Black-box:** chỉ đọc pixel màn đã render — không đọc code sản phẩm / GitNexus lúc runtime. (Tường 2)
- **Oracle = baseline PNG người-duyệt, KHÔNG phải SPEC.** `specs.md` chỉ dùng chọn màn (scope). (Tường 1)
- **Verdict:** `PASS` (diffRatio ≤ ngưỡng) · `FAIL` (>) · `未実施` (không vào được màn) · `NEW-BASELINE` (chưa có chuẩn). **KHÔNG BAO GIỜ SPEC-GAP.**
- **Ngưỡng mặc định:** `diffRatio > 0.001` (0.1% pixel khác sau mask) = FAIL. pixelmatch per-pixel `threshold: 0.1`.
- **Baseline:** `baselines/<app>/<slug>.png` ở **gốc repo**, commit git, luôn là ảnh **đã mask**. Repo root = `path.resolve(__dirname,'../../../')` từ script dir.
- **Dedup sổ bug:** 1 bug / màn FAIL (không tách theo vùng). NEW-BASELINE / 未実施 KHÔNG vào sổ bug.
- **Deliverable** ở `wtf-is-this/<Case>/`; script ở `.claude/skills-scripts/testcase-evidence/` (viết tắt `S=` dưới); baseline ở `baselines/`.
- **KHÔNG file input mới do người dùng viết** — chỉ 1 `specs.md`. **KHÔNG mask tay** — mask do authoring sinh.
- Lệnh chạy từ **repo root** `master_qa/`.

---

### Task 1: `visual_lib.compareToBaseline` + deps (core diff, deterministic)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/package.json`
- Create: `.claude/skills-scripts/testcase-evidence/visual_lib.js`
- Test: `.claude/skills-scripts/testcase-evidence/visual_lib.test.js`

**Interfaces:**
- Consumes: `pixelmatch` (v5, CJS default export), `pngjs` (`{PNG}`), `fs`.
- Produces:
  - `slugify(url) -> string` (URL path → slug, `/booking?x=1` → `booking-x-1`, root → `root`).
  - `baselinePath(app, url) -> string` (absolute `<repoRoot>/baselines/<app>/<slug>.png`).
  - `compareToBaseline(curPngPath, basePngPath, diffOutPath, opts={}) -> { diffRatio, diffPixels, total, sizeMismatch, diffPath }`. Dims khác nhau → `{sizeMismatch:true, diffRatio:1, diffPath:null}` (không gọi pixelmatch). `opts.threshold` mặc định `0.1`.

- [ ] **Step 1: Cài deps**

Run:
```bash
cd .claude/skills-scripts/testcase-evidence && npm i pixelmatch@^5 pngjs@^7
```
Expected: `package.json` `dependencies` có `pixelmatch` (^5) + `pngjs` (^7). (pixelmatch ^5 vì ^6 là ESM-only, `require()` sẽ vỡ.)

- [ ] **Step 2: Viết test thất bại**

Create `visual_lib.test.js`:
```js
const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { PNG } = require('pngjs');
const { slugify, compareToBaseline } = require('./visual_lib');

function solidPng(w, h, r, g, b) {
  const png = new PNG({ width: w, height: h });
  for (let i = 0; i < w * h; i++) {
    png.data[i * 4] = r; png.data[i * 4 + 1] = g; png.data[i * 4 + 2] = b; png.data[i * 4 + 3] = 255;
  }
  return PNG.sync.write(png);
}

test('slugify: URL path -> slug', () => {
  assert.equal(slugify('/booking'), 'booking');
  assert.equal(slugify('https://x.com/coupon-reports/sales/'), 'coupon-reports-sales');
  assert.equal(slugify('/'), 'root');
});

test('compareToBaseline: ảnh giống hệt -> diffRatio 0', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'vis-'));
  const a = path.join(d, 'a.png'), b = path.join(d, 'b.png'), o = path.join(d, 'diff.png');
  fs.writeFileSync(a, solidPng(20, 20, 255, 255, 255));
  fs.writeFileSync(b, solidPng(20, 20, 255, 255, 255));
  const r = compareToBaseline(a, b, o);
  assert.equal(r.diffRatio, 0);
  assert.equal(r.sizeMismatch, false);
});

test('compareToBaseline: ảnh khác -> diffRatio > 0 + diff file', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'vis-'));
  const a = path.join(d, 'a.png'), b = path.join(d, 'b.png'), o = path.join(d, 'diff.png');
  fs.writeFileSync(a, solidPng(20, 20, 255, 255, 255));
  fs.writeFileSync(b, solidPng(20, 20, 0, 0, 0));
  const r = compareToBaseline(a, b, o);
  assert.ok(r.diffRatio > 0.9, 'toàn ảnh khác -> ratio cao: ' + r.diffRatio);
  assert.ok(fs.existsSync(o), 'phải ghi diff image');
});

test('compareToBaseline: kích thước khác -> sizeMismatch', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'vis-'));
  const a = path.join(d, 'a.png'), b = path.join(d, 'b.png'), o = path.join(d, 'diff.png');
  fs.writeFileSync(a, solidPng(20, 20, 255, 255, 255));
  fs.writeFileSync(b, solidPng(30, 30, 255, 255, 255));
  const r = compareToBaseline(a, b, o);
  assert.equal(r.sizeMismatch, true);
  assert.equal(r.diffRatio, 1);
});
```

- [ ] **Step 3: Chạy test — xác nhận FAIL**

Run: `cd .claude/skills-scripts/testcase-evidence && node --test visual_lib.test.js`
Expected: FAIL — `Cannot find module './visual_lib'`.

- [ ] **Step 4: Viết `visual_lib.js` (phần Task 1)**

Create `visual_lib.js`:
```js
// visual_lib.js — Visual regression black-box: chỉ đọc pixel màn đã render. Oracle = baseline người-duyệt.
const fs = require('fs');
const path = require('path');
const pixelmatch = require('pixelmatch');
const { PNG } = require('pngjs');

const REPO_ROOT = path.resolve(__dirname, '../../../');

function slugify(url) {
  const p = String(url).replace(/^https?:\/\/[^/]+/, '').split('?')[0];
  const s = p.replace(/[^a-z0-9]+/gi, '-').replace(/^-+|-+$/g, '').toLowerCase();
  return s || 'root';
}

function baselinePath(app, url) {
  return path.join(REPO_ROOT, 'baselines', app, slugify(url) + '.png');
}

function compareToBaseline(curPath, basePath, diffOutPath, opts = {}) {
  const cur = PNG.sync.read(fs.readFileSync(curPath));
  const base = PNG.sync.read(fs.readFileSync(basePath));
  if (cur.width !== base.width || cur.height !== base.height) {
    return { diffRatio: 1, diffPixels: -1, total: -1, sizeMismatch: true, diffPath: null };
  }
  const { width, height } = cur;
  const diff = new PNG({ width, height });
  const diffPixels = pixelmatch(cur.data, base.data, diff.data, width, height,
    { threshold: opts.threshold != null ? opts.threshold : 0.1 });
  fs.mkdirSync(path.dirname(diffOutPath), { recursive: true });
  fs.writeFileSync(diffOutPath, PNG.sync.write(diff));
  const total = width * height;
  return { diffRatio: diffPixels / total, diffPixels, total, sizeMismatch: false, diffPath: diffOutPath };
}

module.exports = { slugify, baselinePath, compareToBaseline, REPO_ROOT };
```

- [ ] **Step 5: Chạy test — xác nhận PASS**

Run: `cd .claude/skills-scripts/testcase-evidence && node --test visual_lib.test.js`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/{package.json,package-lock.json,visual_lib.js,visual_lib.test.js}
git commit -m "feat(visual): visual_lib.compareToBaseline (pixelmatch) + slugify/baselinePath"
```

---

### Task 2: `visual_lib.captureMasked` + `detectDynamic` (cần Playwright page)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/visual_lib.js`
- Modify: `.claude/skills-scripts/testcase-evidence/visual_lib.test.js`

**Interfaces:**
- Consumes: một Playwright `page`, `chromium` (test).
- Produces:
  - `captureMasked(page, outPath, maskSelectors=[]) -> outPath` — chụp full-page, che các `maskSelectors` bằng Playwright `screenshot({mask})` (Playwright tô hộp hồng lên vùng mask → ổn định giữa các lần).
  - `detectDynamic(page, opts={}) -> [{x,y,width,height, selector}]` — chụp cùng màn 2 lần cách nhau `opts.gapMs`(mặc định 400), pixel-diff → gom vùng khác → trả bounding box + best-effort `selector` (qua `elementFromPoint` tại tâm box). Vùng nào KHÔNG map được selector → `selector:null` (người duyệt xử).

- [ ] **Step 1: Thêm test thất bại**

Append vào `visual_lib.test.js`:
```js
const { chromium } = require('playwright');
const { captureMasked, detectDynamic } = require('./visual_lib');

test('captureMasked: chụp có mask không vỡ + ra file PNG', async () => {
  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await page.setContent('<div id="a">tĩnh</div><div id="dyn">x</div>');
    const d = fs.mkdtempSync(path.join(os.tmpdir(), 'vis-'));
    const out = path.join(d, 'shot.png');
    await captureMasked(page, out, ['#dyn']);
    assert.ok(fs.existsSync(out) && fs.statSync(out).size > 0, 'phải ra PNG');
  } finally { await browser.close(); }
});

test('detectDynamic: bắt được phần tử tự đổi giữa 2 lần chụp', async () => {
  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    // #clock tự đổi text mỗi 100ms -> vùng động; #static đứng yên
    await page.setContent(`<div id="static" style="height:40px">STATIC</div>
      <div id="clock" style="height:40px">0</div>
      <script>let n=0;setInterval(()=>{document.getElementById('clock').textContent=(++n)+' '+Math.random();},100);</script>`);
    const regions = await detectDynamic(page, { gapMs: 400 });
    assert.ok(regions.length >= 1, 'phải tìm ra ≥1 vùng động');
    // vùng động phải nằm ở nửa dưới (clock), không phải static ở trên
    assert.ok(regions.some(r => r.y >= 30), 'vùng động phải ở khu #clock: ' + JSON.stringify(regions));
  } finally { await browser.close(); }
});
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Run: `node --test visual_lib.test.js`
Expected: FAIL — `captureMasked is not a function`.

- [ ] **Step 3: Viết thêm vào `visual_lib.js`**

Thêm 2 hàm trước `module.exports`, và cập nhật export:
```js
async function captureMasked(page, outPath, maskSelectors = []) {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  const masks = maskSelectors.map(s => page.locator(s));
  await page.screenshot({ path: outPath, fullPage: true, mask: masks, animations: 'disabled' });
  return outPath;
}

async function _shotBuffer(page) {
  return await page.screenshot({ fullPage: true, animations: 'disabled' });
}

// Gom pixel khác thành bounding boxes thô (bao toàn bộ vùng khác trong mỗi hàng liên tục).
async function detectDynamic(page, opts = {}) {
  const gap = opts.gapMs != null ? opts.gapMs : 400;
  const b1 = PNG.sync.read(await _shotBuffer(page));
  await page.waitForTimeout(gap);
  const b2 = PNG.sync.read(await _shotBuffer(page));
  if (b1.width !== b2.width || b1.height !== b2.height) return [];
  const { width, height } = b1;
  const diff = new PNG({ width, height });
  const n = pixelmatch(b1.data, b2.data, diff.data, width, height, { threshold: 0.1 });
  if (n === 0) return [];
  // bounding box của toàn bộ pixel khác (đơn giản, đủ cho v1 — người duyệt tinh chỉnh)
  let minX = width, minY = height, maxX = 0, maxY = 0;
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    const i = (y * width + x) * 4;
    if (diff.data[i] === 255 && diff.data[i + 1] === 0) { // pixelmatch tô đỏ chỗ khác
      if (x < minX) minX = x; if (x > maxX) maxX = x;
      if (y < minY) minY = y; if (y > maxY) maxY = y;
    }
  }
  const box = { x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1 };
  const dsf = Number(process.env.DSF || 2);
  const cx = (box.x + box.width / 2) / dsf, cy = (box.y + box.height / 2) / dsf; // ảnh scale theo DSF -> CSS px
  const selector = await page.evaluate(([x, y]) => {
    const el = document.elementFromPoint(x, y);
    if (!el) return null;
    if (el.id) return '#' + el.id;
    const cls = (el.className && el.className.toString().trim().split(/\s+/)[0]) || '';
    return cls ? el.tagName.toLowerCase() + '.' + cls : el.tagName.toLowerCase();
  }, [cx, cy]).catch(() => null);
  return [{ ...box, selector }];
}
```
Và đổi export cuối file thành:
```js
module.exports = { slugify, baselinePath, compareToBaseline, captureMasked, detectDynamic, REPO_ROOT };
```

- [ ] **Step 4: Chạy test — xác nhận PASS**

Run: `node --test visual_lib.test.js`
Expected: PASS (6 tests). Nếu chromium thiếu → `npx playwright install chromium` rồi chạy lại.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/{visual_lib.js,visual_lib.test.js}
git commit -m "feat(visual): captureMasked (Playwright mask) + detectDynamic (double-snapshot)"
```

---

### Task 3: `build_visual_report.py` — xuất `<Case>.visual.xlsx`

**Files:**
- Create: `.claude/skills-scripts/testcase-evidence/build_visual_report.py`
- Test: `.claude/skills-scripts/testcase-evidence/test_build_visual_report.py`

**Interfaces:**
- Consumes: `visual.results.json` — schema:
  ```json
  { "meta": {"case":"TestCase-11","date":"2026-07-16","tester":"QA-Server-visual"},
    "screens": [
      {"name":"Đặt lịch","app":"pro","url":"/reservations","result":"FAIL","diff_ratio":0.032,
       "baseline":"baselines/pro/reservations.png","current":"shots/vis_reservations_cur.png",
       "diff":"shots/vis_reservations_diff.png"} ] } }
  ```
- Produces: CLI `python3 build_visual_report.py <results.json> <out.xlsx>` → sheet `Visual` (mỗi màn 1 dòng: tên/app/url/verdict/diff% + 3 ảnh baseline|current|diff) + sheet `Màn quét` (per-screen verdict).

- [ ] **Step 1: Viết test thất bại**

Create `test_build_visual_report.py`:
```python
# Chạy: python3 test_build_visual_report.py
import json, os, subprocess, sys, tempfile
from openpyxl import load_workbook
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "build_visual_report.py")

def main():
    results = {"meta": {"case": "T", "date": "2026-07-16", "tester": "QA"},
        "screens": [
            {"name": "Đặt lịch", "app": "pro", "url": "/reservations", "result": "FAIL",
             "diff_ratio": 0.032, "baseline": "", "current": "", "diff": ""},
            {"name": "Login", "app": "pro", "url": "/login", "result": "NEW-BASELINE",
             "diff_ratio": 0, "baseline": "", "current": "", "diff": ""},
        ]}
    d = tempfile.mkdtemp()
    rp = os.path.join(d, "visual.results.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)
    out = os.path.join(d, "T.visual.xlsx")
    subprocess.run([sys.executable, SCRIPT, rp, out], check=True)
    wb = load_workbook(out)
    assert "Visual" in wb.sheetnames and "Màn quét" in wb.sheetnames, wb.sheetnames
    ws = wb["Visual"]
    assert ws.cell(1, 1).value == "Màn", ws.cell(1, 1).value
    assert ws.cell(2, 4).value == "FAIL", ws.cell(2, 4).value
    cov = wb["Màn quét"]
    rows = {cov.cell(r, 1).value: cov.cell(r, 4).value for r in range(4, 6)}
    assert rows.get("Login") == "NEW-BASELINE", rows
    print("✅ test_build_visual_report PASS")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Run: `python3 test_build_visual_report.py`
Expected: FAIL — `No such file ... build_visual_report.py`.

- [ ] **Step 3: Viết `build_visual_report.py`**

Create `build_visual_report.py`:
```python
#!/usr/bin/env python3
"""build_visual_report.py — visual.results.json -> <Case>.visual.xlsx (2 sheet: Visual + Màn quét).
Oracle = baseline người-duyệt. CƠ KHÍ, không reasoning."""
import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage

HEAD = "2C3E50"
VERDICT_FILL = {"FAIL": "C0392B", "PASS": "27AE60", "NEW-BASELINE": "F1C40F", "未実施": "BDC3C7"}
HEADERS = ["Màn", "App", "URL", "Verdict", "Diff %", "Baseline", "Hiện tại", "Diff"]

def _img(ws, cell, base_dir, rel, r):
    if rel and os.path.exists(os.path.join(base_dir, rel)):
        im = XLImage(os.path.join(base_dir, rel)); im.width = 200; im.height = 130
        ws.add_image(im, cell); ws.row_dimensions[r].height = 105

def build(results_path, out_path):
    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)
    base_dir = os.path.dirname(os.path.abspath(results_path))
    meta = data.get("meta", {}); screens = data.get("screens", [])
    wb = Workbook(); ws = wb.active; ws.title = "Visual"
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(1, c, h); cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=HEAD)
    r = 2
    for s in screens:
        ws.cell(r, 1, s.get("name", "")); ws.cell(r, 2, s.get("app", "")); ws.cell(r, 3, s.get("url", ""))
        vc = ws.cell(r, 4, s.get("result", ""))
        vc.fill = PatternFill("solid", fgColor=VERDICT_FILL.get(s.get("result"), "BDC3C7"))
        ws.cell(r, 5, round(s.get("diff_ratio", 0) * 100, 3))
        _img(ws, f"F{r}", base_dir, s.get("baseline", ""), r)
        _img(ws, f"G{r}", base_dir, s.get("current", ""), r)
        _img(ws, f"H{r}", base_dir, s.get("diff", ""), r)
        r += 1
    if r == 2:
        ws.cell(2, 1, "Không có màn nào được quét.")
    for col, w in zip("ABCDEFGH", (18, 10, 24, 14, 9, 30, 30, 30)):
        ws.column_dimensions[col].width = w
    # Sheet coverage
    cov = wb.create_sheet("Màn quét")
    cov.cell(1, 1, f"VISUAL · {meta.get('case','')} · {meta.get('date','')} · {meta.get('tester','')}").font = Font(bold=True)
    for c, h in enumerate(["Màn", "App", "URL", "Verdict", "Diff %"], 1):
        cell = cov.cell(3, c, h); cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=HEAD)
    rr = 4
    for s in screens:
        cov.cell(rr, 1, s.get("name", "")); cov.cell(rr, 2, s.get("app", "")); cov.cell(rr, 3, s.get("url", ""))
        cov.cell(rr, 4, s.get("result", "")); cov.cell(rr, 5, round(s.get("diff_ratio", 0) * 100, 3))
        rr += 1
    for col, w in zip("ABCDE", (18, 10, 24, 14, 9)):
        cov.column_dimensions[col].width = w
    wb.save(out_path)
    print(f"✅ visual report: {out_path} ({len(screens)} màn)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: build_visual_report.py <results.json> <out.xlsx>")
    build(sys.argv[1], sys.argv[2])
```

- [ ] **Step 4: Chạy test — xác nhận PASS**

Run: `python3 test_build_visual_report.py`
Expected: `✅ test_build_visual_report PASS`.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/{build_visual_report.py,test_build_visual_report.py}
git commit -m "feat(visual): build_visual_report.py — sheet Visual (3 ảnh/màn) + Màn quét"
```

---

### Task 4: Sổ bug nhận `bug_type: "Visual"` + BUG-LOG.md

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/build_bug_report.py:380,383`
- Modify: `docs/BUG-LOG.md`
- Test: `.claude/skills-scripts/testcase-evidence/test_bug_report_visual_type.py`

**Interfaces:**
- Consumes: `wtf-is-this/bug-he-thong.tcs.json`.
- Produces: "Tổng quan" hiện nhãn `Visual` trong breakdown-theo-loại; guard KHÔNG raise.

- [ ] **Step 1: Viết test thất bại**

Create `test_bug_report_visual_type.py`:
```python
# Chạy: python3 test_bug_report_visual_type.py
import copy, json, os, subprocess, sys, tempfile
from openpyxl import load_workbook
HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.join(HERE, "..", "..", "..", "wtf-is-this", "bug-he-thong.tcs.json")

def main():
    with open(REAL, encoding="utf-8") as f:
        data = json.load(f)
    a = copy.deepcopy(data["tcs"][0])
    a.update({"bug_id": "BUG-VIS-TEST", "bug_type": "Visual", "result": "FAIL",
              "screen": "Pro — Đặt lịch", "status": "Mở", "found_at": "2026-07-16"})
    data["tcs"].append(a)
    d = tempfile.mkdtemp()
    jp = os.path.join(d, "bugs.tcs.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    out = os.path.join(d, "bugs.xlsx")
    subprocess.run([sys.executable, os.path.join(HERE, "build_bug_report.py"), jp, out], check=True)
    wb = load_workbook(out); ws = wb[wb.sheetnames[0]]
    found = any(c.value == "Visual" for row in ws.iter_rows() for c in row)
    assert found, "Tổng quan phải hiện nhãn 'Visual'"
    print("✅ test_bug_report_visual_type PASS")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Run: `python3 test_bug_report_visual_type.py`
Expected: FAIL — `AssertionError: Tổng quan phải hiện nhãn 'Visual'`.

- [ ] **Step 3: Sửa `build_bug_report.py` (dòng 380 & 383)**

Đổi:
```python
    for i, k in enumerate(("Function", "UI", "Text", "Accessibility")):
```
→
```python
    for i, k in enumerate(("Function", "UI", "Text", "Accessibility", "Visual")):
```
Và dòng 383:
```python
    nrows = max(len(services), 4)
```
→
```python
    nrows = max(len(services), 5)
```

- [ ] **Step 4: Chạy test — xác nhận PASS**

Run: `python3 test_bug_report_visual_type.py`
Expected: `✅ test_bug_report_visual_type PASS`.

- [ ] **Step 5: Cập nhật `docs/BUG-LOG.md`**

Dòng bug_type (đã có `Function / UI / Text / Accessibility`) → thêm `/ Visual`. Thêm 1 dòng note dưới bảng §1:
```
> **Bug Visual** (do `/testcase-visual` sinh): `result` luôn `FAIL` (diff > ngưỡng; NEW-BASELINE/未実施 KHÔNG vào sổ) ·
> `before`=baseline · `after`=ảnh diff (tô đỏ) · dedup **1 bug/màn** (không tách theo vùng).
```

- [ ] **Step 6: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/{build_bug_report.py,test_bug_report_visual_type.py} docs/BUG-LOG.md
git commit -m "feat(visual): sổ bug nhận bug_type Visual + doc BUG-LOG"
```

---

### Task 5: Command `/testcase-visual` + đăng ký doc + live-verify

**Files:**
- Create: `.claude/commands/testcase-visual.md`
- Create: `baselines/.gitkeep` (dựng thư mục kho baseline)
- Modify: `README.md` (§9 + §13), `CLAUDE.md`, `docs/STATE.md`, `docs/ROADMAP.md` (đánh dấu Visual đang làm)
- Verify: live smoke (cần Docker dev — DEFER nếu down)

**Interfaces:**
- Consumes: `visual_lib` (T1/T2), `pw_lib.getPage`/`shot`, `build_visual_report.py` (T3), sổ bug (T4),
  `knowledge/*.md` (`mask:` block — do Task 6 hoặc người soạn), `baselines/`.
- Produces: `wtf-is-this/<Case>/visual.results.json` + `<Case>.visual.xlsx` + append FAIL vào sổ bug + baseline mới (NEW-BASELINE) ở `baselines/<app>/<slug>.png`.

- [ ] **Step 1: Dựng kho baseline**

Run: `mkdir -p baselines && touch baselines/.gitkeep`

- [ ] **Step 2: Viết command doc**

Create `.claude/commands/testcase-visual.md`:
```markdown
# /testcase-visual — Test Visual regression (black-box) một TestCase

So ảnh các màn spec đang test với **baseline người-duyệt** (`baselines/<app>/<slug>.png`, commit git).
**Track RIÊNG**, KHÔNG trộn PASS/FAIL functional. Oracle = **baseline** (không phải spec). Mù code.

## Cách dùng
```
/testcase-visual wtf-is-this/TestCase-XX
```

## TIẾT KIỆM TOKEN
Dùng lại `.claude/skills-scripts/testcase-evidence/`: `pw_lib` (`getPage`), `visual_lib`
(`captureMasked`/`compareToBaseline`/`baselinePath`), `build_visual_report.py`. KHÔNG viết lại.
Setup 1 lần: `cd .claude/skills-scripts/testcase-evidence && npm i`.

## Nguyên tắc (2 tường)
- **Oracle = baseline người-duyệt.** `specs.md` chỉ để **chọn màn (scope)**, KHÔNG làm oracle.
- **Mù code.** Chỉ đọc pixel màn render. Không code / GitNexus / `knowledge/system/**`.

## Quy trình
1. **Chọn màn (scope):** đọc `<folder>/specs.md` mục "3. Ảnh hưởng hệ thống" → app/màn. Có `tcs.json` đã chạy → tái dùng màn/URL.
2. **Đọc `mask:`** của mỗi màn từ `knowledge/*.md` (approved). Màn chưa có `mask:` trong knowledge → chạy `/testcase-systemdoc <flow>` (build-time) để sinh, KHÔNG mask tay ở đây.
3. **Chụp + so** (driver inline):
   ```js
   const P='<repo>/.claude/skills-scripts/testcase-evidence/';
   const { getPage } = require(P+'pw_lib');
   const { captureMasked, compareToBaseline, baselinePath } = require(P+'visual_lib');
   const fs = require('fs');
   (async () => {
     const { browser, page, BASE } = await getPage('pro');
     await page.goto(BASE + '/reservations');
     // chờ render xong (như shot): chờ selector đặc trưng + networkidle
     const cur = '<folder>/shots/vis_reservations_cur.png';
     await captureMasked(page, cur, ['<mask selectors từ knowledge>']);
     const base = baselinePath('pro', '/reservations');
     if (!fs.existsSync(base)) {
       fs.mkdirSync(require('path').dirname(base), {recursive:true}); fs.copyFileSync(cur, base); // NEW-BASELINE
     } else {
       const r = compareToBaseline(cur, base, '<folder>/shots/vis_reservations_diff.png');
       // r.diffRatio > 0.001 => FAIL
     }
     await browser.close();
   })();
   ```
4. **Verdict/màn:** `PASS` (diffRatio ≤ 0.001) · `FAIL` (>) · `未実施` (không vào được màn) · `NEW-BASELINE` (chưa có baseline → vừa tạo).
   ⚠️ Visual **KHÔNG BAO GIỜ** `SPEC-GAP` (oracle là baseline, luôn có/không).
   ⚠️ **NEW-BASELINE cần NGƯỜI GẬT** "nhìn đúng" rồi mới `git add baselines/... && commit` — nếu ảnh xấu thì đừng commit, sửa app trước.
5. **Viết `<folder>/visual.results.json`** (schema ở `build_visual_report.py`): meta + screens[] {name,app,url,result,diff_ratio,baseline,current,diff}.
6. **Build report:** `python3 .../build_visual_report.py <folder>/visual.results.json <folder>/<Tên>.visual.xlsx`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/màn** → append `wtf-is-this/bug-he-thong.tcs.json` (`bug_type:"Visual"`, `result:"FAIL"`, `pri` theo diff_ratio, `screen`="<App> — <Màn>", `source`=TestCase-XX, `title`="Visual: <màn> lệch X% so baseline", `before`=baseline, `after`=ảnh diff), rồi build lại `bug-he-thong.xlsx`.
8. **Báo cáo:** bảng màn × verdict + diff%. Liệt kê NEW-BASELINE cần người gật/commit.

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG** (chỉ đọc pixel).
- [ ] Verdict chỉ dựa diff pixel với baseline (không tự bịa)? Không dùng specs.md làm oracle?
- [ ] NEW-BASELINE đã nhắc người GẬT trước khi commit chưa? (không auto-commit baseline chưa duyệt)
- [ ] Màn chưa có `mask:` → đã dừng + nhắc `/testcase-systemdoc`, KHÔNG mask tay?
```

- [ ] **Step 3: Đăng ký doc**

- `README.md` §9: thêm sau dòng `/testcase-a11y`:
  ```
  /testcase-visual <folder>   so ảnh màn với baseline người-duyệt → report visual + sổ bug
  ```
- `README.md` §13 bảng: `| **Test visual regression** một TestCase | `.claude/commands/testcase-visual.md` |`
- `CLAUDE.md` "Cách xài": thêm mục 6:
  ```
  6. (tuỳ chọn) `/testcase-visual wtf-is-this/TestCase-XX` → so ảnh màn với baseline người-duyệt (regression UI).
     Track RIÊNG, oracle = baseline, mù code. Baseline ở `baselines/` (commit git), mask từ knowledge.
  ```
- `docs/STATE.md` §2: thêm bullet (⚠️ live-verify treo nếu Docker down):
  ```
  - ✅ **Track Visual** (`/testcase-visual`) — pixelmatch, baseline `baselines/<app>/<slug>.png` (commit git),
    report `.visual.xlsx` + sổ bug (`bug_type: Visual`). Type test thứ 3. ⚠️ **CÒN TREO: live-verify** (cần Docker dev).
    Spec/plan: `docs/superpowers/{specs,plans}/2026-07-16-visual-track*`.
  ```
- `docs/ROADMAP.md`: đổi dòng Visual từ `⏸️ HOÃN` → `🔨 đang build v1` (giữ ghi chú "mature-only").

- [ ] **Step 4: Live-verify (cần Docker dev)**

Best-effort: kiểm dev reachable. Nếu KHÔNG → **DEFERRED** trong report (như a11y), báo DONE_WITH_CONCERNS.
Nếu CÓ: `/testcase-visual wtf-is-this/TestCase-11` → lần đầu NEW-BASELINE; chạy lại → PASS; giả lập đổi (vd `page.evaluate` zoom) → FAIL + diff đỏ. KHÔNG bịa kết quả.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/testcase-visual.md baselines/.gitkeep README.md CLAUDE.md docs/STATE.md docs/ROADMAP.md
git commit -m "feat(visual): command /testcase-visual + kho baselines + đăng ký doc"
```

---

### Task 6: Authoring sinh `mask:` tự động (`/testcase-systemdoc` + `explorer.js`)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.js` (thêm subcommand `dynamic` + block mask trong `emitNavBlock`)
- Test: `.claude/skills-scripts/testcase-evidence/explorer.test.js` (thêm case emitNavBlock có mask)
- Modify: `.claude/commands/testcase-systemdoc.md` (thêm bước auto-detect vùng động)

**Interfaces:**
- Consumes: `visual_lib.detectDynamic` (T2), `parseArgs`/`replay` sẵn của explorer.
- Produces:
  - CLI `node explorer.js dynamic --target <t> --url <path>` → in JSON `[{x,y,width,height,selector}]` (vùng động, để người liếc).
  - `emitNavBlock(flowId, steps, meta)` khi `meta.mask` (mảng selector) không rỗng → thêm khối:
    ```
    mask:
      - <selector1>
      - <selector2>
    ```
    vào block navigation (giữ FIREWALL HOW-only: mask là HOW — cách quan sát ổn định).

- [ ] **Step 1: Thêm test thất bại**

Append vào `explorer.test.js`:
```js
test('emitNavBlock: có meta.mask -> block chứa danh sách mask', () => {
  const { emitNavBlock } = require('./explorer');
  const out = emitNavBlock('pro-open-booking', [{ action: 'click', role: 'button', name: 'X' }],
    { mask: ['#clock', '.balance'] });
  assert.match(out, /mask:/);
  assert.match(out, /#clock/);
  assert.match(out, /\.balance/);
});
```

- [ ] **Step 2: Chạy test — xác nhận FAIL**

Run: `node --test explorer.test.js`
Expected: FAIL — output không có `mask:` (emitNavBlock chưa xử meta.mask).

- [ ] **Step 3: Sửa `explorer.js`**

Trong `emitNavBlock(flowId, steps, meta={})`, trước khi return chuỗi, chèn phần mask nếu có. Tìm chỗ build chuỗi block và thêm:
```js
  const maskBlock = (meta.mask && meta.mask.length)
    ? '\nmask:\n' + meta.mask.map(m => '  - ' + scrub(String(m))).join('\n') + '\n'
    : '';
```
rồi nối `maskBlock` vào chuỗi output (sau navigation steps, trước source metadata). (Đọc hàm hiện tại để chèn đúng vị trí — giữ format YAML-ish sẵn có.)

Thêm subcommand `dynamic` trong khối CLI (`if (cmd === 'snapshot') … else if (cmd === 'dynamic')`):
```js
    } else if (cmd === 'dynamic') {
      const { detectDynamic } = require('./visual_lib');
      const { browser, page, BASE } = await require('./pw_lib').getPage(a.target);
      await page.goto(BASE + a.url);
      const regions = await detectDynamic(page);
      console.log(JSON.stringify(regions, null, 2));
      await browser.close();
```
(cập nhật dòng `console.error('cmd: snapshot | run | replay | emit')` → thêm `| dynamic`.)

- [ ] **Step 4: Chạy test — xác nhận PASS**

Run: `node --test explorer.test.js`
Expected: PASS (test cũ vẫn xanh + test mask mới xanh).

- [ ] **Step 5: Cập nhật `.claude/commands/testcase-systemdoc.md`**

Trong bước 3 (UI-confirm bằng explorer), thêm 1 gạch đầu dòng trước bước `emit`:
```
- `node explorer.js dynamic --target <t> --url <path>` → liệt kê vùng ĐỘNG (đồng hồ/tên/số dư). Claude
  liếc + chọn selector che → truyền vào `emit` qua `--mask "sel1||sel2"`. Đây là cách sinh `mask:` cho
  Visual regression (KHÔNG mask tay lúc `/testcase-visual`). Mask là HOW (quan sát ổn định) → không phá FIREWALL.
```
Và trong dòng lệnh `emit`, ghi chú thêm cờ `--mask` (parseArgs đã tách `--x y` generic nên `a.mask` tự có; nếu cần split `||` thì xử ở khối emit — thêm: `const mask = a.mask ? a.mask.split('||') : [];` rồi truyền `{ sourceSymbols: symbols, mask }`).

- [ ] **Step 6: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/{explorer.js,explorer.test.js} .claude/commands/testcase-systemdoc.md
git commit -m "feat(visual): authoring auto-detect vùng động -> emit mask: vào knowledge (explorer dynamic + emitNavBlock)"
```

---

## Ghi chú thực thi

- **Thứ tự:** 1 → 2 → 3 → 4 → 5 → 6. Track chạy được sau Task 5 (mask có thể thêm tay tạm nếu Task 6 chưa xong — nhưng plan làm hết).
- **Test nhanh toàn bộ** (sau Task 4):
  ```bash
  cd .claude/skills-scripts/testcase-evidence
  node --test visual_lib.test.js && python3 test_build_visual_report.py && python3 test_bug_report_visual_type.py
  ```
- **YAGNI:** KHÔNG đa-viewport (Compatibility lo) · KHÔNG auto-update baseline hàng loạt · KHÔNG so component-level.
- **Rủi ro:** noise render (font/anti-alias) → nếu diff giả, siết mask, KHÔNG nới ngưỡng bừa. Baseline chụp máy A chạy máy B có thể lệch — v1 giả định cùng harness Chromium pinned.
