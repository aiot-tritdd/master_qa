---
id: observation-channels
status: approved
kind: channels
spans_repos: [pro, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: 2026-07-07
confidence: 🟢
verify_by: "Mở từng kênh quan sát bằng pw_lib.getPage(<target>). Không có source_symbols → stale_check bỏ qua, phải tự kiểm."
---
# Kênh quan sát black-box (WHAT observe → WHERE)

> QA quan sát kết quả bằng **UI đang chạy**, KHÔNG đọc DB/code.
> ✅ UI-confirmed 2026-07-07 (đã click thật từng kênh).

| Quan sát                                                      | Kênh (UI)                                                   | getPage()                   | Login                                                               |
| -------------------------------------------------------------- | ------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------- |
| Booking / hóa đơn / số dư vé (Pro)                       | https://develop.pro.threease.com                             | `getPage('pro')`          | TESTSEED001 / STAFF001 / password123 (basic: threesides/threesides) |
| **Gói vé + 使用履歴 + trạng thái pack** (per khách) | https://ticket-dev.threease.com/**customer/<id></id>** | `getPage('ticket')`       | TESTSEED001 / STAFF001 / password123                                |
| Model**sync** (customer/institute/branch/staff)          | https://ticket-dev.threease.com/admin                        | `getPage('ticket_admin')` | admin / password123                                                 |

⚠️ **Đã sửa (UI-confirm bắt được):** gói vé/使用履歴 nằm ở **ticket-app** (顧客 → `/customer/<id>/`:
cột 保有チケット, ステータス, 枚数 X/Y, bảng 最近の使用履歴), **KHÔNG** ở Django admin. Django admin chỉ
lộ model sync — dùng để quan sát đồng bộ customer/institute, không phải gói vé.

## Quy tắc sync Pro → ticket

Sau thao tác trên Pro, gói vé sync sang ticket **không tức thì**. Trước khi quan sát
ticket-admin: chờ ~5–8 giây rồi mới đọc. Không thấy → chờ thêm 1 nhịp rồi mới kết luận.
KHÔNG truy cập DB, KHÔNG đọc code để "chắc".

## Cách dùng trong script

`const { getPage } = require('<repo>/.claude/skills-scripts/testcase-evidence/pw_lib');`
`getPage('pro')` · `getPage('ticket_admin')` · `getPage('ticket')`.

---

## Kênh quan sát qua API (đã GỌI THẬT 2026-07-09 — không phải đọc code)

`withApi()` (`pw_api.js`) nghe lén devise-token từ request thật của app rồi tái dùng.
Trả `{status, body, ok}` — **`status` là bằng chứng quan sát được** (dùng cho case chống bypass).

| Quan sát | Gọi | Đã verify live |
|---|---|---|
| Danh sách preset quyền | `api.get('/permissions/presets')` | ✅ `200`, 7 preset (`本社`, `AIOT-TEST-105`, `マネージャー`…) |
| Booking theo khoảng ngày | `api.get('/branches/{b}/reservations?start_date=YYYYMMDD&end_date=…&session=all')` | ✅ `200` (branch 2/3/4); **branch sai → `404`** |
| Tài nguyên không tồn tại | vd `api.get('/permissions/presets/999999999')` | ✅ `404` |

```js
const { withApi } = require('<repo>/.claude/skills-scripts/testcase-evidence/pw_api');
await withApi(async ({ api }) => {
  const r = await api.get('/permissions/presets');
  console.log(r.status, r.body);            // status DÙNG ĐƯỢC làm evidence
});
```

⚠️ **Branch của phiên đổi theo phiên/data** (đã thấy 4 → 2 → 3). Sai branch → **`404`**, không phải `403`.
Đo 2026-07-09: phiên `TESTSEED001` = branch **3**.
→ Endpoint **chưa gọi thật** nằm ở `knowledge/system/api-endpoints.md` (build-time, QA cấm đọc).
   Gọi thật rồi thì **chuyển sang bảng này**.
