// cleanup.js — dọn dữ liệu test tạo trên dev DÙNG CHUNG, theo QUY ƯỚC ĐẶT TÊN. CƠ KHÍ, không reasoning.
//
//   node cleanup.js            -> DRY-RUN: chỉ liệt kê thứ khớp prefix (KHÔNG xóa)
//   node cleanup.js --apply    -> XÓA preset khớp prefix + xóa reservation theo RESV_IDS
//
// Env: PRESET_PREFIX=AIOT-TEST | STAFF_PREFIX=AIOTTEST | BRANCH_ID=<số> | RESV_IDS=734,737
//
// ⚠️ BRANCH_ID đổi theo phiên/data — KHÔNG có giá trị mặc định đúng vĩnh viễn.
//    (đã ghi nhận: TESTSEED001 map branch 4 -> 2 -> 3 qua các ngày). Luôn set tường minh.
// ⚠️ Staff KHÔNG có API xóa -> chỉ liệt kê, user deactivate/xóa tay.
// ⚠️ Booking đã thanh toán: PUT /transactions/{id} status=cancelled TRƯỚC, rồi mới DELETE.
//    Booking phát hành gói vé còn vé đã dùng -> 422「使用済みチケット」-> xóa 2 vòng
//    (vòng 1: booking TIÊU THỤ vé để nhả vé; vòng 2: booking PHÁT HÀNH).
const { withApi } = require('./pw_api');

const E = process.env;
const PRESET_PREFIX = E.PRESET_PREFIX || 'AIOT-TEST';
const STAFF_PREFIX = E.STAFF_PREFIX || 'AIOTTEST';
const BRANCH = E.BRANCH_ID;
const RESV_IDS = (E.RESV_IDS || '').split(',').map((s) => s.trim()).filter(Boolean);
const APPLY = process.argv.includes('--apply');

withApi(async ({ api }) => {
  console.log(`Mode: ${APPLY ? 'APPLY (XÓA THẬT)' : 'DRY-RUN (chỉ liệt kê)'}\n`);

  // 1) Preset khớp prefix (không phụ thuộc branch)
  const pr = await api.get('/permissions/presets');
  const presets = ((pr.body && pr.body.presets) || []).filter((p) => (p.name || '').startsWith(PRESET_PREFIX));
  console.log(`[Preset] khớp "${PRESET_PREFIX}*": ${presets.length}`);
  for (const p of presets) {
    if (APPLY) {
      const d = await api.del(`/permissions/presets/${p.id}`);
      console.log(`  - ${p.name} (id=${p.id}) -> DELETE ${d.status}`);
    } else {
      console.log(`  - ${p.name} (id=${p.id})`);
    }
  }

  if (!BRANCH) {
    console.log(`\n⚠️  BRANCH_ID chưa set -> bỏ qua Staff + Reservation (2 mục này cần branch của PHIÊN HIỆN TẠI).`);
    console.log(`    Xác nhận branch của phiên rồi chạy lại: BRANCH_ID=<n> node cleanup.js`);
    console.log('\nXong.' + (APPLY ? '' : ' (chạy lại kèm --apply để thực thi)'));
    return;
  }

  // 2) Staff khớp prefix — CHỈ LIỆT KÊ (không có API xóa)
  const st = await api.get(`/branches/${BRANCH}/staff?page=1&per=100`);
  const staff = ((st.body && (st.body.staff || st.body.data)) || [])
    .filter((s) => (s.staff_code || '').startsWith(STAFF_PREFIX));
  console.log(`\n[Staff] khớp "${STAFF_PREFIX}*" (branch=${BRANCH}): ${staff.length} — KHÔNG có API xóa, deactivate/xóa tay`);
  for (const s of staff) console.log(`  - ${s.staff_code} / ${s.name} (id=${s.id})`);

  // 3) Reservation theo id chỉ định
  if (RESV_IDS.length) {
    console.log(`\n[Reservation] branch=${BRANCH} ids=${RESV_IDS.join(',')}`);
    for (const id of RESV_IDS) {
      if (!APPLY) { console.log(`  - id=${id} (sẽ xóa khi --apply)`); continue; }
      let d = await api.del(`/branches/${BRANCH}/reservations/${id}`);
      if (d.status === 422 || d.status === 409) {
        // booking đã TT / còn vé -> hủy giao dịch trước rồi thử lại 1 lần
        console.log(`  - id=${id} -> DELETE ${d.status}; thử hủy giao dịch trước…`);
        const detail = await api.get(`/branches/${BRANCH}/reservations/${id}`);
        const txs = (detail.body && (detail.body.transactions || (detail.body.reservation || {}).transactions)) || [];
        for (const t of txs) {
          const c = await api.put(`/branches/${BRANCH}/transactions/${t.id}`, { transaction: { status: 'cancelled' } });
          console.log(`      cancel tx ${t.id} -> ${c.status}`);
        }
        d = await api.del(`/branches/${BRANCH}/reservations/${id}`);
      }
      console.log(`  - id=${id} -> DELETE ${d.status}${d.status === 422 ? ' (còn vé đã dùng? xóa booking TIÊU THỤ trước — xem vòng 2)' : ''}`);
    }
  }

  console.log('\nCòn tồn (không có API xóa, xử lý tay): ticket master AIOT-TEST-TK* · khách hàng AIOTTEST-KH* · vé đã quét trên Hệ thống Vé.');
  console.log('Xong.' + (APPLY ? '' : ' (chạy lại kèm --apply để thực thi)'));
}).catch((e) => { console.error('FAILED:', e.message); process.exit(1); });
