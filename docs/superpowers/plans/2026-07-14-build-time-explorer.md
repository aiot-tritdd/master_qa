# explorer.js — Bộ dò-đường tự-lái (build-time UI-confirm) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây `explorer.js` — đồ nghề build-time để máy tự dò + lái + nghiệm một flow UI (bằng a11y-name, không toạ độ mù), nhả navigation block HOW-only cho `knowledge/<flow>.md`; người confirm nhẹ bằng 1 ảnh replay.

**Architecture:** Claude = ĐẦU (nghĩ, soạn step-list, vá bước gãy), `explorer.js` = TAY (cơ khí). Bọc mỏng native Playwright (`ariaSnapshot` / `getByRole` / `getByLabel`), tái dùng trọn `pw_lib.getPage` cho login/locale/session. Vòng lặp: snapshot→Claude soạn step-list→explorer chạy per-step báo bằng chữ→Claude vá→replay session sạch→emit nav block.

**Tech Stack:** Node 24 (CommonJS), Playwright 1.61.1 (đã cài, native `ariaSnapshot`), `node:test` + `node:assert` (built-in, không thêm dep). Fixtures test = `page.setContent()`.

## Global Constraints

- **KHÔNG thêm dependency** — chỉ Playwright đã cài + built-in Node. Không MCP, không process sống dai/REPL.
- **CommonJS** (`require`/`module.exports`) — khớp `pw_lib.js`. Không `import`.
- **Tái dùng `pw_lib.getPage(target)`** cho login/locale(`ja-JP`)/viewport/session — KHÔNG giải lại login.
- **Build-time only** — đồ nghề này không dính `/testcase-run`; không đụng evidence/Excel/cleanup.
- **Tường HOW/WHAT:** navigation block **chỉ ghi HOW** (đường bấm + nơi quan sát), **cấm** kết quả kỳ vọng / pass-fail (WHAT). Ép bằng cấu trúc: template không có ô "expected".
- **Toạ độ chỉ khi bất khả kháng** và **bắt buộc gắn cờ** `fragile:coordinate` — không lén đóng dấu như locator sạch.
- **Oracle vẫn là SPEC** — explorer không bao giờ phán đúng/sai.
- Đặt file cạnh `pw_lib.js`: `.claude/skills-scripts/testcase-evidence/`.
- Commit prefix theo repo: `feat:` / `docs:` (tiếng Việt phần mô tả OK).

---

## File Structure

| File | Trách nhiệm |
|---|---|
| Create `.claude/skills-scripts/testcase-evidence/explorer.js` | Toàn bộ primitives + CLI dispatcher. Exports: `snapshot, act, nearLabel, runSteps, replay, emitNavBlock, parseArgs`. |
| Create `.claude/skills-scripts/testcase-evidence/explorer.test.js` | Test `node:test` chạy trên fixtures `setContent()`. |
| Modify `.claude/skills-scripts/testcase-evidence/package.json` | Thêm `scripts.test`. |
| Modify `.claude/commands/testcase-systemdoc.md:10-18` | Bước 3 dùng explorer thay vì "click pw_lib 1 lần". |

**Exported interface (khoá cứng — mọi task theo đúng tên/kiểu này):**
```
snapshot(page, opts?)            -> Promise<string>      // opts.region (selector, default 'body')
act(page, step)                  -> Promise<void>        // throw khi fail; step schema §Task 2
nearLabel(page, label)           -> Promise<Locator>     // control gần nhất DƯỚI nhãn
runSteps(page, steps)            -> Promise<{reached:boolean, results:Array<{step,ok,error?,snapshot?}>}>
replay(target, url, steps, opts?)-> Promise<{reached,results,screenshot}>  // opts.open (inject), opts.shot (path)
emitNavBlock(flowId, steps, meta)-> string               // meta.sourceSymbols[], meta.uiConfirmedAt?
parseArgs(argv)                  -> object               // {--k v} -> {k:v}
```
**`step` schema:** `{ action:'click'|'fill'|'coord', role?, name?, label?, text?, value?, via?:'nearLabel', x?, y?, fragile?, timeout?, note? }`

