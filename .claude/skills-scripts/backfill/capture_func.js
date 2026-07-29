// capture_func.js <folder> <before|after> — chụp ảnh UI cho TỪNG case trong FUNC_CASES.json
// (sheet 3_CHUCNANG). Mục tiêu: sau migrate, MỌI flow đụng vé đều có ảnh trước/sau chứng minh
// "vẫn chạy bình thường" — không chỉ 1 ảnh customer như bản v1.
//
// AN TOÀN (DB dev dùng chung):
//   - Script này CHỈ MỞ MÀN + CHỤP. TUYỆT ĐỐI không bấm nút thực thi (hủy/hoàn/chuyển/dùng buổi).
//   - Phần "chạy logic thật" do confirm_bugs.py làm, trên data test tự tạo, có revert.
//   - Ngoại lệ đọc-only: mở tab チケット情報 bên Pro tự gọi API refundability → nếu 500 thì đó
//     chính là BUG-1 lộ ra mà KHÔNG cần bấm 返金 (ghi vào note + http_errors).
//
// Case B1/B7/B8 trùng ảnh với sheet 2_REPORT → ghi entry ref_screen, không chụp lại.
const L = require('./lib_backfill.js');
const fs = require('fs');
const path = require('path');

const CASES = path.join(__dirname, '..', '..', 'skills', 'backfill', 'FUNC_CASES.json');

