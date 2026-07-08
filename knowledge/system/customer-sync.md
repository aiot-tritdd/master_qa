---
id: system-customer-sync
status: draft
kind: system-map
spans_repos: [backend, ticket]
source_symbols:
  - "backend: app/models/concerns/threease_ticket_syncable.rb"
  - "backend: app/jobs/threease_ticket_sync_job.rb#perform"
  - "backend: app/controllers/api/webhooks/threease_ticket/sync_controller.rb (handle_customer_upserted/deleted)"
  - "ticket: admin_api/data_sync/handlers.py"
  - "ticket: th/services/pro_backend_sync.py + SyncOutboxEvent"
source_hash: null
note: "MÔ TẢ code đang làm gì — KHÔNG phải oracle. Cần người duyệt."
---
# Domain: Customer / Master sync (backend Rails ↔ ticket Django)

> Đồng bộ 2 chiều customer/institute/branch/staff giữa hub (Rails) và ticket (Django).

## Entities & khóa
- Customer: **chung khóa `id`** (Django `Customer.id` = Rails `Therapists::Customer.id`).
  (Khác Ticket/Pack/Coupon dùng dual-ID `pro_*_id`.) → quan trọng khi đối chiếu.
- Master khác: Institute / Branch / Staff(Therapist) — cũng sync.

## Flow forward (Rails → ticket) — 2 tầng: direct-first, outbox-fallback
```
create/update model include ThreeaseTicketSyncable
  → after_commit → ThreeaseTicketSyncJob.perform_later (Sidekiq, worker chạy ngay)
      ├─ ticket reachable → direct HMAC webhook POST /admin-api/sync → "sent directly"   ← INSTANT
      └─ ticket down      → ThreeaseTicketOutboxEvent.create!(pending)                    ← fallback
                            → drained bởi  rake threease_ticket:flush_outbox
  ticket nhận: admin_api/data_sync/handlers.py → upsert th_customer/th_institute/...
```
- **Đường chuẩn = TỨC THÌ** (worker). Outbox chỉ khi direct fail (vd ticket restart) → nằm `pending` tới khi flush.
- Chống loop: `Thread.current[:skip_threease_ticket_sync]` bật khi Django ghi ngược về Rails.

## Flow reverse (ticket → Rails)
`th/services/pro_backend_sync.py` + `SyncOutboxEvent` → drained bởi `python manage.py flush_sync_outbox`.
Rails nhận ở `SyncController` (`handle_customer_upserted/deleted/institute/branch/staff`) — `save!(validate:false)`
+ set `Thread.current[:skip_threease_ticket_sync]=true` để không sync ngược.

## Auth & config
- HMAC-SHA256 (timestamp + payload), key/secret khớp 2 phía. `SYNC_START_ID=200000` (bỏ qua data cũ).
- Config ticket: `config/admin_api_settings.py` (gitignore) phải khớp backend `development.rb`.

## Điểm QA hay đụng (khi test)
- Tạo/sửa customer trên Pro/backend → **quan sát** ticket-admin (`/admin/th/customer/`) thấy bản sao (chờ vài giây nếu qua outbox).
- `customer_deleted` → ticket set `hidden=true` (không xóa cứng).

## ⚠️ Draft — cần
- Đọc code thật xác nhận danh sách event đầy đủ + edge (partial sync, retry).
- source_hash thật (GĐ-0).
