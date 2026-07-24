// migrate.js <folder> — chạy backfill migrate cho branch trong config (đọc sot). IRREVERSIBLE.
// Loop tới khi hết candidates (Rails archive theo lô 100). Chụp modal + result vào after/.
// KHÔNG hardcode branch/sot — lấy từ config.json.
const L = require('./lib_backfill.js');
const path = require('path');

(async () => {
  const folder = process.argv[2];
  const cfg = L.loadConfig(folder);
  const OUT = path.join(folder, 'after');
  const { branch_id, sot, branch_name_jp } = cfg;

  const { browser, page, BASE } = await L.getPage('ticket_admin', cfg);
  const url = BASE + '/superuser/backfill/ticket-packs/';

  for (let batch = 1; batch <= 10; batch++) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const row = page.locator('tr', { hasText: branch_name_jp }).first();
    if (!(await row.count())) { console.log('ERR: branch row not found:', branch_name_jp); break; }
    // trạng thái: nếu đã 移行済み thì dừng
    const rowTxt = (await row.innerText().catch(() => '')).replace(/\s+/g, ' ');
    if (batch > 1 && rowTxt.includes('移行済み')) { console.log('=== migrated (移行済み) ==='); break; }

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
  }
  // chụp row sau cùng
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  const finalRow = page.locator('tr', { hasText: branch_name_jp }).first();
  if (await finalRow.count()) await finalRow.screenshot({ path: `${OUT}/bf_row_after.png` });
  await browser.close();
  console.log('DONE migrate', branch_id, sot);
})();
