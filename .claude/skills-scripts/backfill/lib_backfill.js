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
// ⚠️⚠️ SET ENV CHO **MỌI** TARGET, KHÔNG CHỈ TARGET ĐANG GỌI.
// pw_lib build hằng CFG **một lần duy nhất lúc require**. Nếu chỉ set env của target hiện tại thì
// target nào require pw_lib TRƯỚC sẽ quyết định CFG của cả các target sau:
//   capture.js gọi getPage('ticket') trước → lúc đó BASE_URL chưa set → CFG.pro.BASE rơi về
//   default = 'https://develop.pro.threease.com' (**DEV REMOTE**) → getPage('pro') mở server
//   REMOTE + dùng state cache của account remote (テスト 管理者) → chụp evidence của MÔI TRƯỜNG
//   KHÁC mà không ai biết. Đo thật 2026-07-28, mất 4 lượt chạy mới ra.
// → Đặt hết env ở đây, trước bất kỳ require nào. Có kiểm tra chốt lại ở cuối hàm.
function setAllEnv(cfg) {
  process.env.NO_STATE = '1';                         // luôn login sạch (LOCAL khác remote state)
  process.env.BASIC_USER = process.env.BASIC_USER || 'x';
  process.env.BASIC_PASS = process.env.BASIC_PASS || 'x';
  process.env.BASE_URL = 'http://localhost:8080';     // Pro
  process.env.INST = cfg.institute_code;
  process.env.THER = cfg.pro_staff_code;
  process.env.PW = cfg.password || 'password123';
  process.env.TICKET_URL = 'http://localhost:8000';   // Ticket app
  process.env.TK_INST = cfg.institute_code;
  process.env.TK_STAFF = cfg.ticket_staff_code;
  process.env.TK_PW = cfg.password || 'password123';
  process.env.TICKET_ADMIN_URL = 'http://localhost:8000';
  process.env.TK_ADMIN_USER = cfg.backfill_admin_user || 'superadmin';
  process.env.TK_ADMIN_PASS = cfg.backfill_admin_pass || 'Admin1234!';
}

function getPage(target, cfg) {
  setAllEnv(cfg);
  const PW = require(PW_LIB);
  if (target !== 'pro') return PW.getPage(target).then((r) => assertLocal(r, target));
  // Pro (Nuxt node14) login HAY FLAKE: pw_lib dùng waitForURL(...).catch(() => {}) nên login trượt
  // là im lặng đứng ở /login (đo 2026-07-28: cùng account, lần được lần không). Pipeline backfill dài
  // (23 report + 23 case) → trượt 1 nhịp là mất cả lượt chạy. Ở đây retry login TƯỜNG MINH.
  return getPageProWithRetry(PW, cfg);
}

// CHỐT CỨNG: backfill là DEV LOCAL ONLY. Nếu vì bất kỳ lý do gì page trỏ ra host khác localhost
// thì DỪNG NGAY — thà không có evidence còn hơn có evidence của môi trường khác (hoặc thao tác
// migrate phá huỷ lên môi trường người khác).
function assertLocal(r, target) {
  const u = r.page.url();
  const base = r.BASE || '';
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)[:/]/.test(base) || (u && !/^https?:\/\/(localhost|127\.0\.0\.1)[:/]/.test(u) && !u.startsWith('about:'))) {
    r.browser.close().catch(() => {});
    throw new Error(`[backfill] TARGET '${target}' KHÔNG phải localhost (BASE=${base} URL=${u}). `
      + `Backfill chỉ được chạy trên DEV LOCAL — dừng ngay.`);
  }
  return r;
}

