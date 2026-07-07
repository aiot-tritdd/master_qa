---
id: observation-channels
status: approved
kind: channels
spans_repos: [pro, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: 2026-07-07
---
# Kênh quan sát black-box (WHAT observe → WHERE)

> QA quan sát kết quả bằng **UI đang chạy**, KHÔNG đọc DB/code.
> ✅ UI-confirmed 2026-07-07 (đã click thật từng kênh).

| Quan sát | Kênh (UI) | getPage() | Login |
|---|---|---|---|
| Booking / hóa đơn / số dư vé (Pro) | https://develop.pro.threease.com | `getPage('pro')` | TESTSEED001 / STAFF001 / password123 (basic: threesides/threesides) |
| **Gói vé + 使用履歴 + trạng thái pack** (per khách) | https://ticket-dev.threease.com/**customer/<id>/** | `getPage('ticket')` | TESTSEED001 / STAFF001 / password123 |
| Model **sync** (customer/institute/branch/staff) | https://ticket-dev.threease.com/admin | `getPage('ticket_admin')` | admin / password123 |

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
