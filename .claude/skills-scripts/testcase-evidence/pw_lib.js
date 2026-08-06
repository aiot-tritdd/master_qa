// pw_lib.js — Playwright helper cho Threease dev. CƠ KHÍ, không reasoning.
// getPage(target) -> { browser, context, page, BASE }. Mặc định đăng nhập Pro.
// shot(page, path, readySelector) -> chụp AN TOÀN (chờ màn render xong). BẮT BUỘC dùng thay screenshot trần.
//
// Creds đọc từ .env (repo root master_qa/, gitignored) — KHÔNG hardcode trong file này.
//   Xem .env.example cho danh sách biến. Override URL/hành vi: BASE_URL, HEADED=1, LOCALE…
// Cache session: .state.<target>.json cạnh file này (KHÔNG phải deliverable, không leak ra <folder>).
//   NO_STATE=1 để tắt cache (khi cần login sạch, vd đổi account giữa chừng).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// ── Nạp .env (repo root) vào process.env — KHÔNG ghi đè biến đã set sẵn ngoài shell, KHÔNG cần dependency.
//    Creds THẬT sống ở .env (gitignored); danh sách biến xem .env.example.
(() => {
  const envPath = path.join(__dirname, '../../..', '.env');
  if (!fs.existsSync(envPath)) return;
  for (const raw of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const i = line.indexOf('=');
    const k = line.slice(0, i).trim();
    const v = line.slice(i + 1).trim().replace(/^["']|["']$/g, '');
    if (k && !(k in process.env)) process.env[k] = v;
  }
})();

// Biến bắt buộc theo target — thiếu thì báo RÕ (không hardcode creds làm fallback nữa).
const REQ = {
  pro:          ['BASIC_USER', 'BASIC_PASS', 'INST', 'THER', 'PW'],
  reservation:  ['BASIC_USER', 'BASIC_PASS'],
  admin:        [],
  ticket_admin: ['TK_ADMIN_USER', 'TK_ADMIN_PASS'],
  ticket:       ['TK_INST', 'TK_STAFF', 'TK_PW'],
};
function requireEnv(target) {
  const missing = (REQ[target] || REQ.pro).filter((n) => !process.env[n]);
  if (missing.length) {
    throw new Error(
      `[pw_lib] Thiếu biến môi trường cho target '${target}': ${missing.join(', ')}.\n` +
      `→ Copy .env.example thành .env (repo root master_qa/) rồi điền (xin team lead). Xem docs/SETUP.md §A3.`,
    );
  }
}

const CFG = {
  pro: {
    BASE: process.env.BASE_URL || 'https://develop.pro.threease.com',
    basic: { username: process.env.BASIC_USER, password: process.env.BASIC_PASS },
    login: {
      inst: process.env.INST,
      // Pro login dùng therapist code (2026/07/10 đổi cơ chế). Giá trị ở .env (THER).
      ther: process.env.THER,
      pw:   process.env.PW,
    },
  },
  reservation: {
    BASE: process.env.BASE_URL || 'https://reservation-dev.threease.com',
    basic: { username: process.env.BASIC_USER, password: process.env.BASIC_PASS },
    login: null,
  },
  admin: {
    BASE: process.env.BASE_URL || 'https://admin-dev.threease.com',
    basic: null,
    login: null, // form login riêng, điền trong script khi cần (creds ở .env)
  },
  ticket_admin: {
    BASE: process.env.TICKET_ADMIN_URL || 'https://ticket-dev.threease.com',
    basic: null,
    django_admin: {
      user: process.env.TK_ADMIN_USER,
      pass: process.env.TK_ADMIN_PASS,
    },
  },
  ticket: {
    BASE: process.env.TICKET_URL || 'https://ticket-dev.threease.com',
    basic: null,
    django_login: {
      inst:  process.env.TK_INST,
      // Staff mặc định đủ quyền coupon 設定/登録/編集 + report; vài màn report cần staff quyền cao hơn → đổi TK_STAFF (.env).
      staff: process.env.TK_STAFF,
      pw:    process.env.TK_PW,
    },
  },
};

const stateFile = (target) => path.join(__dirname, `.state.${target}.json`);

async function getPage(target = 'pro') {
  requireEnv(target);
  const c = CFG[target] || CFG.pro;
  const browser = await chromium.launch({ headless: !process.env.HEADED });

  const opts = {
    httpCredentials: c.basic ? { username: c.basic.username, password: c.basic.password } : undefined,
    viewport: { width: 1440, height: 900 },
    // ⚠️ locale QUYẾT ĐỊNH NGÔN NGỮ UI. Không set → app chạy EN (`/en/shifts`, sidebar "Home/Reservation").
    //    Spec viết bằng tiếng Nhật (未払い/支払い済/請求書/キャンセル) sẽ KHÔNG match → FAIL SAI do harness.
    //    (Đo 2026-07-09: ja-JP → `/shifts`, sidebar ホーム/予約/会計.) Ghi đè bằng env LOCALE nếu cần test EN.
    locale: process.env.LOCALE || 'ja-JP',
    // Ảnh evidence nét gấp đôi (2880×1800 thay vì 1440×900) — chuẩn giao hàng là "PNG rõ".
    deviceScaleFactor: Number(process.env.DSF || 2),
  };
  // Tái dùng session đã đăng nhập -> bỏ qua form login (tiết kiệm 5-8s/script).
  const SF = stateFile(target);
  if (!process.env.NO_STATE && fs.existsSync(SF)) opts.storageState = SF;

  const context = await browser.newContext(opts);
  const page = await context.newPage();

  // ⚠️ Lưu state NGAY sau khi URL đổi là SAI: app chưa kịp ghi devise-token vào localStorage
  //    → state rỗng session → lần sau tưởng có cache nhưng vẫn bị đá về /login (đo 2026-07-09).
  //    Phải chờ app ổn định (networkidle + đệm) rồi mới snapshot.
  const save = async () => {
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(1500);
    try { await context.storageState({ path: SF }); } catch (e) {}
  };

  // Vuetify + i18n: form login re-render sau khi nạp locale → element bị detach giữa chừng.
  // Chờ input visible NGAY TRƯỚC mỗi lần fill, và retry 1 lần nếu detach.
  const fillSafe = async (sel, val) => {
    for (let i = 0; i < 3; i++) {
      try {
        await page.locator(sel).waitFor({ state: 'visible', timeout: 10000 });
        await page.fill(sel, val, { timeout: 10000 });
        return;
      } catch (e) {
        if (i === 2) throw e;
        await page.waitForTimeout(1000); // đợi re-render xong rồi thử lại
      }
    }
  };

  // Django admin (ticket-dev) — form login riêng, không phải Nuxt data-cy.
  if (c.django_admin) {
    await page.goto(c.BASE + '/admin/login/', { waitUntil: 'domcontentloaded' });
    if (await page.locator('#id_username').isVisible().catch(() => false)) {
      await fillSafe('#id_username', c.django_admin.user);
      await fillSafe('#id_password', c.django_admin.pass);
      await page.click('input[type=submit]');
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      await save();
    }
    return { browser, context, page, BASE: c.BASE };
  }

  // Ticket-app (ticket-dev) — Django form login: institute/staff/password.
  if (c.django_login) {
    await page.goto(c.BASE + '/accounts/login/', { waitUntil: 'domcontentloaded' });
    if (await page.locator('#id_institute_code').isVisible().catch(() => false)) {
      await fillSafe('#id_institute_code', c.django_login.inst);
      await fillSafe('#id_staff_code', c.django_login.staff);
      await fillSafe('#id_password', c.django_login.pw);
      await page.click('button[type=submit], input[type=submit]');
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      await save();
    }
    return { browser, context, page, BASE: c.BASE };
  }

  await page.goto(c.BASE + '/', { waitUntil: 'domcontentloaded' });

  // Login form Pro (data-cy) — chỉ điền NẾU thật sự chưa đăng nhập.
  // ⚠️ Ba cách SAI đã đo (2026-07-09) — app luôn render form login một nhịp rồi mới xác thực xong:
  //    · `count()`                 → đếm cả node ẨN → tưởng cần login → treo.
  //    · `url().includes('login')` → RACE: app ghé /login rồi mới sang /shifts.
  //    · `waitFor({visible})` sớm  → form CÓ visible một nhịp kể cả khi session hợp lệ, rồi unmount.
  //    → Đúng: để trang LẮNG XUỐNG (networkidle + đệm) rồi mới hỏi form còn visible không.
  let needLogin = false;
  if (c.login) {
    await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(2500); // đệm cho auth-check + redirect xong
    needLogin = await page.locator('input[data-cy=institute_code]').isVisible().catch(() => false);
  }
  if (needLogin) {
    await fillSafe('input[data-cy=institute_code]', c.login.inst);
    await fillSafe('input[data-cy=therapist_code]', c.login.ther);
    await fillSafe('input[data-cy=password]', c.login.pw);
    await page.click('[data-cy=loginButton]');
    await page.waitForURL((u) => !u.href.includes('login'), { timeout: 30000 }).catch(() => {});
    await save();
  }
  return { browser, context, page, BASE: c.BASE };
}

// Chụp ảnh AN TOÀN: chờ màn render xong rồi mới chụp (tránh dính spinner/màn trắng).
// readySelector = selector/text đặc trưng chứng tỏ màn hình đã load (vd 'text=権限設定').
// LUÔN dùng hàm này. KHÔNG dùng `waitForTimeout(6000) + page.screenshot()` — 6s là con số cầu may.
// Ảnh giữ nguyên PNG rõ (KHÔNG nén JPG) — build_evidence.py tự scale khi nhúng.
async function shot(page, filePath, readySelector, opts = {}) {
  if (readySelector) {
    await page.waitForSelector(readySelector, { timeout: opts.timeout || 15000 });
  }
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}); // SPA polling -> bỏ qua nếu không idle
  await page.waitForTimeout(opts.settle || 500); // đệm animation/render client
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  await page.screenshot({ path: filePath, ...opts.screenshot });
  return filePath;
}

module.exports = { getPage, shot, CFG };
