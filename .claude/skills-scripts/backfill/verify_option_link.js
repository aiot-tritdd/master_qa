// verify_option_link.js <folder> — BƯỚC 2 sau khi điền ticket_option_id cho pack migrate.
//
// Trả lời bằng QUAN SÁT UI (không suy từ code) đúng 1 câu đang nợ:
//   Lọc danh sách vé theo LOẠI VÉ (chip 「チケット」) có thấy pack migrate không?
//   Claim cũ (`traced-only`): `Tickets::Pack.with_ticket_options` (pack.rb:42) lọc qua
//   `joins(:reservation_ticket)`, mà pack migrate có reservation_ticket_id = nil CỐ Ý
//   (pack_migration_service.rb:56) ⇒ nghi là điền ticket_option_id KHÔNG đủ.
//
// So sánh 3 mốc, cùng 1 phiên, cùng 1 branch:
//   A. không lọc            → tổng bao nhiêu vé
//   B. lọc theo loại vé     → còn bao nhiêu
//   C. đếm trong DB         → con số đúng phải là bao nhiêu
// B == C ⇒ bộ lọc ĐÚNG. B == 0 (mà C > 0) ⇒ bộ lọc bỏ sót pack migrate.
//
// ⚠️ Trang tải CHẬM và render 2 nhịp: nhịp đầu 「店舗数 0 / データなし」, chip 「チケット」
//    CHƯA có. Chụp lúc đó là ảnh RỖNG → tưởng "không thấy pack" (đo 2026-07-29, suýt kết
//    luận sai). Phải đợi tới khi tổng số vé > 0 rồi mới thao tác.
//
// CHỈ ĐỌC: mở màn, lọc, chụp. Không bấm nút ghi nào.
const L = require('./lib_backfill.js');
const fs = require('fs');
const path = require('path');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const folder = process.argv[2];
  const OPT_NAME = process.argv[3] || 'プレミアムチケット1万円';
  const cfg = L.loadConfig(folder);
  const OUT = path.join(folder, 'verify_option');
  fs.mkdirSync(OUT, { recursive: true });

  const { browser, page, BASE } = await L.getPage('pro', cfg);
  const out = { opt_name: OPT_NAME, steps: {} };

  // đọc tổng "N チケット" ở chân bảng
  // Chân bảng ghi "1 ~ 10 / 24112 チケット". Lấy số LỚN NHẤT khớp mẫu — vì chuỗi
  // "1 ~ 10 / N" cũng khớp và có thể trả nhầm số nhỏ; lúc đang tải thì là "0 チケット".
  let lastRaw = '';
  const readTotal = async () => {
    const t = await page.locator('body').innerText().catch(() => '');
    const all = [...t.matchAll(/([0-9,]+)\s*チケット/g)].map((m) => parseInt(m[1].replace(/,/g, ''), 10));
    lastRaw = (t.match(/[^\n]*チケット[^\n]*/) || [''])[0].slice(0, 80);
    return all.length ? Math.max(...all) : null;
  };

  try {
    // storageState có thể đã ở sẵn đúng branch. switchBranch bị flaky (panel chọn branch
    // render chậm → báo nhầm "staff không có quyền"), nên CHỈ switch khi header chưa đúng.
    await page.goto(BASE + '/tickets/packs', { waitUntil: 'domcontentloaded', timeout: 120000 });
    await sleep(6000);
    const header = await page.locator('body').innerText().catch(() => '');
    out.steps.branch_dung_san = header.includes(cfg.branch_name_jp.replace(/\s+/g, ''))
      || header.includes(cfg.branch_name_jp);
    if (!out.steps.branch_dung_san) {
      await L.switchBranch(page, cfg.branch_name_jp);
      await page.goto(BASE + '/tickets/packs', { waitUntil: 'domcontentloaded', timeout: 120000 });
    }

    // đợi bảng THỰC SỰ có dữ liệu (không tin timeout cứng)
    let total = null;
    for (let i = 0; i < 40; i++) {
      await sleep(1500);
      total = await readTotal();
      if (total && total > 0) break;
    }
    out.steps.A_khong_loc = total;
    await L.shot(page, `${OUT}/A_khong_loc.png`, null, { screenshot: { fullPage: true } });

    // mở chip 「チケット」 (loại vé) và chọn OPT_NAME
    const chip = page.locator('button:has-text("チケット"), [class*=chip]:has-text("チケット")').first();
    out.steps.chip_thay = await chip.count();
    if (await chip.count()) {
      await chip.click();
      await sleep(2500);
      await L.shot(page, `${OUT}/B1_menu_loai_ve.png`, null, { screenshot: { fullPage: true } });

      // Menu lọc = ô 検索 riêng + danh sách checkbox + nút 適用.
      // ⚠️ KHÔNG dùng `text=<tên>` trần: nó khớp luôn ô <td> trong BẢNG phía sau (tên vé cũng
      //    nằm trong bảng) → click vào bảng, menu không đổi gì. Phải scope trong menu.
      const menu = page.locator('div:has(> input), [role=menu], [class*=menu], [class*=dropdown]')
        .filter({ has: page.locator('text=適用') }).last();
      out.steps.menu_scope_thay = await menu.count();

      const box = menu.locator('input[type=text], input:not([type=checkbox])').first();
      if (await box.count()) { await box.fill(OPT_NAME); await sleep(2500); }
      await L.shot(page, `${OUT}/B1b_sau_khi_go_tim.png`, null, { screenshot: { fullPage: true } });

      // Bảng 発行済みチケット一覧 KHÔNG có cột checkbox nào → mọi checkbox đang hiện trên
      // trang đều thuộc menu lọc. Dùng thẳng, khỏi đoán selector container (đã thử scope
      // theo div/[role=menu] → bắt hụt, chỉ thấy 1 ô rồi tick nhầm 「すべて」 = chọn cả 194
      // loại = không lọc gì, tổng vẫn 24112).
      // Checkbox ở đây là loại tuỳ biến (input thật bị ẩn) → `input[type=checkbox]:visible`
      // chỉ thấy 1 ô và tick nhầm 「すべて」 (= chọn cả 194 loại = không lọc gì).
      // Cách ăn chắc: click vào NHÃN CHỮ của mục, khớp CHÍNH XÁC.
      // Menu hiện tên master 「・プレミアムチケット」, còn ô <td> trong bảng là
      // 「・プレミアムチケット1万円」 → exact match tự loại bảng ra, không cần scope container.
      const labels = page.getByText('・プレミアムチケット', { exact: true });
      let n = await labels.count();
      out.steps.nhan_khop_chinh_xac = n;
      if (!n) {   // dự phòng: lấy mục thứ 2 trong menu (bỏ 「すべて」)
        const alt = page.locator('label, [class*=item]').filter({ hasText: 'プレミアム' });
        n = await alt.count(); out.steps.fallback_nhan = n;
        if (n) await alt.first().click({ force: true }).catch(() => {});
      } else {
        await labels.first().click({ force: true }).catch(() => {});
      }
      {
        await sleep(1000);
        await L.shot(page, `${OUT}/B1c_da_tick.png`, null, { screenshot: { fullPage: true } });
        const apply = page.locator('text=適用').first();
        out.steps.co_nut_ap_dung = await apply.count();
        if (await apply.count()) {
          await apply.click();
          for (let i = 0; i < 25; i++) { await sleep(1500); if ((await readTotal()) !== total) break; }
        }
        out.steps.B_co_loc = await readTotal();
        await L.shot(page, `${OUT}/B2_da_loc.png`, null, { screenshot: { fullPage: true } });
      }
    }
  } catch (e) {
    out.error = e.message.slice(0, 200);
  }

  fs.writeFileSync(path.join(OUT, 'result.json'), JSON.stringify(out, null, 2));
  console.log(JSON.stringify(out, null, 2));
  await browser.close();
})().catch((e) => { console.error('LỖI:', e.message); process.exit(1); });