async function getPageProWithRetry(PW, cfg, tries = 3) {
  let last;
  for (let i = 1; i <= tries; i++) {
    const r = assertLocal(await PW.getPage('pro'), 'pro');
    if (!/\/login/.test(r.page.url())) return r;
    // thử điền form login lại trong CHÍNH page này (khỏi mở browser mới)
    for (let k = 0; k < 2; k++) {
      try {
        await r.page.locator('input[data-cy=institute_code]').waitFor({ state: 'visible', timeout: 15000 });
        await r.page.fill('input[data-cy=institute_code]', cfg.institute_code);
        await r.page.fill('input[data-cy=therapist_code]', cfg.pro_staff_code);
        await r.page.fill('input[data-cy=password]', cfg.password || 'password123');
        await r.page.click('[data-cy=loginButton]');
        await r.page.waitForURL((u) => !u.href.includes('login'), { timeout: 45000 });
        // chờ app ghi devise-token xong, đừng trả page về sớm (xem ghi chú ở switchBranch)
        await r.page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
        await r.page.waitForTimeout(2500);
        return r;
      } catch (e) { last = e; await r.page.waitForTimeout(2000); }
    }
    console.log(`[backfill] Pro login trượt lần ${i}/${tries} (đang ở ${r.page.url()}) — thử lại...`);
    await r.browser.close().catch(() => {});
  }
  throw new Error(`[backfill] Pro login thất bại sau ${tries} lần với inst='${cfg.institute_code}' `
    + `staff='${cfg.pro_staff_code}'. Account đã verify OK trong DB thì đây là flake UI/timing. `
    + `Chi tiết cuối: ${last && last.message ? last.message.slice(0, 120) : 'n/a'}`);
}

// Chuyển branch context trên Pro SPA.
// Dò 2026-07-28: nút chuyển branch là tên branch hiện tại + icon `arrow_drop_down` ở góc trên trái;
// bấm ra panel có ô 検索 + danh sách branch NHÓM THEO TỈNH — và CHỈ liệt kê branch mà staff đang
// login có quyền. Staff không có quyền branch đích → danh sách trống → THROW rõ ràng thay vì chụp
// nhầm branch khác (đã từng suýt sai: matuda chỉ thấy はまのまち院, không thấy 福山院).
async function switchBranch(page, branchNameJp) {
  // ⚠️ KHÔNG goto('/') ở đây. Sau login, devise-token mới ghi vào localStorage; hard-reload ngay
  //    một nhịp là app coi như chưa auth → đá về /login (đo 2026-07-28, mất 3 lượt chạy vì lỗi này).
  //    getPage đã để ta ở trang trong (vd /shifts) rồi — cứ bấm dropdown ngay trên trang đó.
  if (/\/login/.test(page.url())) {
    throw new Error(`[backfill] Pro đang ở ${page.url()} — chưa login xong, không switch branch được.`);
  }
  // SPA Nuxt node14 boot chậm và KHÔNG đều (8s có lúc chưa xong) → chờ theo ĐIỀU KIỆN, đừng sleep cố định.
  const dd = page.locator('text=arrow_drop_down').first();
  try {
    await dd.waitFor({ state: 'visible', timeout: 60000 });
  } catch (e) {
    if (/\/login/.test(page.url())) {
      throw new Error(`[backfill] Pro KHÔNG login được với inst='${process.env.INST}' staff='${process.env.THER}' `
        + `(đứng ở ${page.url()}). Kiểm pro_staff_code trong config.json + chạy ./seed_dev_accounts.sh.`);
    }
    throw new Error(`[backfill] chờ 60s vẫn không thấy nút chuyển branch (arrow_drop_down) trên Pro. URL=${page.url()}. `
      + `Nếu UI đổi → dò lại bằng GitNexus.`);
  }
  await page.waitForTimeout(1500);
  await dd.click();
  await page.waitForTimeout(2000);
  const box = page.locator('input').first();
  if (await box.count()) { await box.fill(branchNameJp.slice(0, 4)).catch(() => {}); await page.waitForTimeout(2000); }
  const target = page.locator(`text=${branchNameJp}`);
  if (!(await target.count())) {
    const seen = (await page.locator('body').innerText()).replace(/\s+/g, ' ').slice(0, 300);
    throw new Error(`[backfill] staff '${process.env.THER}' KHÔNG có quyền vào branch '${branchNameJp}' `
      + `(danh sách chọn không có). Đổi pro_staff_code trong config.json sang staff có quyền — HỎI USER, `
      + `đừng tự đoán. Panel đang thấy: ${seen}`);
  }
  await target.last().click();
  await page.waitForTimeout(5000);
  // CHỐT: header phải mang tên branch đích. Không assert là có ngày chụp cả bộ ảnh của branch khác
  // mà không ai biết (đã suýt xảy ra: session lạc sang user 'テスト 管理者' giữa các lượt chạy).
  const head = (await page.locator('body').innerText()).slice(0, 80);
  if (!head.includes(branchNameJp)) {
    throw new Error(`[backfill] switch branch Pro THẤT BẠI: header đang là "${head.split('\n')[0]}" `
      + `chứ không phải "${branchNameJp}". Dừng để không chụp sai branch.`);
  }
  return true;
}

