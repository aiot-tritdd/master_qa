// capture_bugs.js <folder> — ảnh UI THẬT cho từng bug confirmed (sheet 4_BUGS).
// Sếp/khách đọc ảnh UI, không đọc stacktrace → ảnh UI là bằng chứng CHÍNH, panel text
// (make_bug_images.py) chỉ là "chi tiết kỹ thuật cho dev" đặt bên dưới.
//
// AN TOÀN: chỉ bấm nút MỞ (返金 mở modal), TUYỆT ĐỐI không bấm nút xác nhận cuối.
// Với BUG-1 thì chính việc mở màn đã làm API refundability lỗi 500 → thấy ngay, không cần bấm.
// Bug nào không lộ được trên UI → ghi ui_capture=null + lý do, KHÔNG dựng ảnh giả.
const L = require('./lib_backfill.js');
const fs = require('fs');
const path = require('path');

(async () => {
  const folder = process.argv[2];
  const cfg = L.loadConfig(folder);
  const OUT = path.join(folder, 'after');
  fs.mkdirSync(OUT, { recursive: true });

  const bugsP = path.join(folder, 'bugs.json');
  if (!fs.existsSync(bugsP)) { console.log('capture_bugs: chưa có bugs.json — chạy confirm_bugs.py trước.'); return; }
  const data = JSON.parse(fs.readFileSync(bugsP, 'utf8'));
  const bugs = data.bugs || [];
  if (!bugs.length) { console.log('capture_bugs: 0 bug confirmed → không cần ảnh.'); return; }

  const dataA = path.join(folder, 'data_after.json');
  const D = fs.existsSync(dataA) ? JSON.parse(fs.readFileSync(dataA, 'utf8')) : { rails: {}, django: {} };
  const custPro = (D.rails || {}).rails_sample_cust_code;
  const shots = {};   // bug id → { ui: [file...], why: string }
  const need = (id) => bugs.some((b) => b.id === id);

  // ---------- Pro: BUG-1 (refund crash) + BUG-2 (tổng buổi dư) ----------
  if ((need('BUG-1') || need('BUG-2')) && custPro && custPro !== '0') {
    const { browser, page, BASE } = await L.getPage('pro', cfg);
    const httpErrors = [];
    page.on('response', (r) => { if (r.status() >= 400) httpErrors.push(`${r.status()} ${r.url().split('?')[0]}`); });
    try {
      await L.switchBranch(page, cfg.branch_name_jp);
      await page.locator('text=顧客管理').first().click();
      await page.waitForTimeout(4500);

      if (need('BUG-2')) {
        // Con số bị lỗi là cột `チケット残高` (tổng buổi còn lại) trong danh sách 顧客管理.
        // ⚠️ Cột này KHÔNG bật sẵn — phải mở bảng chọn cột (nút 設定 CỦA DANH SÁCH, không phải 設定 ở
        //    sidebar) rồi tick nó. Chụp màn mặc định thì ảnh KHÔNG chứa con số cần chứng minh
        //    (sếp phát hiện 2026-07-28: "cái chỗ hiển thị tổng buổi còn lại ở đâu?").
        const f = `${OUT}/bug_BUG-2_ui.png`;
        let boxes = [];
        let val = '?';
        try {
          const all = page.locator(':text-is("設定")');
          const n = await all.count();
          let best = -1, bx = -1;
          for (let i = 0; i < n; i++) {
            const b = await all.nth(i).boundingBox().catch(() => null);
            if (b && b.x > bx) { bx = b.x; best = i; }
          }
          if (best >= 0) {
            await all.nth(best).click(); await page.waitForTimeout(3000);
            const it = page.locator(':text-is("チケット残高")').first();
            if (await it.count()) { await it.click(); await page.waitForTimeout(2000); }
            await page.keyboard.press('Escape'); await page.waitForTimeout(2500);
          }
          // lọc đúng khách (search khớp cả 789 khi tìm "78" → phải so khớp TUYỆT ĐỐI theo ô 顧客ID)
          const s = page.locator('input[type=text]').first();
          await s.fill(String(custPro)); await s.press('Enter'); await page.waitForTimeout(5000);

          const heads = await page.locator('thead th, thead td').allInnerTexts();
          const colIdx = heads.findIndex((h) => h.includes('チケット残高'));
          const rows = page.locator('tr');
          const rn = await rows.count();
          let target = null;
          for (let i = 0; i < rn; i++) {
            const id = (await rows.nth(i).locator('td').nth(1).innerText().catch(() => '')).trim();
            if (id === String(custPro)) { target = rows.nth(i); break; }
          }
          const vp = page.viewportSize() || { width: 1440, height: 900 };
          const full = await page.evaluate(() => [document.body.scrollWidth, document.body.scrollHeight]);
          const toFrac = (b) => [b.x / full[0], b.y / full[1], b.width / full[0], b.height / full[1]];
          if (target && colIdx >= 0) {
            const cell = target.locator('td').nth(colIdx);
            await cell.scrollIntoViewIfNeeded().catch(() => {});
            await page.waitForTimeout(800);
            val = (await cell.innerText().catch(() => '?')).trim();
            const cb = await cell.boundingBox();
            const hb = await page.locator('thead').locator(':text-is("チケット残高")').first().boundingBox().catch(() => null);
            if (cb) boxes.push(toFrac(cb));
            if (hb) boxes.push(toFrac(hb));
          }
          await L.shot(page, f, null, { screenshot: { fullPage: true } });
        } catch (e) {
          await L.shot(page, f, null, { screenshot: { fullPage: true } }).catch(() => {});
        }
        shots['BUG-2'] = {
          ui: [f], boxes,
          why: `Đã bật cột 「チケット残高」(tổng buổi còn lại) trong danh sách khách. Khoanh đỏ = ô của khách `
             + `${custPro}: hệ thống ghi **${val}** buổi, trong khi khách thật sự chỉ dùng được 4 buổi `
             + `(xem danh sách vé ở 3_CHUCNANG case B2). Con số này bị cộng thêm cả vé cũ đã khoá.`,
        };
      }

      // mở khách có vé migrate (danh sách phân trang → helper tự lọc bằng ô 検索)
      httpErrors.length = 0;
      const found = await L.openCustomerTicketTab(page, custPro, (D.rails || {}).rails_sample_cust_name);
      if (found) {
        const f1 = `${OUT}/bug_BUG-1_ui.png`;
        await L.shot(page, f1, null, { screenshot: { fullPage: true } });
        const errs = httpErrors.filter((e) => /refund|ticket_pack/.test(e));

        // Khoanh vùng CHÍNH XÁC bằng toạ độ element (không đoán): nút 返金 + dòng vé migrate
        const full1 = await page.evaluate(() => [document.body.scrollWidth, document.body.scrollHeight]);
        const frac = (b) => [b.x / full1[0], b.y / full1[1], b.width / full1[0], b.height / full1[1]];
        const boxes1 = [];
        let btnState = 'không thấy nút 返金';
        const btn = page.locator('button:has-text("返金"), :text("返金")').first();
        if (await btn.count()) {
          const bb = await btn.boundingBox().catch(() => null);
          if (bb) boxes1.push(frac(bb));
          const dis = await btn.getAttribute('disabled').catch(() => null);
          const cls = (await btn.getAttribute('class').catch(() => '')) || '';
          btnState = (dis !== null || /disabled/.test(cls)) ? 'BỊ VÔ HIỆU (xám, không bấm được)' : 'bấm được';
        }
        const packRow = page.locator(':text("プレミアムチケット")').last();
        if (await packRow.count()) {
          const pb = await packRow.boundingBox().catch(() => null);
          if (pb) boxes1.push(frac(pb));
        }
        let f2 = null;
        if (await btn.count()) {
          await btn.click().catch(() => {});
          await page.waitForTimeout(2500);
          f2 = `${OUT}/bug_BUG-1_ui_2.png`;
          await L.shot(page, f2, null, { screenshot: { fullPage: true } });
        }
        if (need('BUG-1')) {
          shots['BUG-1'] = {
            ui: [f1].concat(f2 ? [f2] : []), boxes: boxes1,
            why: `Màn チケット情報 của khách ${custPro}. Khoanh đỏ = nút 返金 (hoàn tiền) và dòng vé vừa `
               + `đồng bộ. Quan sát: nút 返金 ${btnState}; lỗi HTTP khi mở màn: `
               + `${errs.length ? errs.join(' | ') : 'KHÔNG có'}. Nghĩa là nhân viên CHƯA gặp lỗi trên màn `
               + `này — lỗi nằm bên trong, chỉ bung ra khi vé đã dùng ít nhất 1 buổi rồi mới bấm hoàn tiền.`,
          };
        }
        if (need('BUG-2') && shots['BUG-2']) shots['BUG-2'].ui.push(f1);
      } else if (need('BUG-1')) {
        shots['BUG-1'] = { ui: [], why: `không thấy khách code ${custPro} trong danh sách 顧客管理` };
      }
    } catch (e) {
      for (const id of ['BUG-1', 'BUG-2']) if (need(id) && !shots[id]) shots[id] = { ui: [], why: `lỗi khi drive UI Pro: ${e.message.slice(0, 90)}` };
    }
    await browser.close();
  }

  // ---------- Ticket app: BUG-5 / BUG-6 (khách mất vé bên kia) ----------
  if (need('BUG-5') || need('BUG-6')) {
    const custDj = (D.django || {}).dj_sample_customer_id;
    if (custDj) {
      const { browser, page, BASE } = await L.getPage('ticket', cfg);
      try {
        const f = `${OUT}/bug_${need('BUG-5') ? 'BUG-5' : 'BUG-6'}_ui.png`;
        await page.goto(`${BASE}/ticket-ops/view/customer/${custDj}/`, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2500);
        await L.shot(page, f, null, { screenshot: { fullPage: true } });
        for (const id of ['BUG-5', 'BUG-6']) if (need(id)) shots[id] = { ui: [f], why: `Màn vé của khách ${custDj} bên Ticket app — vé đáng ra phải có mà KHÔNG thấy.` };
      } catch (e) {
        for (const id of ['BUG-5', 'BUG-6']) if (need(id)) shots[id] = { ui: [], why: `lỗi drive UI Ticket: ${e.message.slice(0, 90)}` };
      }
      await browser.close();
    }
  }

  // ---------- ghi lại vào bugs.json + đưa ảnh bug vào captures.json để annotate.py VẼ KHUNG ----------
  for (const b of bugs) {
    const s = shots[b.id];
    b.ui_capture = s && s.ui.filter(Boolean).length ? s.ui.filter(Boolean) : null;
    b.ui_note = s ? s.why : 'không quan sát được trên UI (bug ở tầng dữ liệu/đồng bộ, không có màn nào hiển thị)';
    b.ui_boxes = (s && s.boxes) || [];
    if (b.ui_capture) {
      b.ui_capture.forEach((f, i) => {
        L.addCapture(folder, 'after', {
          sheet: '4_BUGS', screen: `bug_${b.id}_ui${i ? '_' + (i + 1) : ''}`, phase: 'after', file: f,
          boxes: i === 0 ? b.ui_boxes : [],
          note: `${b.id} — ${b.title || ''}`,
          diff_note: b.ui_note,
        });
      });
    }
  }
  fs.writeFileSync(bugsP, JSON.stringify(data, null, 2));
  const withUi = bugs.filter((b) => b.ui_capture).length;
  console.log(`DONE capture_bugs: ${withUi}/${bugs.length} bug có ảnh UI`);
  for (const b of bugs) console.log(`  ${b.id}: ${b.ui_capture ? b.ui_capture.map((f) => path.basename(f)).join(', ') : 'KHÔNG có ảnh UI — ' + b.ui_note}`);
})();
