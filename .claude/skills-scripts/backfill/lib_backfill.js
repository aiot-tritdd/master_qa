// lib_backfill.js — shared helpers cho pipeline backfill GENERAL (đọc config.json, reuse pw_lib).
// CƠ KHÍ, không hardcode branch. Mọi script backfill require file này.
//
// LOCAL dev cố định: localhost, password123, superadmin/Admin1234!. Chỉ staff_code + institute
// lấy từ config.json (do /backfill-checklist sinh ra). pw_lib CFG build lúc load từ process.env
// → PHẢI set env TRƯỚC khi require pw_lib (nên require lazy trong getPage()).
const fs = require('fs');
const path = require('path');

const PW_LIB = path.join(__dirname, '..', 'testcase-evidence', 'pw_lib.js');

function loadConfig(folder) {
  const p = path.join(folder, 'config.json');
  if (!fs.existsSync(p)) throw new Error(`[backfill] thiếu ${p} — chạy /backfill-checklist trước.`);
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

// Set env LOCAL theo config, RỒI require pw_lib (lazy, để CFG đọc đúng env).
function getPage(target, cfg) {
  process.env.NO_STATE = '1';                         // luôn login sạch (LOCAL khác remote state)
  process.env.BASIC_USER = process.env.BASIC_USER || 'x';
  process.env.BASIC_PASS = process.env.BASIC_PASS || 'x';
  if (target === 'pro') {
    process.env.BASE_URL = 'http://localhost:8080';
    process.env.INST = cfg.institute_code;
    process.env.THER = cfg.pro_staff_code;
    process.env.PW = cfg.password || 'password123';
  } else if (target === 'ticket') {
    process.env.TICKET_URL = 'http://localhost:8000';
    process.env.TK_INST = cfg.institute_code;
    process.env.TK_STAFF = cfg.ticket_staff_code;
    process.env.TK_PW = cfg.password || 'password123';
  } else if (target === 'ticket_admin') {
    process.env.TICKET_ADMIN_URL = 'http://localhost:8000';
    process.env.TK_ADMIN_USER = cfg.backfill_admin_user || 'superadmin';
    process.env.TK_ADMIN_PASS = cfg.backfill_admin_pass || 'Admin1234!';
  }
  const PW = require(PW_LIB);
  return PW.getPage(target);
}

// Chuyển branch context trên Pro SPA (header dropdown → click tên branch JP).
async function switchBranch(page, branchNameJp) {
  await page.goto((process.env.BASE_URL || 'http://localhost:8080') + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4000);
  await page.locator('header, .v-app-bar').locator('text=整骨院').first().click();
  await page.waitForTimeout(1000);
  await page.locator(`text=${branchNameJp}`).last().click();
  await page.waitForTimeout(4000);
}

// Chụp AN TOÀN (reuse shot của pw_lib).
async function shot(page, filePath, readySelector, opts) {
  const PW = require(PW_LIB);
  return PW.shot(page, filePath, readySelector, opts);
}

// Chụp dòng 合計 (Total) trên bảng packs — scroll into view + clip.
async function captureTotalRow(page, filePath) {
  const row = page.locator('tr', { has: page.locator('text=合計') }).first();
  const target = (await row.count()) ? row : page.locator('text=合計').first();
  await target.scrollIntoViewIfNeeded().catch(() => {});
  await page.waitForTimeout(800);
  let txt = '';
  try { txt = (await target.innerText()).replace(/\s+/g, ' '); } catch (e) {}
  const box = await target.boundingBox();
  if (box) {
    await page.screenshot({ path: filePath, clip: { x: 0, y: Math.max(0, box.y - 15), width: 2880, height: Math.min(160, box.height + 30) } });
  }
  return txt;
}

// Manifest ảnh (captures.json) — append 1 entry vào phase (before|after).
function addCapture(folder, phase, entry) {
  const p = path.join(folder, 'captures.json');
  let m = { before: [], after: [] };
  if (fs.existsSync(p)) m = JSON.parse(fs.readFileSync(p, 'utf8'));
  m[phase] = m[phase] || [];
  // ghi đè entry cùng screen (idempotent khi chạy lại)
  m[phase] = m[phase].filter((e) => e.screen !== entry.screen);
  m[phase].push(entry);
  fs.writeFileSync(p, JSON.stringify(m, null, 2));
}

module.exports = { loadConfig, getPage, switchBranch, shot, captureTotalRow, addCapture };
