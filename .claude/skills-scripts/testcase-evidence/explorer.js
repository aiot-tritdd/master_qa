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

module.exports = { snapshot, act, nearLabel, runSteps, replay, emitNavBlock };