---

## Task 1: Scaffold + `snapshot()` + test harness

**Files:**
- Create: `.claude/skills-scripts/testcase-evidence/explorer.js`
- Create: `.claude/skills-scripts/testcase-evidence/explorer.test.js`
- Modify: `.claude/skills-scripts/testcase-evidence/package.json`

**Interfaces:**
- Consumes: `playwright` (`chromium`), `pw_lib.js` (`shot`, `getPage` — dùng ở task sau).
- Produces: `snapshot(page, opts?)`; test helper `withPage(html, fn)` (nội bộ test file).

- [ ] **Step 1: Thêm test script vào package.json**

```json
{
  "name": "testcase-evidence",
  "version": "1.0.0",
  "private": true,
  "description": "Harness cơ khí cho qa-brain: Playwright chạy test + chụp evidence (pw_lib/pw_api). Build Excel = build_evidence.py.",
  "scripts": {
    "test": "node --test"
  },
  "dependencies": {
    "playwright": "^1.44.0"
  }
}
```

- [ ] **Step 2: Viết test thất bại cho `snapshot`**

Create `explorer.test.js`:
```js
const { test } = require('node:test');
const assert = require('node:assert');
const { chromium } = require('playwright');
const { snapshot } = require('./explorer');

async function withPage(html, fn) {
  const b = await chromium.launch({ headless: true });
  try {
    const p = await (await b.newContext()).newPage();
    await p.setContent(html);
    await fn(p);
  } finally { await b.close(); }
}
module.exports = { withPage };

test('snapshot trả cấu trúc trang có TÊN (a11y)', async () => {
  await withPage('<button>追加</button><div role="tab">チケット</div>', async (p) => {
    const s = await snapshot(p);
    assert.match(s, /button "追加"/);
    assert.match(s, /tab "チケット"/);
  });
});
```

- [ ] **Step 3: Chạy test để chắc nó FAIL**

Run: `cd .claude/skills-scripts/testcase-evidence && npm test`
Expected: FAIL — `Cannot find module './explorer'`.

- [ ] **Step 4: Viết `explorer.js` tối thiểu**

```js
// explorer.js — Bộ dò-đường tự-lái, BUILD-TIME. CƠ KHÍ (Claude là đầu, file này là tay).
// Bọc mỏng native Playwright: ariaSnapshot (nhìn) + getByRole/Label (bấm). Tái dùng pw_lib cho login.
// ⚠️ CẤM dùng lúc /testcase-run (đây là đồ build-time). Nav block chỉ ghi HOW, không WHAT.
const fs = require('fs');
const { getPage, shot } = require('./pw_lib');

// snapshot(page): trả cấu trúc trang bằng CHỮ (button/combobox/tab + tên). Thay tấm-ảnh-mù bằng danh-sách-chữ.
async function snapshot(page, opts = {}) {
  const region = opts.region || 'body';
  return await page.locator(region).ariaSnapshot();
}

module.exports = { snapshot };
```

- [ ] **Step 5: Chạy test để chắc nó PASS**

Run: `npm test`
Expected: PASS — 1 test.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/explorer.js .claude/skills-scripts/testcase-evidence/explorer.test.js .claude/skills-scripts/testcase-evidence/package.json
git commit -m "feat(explorer): scaffold + snapshot() a11y-text primitive"
```

---

## Task 2: `act()` — bấm/điền theo tên/role/nhãn (+ toạ độ có cờ)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.js`
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.test.js`

**Interfaces:**
- Consumes: `snapshot` (task 1).
- Produces: `act(page, step)`. `step.timeout` (ms, default 10000) — cho test set ngắn.

- [ ] **Step 1: Viết test thất bại cho `act`**

Thêm vào `explorer.test.js`:
```js
const { act } = require('./explorer');

