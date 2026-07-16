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

module.exports = { slugify, baselinePath, compareToBaseline, REPO_ROOT };
