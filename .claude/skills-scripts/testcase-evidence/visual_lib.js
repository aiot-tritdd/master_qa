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

module.exports = { slugify, baselinePath, compareToBaseline, captureMasked, detectDynamic, REPO_ROOT };
