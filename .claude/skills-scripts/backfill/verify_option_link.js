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
  const readTotal = async () => {
    const t = await page.locator('body').innerText().catch(() => '');
    const m = t.match(/([0-9,]+)\s*チケット/);
    return m ? parseInt(m[1].replace(/,/g, ''), 10) : null;
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

      const item = page.locator(`text=${OPT_NAME}`).first();
      out.steps.tim_thay_loai_ve = await item.count();
      if (await item.count()) {
        await item.click();
        await sleep(1500);
        // đóng menu để bảng load lại
        await page.keyboard.press('Escape').catch(() => {});
        for (let i = 0; i < 20; i++) { await sleep(1500); if ((await readTotal()) !== total) break; }
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
