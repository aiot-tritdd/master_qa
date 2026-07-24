// capture.js <folder> <before|after> — chụp mọi màn liên quan (Ticket reports, Pro stats/合計,
// customer チケット情報, 精算, reservations, backfill row) cho branch trong config. Ghi captures.json.
// KHÔNG hardcode branch. Customer code lấy từ data_<phase>.json (rails_sample_cust_code).
const L = require('./lib_backfill.js');
const fs = require('fs');
const path = require('path');

(async () => {
  const folder = process.argv[2];
  const phase = process.argv[3] || 'before';
  const cfg = L.loadConfig(folder);
  const OUT = path.join(folder, phase);
  const NAME = cfg.branch_name_jp;
  fs.mkdirSync(OUT, { recursive: true });
  const dataP = path.join(folder, `data_${phase}.json`);
  const custCode = fs.existsSync(dataP) ? (JSON.parse(fs.readFileSync(dataP, 'utf8')).rails?.rails_sample_cust_code) : null;

  // ---------- TICKET (Django) reports ----------
  {
    const { browser, page, BASE } = await L.getPage('ticket', cfg);
    const reps = [
      ['tk_reports', '/reports/', 'dashboard 過去30日 (販売金額 bất biến, 販売冊数 có thể phồng)', false],
      ['tk_sales', '/reports/sales/', '販売記録 doanh số (dùng Sum price → bất biến)', true],
      ['tk_timeline', '/reports/timeline/', '月次集計 theo tháng', true],
      ['tk_branches', '/reports/branches/', `店舗別 số dư — dòng ${NAME}`, true],
    ];
    for (const [screen, url, note, needSearch] of reps) {
      await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2000);
      if (needSearch) {
        const b = page.locator('button:has-text("検索"), input[value="検索"]').first();
        if (await b.count()) { await b.click(); await page.waitForTimeout(2500); }
      }
      const file = `${OUT}/${screen}_${phase}.png`;
      await L.shot(page, file, null, { screenshot: { fullPage: true } });
      L.addCapture(folder, phase, { sheet: '2_REPORT', screen, url: BASE + url, phase, file, note, boxes: [] });
    }
    await browser.close();
  }

  // ---------- BACKFILL admin: dòng branch ----------
  {
    const { browser, page, BASE } = await L.getPage('ticket_admin', cfg);
    await page.goto(BASE + '/superuser/backfill/ticket-packs/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const row = page.locator('tr', { hasText: NAME }).first();
    const file = `${OUT}/bf_row_${phase}.png`;
    if (await row.count()) { await row.scrollIntoViewIfNeeded(); await page.waitForTimeout(400); await row.screenshot({ path: file }); }
    L.addCapture(folder, phase, { sheet: '1_DATA', screen: 'bf_row', url: BASE + '/superuser/backfill/ticket-packs/', phase, file, note: `Backfill row branch ${cfg.branch_id} (${NAME})`, boxes: [] });
    await browser.close();
  }

  // ---------- PRO: packs 合計 + customer + 精算 + reservations ----------
  {
    const { browser, page, BASE } = await L.getPage('pro', cfg);
    await L.switchBranch(page, NAME);

    // packs 合計
    await page.goto(BASE + '/tickets/packs', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(6000);
    const totFile = `${OUT}/pro_packs_total_${phase}.png`;
    const totTxt = await L.captureTotalRow(page, totFile);
    L.addCapture(folder, phase, { sheet: '2_REPORT', screen: 'pro_packs_total', url: BASE + '/tickets/packs', phase, file: totFile, note: `Pro stats 合計 (販売金額 phải bất biến): ${totTxt}`, boxes: [] });

    // customer チケット情報 (nếu có custCode)
    if (custCode && custCode !== '0') {
      try {
        await page.locator('text=顧客管理').first().click();
        await page.waitForTimeout(4500);
        const rows = page.locator('tbody tr');
        const n = await rows.count();
        for (let i = 0; i < n; i++) {
          const id = (await rows.nth(i).locator('td').nth(1).innerText().catch(() => '')).trim();
          if (id === String(custCode)) { await rows.nth(i).locator('td').nth(2).click(); break; }
        }
        await page.waitForTimeout(4000);
        await page.locator('text=チケット情報').first().click();
        await page.waitForTimeout(3000);
        const cFile = `${OUT}/pro_customer_ticket_${phase}.png`;
        await L.shot(page, cFile, null, { screenshot: { fullPage: true } });
        L.addCapture(folder, phase, { sheet: '3_CHUCNANG', screen: 'customer_ticket', url: BASE + `/customers (code ${custCode})`, phase, file: cFile, note: `Customer ${custCode} tab チケット情報: vé migrate hiện đúng, vé cũ archived ẩn. Nút 返金 = BUG refund.`, boxes: [] });
        await page.keyboard.press('Escape').catch(() => {});
      } catch (e) { console.log('customer capture skip:', e.message.slice(0, 60)); }
    }

    // 精算 Journal Summary
    try {
      await page.goto(BASE + '/accounting', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(3500);
      await page.locator('button:has-text("PRINT JOURNAL"), :text("PRINT JOURNAL")').first().click();
      await page.waitForTimeout(2500);
      const jFile = `${OUT}/pro_journal_${phase}.png`;
      await L.shot(page, jFile, null, { screenshot: { fullPage: true } });
      L.addCapture(folder, phase, { sheet: '2_REPORT', screen: 'journal', url: BASE + '/accounting → PRINT JOURNAL', phase, file: jFile, note: '精算 Journal Summary (SAFE, có dòng 回数券).', boxes: [] });
    } catch (e) { console.log('journal skip:', e.message.slice(0, 60)); }

    // Reservations export (ホーム 予約履歴 EXCEL)
    try {
      await page.locator('text=ホーム').first().click();
      await page.waitForTimeout(5000);
      const rFile = `${OUT}/pro_reservations_${phase}.png`;
      await L.shot(page, rFile, null, { screenshot: { fullPage: true } });
      L.addCapture(folder, phase, { sheet: '2_REPORT', screen: 'reservations', url: BASE + '/dashboard → 予約履歴 EXCEL', phase, file: rFile, note: 'Reservations export (SAFE) — bảng 予約履歴 + nút EXCEL.', boxes: [] });
    } catch (e) { console.log('reservations skip:', e.message.slice(0, 60)); }

    await browser.close();
  }
  console.log(`DONE capture ${phase} — manifest: ${path.join(folder, 'captures.json')}`);
})();
