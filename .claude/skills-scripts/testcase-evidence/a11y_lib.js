// a11y_lib.js — chạy axe-core trên 1 Playwright page (black-box: chỉ đọc DOM đã render).
// Oracle = WCAG. KHÔNG đọc code sản phẩm. Trả violations ĐÃ CHUẨN HOÁ (khớp schema build_a11y_report).
const { AxeBuilder } = require('@axe-core/playwright');

const IMPACTS = ['critical', 'serious', 'moderate', 'minor'];
const DEFAULT_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];
const WCAG_SC = /^wcag(\d)(\d)(\d+)$/;   // tag success-criterion: wcag412 -> "4.1.2" (bỏ tag version wcag2aa…)

function wcagFromTags(tags) {
  for (const t of tags || []) {
    const m = WCAG_SC.exec(t);
    if (m) return `${m[1]}.${m[2]}.${m[3]}`;
  }
  return '';
}

// shotViolation(page, nodes, outPath): chụp FULL màn, khoanh ĐỎ MỌI element vi phạm (nodes[].target).
// Vì sao KHÔNG chụp element lẻ: 1 crop rời khỏi màn = vô nghĩa (nhất là rule N-phần-tử như color-contrast
// 20-53 chỗ — crop 1/53 chả nói lên gì). Khoanh tất cả tại chỗ → nhìn ra "lỗi ở ĐÂU trên màn".
// Dọn outline sau khi chụp để lần runAxe kế KHÔNG dính khung đỏ.
async function shotViolation(page, nodes, outPath) {
  const selectors = (nodes || [])
    .map(n => (Array.isArray(n.target) ? n.target[0] : n.target))
    .filter(s => typeof s === 'string');
  const applied = await page.evaluate((sels) => {
    const touched = [];
    sels.forEach((sel, i) => {
      let el; try { el = document.querySelector(sel); } catch (_) { el = null; }
      if (!el) return;
      touched.push({ sel, outline: el.style.outline, offset: el.style.outlineOffset, bg: el.style.backgroundColor });
      el.style.outline = '3px solid #e60000';
      el.style.outlineOffset = '2px';
      el.style.backgroundColor = 'rgba(230,0,0,0.12)';
      if (i === 0) el.scrollIntoView({ block: 'center', inline: 'center' });
    });
    return touched;
  }, selectors);
  await page.waitForTimeout(150); // đợi scroll + paint khung đỏ xong
  await page.screenshot({ path: outPath, fullPage: true, animations: 'disabled' });
  await page.evaluate((touched) => {                       // dọn: trả style cũ
    for (const t of touched) {
      let el; try { el = document.querySelector(t.sel); } catch (_) { el = null; }
      if (el) { el.style.outline = t.outline; el.style.outlineOffset = t.offset; el.style.backgroundColor = t.bg; }
    }
  }, applied);
  return outPath;
}

async function runAxe(page, opts = {}) {
  let builder = new AxeBuilder({ page }).withTags(opts.tags || DEFAULT_TAGS);
  if (opts.include) builder = builder.include(opts.include);
  if (opts.exclude) builder = builder.exclude(opts.exclude);
  const results = await builder.analyze();
  const violations = results.violations.map(v => ({
    rule: v.id,
    impact: v.impact,
    wcag: wcagFromTags(v.tags),
    help: v.help,             // câu yêu cầu ngắn ("Elements must meet minimum contrast…")
    description: v.description, // mô tả rule kiểm cái gì
    helpUrl: v.helpUrl,
    tags: v.tags,
    // failureSummary = chẩn đoán CỤ THỂ vì sao node này fail (đo được: màu #hex, tỉ lệ 2.9:1, cần 4.5:1).
    // Đây là thứ làm report "hiểu được" — KHÔNG vứt đi.
    nodes: (v.nodes || []).map(n => ({ target: n.target, html: n.html, failureSummary: n.failureSummary })),
  }));
  const counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of violations) {
    if (v.impact && v.impact in counts) counts[v.impact] += 1;
  }
  return { violations, counts };
}

module.exports = { runAxe, shotViolation, wcagFromTags, IMPACTS, DEFAULT_TAGS };
