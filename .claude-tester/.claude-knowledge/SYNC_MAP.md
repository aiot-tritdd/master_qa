# SYNC_MAP — Đồng bộ dữ liệu Hệ thống Lõi ↔ Hệ thống Vé

> Quy ước "fact confidence": mỗi mục có **Nguồn** (file:line) · **Ngày đọc** · **Độ ổn định**
> (⭐ code cứng, ít đổi / 🟢 ổn định / 🟡 đổi theo release / 🔴 suy luận, chưa xác nhận hết) ·
> **Cần verify bằng** (cách tự kiểm lại khi nghi ngờ).
> Tên nghiệp vụ dùng ở đây theo bảng thuật ngữ `DOMAIN.md` (Hệ thống Lõi = Rails/threease_backend,
> Hệ thống Vé = Django/threease_ticket).

## 1. Chiều Hệ thống Lõi → Hệ thống Vé (Rails → Django)
**Nguồn**: [`threease_ticket_service.rb:38`](/Applications/Workspaces/threease/threease_backend/app/services/threease_ticket_service.rb:38) (`send_sync_request`)
· **Ngày đọc**: 2026/07/08 · **Độ ổn định**: ⭐ (code hiện hành, đọc trực tiếp) · **Verify bằng**: đọc lại
file trên nếu nghi thay đổi.

- **Endpoint**: `POST /admin-api/sync` (hằng số `API_ENDPOINT_WEBHOOK_SYNC`, cùng file).
- **Bảo mật**: mã hóa payload AES-256-GCM (PBKDF2 salt ngẫu nhiên) + header `Signature` (HMAC-SHA256
  trên timestamp+body), `Api-Key` riêng — không phải cùng cơ chế devise token của user.
- **Model có serializer sync** ([`threease_ticket_service.rb:85`](/Applications/Workspaces/threease/threease_backend/app/services/threease_ticket_service.rb:85)
  method `get_sync_serializer_class`, đến dòng 109):
  `Therapists::Customer`, `Therapist`, `Therapists::Coupon`, `Therapists::ReservationCoupon`,
  `Tickets::Pack`, `Tickets::Ticket`, `Tickets::Option`, `Therapists::Institute`, `Therapists::Branch`.
  → Model KHÔNG nằm trong danh sách này sẽ raise lỗi `"Serializer not found for model"` phía Rails
  (fail sớm, không gửi đi) — khác với gap ở mục 3 (Rails gửi được nhưng Django từ chối).
- **Retry khi lỗi**: outbox pattern.
  - Model: [`threease_ticket_outbox_event.rb:7`](/Applications/Workspaces/threease/threease_backend/app/models/threease_ticket_outbox_event.rb:7)
    — `MAX_RETRIES = 5`, trạng thái `pending/sent/failed`.
  - Cron flush: [`schedule.rb:35`](/Applications/Workspaces/threease/threease_backend/config/schedule.rb:35)
    — `every 5.minutes do rake 'threease_ticket:flush_outbox' end`.
  - → Độ trễ worst-case khi lỗi lần đầu: **~5 phút** (không phải ~1 phút như ghi chú cũ trước 2026/07/08).

## 2. Chiều Hệ thống Vé → Hệ thống Lõi (Django → Rails) — receiver CÓ, sender CHƯA XÁC NHẬN
**Nguồn**: [`sync_controller.rb:3`](/Applications/Workspaces/threease/threease_backend/app/controllers/api/webhooks/threease_ticket/sync_controller.rb:3)
(comment đầu file mô tả mục đích) + [`routes.rb:394`](/Applications/Workspaces/threease/threease_backend/config/routes.rb:394)
(khai báo route) · **Ngày đọc**: 2026/07/08 · **Độ ổn định**: 🔴 (receiver xác nhận có code, nhưng
CHƯA xác nhận có ai gọi tới nó trong thực tế — không suy diễn thêm ngoài 2 fact này) · **Verify bằng**:
hỏi dev trực tiếp, hoặc xem log Rails có request nào tới endpoint này trong môi trường thật không.

