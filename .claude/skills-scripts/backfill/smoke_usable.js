// smoke_usable.js <folder> — CỬA CHẶN SỚM sau migrate: "vé mới có XÀI ĐƯỢC không", không phải
// "dữ liệu có đúng không". Chạy NGAY sau migrate.js, TRƯỚC mọi bước chụp report/case.
//
// VÌ SAO CÓ FILE NÀY (branch 66 gerbill, 2026-07-29): 4 bất biến dữ liệu (đếm vé, tổng tiền, tổng
// buổi, đồng bộ 2 hệ) đều XANH sau migrate, mà thao tác TAY của 1 nhân viên phát hiện: vé mới KHÔNG
// CHỌN ĐƯỢC PRODUCT nào để dùng — vé thành đồ trang trí. Gốc rễ CONFIRM bằng code + dữ liệu 2 branch
// (124: 169/176 = 96% dính; 179: 90/90 = 100% dính):
//   sync_controller.rb#handle_pack_issued (chiều sot=ticket_app, dòng 236-249) tạo Tickets::Pack khi
//   nhận vé từ Ticket App, set product_option nhưng KHÔNG set products:/items: — khác migrate! (chiều
//   sot=pro, dòng 48-49) có copy 2 field này. Vé product_option='custom' + item_ids rỗng ⇒ theo đúng
//   logic frontend (ReservationSelectedItemCard.vue:222) KHÔNG BAO GIỜ chọn được product.
//
// KỸ THUẬT ĐO — không đoán, không gọi thẳng Rails console:
//   Chặn response API thật `GET .../customers/:id/ticket_packs` (action Vuex
//   `ticket/fetchCustomerTicketPacks`) — ĐÚNG endpoint mà màn đặt lịch (ReservationCustomerWidget.vue
//   dòng 483/511/527) VÀ màn チケット情報 (đã dùng ở capture_bugs.js) cùng gọi, xác nhận bằng đọc code
//   (2 file cùng dispatch 1 action). Lấy JSON THẬT trả về, áp ĐÚNG logic filter thật của frontend
//   (product_option==='all' ? true : item_ids.includes(item_id)) — không suy diễn, không hỏi Rails.
//   Mở màn qua L.openCustomerTicketTab (đã có, không cần tự dò lại UI mỗi lần).
//
// AN TOÀN: CHỈ ĐỌC — mở màn, đọc response, không bấm nút ghi nào.
const L = require('./lib_backfill.js');
const fs = require('fs');
const path = require('path');

// Logic ĐÚNG BẢN GỐC threease_pro/components/features/reservations/reservation_form/Widget/
// ReservationSelectedItemCard.vue (computed customerAvailableTickets) — copy y hệt, KHÔNG diễn giải lại.
function usableForAnyProduct(pack) {
  if (pack.redeemable_count <= 0) return { usable: null, why: 'hết buổi, không xét được' };
  if (pack.product_option === 'all') return { usable: true, why: "product_option='all' → luôn chọn được" };
  const ids = pack.item_ids || [];
  return {
    usable: ids.length > 0,
    why: ids.length > 0
      ? `product_option='${pack.product_option}', item_ids=[${ids.length} món] → chọn được món trong danh sách`
      : `product_option='${pack.product_option}' NHƯNG item_ids RỖNG → KHÔNG chọn được món nào`,
  };
}

async function fetchTicketPacksViaUI(page, code, name) {
  const responses = [];
  const onResp = async (r) => {
    if (r.request().method() === 'GET' && /\/ticket_packs(\?|$)/.test(r.url())) {
      try { responses.push(await r.json()); } catch (e) { /* not json, ignore */ }
    }
  };
  page.on('response', onResp);
  const opened = await L.openCustomerTicketTab(page, code, name);
  await page.waitForTimeout(2500);
  page.off('response', onResp);
  if (!opened) return { opened: false, packs: [] };
  const last = responses[responses.length - 1];
  return { opened: true, packs: (last && last.ticket_packs) || [] };
}

