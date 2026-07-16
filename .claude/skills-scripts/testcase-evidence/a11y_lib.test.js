const { test } = require('node:test');
const assert = require('node:assert');
const { chromium } = require('playwright');
const { runAxe } = require('./a11y_lib');

// Fixture: 3 lỗi a11y KINH ĐIỂN, axe luôn bắt được (deterministic).
const FIXTURE = `<!doctype html><html lang="en"><head><title>t</title></head><body>
  <button><span class="icon"></span></button>   <!-- button-name: nút không có text -->
  <img src="x.png">                              <!-- image-alt: ảnh thiếu alt -->
  <input type="text">                            <!-- label: input không gắn label -->
</body></html>`;

test('runAxe bắt được button-name / image-alt / label + đếm theo impact', async () => {
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.setContent(FIXTURE);
    const { violations, counts } = await runAxe(page);
    const ids = violations.map(v => v.id);
    assert.ok(ids.includes('button-name'), 'phải bắt button-name, có: ' + ids.join(','));
    assert.ok(ids.includes('image-alt'), 'phải bắt image-alt, có: ' + ids.join(','));
    assert.ok(ids.includes('label'), 'phải bắt label, có: ' + ids.join(','));
    assert.ok((counts.critical + counts.serious) >= 1, 'phải có ≥1 critical/serious');
    await context.close();
  } finally {
    await browser.close();
  }
});
