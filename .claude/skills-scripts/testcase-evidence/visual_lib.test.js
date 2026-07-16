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