(async () => {
  const folder = process.argv[2];
  const cfg = L.loadConfig(folder);
  const dataP = path.join(folder, 'data_after.json');
  if (!fs.existsSync(dataP)) {
    console.log('SKIP smoke_usable: chưa có data_after.json — chạy sau migrate.js + db.py after.');
    process.exit(0);
  }
  const D = JSON.parse(fs.readFileSync(dataP, 'utf8'));
  const custCode = D.rails && D.rails.rails_sample_cust_code;
  const custName = D.rails && D.rails.rails_sample_cust_name;
  if (!custCode) {
    console.log('SKIP smoke_usable: data_after.json không có rails_sample_cust_code.');
    process.exit(0);
  }

  const { browser, page } = await L.getPage('pro', cfg);
  const out = { branch_id: cfg.branch_id, sot: cfg.sot, checked_at: 'after-migrate', customer: custCode };
  let failCount = 0, checkedCount = 0;
  const details = [];

  try {
    await L.switchBranch(page, cfg.branch_name_jp);
    const { opened, packs } = await fetchTicketPacksViaUI(page, custCode, custName);
    out.opened_customer_screen = opened;
    if (!opened) {
      console.log(`smoke_usable: KHÔNG mở được màn khách ${custCode} — không đo được. Xem log Playwright.`);
      out.error = 'khong_mo_duoc_man_khach';
    } else {
      // vé MỚI = sinh ra từ migrate/sync: from_threease_ticket=true (webhook, sot=ticket_app)
      // HOẶC vé có id nằm trong dải mới sinh sau migrate (sot=pro, capture qua original_pack ở BE
      // nhưng API không trả original_pack_id trực tiếp — dùng from_threease_ticket + price=0 làm dấu
      // hiệu chung cho "vé không phải mua trực tiếp tại quầy", đúng cho cả 2 chiều).
      const newPacks = packs.filter((p) => p.from_threease_ticket || Number(p.price) === 0);
      out.new_packs_seen = newPacks.length;
      for (const p of newPacks) {
        const r = usableForAnyProduct(p);
        checkedCount++;
        details.push({ pack_id: p.id, product_option: p.product_option, item_ids_count: (p.item_ids || []).length, redeemable_count: p.redeemable_count, ...r });
        if (r.usable === false) failCount++;
      }
    }
  } catch (e) {
    out.error = `lỗi khi đo: ${e.message.slice(0, 200)}`;
  }

  out.checked = checkedCount;
  out.fail = failCount;
  out.details = details;
  fs.writeFileSync(path.join(folder, 'smoke_usable.json'), JSON.stringify(out, null, 2));

  console.log(`SMOKE USABLE — branch ${cfg.branch_id} (sot=${cfg.sot}), khách ${custCode}:`);
  console.log(`  vé mới quan sát được: ${checkedCount} | KHÔNG chọn được product: ${failCount}`);
  for (const d of details) console.log(`  pack ${d.pack_id}: ${d.why}`);

  await browser.close();

  if (out.error) { console.log(`DỪNG: ${out.error}`); process.exit(2); }
  if (checkedCount === 0) {
    console.log('smoke_usable: 0 vé mới quan sát được ở khách mẫu — KHÔNG kết luận được PASS hay FAIL. '
      + 'Không tự tin báo "ổn"; cần chọn khách mẫu khác có vé mới.');
    process.exit(3);
  }
  if (failCount > 0) {
    console.log(`❌ FAIL: ${failCount}/${checkedCount} vé mới KHÔNG chọn được product nào để dùng. `
      + 'DỪNG PIPELINE — báo user ngay, đây là bug xài-được, không phải bug dữ liệu.');
    process.exit(1);
  }
  console.log(`✅ PASS: ${checkedCount}/${checkedCount} vé mới chọn được product bình thường.`);
})().catch((e) => { console.error('LỖI smoke_usable:', e.message); process.exit(1); });