test('act: click theo role+name', async () => {
  await withPage(`<button onclick="this.textContent='clicked'">追加</button>`, async (p) => {
    await act(p, { action: 'click', role: 'button', name: '追加' });
    assert.strictEqual(await p.getByRole('button').textContent(), 'clicked');
  });
});

test('act: fill theo label', async () => {
  await withPage('<label>お客様<input></label>', async (p) => {
    await act(p, { action: 'fill', label: 'お客様', value: 'AIOTTEST-KH3' });
    assert.strictEqual(await p.getByLabel('お客様').inputValue(), 'AIOTTEST-KH3');
  });
});

test('act: click theo text', async () => {
  await withPage(`<a href="#" onclick="this.dataset.hit='1'">AIOT-TEST-TK10</a>`, async (p) => {
    await act(p, { action: 'click', text: 'AIOT-TEST-TK10' });
    assert.strictEqual(await p.getByText('AIOT-TEST-TK10').getAttribute('data-hit'), '1');
  });
});

test('act: toạ độ KHÔNG fragile -> ném lỗi (ép luật gắn cờ)', async () => {
  await withPage('<div></div>', async (p) => {
    await assert.rejects(act(p, { action: 'coord', x: 10, y: 10 }), /fragile/);
  });
});
```

- [ ] **Step 2: Chạy test để chắc nó FAIL**

Run: `npm test`
Expected: FAIL — `act is not a function`.

- [ ] **Step 3: Cài `act` + `resolve` vào `explorer.js`**

Thêm trên dòng `module.exports`:
```js
// resolve(page, step): step ngữ nghĩa -> Locator. Ưu tiên nearLabel > role+name > label > text.
async function resolve(page, step) {
  if (step.via === 'nearLabel') return nearLabel(page, step.label);
  if (step.role) return page.getByRole(step.role, { name: step.name, exact: false });
  if (step.label) return page.getByLabel(step.label);
  if (step.text) return page.getByText(step.text, { exact: false });
  throw new Error('step thiếu selector ngữ nghĩa (role/label/text) hoặc via');
}

// act(page, step): làm MỘT bước. Retry 3 lần vì Vuetify hay detach giữa chừng (mẫu từ pw_lib.fillSafe).
// Toạ độ (action:'coord') CHỈ chạy khi step.fragile===true — ép luật "không lén đóng dấu toạ độ".
async function act(page, step) {
  if (step.action === 'coord') {
    if (!step.fragile) throw new Error('bước toạ độ bắt buộc fragile:true (a11y không thấy được element)');
    await page.mouse.click(step.x, step.y);
    return;
  }
  const T = step.timeout || 10000;
  for (let i = 0; i < 3; i++) {
    try {
      const loc = (await resolve(page, step)).first();
      await loc.waitFor({ state: 'visible', timeout: T });
      if (step.action === 'fill') await loc.fill(String(step.value), { timeout: T });
      else await loc.click({ timeout: T });
      return;
    } catch (e) {
      if (i === 2) throw e;
      await page.waitForTimeout(Math.min(800, T)); // đợi re-render rồi thử lại
    }
  }
}
```
Cập nhật export: `module.exports = { snapshot, act };`

- [ ] **Step 4: Chạy test để chắc nó PASS**

Run: `npm test`
Expected: PASS — 5 tests (1 cũ + 4 mới). (`nearLabel` chưa cài nhưng chưa test tới → resolve chỉ gọi khi `via:'nearLabel'`.)

- [ ] **Step 5: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/explorer.js .claude/skills-scripts/testcase-evidence/explorer.test.js
git commit -m "feat(explorer): act() drive-by-name (role/label/text) + toạ độ ép fragile"
```

---

