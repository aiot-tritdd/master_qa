const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');
const { runAxe, shotViolation, wcagFromTags } = require('./a11y_lib');

const FIXTURE = `<!doctype html><html lang="en"><head><title>t</title></head><body>
  <button><span class="icon"></span></button>   <!-- button-name -->
  <img src="x.png">                              <!-- image-alt -->
  <input type="text">                            <!-- label -->
</body></html>`;

test('runAxe trả violations ĐÃ CHUẨN HOÁ (rule/wcag/impact/nodes) + counts theo impact', async () => {
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext();  // @axe-core/playwright yêu cầu newContext, không dùng newPage trực tiếp
    const page = await context.newPage();
    await page.setContent(FIXTURE);
    const { violations, counts } = await runAxe(page);
    const rules = violations.map(v => v.rule);
    assert.ok(rules.includes('button-name'), 'phải bắt button-name, có: ' + rules.join(','));
    assert.ok(rules.includes('image-alt'), 'phải bắt image-alt, có: ' + rules.join(','));
    assert.ok(rules.includes('label'), 'phải bắt label, có: ' + rules.join(','));
    const bn = violations.find(v => v.rule === 'button-name');
    assert.match(bn.wcag, /^\d\.\d\.\d+$/, 'wcag phải parse thành d.d.d, có: ' + bn.wcag);
    assert.ok(bn.impact, 'phải có impact');
    assert.ok(Array.isArray(bn.nodes) && bn.nodes[0].target, 'nodes[].target phải có');
    assert.ok('html' in bn.nodes[0], 'nodes[].html phải có');
    assert.ok('failureSummary' in bn.nodes[0], 'nodes[].failureSummary phải giữ (chẩn đoán vì sao fail)');
    assert.ok(bn.description, 'violation phải có description (rule kiểm cái gì)');
    assert.ok((counts.critical + counts.serious) >= 1, 'phải có ≥1 critical/serious');
  } finally {
    await browser.close();
  }
});

test('shotViolation chụp ra file + DỌN outline sau khi chụp (không để dính khung đỏ cho lần quét sau)', async () => {
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.setContent('<!doctype html><html><body>'
      + '<p id="a" style="color:#bbb">low contrast</p>'
      + '<p id="b">two</p></body></html>');
    const out = path.join(os.tmpdir(), `shotviol_${Date.now()}.png`);
    const nodes = [{ target: ['#a'] }, { target: ['#b'] }];
    await shotViolation(page, nodes, out);
    assert.ok(fs.existsSync(out) && fs.statSync(out).size > 1000, 'ảnh phải được ghi ra');
    // sau khi chụp, outline phải được trả về rỗng (đã dọn) — không còn khung đỏ trên DOM
    const outlineA = await page.evaluate(() => document.querySelector('#a').style.outline);
    assert.equal(outlineA, '', 'outline phải được dọn sau khi chụp, còn: ' + outlineA);
    fs.unlinkSync(out);
  } finally {
    await browser.close();
  }
});

test('wcagFromTags parse tag success-criterion, bỏ tag version', () => {
  assert.equal(wcagFromTags(['cat.forms', 'wcag2a', 'wcag412']), '4.1.2');
  assert.equal(wcagFromTags(['wcag1410']), '1.4.10');
  assert.equal(wcagFromTags(['wcag2aa', 'wcag21aa']), '');
  assert.equal(wcagFromTags([]), '');
});