(async () => {
  const folder = process.argv[2];
  const phase = process.argv[3] || 'before';
  const cfg = L.loadConfig(folder);
  const OUT = path.join(folder, phase);
  const NAME = cfg.branch_name_jp;
  fs.mkdirSync(OUT, { recursive: true });

  const cases = JSON.parse(fs.readFileSync(CASES, 'utf8')).cases;
  const byId = Object.fromEntries(cases.map((c) => [c.id, c]));
  const dataP = path.join(folder, `data_${phase}.json`);
  const D = fs.existsSync(dataP) ? JSON.parse(fs.readFileSync(dataP, 'utf8')) : { rails: {}, django: {} };
  const dj = D.django || {};
  const rl = D.rails || {};
  const custDj = dj.dj_sample_customer_id;
  const packDj = dj.dj_sample_pack_id;
  const tkId = dj.dj_sample_ticket_id;
  const custPro = rl.rails_sample_cust_code;

  const ok = []; const skip = [];

  const add = (c, file, extra) => L.addCapture(folder, phase, Object.assign({
    sheet: '3_CHUCNANG', screen: `func_${c.id}`, case_id: c.id, url: c.route, phase, file,
    note: `${c.id} ${c.name_vi} (${c.name_jp}) — kỳ vọng: ${c.expect}`, boxes: [],
  }, extra || {}));

  const miss = (c, why) => { skip.push(`${c.id}: ${why}`); add(c, null, { note: `${c.id} ${c.name_vi} — KHÔNG chụp được: ${why}` }); };

  // ============ TICKET app (Django) — nhóm A ============
  {
    const { browser, page, BASE } = await L.getPage('ticket', cfg);
    // suffix: khi 1 case có nhiều màn (vd A10 = list + detail + calc) → screen key phải KHÁC nhau,
    // nếu không addCapture dedupe theo screen sẽ ghi đè mất ảnh trước.
    const go = async (c, url, suffix) => {
      const screen = `func_${c.id}${suffix ? '_' + suffix : ''}`;
      const file = `${OUT}/${screen}_${phase}.png`;
      const resp = await page.goto(BASE + url, { waitUntil: 'domcontentloaded' }).catch(() => null);
      await page.waitForTimeout(1600);
      const code = resp ? resp.status() : 0;
      await L.shot(page, file, null, { screenshot: { fullPage: true } });
      add(c, file, { screen, http: code, note: `${c.id} ${c.name_vi} (${c.name_jp}) — ${BASE}${url} → HTTP ${code}. Kỳ vọng: ${c.expect}` });
      if (code >= 400) skip.push(`${c.id} HTTP ${code}`); else ok.push(c.id);
    };

    await go(byId.A1, '/ticketpack/');
    if (packDj) {
      await go(byId.A2, `/ticketpack/${packDj}/`);
      await go(byId.A6, `/ticketpack/${packDj}/cancel/`);   // CHỈ mở màn xác nhận, KHÔNG submit
      await go(byId.A7, `/ticketpack/${packDj}/refund/`);   // CHỈ mở form, KHÔNG submit
      await go(byId.A8, `/ticketpack/${packDj}/transfer/`); // CHỈ mở form, KHÔNG submit
    } else {
      for (const id of ['A2', 'A6', 'A7', 'A8']) miss(byId[id], 'chưa có dj_sample_pack_id trong data_' + phase + '.json');
    }
    if (custDj) {
      await go(byId.A3, `/ticket-ops/view/customer/${custDj}/`);
      await go(byId.A4, `/ticket-ops/use/customer/${custDj}/`);   // mở form dùng buổi, KHÔNG submit
      await go(byId.A5, `/ticket-ops/issue/customer/${custDj}/`); // mở form phát hành, KHÔNG submit
    } else {
      for (const id of ['A3', 'A4', 'A5']) miss(byId[id], 'chưa có dj_sample_customer_id');
    }
    await go(byId.A9, '/customer/link/');
    await go(byId.A10, '/ticket/');
    if (tkId) await go(byId.A10, `/ticket/${tkId}/`, 'detail');
    await go(byId.A10, '/ticket/calc/', 'calc');
    await browser.close();
  }

  // ============ PRO (Rails/Nuxt) — nhóm B ============
  {
    const { browser, page, BASE } = await L.getPage('pro', cfg);
    const httpErrors = [];
    page.on('response', (r) => { if (r.status() >= 400) httpErrors.push(`${r.status()} ${r.url().split('?')[0]}`); });
    await L.switchBranch(page, NAME);

    // B1/B7/B8 dùng lại ảnh sheet 2_REPORT (cùng màn, khỏi chụp 2 lần)
    for (const [id, refScreen] of [['B1', 'pro_packs_total'], ['B7', 'pro_journal'], ['B8', 'pro_reservations']]) {
      const c = byId[id];
      L.addCapture(folder, phase, {
        sheet: '3_CHUCNANG', screen: `func_${id}`, case_id: id, url: c.route, phase, file: null,
        ref_screen: refScreen,
        note: `${id} ${c.name_vi} (${c.name_jp}) — ảnh xem ở 2_REPORT (${refScreen}). Kỳ vọng: ${c.expect}`,
        boxes: [],
      });
      ok.push(id);
    }

    // B2 + B5 + B6: màn khách — mở tab チケット情報 tự gọi refundability (đọc-only)
    if (custPro && custPro !== '0') {
      try {
        httpErrors.length = 0;
        await page.locator('text=顧客管理').first().click();
        await page.waitForTimeout(4500);
        const listFile = `${OUT}/func_B6_${phase}.png`;
        await L.shot(page, listFile, null, { screenshot: { fullPage: true } });
        add(byId.B6, listFile, {
          note: `B6 ${byId.B6.name_vi} — danh sách khách (cột tổng buổi còn lại). Đối chiếu với danh sách vé thật ở B2: lệch = BUG-2. Kỳ vọng: ${byId.B6.expect}`,
        });
        ok.push('B6');

        const found = await L.openCustomerTicketTab(page, custPro, rl.rails_sample_cust_name);
        if (!found) throw new Error(`không thấy khách code ${custPro} (${rl.rails_sample_cust_name || '?'}) dù đã lọc bằng ô 検索`);

        const cFile = `${OUT}/func_B2_${phase}.png`;
        await L.shot(page, cFile, null, { screenshot: { fullPage: true } });
        const errs = httpErrors.filter((e) => /refund|ticket_pack/.test(e));
        add(byId.B2, cFile, {
          note: `B2 ${byId.B2.name_vi} — khách ${custPro}, tab チケット情報. Kỳ vọng: ${byId.B2.expect}`,
          http_errors: errs,
        });
        ok.push('B2');
        // B5: CÙNG MÀN với B2 → trỏ ref_screen, KHÔNG ghi lại `file` giống B2.
        // Nếu 2 entry cùng trỏ 1 file thì annotate.py vẽ caption 2 lần lên cùng ảnh, caption sau ghi
        // đè caption trước ⇒ ảnh của B2 lại mang chú thích của B5 (đo 2026-07-28, sếp phát hiện).
        L.addCapture(folder, phase, {
          sheet: '3_CHUCNANG', screen: 'func_B5', case_id: 'B5', url: byId.B5.route, phase,
          file: null, ref_screen: 'func_B2', boxes: [],
          note: `B5 ${byId.B5.name_vi} — mở màn này tự gọi API refundability. Lỗi HTTP quan sát được: ${errs.length ? errs.join(' | ') : 'không có'}. KHÔNG bấm 返金 (vé khách thật). Kỳ vọng: ${byId.B5.expect}`,
          http_errors: errs,
        });
        ok.push('B5');
        await page.keyboard.press('Escape').catch(() => {});
      } catch (e) {
        for (const id of ['B2', 'B5']) miss(byId[id], e.message.slice(0, 80));
      }
    } else {
      for (const id of ['B2', 'B5', 'B6']) miss(byId[id], 'chưa có rails_sample_cust_code');
    }

    // B9 master 回数券設定
    try {
      const f = `${OUT}/func_B9_${phase}.png`;
      await page.goto(BASE + '/clinic_setting/tickets', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(5000);
      await L.shot(page, f, null, { screenshot: { fullPage: true } });
      add(byId.B9, f); ok.push('B9');
    } catch (e) { miss(byId.B9, e.message.slice(0, 80)); }

    await browser.close();
  }

  // ============ C1 — app KHÁCH tự xem vé ============
  {
    const c = byId.C1;
    try {
      process.env.BASE_URL = 'http://localhost:8082';
      const { browser, page } = await L.getPage('reservation', cfg);
      const f = `${OUT}/func_C1_${phase}.png`;
      const resp = await page.goto('http://localhost:8082/', { waitUntil: 'domcontentloaded' }).catch(() => null);
      await page.waitForTimeout(4000);
      await L.shot(page, f, null, { screenshot: { fullPage: true } });
      add(c, f, {
        http: resp ? resp.status() : 0,
        note: `C1 ${c.name_vi} — app khách (8082) mở được, NHƯNG chưa có cơ chế login khách bằng Playwright (pw_lib target reservation login=null) → KHÔNG chụp được màn vé của 1 khách cụ thể. Xác minh tầng API/serializer ở confirm_bugs.py, nhãn observed-API. ${c.note_limit}`,
      });
      skip.push('C1: chỉ chụp được trang ngoài, chưa login được khách');
      await browser.close();
    } catch (e) { miss(c, `app khách không mở được: ${e.message.slice(0, 60)}`); }
  }

  console.log(`DONE capture_func ${phase}: ${ok.length} case có ảnh` + (skip.length ? `\n  CHƯA/THIẾU: ${skip.join(' | ')}` : ''));
})();