## Task 3: `nearLabel()` — control gần nhãn (ca dropdown お客様)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.js`
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.test.js`

**Interfaces:**
- Consumes: —
- Produces: `nearLabel(page, label) -> Promise<Locator>` (dùng bởi `resolve` khi `via:'nearLabel'`).

- [ ] **Step 1: Viết test thất bại cho `nearLabel`**

Thêm vào `explorer.test.js`:
```js
const { nearLabel } = require('./explorer');

test('nearLabel: chọn control NGAY DƯỚI nhãn, không dính control xa', async () => {
  await withPage(`
    <div style="position:absolute;top:0px;left:0">お客様</div>
    <input id="near" style="position:absolute;top:30px;left:0">
    <input id="far"  style="position:absolute;top:300px;left:0">`, async (p) => {
    const loc = await nearLabel(p, 'お客様');
    await loc.fill('X');
    assert.strictEqual(await p.locator('#near').inputValue(), 'X');
    assert.strictEqual(await p.locator('#far').inputValue(), '');
  });
});
```

- [ ] **Step 2: Chạy test để chắc nó FAIL**

Run: `npm test`
Expected: FAIL — `nearLabel is not a function`.

- [ ] **Step 3: Cài `nearLabel`**

Thêm trước `resolve`:
```js
// nearLabel(page, label): tìm control (input/combobox/arrow/select) gần NHẤT nằm DƯỚI nhãn.
// Giải ca "nhiều dropdown giống nhau" (obs 3687): định vị theo hình học thay vì đoán index.
async function nearLabel(page, label) {
  const lab = page.getByText(label, { exact: false }).first();
  const box = await lab.boundingBox();
  if (!box) throw new Error(`nearLabel: không thấy nhãn "${label}"`);
  const cands = page.locator('input, [role=combobox], [role=button], .mdi-menu-down, select');
  const n = await cands.count();
  let best = null, bestDy = Infinity;
  for (let i = 0; i < n; i++) {
    const c = cands.nth(i);
    const b = await c.boundingBox();
    if (!b) continue;
    const dy = b.y - box.y;           // control nằm dưới/ngang nhãn
    if (dy >= -5 && dy < bestDy) { bestDy = dy; best = c; }
  }
  if (!best) throw new Error(`nearLabel: không thấy control gần "${label}"`);
  return best;
}
```
Cập nhật export: `module.exports = { snapshot, act, nearLabel };`

- [ ] **Step 4: Chạy test để chắc nó PASS**

Run: `npm test`
Expected: PASS — 6 tests.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/explorer.js .claude/skills-scripts/testcase-evidence/explorer.test.js
git commit -m "feat(explorer): nearLabel() định vị control theo hình học (ca đa-dropdown)"
```

---

## Task 4: `runSteps()` — chạy step-list, dừng ở bước gãy, báo bằng CHỮ

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.js`
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.test.js`

**Interfaces:**
- Consumes: `act`, `snapshot`.
- Produces: `runSteps(page, steps) -> {reached, results:[{step, ok, error?, snapshot?}]}`. Dừng NGAY bước fail, đính snapshot tại chỗ gãy (để Claude thấy vá).

- [ ] **Step 1: Viết test thất bại cho `runSteps`**

Thêm vào `explorer.test.js`:
```js
const { runSteps } = require('./explorer');

test('runSteps: chạy hết -> reached true', async () => {
  await withPage(`<button onclick="this.textContent='x'">A</button>`, async (p) => {
    const r = await runSteps(p, [{ action: 'click', role: 'button', name: 'A' }]);
    assert.strictEqual(r.reached, true);
    assert.strictEqual(r.results[0].ok, true);
  });
});

test('runSteps: dừng ở bước gãy + đính snapshot bằng chữ', async () => {
  await withPage('<button>A</button>', async (p) => {
    const r = await runSteps(p, [
      { action: 'click', role: 'button', name: 'A' },
      { action: 'click', role: 'button', name: 'KHÔNG-CÓ', timeout: 300 },
    ]);
    assert.strictEqual(r.reached, false);
    assert.strictEqual(r.results.length, 2);
    assert.strictEqual(r.results[0].ok, true);
    assert.strictEqual(r.results[1].ok, false);
    assert.match(r.results[1].snapshot, /button "A"/); // Claude thấy trang lúc gãy
  });
});
```

