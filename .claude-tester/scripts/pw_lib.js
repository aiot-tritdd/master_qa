// Helper Playwright: đăng nhập + giữ session cho Threease Pro (dev).
// Cấu hình qua biến môi trường (đều có mặc định cho dev):
//   BASE_URL      = https://develop.pro.threease.com
//   BASIC_USER/BASIC_PASS = threesides / threesides   (HTTP basic auth)
//   INST/THER/PW  = TESTSEED001 / STAFF001 / password123  (form đăng nhập)
//   STATE_FILE    = <script_dir>/.state.json  (cache session dùng chung — KHÔNG phải deliverable,
//                    nên mặc định nằm cạnh script, không leak ra cwd/root khi skill quên set SHOTS_DIR)
//   SHOTS_DIR     = <folder>/shots — LUÔN set tường minh khi gọi (xem testcase-run.md/testcase-retest.md),
//                    default dưới đây chỉ là an toàn dự phòng, không dùng trong vận hành thật
// require('/Users/hieulnd/.claude-tester/scripts/pw_lib.js')
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const E = process.env;
const BASE = E.BASE_URL || 'https://develop.pro.threease.com';
const STATE = E.STATE_FILE || path.join(__dirname, '.state.json');
const SHOTS = E.SHOTS_DIR || path.join(__dirname, '.shots');
try { fs.mkdirSync(SHOTS, { recursive: true }); } catch (e) {}

async function getPage() {
  const browser = await chromium.launch();
  const opts = {
    httpCredentials: { username: E.BASIC_USER || 'threesides', password: E.BASIC_PASS || 'threesides' },
    viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2, locale: 'ja-JP',
  };
  if (fs.existsSync(STATE)) opts.storageState = STATE;
  const ctx = await browser.newContext(opts);
  const page = await ctx.newPage();
  await page.goto(BASE + '/shifts', { waitUntil: 'networkidle', timeout: 60000 });
  if (page.url().includes('login')) {
    await page.fill('input[data-cy=institute_code]', E.INST || 'TESTSEED001');
    await page.fill('input[data-cy=therapist_code]', E.THER || 'STAFF001');
    await page.fill('input[data-cy=password]', E.PW || 'password123');
    await page.click('[data-cy=loginButton]');
    await page.waitForURL((u) => !u.href.includes('login'), { timeout: 30000 });
    await ctx.storageState({ path: STATE });
  }
  return { browser, ctx, page, BASE, SHOTS };
}

// Chụp ảnh AN TOÀN: chờ màn hình render xong rồi mới chụp (tránh dính spinner/màn trắng).
// readySelector = selector/text đặc trưng chứng tỏ màn hình đã load (vd 'text=権限設定').
async function shot(page, path, readySelector, opts = {}) {
  if (readySelector) await page.waitForSelector(readySelector, { timeout: opts.timeout || 15000 });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}); // SPA có polling → bỏ qua nếu không idle
  await page.waitForTimeout(opts.settle || 500); // đệm cho animation/render client
  await page.screenshot({ path, ...opts.screenshot });
}

module.exports = { getPage, shot, BASE, SHOTS };
