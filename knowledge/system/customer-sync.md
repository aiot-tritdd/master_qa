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
source_hash: c487981641476afe
note: "MÔ TẢ code đang làm gì — KHÔNG phải oracle. Cần người duyệt."
confidence: 🟡
verify_by: "Code-derived (đọc 2026/07/08). Endpoint/outbox/cron đổi theo release → đọc lại threease_ticket_service.rb + handlers.py."
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

---

## 📥 Nhập từ `.claude-tester/.claude-knowledge/SYNC_MAP.md` §1 (2026-07-09, cửa WHAT)
> `grown_from: .claude-tester/.claude-knowledge/SYNC_MAP.md#1-chiều-lõi-vé`
> Nguồn gốc: đọc code 2026/07/08 · ⛔ **QA-runtime CẤM đọc mục này.**

- **Endpoint forward:** `POST /admin-api/sync` (hằng `API_ENDPOINT_WEBHOOK_SYNC`,
  `threease_backend/app/services/threease_ticket_service.rb:38` `send_sync_request`).
- **Bảo mật:** payload AES-256-GCM (PBKDF2 salt ngẫu nhiên) + header `Signature` (HMAC-SHA256 trên
  timestamp+body) + `Api-Key` riêng — **không** dùng devise-token của user.
- **9 model có serializer sync** (`threease_ticket_service.rb:85-109`, `get_sync_serializer_class`):
  `Therapists::Customer` · `Therapist` · `Therapists::Coupon` · `Therapists::ReservationCoupon` ·
  `Tickets::Pack` · `Tickets::Ticket` · `Tickets::Option` · `Therapists::Institute` · `Therapists::Branch`.
  Model ngoài danh sách → Rails raise `"Serializer not found for model"` (fail sớm, không gửi).
- **Outbox:** `threease_ticket_outbox_event.rb:7` — `MAX_RETRIES = 5`, trạng thái `pending/sent/failed`.
  Cron flush `config/schedule.rb:35` — `every 5.minutes`. ⇒ **worst-case trễ ~5 phút** khi lần đầu lỗi
  (không phải ~1 phút như ghi chú cũ trước 2026/07/08).
- ⚠️ **Local docker KHÔNG có scheduler** → event `failed` nằm `pending` tới khi flush tay.
  Nhưng đường **direct webhook là TỨC THÌ**; create khoẻ mạnh không hề chạm outbox.

## ⛔ Known gap (đã verify code 2026/07/08) — `handlers.py:13` `sync_data()`
Phía Django **chỉ có handler** cho `Therapists::Customer` và `Therapist`.
Model khác Rails gửi được (Pack/Ticket/Option/Coupon/Institute/Branch) → Django trả `Unknown model`/400
→ outbox `failed` sau 5 lần retry, **không cảnh báo chủ động**.
→ Hệ quả test: số dư vé/coupon hiển thị bên **Hệ thống Vé** không đáng tin làm bằng chứng duy nhất.
*(Kênh quan sát 2 phía → `knowledge/observation-channels.md`. Timeline vá handler → `OPEN-QUESTIONS.md#OQ-04`.)*