// Chuyển branch trên Ticket app (Django). Dò 2026-07-28: `select[name=branch_id]` (value = branch id)
// trong form POST /switch-branch, liệt kê MỌI branch của institute. Không switch thì report
// dashboard/販売 lấy số của branch đang chọn = SAI branch.
async function switchBranchTicket(page, branchId) {
  const sel = page.locator('select[name=branch_id]');
  if (!(await sel.count())) throw new Error('[backfill] không thấy select[name=branch_id] trên Ticket app — UI đổi.');
  const has = await sel.locator(`option[value="${branchId}"]`).count();
  if (!has) throw new Error(`[backfill] Ticket app: staff '${process.env.TK_STAFF}' không thấy branch ${branchId} trong select.`);
  await sel.selectOption(String(branchId));
  await page.waitForTimeout(1500);
  // onchange có thể chưa submit → submit form thủ công
  const cur = await sel.inputValue().catch(() => '');
  if (cur === String(branchId)) {
    await page.evaluate(() => {
      const s = document.querySelector('select[name=branch_id]');
      if (s && s.form) s.form.submit();
    });
  }
  await page.waitForTimeout(3000);
  return true;
}

// Mở màn チケット情報 của 1 khách bên Pro.
// Dò 2026-07-28: danh sách 顧客管理 PHÂN TRANG (`/customers?page=1`, 100 dòng/trang) → khách ở trang
// sau thì duyệt tbody không bao giờ thấy (đã mất ảnh B2/B5 vì lỗi này). Phải gõ ô `検索` để lọc trước.
// Cột đầu là 顧客ID (td index 1). Trả true nếu mở được tab チケット情報.
async function openCustomerTicketTab(page, code, name) {
  await page.locator('text=顧客管理').first().click();
  await page.waitForTimeout(6000);
  const search = page.locator('input[type=text]').first();
  for (const q of [String(code), name].filter(Boolean)) {
    if (await search.count()) {
      await search.fill(String(q)).catch(() => {});
      // ⚠️ PHẢI Enter. Chỉ fill thôi thì danh sách KHÔNG lọc (vẫn 100 dòng trang 1) — đã mất 2 lượt
      // chạy vì tưởng "không có khách này". Sau Enter thì còn đúng dòng cần tìm.
      await search.press('Enter').catch(() => {});
      await page.waitForTimeout(5000);
    }
    const rows = page.locator('tr');
    const n = await rows.count();
    for (let i = 0; i < n; i++) {
      const id = (await rows.nth(i).locator('td').nth(1).innerText().catch(() => '')).trim();
      if (id === String(code)) {
        await rows.nth(i).locator('td').nth(2).click();
        await page.waitForTimeout(4500);
        await page.locator('text=チケット情報').first().click();
        await page.waitForTimeout(3500);
        return true;
      }
    }
  }
  return false;
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

module.exports = { loadConfig, getPage, switchBranch, switchBranchTicket, openCustomerTicketTab, shot, captureTotalRow, addCapture };
