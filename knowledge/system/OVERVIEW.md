---
id: system-overview
status: draft
kind: system-map
spans_repos: [backend, ticket, pro, admin, reservation]
source: "GitNexus (5 repo index, ~473 flows) + /Users/tritdd/Work/ThreeSides/CLAUDE.md + UI-confirm (phiên 2026-07)"
note: "MÔ TẢ code/hệ thống đang LÀM GÌ — KHÔNG phải oracle. Oracle = SPEC từng feature."
source_hash: null
---
# System Business Map — ThreeSides (backbone để hiểu toàn hệ)

> Bản đồ **domain × flow × repo** của cả hệ. Mỗi domain sẽ có 1 file deep-dive `knowledge/system/<domain>.md`
> (dựng dần). File này là mục lục + wiring xuyên hệ. **draft** — grow/duyệt dần.

## Kiến trúc (nhắc — chi tiết ở /Users/tritdd/Work/ThreeSides/CLAUDE.md)
```
pro(Nuxt,8080) ─┐
admin(Nuxt,8081)├─HTTP▶ backend(Rails,3000, HUB) ─HTTP▶ ticket(Django,8000)
reservation ────┘        (mọi FE gọi hub)          (backend↔ticket đồng bộ 2 chiều HMAC)
(Nuxt,8082)
```
⚠️ Link là **HTTP**, không phải call-graph gộp. GitNexus **0 auto-link** cross-repo (§3) → wiring dưới lấy từ CLAUDE.md + UI-confirm.

## Danh mục DOMAIN (× repo × trạng thái hiểu biết)
| # | Domain | Repo chính | Trạng thái knowledge |
|---|---|---|---|
| 1 | **Customer/Master sync** (customer/institute/branch/staff) backend↔ticket | backend+ticket | 🟢 rõ (CLAUDE.md §8) — cần file deep-dive |
| 2 | **Ticket issue + sync** (Pro thanh toán → phát hành gói vé → sync ticket) | backend+pro+ticket | 🟡 một phần (UI-confirm phát hành ở draft `issue-ticket-pack`) |
| 3 | **Payment / Invoice + Cancel** (cancel payment/booking/delete, guard vé-đã-dùng) | pro+backend | 🟢 UI-confirmed phiên này (`pro-open-booking` approved) |
| 4 | **Coupon / SC** (CouponPack/Usage/Transaction, FIFO, reverse-sync Pro↔ticket) | ticket+backend+pro | 🟡 report UI rõ (`ticket-coupon-reports`); cơ chế SC cần deep-dive |
| 5 | **Reports** (ticket report + coupon report) | ticket | 🟢 route rõ (route_map) — `ticket-coupon-reports` approved |
| 6 | **Booking lifecycle** (tạo/xác nhận/hủy/xóa reservation) | pro+backend | 🟡 mở/hủy/xóa UI-confirmed; tạo mới chưa |
| 7 | **Reservation widget** (đặt lịch public → backend) | reservation+backend | 🔴 chưa đụng (Nuxt 0 process — cần UI-confirm) |
| 8 | **Admin panel** (super-admin) | admin+backend | 🔴 chưa đụng |

Chú: 🟢 hiểu tốt · 🟡 một phần · 🔴 chưa.

## Wiring xuyên hệ then chốt (từ CLAUDE.md — graph không thấy)
- **Sync backend↔ticket = 2 tầng: direct-first, outbox-fallback.** `ThreeaseTicketSyncable` (after_commit)
  → `ThreeaseTicketSyncJob` → ticket khỏe: HMAC webhook `/admin-api/sync` (INSTANT) · ticket down: outbox
  (`rake threease_ticket:flush_outbox`). Reverse: ticket `pro_backend_sync.py` + `SyncOutboxEvent`.
- **Guard "vé đã dùng"** (phiên này UI-confirm): chặn cancel payment/booking/delete/remove khi gói có vé đã dùng;
  message JP đúng ở A/B, raw i18n key ở Remove (bug).
- **Coupon SC:** đếm theo SC (store credit), FIFO toàn tài khoản; report `/coupon-reports/{sales,usage}` (2/5 sub-tab build).

## Cách dựng deep-dive mỗi domain (lặp)
1. `query({repo:"@threease", search_query:"<domain>"})` + `context` → symbol + flow.
2. Đọc code tại pinpoint + trám cross-repo bằng CLAUDE.md.
3. Viết `knowledge/system/<domain>.md`: entities · flows · rules · state-machine · cross-repo wiring · `source_symbols`+`source_hash`. status: draft → người duyệt.
4. (Nếu domain cần cho QA dựng precondition → UI-confirm phần navigation → tách sang `knowledge/<flow>.md` approved.)

## Thứ tự đề xuất (giá trị cao trước)
① Customer/Master sync (đã rõ, viết nhanh) → ② Payment/Cancel (đã UI-confirm) → ③ Ticket issue+sync →
④ Coupon/SC → ⑤ Reports → ⑥ Booking → ⑦ Reservation widget → ⑧ Admin.