- **Endpoint nhận**: `POST /api/v1/webhooks/threease_ticket/sync` (route tại `routes.rb:394`,
  namespace `webhooks/threease_ticket`, action `sync#sync`). Comment ở `sync_controller.rb:3` mô tả
  đây là "controller nhận đồng bộ chiều ngược từ Django" (nguyên văn theo comment code, không phải
  suy diễn của người đọc).
- **Auth**: HMAC-SHA256 (`verify_hmac_signature!`, cùng key/secret chiều Rails→Django).
- **13 event được hỗ trợ** (case/when trong action `sync`):
  `ticket_pack_used`, `ticket_pack_cancelled`, `ticket_pack_issued`, `ticket_upserted`,
  `ticket_option_upserted`, `coupon_upserted`, `coupon_pack_issued`, `coupon_sc_used`,
  `institute_upserted`, `branch_upserted`, `customer_upserted`, `customer_deleted`, `staff_upserted`.
- **Cutover guard**: hằng số `SYNC_START_ID = 200000` — pack ID nhỏ hơn giá trị này bị coi là dữ liệu
  cũ trước khi deploy cơ chế này, tự động bỏ qua (comment: phải reset sequence 2 hệ ≥ giá trị này
  trước khi deploy).
- **⚠️ TRẠNG THÁI THỰC TẾ — diễn đạt đúng mức, không khẳng định quá tay**:
  Chỉ có 2 fact đã verify: (a) Rails **có sẵn code nhận** (receiver) đầy đủ logic cho chiều này;
  (b) grep toàn bộ `threease_ticket/` (Django) theo `requests.post|httpx.post|session.post` và theo
  tên 13 event ở trên → **không tìm thấy nơi nào phía
  Django gọi tới endpoint này hoặc tham chiếu các tên event này**.
  → Kết luận tạm: **receiver đã build sẵn nhưng sender phía Django chưa xác nhận được đã triển khai**
  (có thể: (a) chưa làm xong, (b) code sender nằm ở nơi khác ngoài `threease_ticket/admin_api`,
  (c) gọi qua Celery task/queue riêng chưa grep ra). **CẦN HỎI DEV** thay vì tự kết luận đã hoạt động
  hay chưa — đây là khoảng trống thông tin, không phải khoảng trống code (khác mục 3).

## 3. Known gaps theo code hiện tại (đã verify, không phải suy đoán)
**Nguồn**: [`handlers.py:13`](/Applications/Workspaces/threease/threease_ticket/admin_api/data_sync/handlers.py:13)
(hàm `sync_data()`) · **Ngày đọc**: 2026/07/08 · **Độ ổn định**: ⭐ (đúng với checkout code đang đọc —
handler có thể được bổ sung ở version sau, verify lại nếu cách xa ngày đọc) · **Verify bằng**: đọc lại
hàm `sync_data()` ở dòng trên.

- Phía Django, hàm nhận sync **chiều Rails→Django** (mục 1) hiện **chỉ có handler** cho
  `Therapists::Customer` và `Therapist`. Model khác Rails có gửi được (theo mục 1: Pack/Ticket/Option/
  Coupon/Institute/Branch) sẽ bị Django trả lỗi kiểu `Unknown model`/400.
- Hệ quả: outbox (mục 1) sẽ nhận response lỗi → đánh dấu `failed`, retry tới `MAX_RETRIES=5` rồi dừng,
  **không có cảnh báo chủ động** cho ai biết. Muốn phát hiện phải chủ động xem log/bảng outbox.
- **Test impact**: số dư vé/coupon hiển thị bên **Hệ thống Vé** (giao diện Django) không đáng tin cậy
  làm bằng chứng — luôn đối chiếu API Hệ thống Lõi (`GET /branches/{b}/customers/{c}/ticket_packs`)
  trước khi kết luận PASS/FAIL liên quan tới số dư vé.

## 4. Câu hỏi mở cần dev xác nhận (không tự đoán khi test/report)
1. Sender phía Django cho chiều ngược (mục 2) đã triển khai chưa, nằm ở đâu nếu có?
2. Kế hoạch bổ sung handler còn thiếu ở mục 3 (Pack/Ticket/Option/Coupon) — có timeline không?
3. `SYNC_START_ID=200000` đã đúng cấu hình ở môi trường dev/staging hiện tại chưa (ảnh hưởng dữ liệu
   test tạo mới có bị bỏ qua sync ngược hay không)?