- [ ] **Step 2: Chạy test để chắc nó FAIL**

Run: `npm test`
Expected: FAIL — `runSteps is not a function`.

- [ ] **Step 3: Cài `runSteps`**

Thêm trước `module.exports`:
```js
// runSteps(page, steps): chạy tuần tự. Bước fail -> DỪNG, đính snapshot tại chỗ gãy để Claude vá đúng bước đó.
async function runSteps(page, steps) {
  const results = [];
  for (const step of steps) {
    try {
      await act(page, step);
      results.push({ step, ok: true });
    } catch (e) {
      const snap = await snapshot(page).catch(() => '(snapshot lỗi)');
      results.push({ step, ok: false, error: e.message, snapshot: snap });
      return { reached: false, results };
    }
  }
  return { reached: true, results };
}
```
Cập nhật export: `module.exports = { snapshot, act, nearLabel, runSteps };`

- [ ] **Step 4: Chạy test để chắc nó PASS**

Run: `npm test`
Expected: PASS — 8 tests.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/explorer.js .claude/skills-scripts/testcase-evidence/explorer.test.js
git commit -m "feat(explorer): runSteps() per-step, dừng ở bước gãy + snapshot chữ"
```

---

## Task 5: `replay()` — nghiệm bằng THỰC THI từ session sạch

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.js`
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.test.js`

**Interfaces:**
- Consumes: `runSteps`, `getPage`+`shot` (pw_lib).
- Produces: `replay(target, url, steps, opts?)`. `opts.open` = injectable async `() => {browser, page}` (cho test); mặc định `getPage` với `NO_STATE=1` (login sạch). `opts.shot` = đường dẫn ảnh.

- [ ] **Step 1: Viết test thất bại cho `replay` (dùng opener inject)**

Thêm vào `explorer.test.js`:
```js
const { replay } = require('./explorer');

test('replay: chạy trên page inject, báo reached (không cần app dev)', async () => {
  const b = await chromium.launch({ headless: true });
  const p = await (await b.newContext()).newPage();
  await p.setContent(`<button onclick="this.textContent='x'">A</button>`);
  const r = await replay('pro', '/', [{ action: 'click', role: 'button', name: 'A' }],
    { open: async () => ({ browser: null, page: p }) }); // browser:null -> replay không tự đóng
  assert.strictEqual(r.reached, true);
  await b.close();
});
```

- [ ] **Step 2: Chạy test để chắc nó FAIL**

Run: `npm test`
Expected: FAIL — `replay is not a function`.

- [ ] **Step 3: Cài `replay`**

Thêm trước `module.exports`:
```js
// replay(target, url, steps, opts): nghiệm đường đi bằng THỰC THI trên session SẠCH (NO_STATE=1).
// Neo an toàn cho "confirm nhẹ": người tin 1 lần chạy lại tái lập được, không tin lời máy.
// opts.open cho test inject page; opts.shot = đường dẫn ảnh tới điểm quan sát.
async function replay(target, url, steps, opts = {}) {
  const open = opts.open || (async () => {
    process.env.NO_STATE = '1';
    const { browser, page, BASE } = await getPage(target);
    await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    return { browser, page };
  });
  const { browser, page } = await open();
  try {
    const r = await runSteps(page, steps);
    let screenshot = null;
    if (opts.shot) screenshot = await shot(page, opts.shot);
    return { reached: r.reached, results: r.results, screenshot };
  } finally {
    if (browser) await browser.close();
  }
}
```
Cập nhật export: `module.exports = { snapshot, act, nearLabel, runSteps, replay };`

- [ ] **Step 4: Chạy test để chắc nó PASS**

Run: `npm test`
Expected: PASS — 9 tests.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/explorer.js .claude/skills-scripts/testcase-evidence/explorer.test.js
git commit -m "feat(explorer): replay() nghiệm-bằng-thực-thi từ session sạch"
```

