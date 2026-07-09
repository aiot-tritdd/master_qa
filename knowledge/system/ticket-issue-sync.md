---
id: system-ticket-issue-sync
status: draft
kind: system-map
spans_repos: [pro, backend, ticket]
source_symbols:
  - "backend: app/jobs/threease_ticket_sync_job.rb"
  - "backend: app/controllers/api/webhooks/threease_ticket/sync_controller.rb (handle_pack_issued/used/cancelled)"
  - "ticket: admin_api/data_sync/handlers.py"
source_hash: 8e034f0c8d478d29
note: "MÔ TẢ code làm gì — KHÔNG phải oracle."
confidence: 🟡
verify_by: "Code-derived. Verify bằng sync_controller.rb + handlers.py; hành vi thật phải quan sát live 2 phía."
---
# Domain: Ticket issue + sync (phát hành gói vé + đồng bộ Pro↔ticket)

> Vòng đời gói vé (回数券): phát hành khi thanh toán → sync sang ticket → dùng/hết/thu hồi → sync ngược.

## Entities & dual-ID
- `Tickets::Pack` (Rails) ↔ ticket `TicketPack`. **Dual-ID:** `ticket_pack_id` (Django id) + `id` (Rails id / `pro_pack_id`).
  (Khác Customer dùng chung id.) `Tickets::Slip` = vé con (`used` bool). `SYNC_START_ID=200000` (bỏ data cũ).

## Flow chính (từ sync_controller — webhook Django→Rails + ngược lại)
| Event | Handler (backend) | Làm gì |
|---|---|---|
| `ticket_pack_issued` | `handle_pack_issued` | tạo `Tickets::Pack` + N `Slip` (status active); giảm `option.pack_count`; re-sync ticket |
| `ticket_pack_used` | `handle_pack_used` | xóa N redeemable slip (hoặc mark `used`); status → used/expired/refunded/transferred theo `operation` |
| `ticket_pack_cancelled` | `handle_pack_cancelled` | `pack.destroy` (thu hồi cả gói) |

- Forward (Rails→ticket): `ThreeaseTicketSyncJob` (`Tickets::Ticket`/`Pack` … + action) → HMAC webhook `/admin-api/sync`.
- Auth: HMAC-SHA256 (timestamp≤5min + api_key + secret_compare). Legacy allowlist `SyncTicketPackAllowlist` cho pack < SYNC_START_ID.

## Liên kết domain khác
- **Phát hành** = hệ quả của **thanh toán booking** (xem `payment-cancel` + booking): Pro pay invoice →
  phát hành `ReservationTicket`/pack → sync.
- **Thu hồi** = cancel payment/booking/delete (xem `payment-cancel`) → `handle_pack_cancelled` / `sync_remaining`.

## Điểm QA
- Quan sát pack: Pro `Customer→số dư vé`; ticket-app `/customer/<id>/` (保有チケット, 8/10 回, 使用履歴).
- Sync **không tức thì** → chờ vài giây.

## Draft — cần
- Đọc `threease_ticket_sync_job.rb` + `handlers.py` xác nhận đủ event forward. source_hash (`--update`).
