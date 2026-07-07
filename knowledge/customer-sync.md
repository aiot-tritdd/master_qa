---
id: customer-sync
status: approved
spans_repos:
- backend
- ticket
source_symbols:
- backend:app/models/concerns/threease_ticket_syncable.rb
- backend:app/jobs/threease_ticket_sync_job.rb#perform
- ticket:admin_api/data_sync/handlers.py#sync_data
source_hash: 0311392f5585ee48
---

# [DRAFT] Living Doc — Sync Customer từ Backend (Rails) sang Ticket (Django)

> **Trạng thái: BẢN NHÁP — cần người duyệt.**
> Tài liệu mô tả *code đang làm gì* tại thời điểm đọc, không kết luận đúng/sai.
> Phạm vi: đồng bộ `Therapists::Customer` (Rails) → `Customer` (Django Ticket).
> Nguồn: `backend/app/models/concerns/threease_ticket_syncable.rb`,
> `backend/app/jobs/threease_ticket_sync_job.rb`,
> `ticket/admin_api/data_sync/handlers.py`.
>
> ⚠️ Các mục đánh dấu **(suy luận)** dựa trên comment/tham chiếu trong code
> (ví dụ `flush_outbox`) mà **mã nguồn đầy đủ chưa được cung cấp** — cần xác nhận lại.

---

## 1. Bối cảnh & phạm vi

- **Rails (backend)** là nguồn phát sự kiện (source of truth cho Customer).
- **Django (ticket)** là hệ nhận, lưu bản sao Customer để phục vụ vé/回数券.
- Với Customer, hai hệ dùng **chung khóa chính `id`** (Django `Customer.id` = Rails `Therapists::Customer.id`).
  - Khác với `Ticket`/`Pack`/`Coupon` vốn dùng dual-ID (`pro_ticket_id`, `pro_pack_id`…).
  - ⇒ Điều này quan trọng cho việc kiểm chứng ở mục 6.

---

## 2. Business Flow

### 2.1. Kích hoạt (Rails)

Concern `ThreeaseTicketSyncable` gắn callback vào model:

- `after_commit on: [:create, :update]` → `sync_to_threease_ticket`
- `after_destroy_commit` → `sync_deletion_to_threease_ticket`

Callback chạy **sau khi transaction đã commit hoàn toàn** (dùng `after_commit`, không dùng `after_create_commit`).

Bước xử lý trong `sync_to_threease_ticket`:
1. Nếu `Thread.current[:skip_threease_ticket_sync]` bật → **thoát, không sync** (dùng khi Django ghi ngược về Rails để tránh vòng lặp).
2. Lấy `current_id` (ưu tiên `id_in_database`, nếu chưa có thì `id`/`reload.id`).
3. Nếu `current_id` rỗng → **log error và thoát** (không enqueue).
4. Enqueue job: `ThreeaseTicketSyncJob.perform_later('Therapists::Customer', id, 'create_or_update')`.

Xóa (`sync_deletion_to_threease_ticket`) enqueue tương tự với action `'delete'`.

### 2.2. Xử lý job (Rails) — `ThreeaseTicketSyncJob#perform`

1. Nếu `id` rỗng → log error, `return false`.
2. Chuẩn hóa `action` về symbol (`:create_or_update`, `:delete`, …).
3. **Guard `blocked_by_ticket_master_sync_guard?`**: chỉ áp cho `Tickets::Ticket` / `Tickets::Option`.
   → **Không ảnh hưởng `Therapists::Customer`** (rơi vào nhánh `else` → `false`).
4. Với action `:create_or_update`:
   - `find_by(id:)`. Nếu **không tìm thấy** → log info + `return` (bỏ qua).
   - **Nhánh soft-delete**: nếu là `Therapists::Customer` và `instance.hidden?` == true
     → xem như **delete**, gọi `ThreeaseTicketService.sync_deletion(...)`.
   - Ngược lại: gọi `ThreeaseTicketService.sync_record(model_class, instance)` (direct webhook).

### 2.3. Hai nhánh chính

#### Nhánh A — Direct Webhook (happy path)
- Rails gọi thẳng `ThreeaseTicketService.sync_record`/`sync_deletion` → gửi HTTP sang Django.
- Django `sync_data` định tuyến `model == 'Therapists::Customer'` → `sync_customer(data, action)`.
- Django xử lý (mục 2.4). Nếu `success` truthy → coi như đã sync trực tiếp.
- Log Rails: `"... sent directly"`.

#### Nhánh B — Outbox Fallback (khi direct webhook thất bại)
- Nếu `success` là falsy (webhook lỗi/timeout/Django trả không thành công), Rails tạo bản ghi:
  