---

## Task 6: `emitNavBlock()` — nhả doc HOW-only (ép tường bằng cấu trúc)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.js`
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.test.js`

**Interfaces:**
- Consumes: —
- Produces: `emitNavBlock(flowId, steps, meta) -> string`. `meta.sourceSymbols` (string[]), `meta.uiConfirmedAt?` (YYYY-MM-DD; mặc định hôm nay).

- [ ] **Step 1: Viết test thất bại cho `emitNavBlock`**

Thêm vào `explorer.test.js`:
```js
const { emitNavBlock } = require('./explorer');

test('emitNavBlock: CHỈ HOW — không có ô expected (tường HOW/WHAT)', () => {
  const md = emitNavBlock('demo', [{ action: 'click', role: 'button', name: '追加' }],
    { sourceSymbols: ['pro: X.vue'] });
  assert.match(md, /status: draft/);
  assert.match(md, /click button 「追加」/);
  assert.match(md, /source_hash:.*stale_check/);        // để trống, chỉ đường điền bằng tool cũ
  assert.doesNotMatch(md, /expect|expected|kỳ vọng|pass\/fail/i);
  assert.match(md, /KẾT QUẢ ĐÚNG\/SAI = SPEC/);
});

test('emitNavBlock: bước toạ độ bị GẮN CỜ fragile', () => {
  const md = emitNavBlock('demo', [{ action: 'coord', x: 1050, y: 620, fragile: true }], {});
  assert.match(md, /\[fragile:coordinate\]/);
  assert.match(md, /\(1050,620\)/);
});
```

- [ ] **Step 2: Chạy test để chắc nó FAIL**

Run: `npm test`
Expected: FAIL — `emitNavBlock is not a function`.

- [ ] **Step 3: Cài `emitNavBlock`**

Thêm trước `module.exports`:
```js
// emitNavBlock(flowId, steps, meta): sinh block navigation cho knowledge/<flow>.md.
// TƯỜNG ép bằng CẤU TRÚC: template KHÔNG có ô "expected" -> máy vật lý không ghi WHAT được.
// source_hash để TRỐNG (điền bằng stale_check.py --update) -> DRY, không tự hash lại.
function emitNavBlock(flowId, steps, meta = {}) {
  const date = meta.uiConfirmedAt || new Date().toISOString().slice(0, 10);
  const symbols = (meta.sourceSymbols || []).map((s) => `  - "${s}"`).join('\n') || '  - ""';
  const lines = steps.map((s, i) => {
    const n = i + 1;
    if (s.action === 'coord') {
      return `${n}. ⚠ [fragile:coordinate] click toạ độ (${s.x},${s.y}) — ${s.note || 'thay bằng locator khi có thể'}`;
    }
    if (s.action === 'fill') {
      return `${n}. điền 「${s.label || s.name}」 = <giá trị test>${s.via === 'nearLabel' ? ' (nearLabel)' : ''}`;
    }
    const sel = s.name || s.text;
    return `${n}. click ${s.role ? s.role + ' ' : ''}「${sel}」`;
  }).join('\n');
  return `---
id: ${flowId}
status: draft
kind: flow
source_symbols:
${symbols}
source_hash:            # điền bằng: python3 stale_check.py --update
ui_confirmed_at: ${date}
confidence: 🔴          # draft — người flip approved SAU KHI liếc ảnh replay
---

# ${flowId} — Navigation (HOW)

## Các bước drive
${lines}

## Điểm quan sát
- <màn tới đích>   # KẾT QUẢ ĐÚNG/SAI = SPEC, KHÔNG ghi ở đây
`;
}
```
Cập nhật export: `module.exports = { snapshot, act, nearLabel, runSteps, replay, emitNavBlock };`

- [ ] **Step 4: Chạy test để chắc nó PASS**

Run: `npm test`
Expected: PASS — 11 tests.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/explorer.js .claude/skills-scripts/testcase-evidence/explorer.test.js
git commit -m "feat(explorer): emitNavBlock() HOW-only, ép tường bằng cấu trúc"
```

