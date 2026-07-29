// copy_masters.js <institute_code> <django_id> <rails_id> [--dry] [--max N]
//
// Copy các 回数券マスター CHƯA LINK qua lại giữa 2 hệ, trên trang
// /superuser/backfill/tickets/. Mỗi lượt = 1 dòng (nút Copy chỉ hiện khi tick
// ĐÚNG 1 dòng ở ĐÚNG 1 bên — xem tickets.html:367-378), xong thì trang reload
// và NEXT_DJANGO_ID/NEXT_RAILS_ID nhích lên.
//
// AN TOÀN — script DỪNG NGAY nếu:
//   · hiện alert lỗi (vd "Rails API error ... Read timed out")
//   · sau 1 lượt copy mà dòng nguồn KHÔNG chuyển sang trạng thái đã-link
// Lý do: copy là ghi 2 bên. Timeout ở giữa = Rails có thể đã tạo ticket nhưng
// chưa link → cứ chạy tiếp là sinh rác không kiểm soát được. Thà dừng để người xem.
//
// Login: /admin/login/ bằng username thuần (superadmin). Form /accounts/login/
// KHÔNG dùng được cho superuser vì nó ghép username = "<institute>@<staff>"
// (backoffice/forms/auth.py:66) mà superadmin không có staff profile nào.
// playwright chỉ được cài trong testcase-evidence/node_modules (xem package.json ở đó),
// thư mục backfill/ không có node_modules riêng → resolve tường minh theo đường dẫn.
const path = require('path');
const { chromium } = require(path.join(__dirname, '..', 'testcase-evidence', 'node_modules', 'playwright'));

const CODE = process.argv[2] || 'sakainishi';
const DJ_ID = process.argv[3] || '8';
const RA_ID = process.argv[4] || '8';
const DRY = process.argv.includes('--dry');
const MAXI = (() => { const i = process.argv.indexOf('--max'); return i > 0 ? parseInt(process.argv[i + 1], 10) : 60; })();

const BASE = process.env.TICKET_URL || 'http://localhost:8000';
const USER = process.env.BF_ADMIN_USER || 'superadmin';
const PASS = process.env.BF_ADMIN_PASS || 'Admin1234!';
const PAGE_URL = `${BASE}/superuser/backfill/tickets/?django_id=${DJ_ID}&rails_id=${RA_ID}&code=${CODE}`;

if (!BASE.includes('localhost') && !BASE.includes('127.0.0.1')) {
  console.error(`CHẶN: chỉ chạy trên local, BASE=${BASE}`); process.exit(1);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });

  // Alert của trang là kênh báo lỗi duy nhất → phải bắt, không được để nó chặn.
  const dialogs = [];
  page.on('dialog', async (d) => { dialogs.push(d.message()); await d.accept().catch(() => {}); });

  await page.goto(`${BASE}/admin/login/`, { waitUntil: 'domcontentloaded' });
  await page.fill('#id_username', USER);
  await page.fill('#id_password', PASS);
  await page.click('input[type=submit]');
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await sleep(1200);

  const load = async () => {
    await page.goto(PAGE_URL, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#copy-btn', { state: 'attached', timeout: 30000 });
    await sleep(600);
    if (!(await page.locator('.django-check, .rails-check').count())) {
      throw new Error('không thấy checkbox nào — login thất bại hay sai institute id?');
    }
  };

  // Dòng CHƯA link = checkbox còn enabled (dòng xanh đã link thì không cho chọn).
  const unlinked = async (side) => page.$$eval(`.${side}-check`, (els) =>
    els.filter((e) => !e.disabled).map((e) => e.value));

  await load();
  const d0 = await unlinked('django');
  const r0 = await unlinked('rails');
  console.log(`BAN ĐẦU: Django chưa link=${d0.length} [${d0.join(',')}]`);
  console.log(`         Rails  chưa link=${r0.length} [${r0.join(',')}]`);
  if (DRY) { console.log('--dry → không bấm gì.'); await browser.close(); return; }

  let done = 0, iter = 0;
  const log = [];

  // side='django' → tạo bản sao bên Rails; side='rails' → tạo bên Django.
  const copyOne = async (side, id) => {
    await page.click('button:has-text("クリア")').catch(() => {});
    await sleep(300);
    const cb = page.locator(`.${side}-check[value="${id}"]`);
    if (!(await cb.count())) return { id, ok: false, why: 'không còn dòng này trên trang' };
    await cb.check();
    await sleep(500);

    const btn = page.locator('#copy-btn');
    try { await btn.waitFor({ state: 'visible', timeout: 8000 }); }
    catch { return { id, ok: false, why: 'nút Copy không hiện (NEXT_ID null? hoặc đã link)' }; }
    const label = (await btn.textContent()).trim();

    dialogs.length = 0;
    await btn.click();
    await page.waitForSelector('#copyConfirmBtn', { state: 'visible', timeout: 10000 });
    await sleep(400);
    await Promise.all([
      page.waitForLoadState('domcontentloaded', { timeout: 90000 }).catch(() => {}),
      page.click('#copyConfirmBtn'),
    ]);
    await sleep(2500);
    if (dialogs.length) return { id, ok: false, why: `ALERT: ${dialogs.join(' | ').slice(0, 160)}`, label };

    // Xác minh bằng trạng thái trang, KHÔNG tin là thành công chỉ vì không có alert.
    await load();
    const still = await unlinked(side);
    if (still.includes(String(id))) return { id, ok: false, why: 'copy xong mà dòng vẫn CHƯA link', label };
    return { id, ok: true, label };
  };

  for (const side of ['django', 'rails']) {
    for (;;) {
      if (++iter > MAXI) { console.log(`DỪNG: quá ${MAXI} lượt (chốt an toàn).`); break; }
      const left = await unlinked(side);
      if (!left.length) { console.log(`${side}: hết dòng chưa link.`); break; }
      const id = left[0];
      const r = await copyOne(side, id);
      log.push({ side, ...r });
      if (r.ok) { done++; console.log(`  ✅ ${side} id=${id} (${r.label}) — còn ${left.length - 1}`); }
      else {
        console.log(`  ❌ ${side} id=${id}: ${r.why}`);
        console.log('DỪNG LẠI — không chạy tiếp để tránh sinh rác. Xem lại rồi chạy lại.');
        iter = MAXI + 1; break;
      }
    }
    if (iter > MAXI) break;
  }

  const dEnd = await unlinked('django');
  const rEnd = await unlinked('rails');
  console.log(`\nKẾT QUẢ: copy thành công ${done} lượt`);
  console.log(`  Django còn chưa link: ${dEnd.length} [${dEnd.join(',')}]`);
  console.log(`  Rails  còn chưa link: ${rEnd.length} [${rEnd.join(',')}]`);
  const fail = log.filter((l) => !l.ok);
  if (fail.length) console.log(`  THẤT BẠI: ${fail.map((f) => `${f.side}/${f.id}: ${f.why}`).join(' · ')}`);
  await browser.close();
})().catch((e) => { console.error('LỖI:', e.message); process.exit(1); });
