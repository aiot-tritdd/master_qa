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

async function runAxe(page, opts = {}) {
  let builder = new AxeBuilder({ page }).withTags(opts.tags || DEFAULT_TAGS);
  if (opts.include) builder = builder.include(opts.include);
  if (opts.exclude) builder = builder.exclude(opts.exclude);
  const results = await builder.analyze();
  const violations = results.violations.map(v => ({
    rule: v.id,
    impact: v.impact,
    wcag: wcagFromTags(v.tags),
    help: v.help,
    helpUrl: v.helpUrl,
    tags: v.tags,
    nodes: (v.nodes || []).map(n => ({ target: n.target, html: n.html })),
  }));
  const counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of violations) {
    if (v.impact && v.impact in counts) counts[v.impact] += 1;
  }
  return { violations, counts };
}

module.exports = { runAxe, wcagFromTags, IMPACTS, DEFAULT_TAGS };
