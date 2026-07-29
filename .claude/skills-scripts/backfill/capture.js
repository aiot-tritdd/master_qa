// capture.js <folder> <before|after> — chụp MỌI report trong REPORT_REGISTRY.json cho branch trong
// config. KHÔNG hardcode branch, KHÔNG hardcode danh sách màn: registry là nguồn sự thật, thiếu 1
// dòng là build_excel.py in đỏ 未撮影 (không im lặng bỏ qua).
//
// capture: "ui"   → mở URL, chụp full page (need_search → bấm 検索 trước)
//          "xlsx" → do gen_exports.py sinh, script này chỉ ghi manifest placeholder
//          "ref"  → dùng lại ảnh của 1 case chức năng (capture_func.js chụp), bỏ qua ở đây
// Ảnh case CHỨC NĂNG do capture_func.js lo (sheet 3_CHUCNANG).
const L = require('./lib_backfill.js');
const fs = require('fs');
const path = require('path');

const REGISTRY = path.join(__dirname, '..', '..', 'skills', 'backfill', 'REPORT_REGISTRY.json');

(async () => {
  const folder = process.argv[2];
  const phase = process.argv[3] || 'before';
  const cfg = L.loadConfig(folder);
  const OUT = path.join(folder, phase);
  const NAME = cfg.branch_name_jp;
  fs.mkdirSync(OUT, { recursive: true });

  const reports = JSON.parse(fs.readFileSync(REGISTRY, 'utf8')).reports;
  const ui = (sys) => reports.filter((r) => r.system === sys && r.capture === 'ui');
  const dl = (sys) => reports.filter((r) => r.system === sys && r.capture === 'download');
  const done = [];
  const failed = [];

  // ---------- TICKET (Django) — mọi report trong registry ----------
  {
    const { browser, page, BASE } = await L.getPage('ticket', cfg);
    // BẮT BUỘC switch sang branch đích TRƯỚC khi chụp: report dashboard/販売 lấy số theo branch
    // đang chọn trong session → không switch là chụp số của branch KHÁC (sai bằng chứng).
    await page.goto(BASE + '/reports/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    await L.switchBranchTicket(page, cfg.branch_id);
    const cur = await page.locator('select[name=branch_id]').inputValue().catch(() => '?');
    console.log(`Ticket app: branch context = ${cur} (cần ${cfg.branch_id})`);
    if (String(cur) !== String(cfg.branch_id)) throw new Error(`[backfill] switch branch Ticket THẤT BẠI (đang ở ${cur}) — dừng để không chụp sai branch.`);
    for (const r of ui('ticket')) {
      const file = `${OUT}/${r.key}_${phase}.png`;
      try {
        const resp = await page.goto(BASE + r.url, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1800);
        const code = resp ? resp.status() : 0;
        if (code >= 400) {
          failed.push(`${r.key} HTTP ${code}`);
          L.addCapture(folder, phase, {
            sheet: '2_REPORT', screen: r.key, url: BASE + r.url, phase, file: null,
            note: `${r.name_vi} — KHÔNG MỞ ĐƯỢC: HTTP ${code} (quyền account hoặc route đổi). ${r.phase7_note}`,
            http: code, boxes: [],
          });
          continue;
        }
        if (r.need_search) {
          const b = page.locator('button:has-text("検索"), input[value="検索"]').first();
          if (await b.count()) { await b.click(); await page.waitForTimeout(2500); }
        }
        await L.shot(page, file, null, { screenshot: { fullPage: true } });
        L.addCapture(folder, phase, {
          sheet: '2_REPORT', screen: r.key, url: BASE + r.url, phase, file,
          note: `${r.name_vi} (${r.name_jp}) — ${r.phase7_note}`, http: code, boxes: [],
        });
        done.push(r.key);
      } catch (e) {
        failed.push(`${r.key} ${e.message.slice(0, 60)}`);
      }
    }

    // report chỉ-có-CSV: đi đúng đường của user (vào trang có nút) rồi tải file thật
    for (const r of dl('ticket')) {
      try {
        await page.goto(BASE + r.download_page, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);
        // Nút CSV chỉ render SAU khi bấm 検索 (trang mở ra chưa có bảng ⇒ chưa có nút) — dò 2026-07-28.
        const s = page.locator('button:has-text("検索"), input[value="検索"]').first();
        if (await s.count()) { await s.click(); await page.waitForTimeout(3000); }
        const btn = page.locator(`button:has-text("${r.download_btn}"), a:has-text("${r.download_btn}"), input[value="${r.download_btn}"]`).last();
        if (!(await btn.count())) throw new Error(`không thấy nút ${r.download_btn} trên ${r.download_page}`);
        const [download] = await Promise.all([page.waitForEvent('download', { timeout: 30000 }), btn.click()]);
        const csv = `${OUT}/${r.key}_${phase}.csv`;
        await download.saveAs(csv);
        const lines = fs.readFileSync(csv, 'utf8').split('\n').filter((l) => l.trim()).length;
        L.addCapture(folder, phase, {
          sheet: '2_REPORT', screen: r.key, url: BASE + r.download_page + ` → ${r.download_btn}`, phase,
          file: null, csv, csv_lines: lines,
          note: `${r.name_vi} (${r.name_jp}) — tải file CSV thật: ${lines} dòng. ${r.phase7_note}`, boxes: [],
        });
        done.push(r.key);
      } catch (e) {
        failed.push(`${r.key} ${e.message.slice(0, 70)}`);
        L.addCapture(folder, phase, {
          sheet: '2_REPORT', screen: r.key, url: r.url, phase, file: null,
          note: `${r.name_vi} — KHÔNG tải được CSV: ${e.message.slice(0, 90)}`, boxes: [],
        });
      }
    }
    await browser.close();
  }

  // ---------- BACKFILL admin: dòng branch (sheet 1_DATA) ----------
  {
    const { browser, page, BASE } = await L.getPage('ticket_admin', cfg);
    await page.goto(BASE + '/superuser/backfill/ticket-packs/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const row = page.locator('tr', { hasText: NAME }).first();
    const file = `${OUT}/bf_row_${phase}.png`;
    let ok = false;
    if (await row.count()) {
      await row.scrollIntoViewIfNeeded(); await page.waitForTimeout(400);
      await row.screenshot({ path: file }); ok = true;
    }
    L.addCapture(folder, phase, {
      sheet: '1_DATA', screen: 'bf_row', url: BASE + '/superuser/backfill/ticket-packs/', phase,
      file: ok ? file : null,
      note: `Dòng branch ${cfg.branch_id} (${NAME}) trên màn backfill — số vé mồ côi 2 bên.`, boxes: [],
    });
    if (ok) done.push('bf_row'); else failed.push('bf_row (không thấy dòng branch)');
    await browser.close();
  }

  // ---------- PRO (Rails/Nuxt) — mọi report registry system=pro ----------
  {
    const { browser, page, BASE } = await L.getPage('pro', cfg);
    await L.switchBranch(page, NAME);

    for (const r of ui('pro')) {
      const file = `${OUT}/${r.key}_${phase}.png`;
      try {
        if (r.key === 'pro_packs_total') {
          await page.goto(BASE + '/tickets/packs', { waitUntil: 'domcontentloaded' });
          await page.waitForTimeout(6000);
          const txt = await L.captureTotalRow(page, file);
          L.addCapture(folder, phase, {
            sheet: '2_REPORT', screen: r.key, url: BASE + '/tickets/packs', phase, file,
            note: `${r.name_vi} — 販売金額 phải BẤT BIẾN. Đọc được: ${txt}`, boxes: [],
          });
          done.push(r.key);
          continue;
        }
        if (r.key === 'pro_journal') {
          await page.goto(BASE + '/accounting', { waitUntil: 'domcontentloaded' });
          await page.waitForTimeout(3500);
          await page.locator('button:has-text("PRINT JOURNAL"), :text("PRINT JOURNAL")').first().click();
          await page.waitForTimeout(2500);
        } else if (r.key === 'pro_reservations') {
          await page.goto(BASE + '/dashboard', { waitUntil: 'domcontentloaded' });
          await page.waitForTimeout(5000);
        } else {
          await page.goto(BASE + r.url, { waitUntil: 'domcontentloaded' });
          await page.waitForTimeout(5000);
        }
        await L.shot(page, file, null, { screenshot: { fullPage: true } });
        L.addCapture(folder, phase, {
          sheet: '2_REPORT', screen: r.key, url: BASE + (r.url.startsWith('/') ? r.url : ''), phase, file,
          note: `${r.name_vi} (${r.name_jp}) — ${r.phase7_note}`, boxes: [],
        });
        done.push(r.key);
      } catch (e) {
        failed.push(`${r.key} ${e.message.slice(0, 60)}`);
        L.addCapture(folder, phase, {
          sheet: '2_REPORT', screen: r.key, url: r.url, phase, file: null,
          note: `${r.name_vi} — KHÔNG chụp được: ${e.message.slice(0, 80)}`, boxes: [],
        });
      }
    }
    await browser.close();
  }

  // ---------- xlsx report (gen_exports.py sinh) → ghi manifest để build_excel đọc số ----------
  for (const r of reports.filter((x) => x.capture === 'xlsx')) {
    const f = path.join(folder, phase, `${r.xlsx_name}_${phase}.xlsx`);
    L.addCapture(folder, phase, {
      sheet: '2_REPORT', screen: r.key, url: r.url, phase,
      file: null, xlsx: fs.existsSync(f) ? f : null,
      note: `${r.name_vi} — ${r.phase7_note}`, boxes: [],
    });
  }

  console.log(`DONE capture ${phase}: ${done.length} màn OK` + (failed.length ? `, ${failed.length} FAIL → ${failed.join(' | ')}` : ''));
  console.log(`manifest: ${path.join(folder, 'captures.json')}`);
})();
