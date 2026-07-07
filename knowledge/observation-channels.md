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

| Quan sát | Kênh (UI) | Login (từ account.txt) |
|---|---|---|
| Booking / hóa đơn / số dư vé (Pro) | https://develop.pro.threease.com | TESTSEED001 / STAFF001 / password123 (basic: threesides/threesides) |
| Gói vé, 使用履歴, trạng thái pack | https://ticket-dev.threease.com/admin | admin / password123 |
| Vé phía khách (ticket app) | https://ticket-dev.threease.com | TESTSEED001 / STAFF001 / password123 |

## Quy tắc sync Pro → ticket
Sau thao tác trên Pro, gói vé sync sang ticket **không tức thì**. Trước khi quan sát
ticket-admin: chờ ~5–8 giây rồi mới đọc. Không thấy → chờ thêm 1 nhịp rồi mới kết luận.
KHÔNG truy cập DB, KHÔNG đọc code để "chắc".

## Cách dùng trong script
`const { getPage } = require('<repo>/.claude/skills-scripts/testcase-evidence/pw_lib');`
`getPage('pro')` · `getPage('ticket_admin')` · `getPage('ticket')`.