---

## Task 7: CLI dispatcher + smoke thật trên app dev

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.js`
- Modify: `.claude/skills-scripts/testcase-evidence/explorer.test.js`

**Interfaces:**
- Consumes: tất cả primitives trên.
- Produces: `parseArgs(argv) -> object`; CLI `node explorer.js <snapshot|run|replay|emit> --k v`.

- [ ] **Step 1: Viết test thất bại cho `parseArgs`**

Thêm vào `explorer.test.js`:
```js
const { parseArgs } = require('./explorer');

test('parseArgs: --k v -> {k:v}', () => {
  assert.deepStrictEqual(parseArgs(['--target', 'pro', '--url', '/reservations']),
    { target: 'pro', url: '/reservations' });
});
```

- [ ] **Step 2: Chạy test để chắc nó FAIL**

Run: `npm test`
Expected: FAIL — `parseArgs is not a function`.

- [ ] **Step 3: Cài `parseArgs` + CLI dispatcher**

Thêm `parseArgs` trước `module.exports`:
```js
// parseArgs(argv): ['--target','pro'] -> {target:'pro'}. CLI tối giản, không dep.
function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) { o[argv[i].slice(2)] = argv[i + 1]; i++; }
  }
  return o;
}
```
Cập nhật export: `module.exports = { snapshot, act, nearLabel, runSteps, replay, emitNavBlock, parseArgs };`

Thêm CLI dispatcher ở CUỐI file (sau export):
```js
// ── CLI: node explorer.js <cmd> --k v .  Claude gọi từng lệnh, đọc stdout (chữ), quyết bước tiếp.
if (require.main === module) {
  (async () => {
    const [cmd, ...rest] = process.argv.slice(2);
    const a = parseArgs(rest);
    if (cmd === 'snapshot') {
      const { browser, page, BASE } = await getPage(a.target || 'pro');
      await page.goto(BASE + (a.url || '/'), { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      console.log(await snapshot(page, { region: a.region }));
      await browser.close();
    } else if (cmd === 'run') {
      const steps = JSON.parse(fs.readFileSync(a.steps, 'utf8'));
      const { browser, page, BASE } = await getPage(a.target || 'pro');
      await page.goto(BASE + (a.url || '/'), { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      console.log(JSON.stringify(await runSteps(page, steps), null, 2));
      await browser.close();
    } else if (cmd === 'replay') {
      const steps = JSON.parse(fs.readFileSync(a.steps, 'utf8'));
      const r = await replay(a.target || 'pro', a.url || '/', steps, { shot: a.shot });
      console.log(JSON.stringify({ reached: r.reached, screenshot: r.screenshot }, null, 2));
    } else if (cmd === 'emit') {
      const steps = JSON.parse(fs.readFileSync(a.steps, 'utf8'));
      const symbols = a.symbols ? a.symbols.split('||') : [];
      console.log(emitNavBlock(a.flow, steps, { sourceSymbols: symbols }));
    } else {
      console.error('cmd: snapshot | run | replay | emit');
      process.exit(1);
    }
  })().catch((e) => { console.error(e.message); process.exit(1); });
}
```

- [ ] **Step 4: Chạy test để chắc nó PASS**

Run: `npm test`
Expected: PASS — 12 tests.

- [ ] **Step 5: Smoke thật trên app dev (thủ công, cần Docker dev chạy + `.env` có creds)**

Run: `cd .claude/skills-scripts/testcase-evidence && node explorer.js snapshot --target pro --url /reservations`
Expected: in ra a11y-tree bằng chữ của màn lịch Pro (thấy `button`/`tab`/`text` tiếng Nhật). Nếu treo login → kiểm `.env` (SETUP.md §A3). **Đây là kiểm cơ khí, KHÔNG phán đúng/sai app.**

- [ ] **Step 6: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/explorer.js .claude/skills-scripts/testcase-evidence/explorer.test.js
git commit -m "feat(explorer): CLI dispatcher (snapshot/run/replay/emit) + parseArgs"
```

---

## Task 8: Cắm explorer vào `/testcase-systemdoc` bước 3

**Files:**
- Modify: `.claude/commands/testcase-systemdoc.md:10-18`

**Interfaces:**
- Consumes: `explorer.js` CLI.
- Produces: — (tài liệu quy trình).

- [ ] **Step 1: Sửa bước 3 của quy trình**

Thay khối "## Quy trình" bước 3 (dòng ~14-17) bằng:
```markdown
3. **UI-confirm bằng explorer (tự-lái, thay cho click tay):**
   - `node explorer.js snapshot --target <t> --url <path>` → Claude THẤY trang bằng chữ.
   - Claude soạn step-list JSON (role/name/label/text; toạ độ chỉ khi bất khả kháng + `fragile:true`).
   - `node explorer.js run --steps steps.json --target <t> --url <path>` → per-step báo chỗ gãy → vá → lặp.
   - `node explorer.js replay --steps steps.json --target <t> --url <path> --shot shots/confirm.png`
     → nghiệm từ session sạch → **1 ảnh tới điểm quan sát** (người liếc để duyệt).
   - `node explorer.js emit --flow <flow-id> --steps steps.json --symbols "repo: path||repo: path2"`
     → nhả navigation block (HOW-only) vào `knowledge/<flow-id>.md`. Điền `ui_confirmed_at`.
   - Chạy `python3 stale_check.py --update` để điền `source_hash`.
4. **Người duyệt** → liếc `shots/confirm.png` + block → đổi `status: draft → approved`.
   Chỉ doc `approved` mới cho QA tin.
```

- [ ] **Step 2: Kiểm FIREWALL còn nguyên**

Đọc lại phần "## FIREWALL" (dưới quy trình) — bảo đảm vẫn cấm ghi kết quả kỳ vọng. explorer emit theo cấu trúc HOW-only (Task 6) → khớp, không cần sửa FIREWALL.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/testcase-systemdoc.md
git commit -m "docs(systemdoc): bước 3 UI-confirm dùng explorer tự-lái"
```

---

## Self-Review (đã chạy)

**1. Spec coverage:**
- §2 native ariaSnapshot → Task 1. §3.1 primitives (snapshot/act/nearLabel/replay) → Task 1-5. §3.2 vòng lặp Claude-lái → Task 4 (runSteps per-step) + Task 7 (CLI). §4 đầu ra (nav block/metadata/ảnh) → Task 5 (shot) + Task 6 (emit). §5 tường HOW/WHAT + cờ fragile → Task 2 (coord ép fragile) + Task 6 (template không ô expected). §6 confirm nhẹ (replay session sạch) → Task 5. §7 chỗ cắm systemdoc → Task 8. §8 Vuetify detach → Task 2 (retry). ✅ đủ.
- `source_hash` nối `stale_check.py` (§4) → Task 6 để trống + Task 8 chạy `--update`. ✅
- (a) hook: ngoài phạm vi plan này (spec §7 nói "về sau"); explorer tạo biên rõ để (a) gác. ✅ không cần task.

**2. Placeholder scan:** không có TBD/TODO trong code; mọi step có code/command thật. `<giá trị test>` / `<màn tới đích>` là placeholder NỘI DUNG người điền trong doc output (đúng thiết kế HOW-only), không phải placeholder của plan.

**3. Type consistency:** `snapshot/act/nearLabel/runSteps/replay/emitNavBlock/parseArgs` nhất quán tên+chữ ký qua các task và khớp bảng "Exported interface". `step` schema thống nhất. `runSteps` trả `{reached, results}` dùng đồng nhất ở Task 4/5/7.
