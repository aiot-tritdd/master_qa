const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { PNG } = require('pngjs');
const { chromium } = require('playwright');
const { slugify, compareToBaseline, captureMasked, detectDynamic } = require('./visual_lib');

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
