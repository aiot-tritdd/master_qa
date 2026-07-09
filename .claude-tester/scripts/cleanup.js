// Dọn dữ liệu test tạo trên dev theo QUY ƯỚC ĐẶT TÊN.
//   node cleanup.js            -> DRY-RUN: chỉ liệt kê thứ khớp prefix (không xóa)
//   node cleanup.js --apply    -> XÓA preset khớp prefix + xóa reservation theo RESV_IDS
// Env: PRESET_PREFIX=AIOT-TEST | STAFF_PREFIX=AIOTTEST | BRANCH_ID=4 | RESV_IDS=734,737
// Lưu ý: staff KHÔNG có API xóa (chỉ deactivate) -> chỉ liệt kê để user xử lý tay.
const { withApi } = require('./pw_api');

const E = process.env;
const PRESET_PREFIX = E.PRESET_PREFIX || 'AIOT-TEST';
const STAFF_PREFIX = E.STAFF_PREFIX || 'AIOTTEST';
const BRANCH = E.BRANCH_ID || '4';
const RESV_IDS = (E.RESV_IDS || '').split(',').map(s => s.trim()).filter(Boolean);
const APPLY = process.argv.includes('--apply');

withApi(async ({ api }) => {
  console.log(`Mode: ${APPLY ? 'APPLY (xóa thật)' : 'DRY-RUN (chỉ liệt kê)'}\n`);

  // 1) Presets khớp prefix
  const pr = await api('GET', '/permissions/presets');
  const presets = (pr.body.presets || []).filter(p => (p.name || '').startsWith(PRESET_PREFIX));
  console.log(`[Preset] khớp "${PRESET_PREFIX}*": ${presets.length}`);
  for (const p of presets) {
    if (APPLY) {
      const d = await api('DELETE', `/permissions/presets/${p.id}`);
      console.log(`  - ${p.name} (id=${p.id}) -> DELETE ${d.status}`);
    } else {
      console.log(`  - ${p.name} (id=${p.id})`);
    }
  }

  // 2) Staff khớp prefix (chỉ liệt kê — không có API xóa)
  const st = await api('GET', `/branches/${BRANCH}/staff?page=1&per=100`);
  const staff = (st.body.staff || st.body.data || []).filter(s => (s.staff_code || '').startsWith(STAFF_PREFIX));
  console.log(`\n[Staff] khớp "${STAFF_PREFIX}*": ${staff.length} (không có API xóa -> deactivate/xóa tay)`);
  for (const s of staff) console.log(`  - ${s.staff_code} / ${s.name} (id=${s.id})`);

  // 3) Reservation theo id chỉ định
  if (RESV_IDS.length) {
    console.log(`\n[Reservation] ids=${RESV_IDS.join(',')}`);
    for (const id of RESV_IDS) {
      if (APPLY) {
        const d = await api('DELETE', `/branches/${BRANCH}/reservations/${id}`);
        console.log(`  - id=${id} -> DELETE ${d.status}`);
      } else {
        console.log(`  - id=${id} (sẽ xóa khi --apply)`);
      }
    }
  }
  console.log('\nXong.' + (APPLY ? '' : ' (chạy lại kèm --apply để thực thi)'));
}).catch(e => { console.error('FAILED:', e.message); process.exit(1); });
