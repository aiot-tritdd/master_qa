// migrate.js <folder> — chạy backfill migrate cho branch trong config (đọc sot). IRREVERSIBLE.
// Loop tới khi hết candidates (Rails archive theo lô 100). Chụp modal + result vào after/.
// KHÔNG hardcode branch/sot — lấy từ config.json.
//
// ⛔⛔ BẤM LẠI **KHÔNG** IDEMPOTENT VỚI CHIỀU sot='pro' — SINH VÉ TRÙNG.
//   Bên nào là SoT thì bên đó chạy `migrate_pack` (backfill_tool/views.py:1896-1908):
//     sot='ticket_app' → Django migrate (ĐỒNG BỘ, xong mới trả về)  → bấm lại vô hại.
//     sot='pro'        → Rails  migrate (Rails `queue_adapter=async`) → API TRẢ VỀ TRƯỚC KHI XONG.
//   Vé gốc chưa kịp archive ⇒ cú bấm kế đọc lại ĐÚNG danh sách ứng viên đó ⇒ migrate lần nữa.
//   Đo thật 2026-07-29 branch 66 (gerbill): loop bấm 11 lần → **1.200 vé mới từ 354 vé gốc**,
//   có vé bị nhân **9 bản**; khách bị cộng khống buổi (15 → 50). Phải xoá tay 846 vé.
//   ⇒ Từ đây: sau mỗi lô PHẢI ĐỢI DÒNG BRANCH ĐỨNG YÊN (job nền cạn) rồi mới được bấm tiếp.
const L = require('./lib_backfill.js');
const path = require('path');

// Đợi job nền chạy xong: đọc dòng branch tới khi nội dung KHÔNG đổi qua STABLE_READS lần liên tiếp.
// Đây là tín hiệu duy nhất quan sát được từ trình duyệt (dòng có sẵn 2 số candidates 2 bên).
const STABLE_READS = 3;
const POLL_MS = 5000;
const MAX_WAIT_MS = 10 * 60 * 1000;

(async () => {
  const folder = process.argv[2];
  const cfg = L.loadConfig(folder);
  const OUT = path.join(folder, 'after');
  const { branch_id, sot, branch_name_jp } = cfg;

  const { browser, page, BASE } = await L.getPage('ticket_admin', cfg);
  const url = BASE + '/superuser/backfill/ticket-packs/';

  // ⚠️ KHÔNG dùng nhãn 移行済み làm điều kiện dừng: nhãn đó hiện SAU MỖI LÔ, kể cả khi còn vé chưa
  //    xử lý ⇒ dừng sớm, migrate thiếu (đo 2026-07-28: branch 124 mới chạy 100/307 vé đã báo xong).
  //    Dòng branch có sẵn 2 số candidates → cứ lặp tới khi NỘI DUNG DÒNG KHÔNG ĐỔI (hết tiến triển).
  let prevRowTxt = null;
  for (let batch = 1; batch <= 40; batch++) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const row = page.locator('tr', { hasText: branch_name_jp }).first();
    if (!(await row.count())) { console.log('ERR: branch row not found:', branch_name_jp); break; }
    const rowTxt = (await row.innerText().catch(() => '')).replace(/\s+/g, ' ');
    if (prevRowTxt !== null && rowTxt === prevRowTxt) {
      console.log(`=== hết tiến triển sau ${batch - 1} lô — dừng. Dòng: ${rowTxt.slice(0, 120)}`);
      break;
    }
    prevRowTxt = rowTxt;
    console.log(`[batch ${batch}] dòng trước khi chạy: ${rowTxt.slice(0, 120)}`);

    await page.locator(`input[name=branch-select][value="${branch_id}"]`).check();
    await page.waitForTimeout(300);
    if (batch === 1) await row.screenshot({ path: `${OUT}/mig_1_selected_row.png` });

    await page.locator('#migrate-btn').click();
    await page.waitForTimeout(1200);
    await page.locator(`input[name=sotChoice][value="${sot}"]`).check();
    await page.waitForTimeout(500);
    const checked = await page.locator(`input[name=sotChoice][value="${sot}"]`).isChecked();
    if (!checked) { console.log(`ABORT: sot=${sot} not checked`); break; }
    if (batch === 1) await page.screenshot({ path: `${OUT}/mig_2_modal_${sot}.png` });

    await page.locator('#migrateConfirmModal').getByText('OK (実行)').click();
    await page.waitForTimeout(6000);
    await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
    if (batch === 1) await page.screenshot({ path: `${OUT}/mig_3_result.png`, fullPage: true });
    console.log(`[batch ${batch}] confirmed sot=${sot}`);

    // ⛔ CHỐT CHỐNG TRÙNG — xem khối cảnh báo đầu file. Tuyệt đối không bỏ.
    // `networkidle` chỉ nói "HTTP xong", KHÔNG nói "job nền xong". Bấm tiếp lúc này = sinh vé trùng.
    const t0 = Date.now();
    let stable = 0, last = null;
    while (Date.now() - t0 < MAX_WAIT_MS) {
      await page.waitForTimeout(POLL_MS);
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1500);
      const r = page.locator('tr', { hasText: branch_name_jp }).first();
      const txt = (await r.count()) ? (await r.innerText().catch(() => '')).replace(/\s+/g, ' ') : null;
      if (txt !== null && txt === last) stable++; else { stable = 0; last = txt; }
      if (stable >= STABLE_READS) break;
    }
    if (stable < STABLE_READS) {
      console.log(`ABORT: sau ${Math.round(MAX_WAIT_MS / 1000)}s job nền VẪN chạy — dừng để khỏi sinh vé trùng.`);
      console.log('  → đợi job cạn rồi chạy lại migrate.js; nó tự bỏ qua phần đã xong.');
      break;
    }
    console.log(`[batch ${batch}] job nền đã cạn (${Math.round((Date.now() - t0) / 1000)}s) — an toàn bấm lô kế.`);
  }
  // chụp row sau cùng
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  const finalRow = page.locator('tr', { hasText: branch_name_jp }).first();
  if (await finalRow.count()) await finalRow.screenshot({ path: `${OUT}/bf_row_after.png` });
  await browser.close();
  console.log('DONE migrate', branch_id, sot);
})();
