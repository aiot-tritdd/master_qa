// a11y_lib.js — chạy axe-core trên 1 Playwright page (black-box: chỉ đọc DOM đã render).
// Oracle = WCAG. KHÔNG đọc code sản phẩm.
const { AxeBuilder } = require('@axe-core/playwright');

const IMPACTS = ['critical', 'serious', 'moderate', 'minor'];
const DEFAULT_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

async function runAxe(page, opts = {}) {
  let builder = new AxeBuilder({ page }).withTags(opts.tags || DEFAULT_TAGS);
  if (opts.include) builder = builder.include(opts.include);
  if (opts.exclude) builder = builder.exclude(opts.exclude);
  const results = await builder.analyze();
  const counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of results.violations) {
    if (v.impact && v.impact in counts) counts[v.impact] += 1;
  }
  return { violations: results.violations, counts };
}

module.exports = { runAxe, IMPACTS, DEFAULT_TAGS };
