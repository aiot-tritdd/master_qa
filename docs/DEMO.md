# Demo script — QA-Server Phase 1

Chuẩn bị: stack ThreeSides `docker compose up -d`; API `uvicorn api.app:app --port 8899`;
UI `cd web && npm run dev` (http://localhost:3001).

Chạy trọn lát dọc trước (README bước 1–4) tới khi **④ Chạy test = ✅ PASS**.

## Punchline A — "Phá code → QA bắt"

1. Đang xanh: ④ Chạy test → ✅ PASS (customer tạo ra sync được sang ticket).
2. Phá sync: trong `ThreeSides/threease_backend/config/environments/development.rb`
   đổi `config.threease_ticket_api_secret` thành giá trị **sai**; restart:
   ```bash
   cd ../ThreeSides && docker compose restart threease_backend worker
   ```
3. Trong UI bấm **④ Chạy test** lại → ❌ **FAIL**: customer không bao giờ về ticket
   (HMAC lệch → webhook bị từ chối → flush cũng không cứu được). Report hiện lý do fail.
4. Khôi phục secret + restart → ④ xanh lại.

→ Ý nghĩa: đây là **lưới chống regression thật** — đổi code làm gãy nghiệp vụ thì QA bắt được ngay.

## Punchline B — "Đổi ý → test đuổi theo" (nếu kịp)

1. Sửa body `knowledge/customer-sync.md`: thêm một rule code **chưa** thoả
   (vd: "customer_code phải bắt đầu bằng `CUST-`"). Duyệt lại (Approve).
2. **③ Sinh test** lại → test tái sinh assert theo rule **mới**.
3. **④ Chạy test** → ❌ FAIL, chứng minh test giờ đo theo **ý định mới**, còn code chưa theo kịp.

→ Ý nghĩa: **anh không đuổi theo test; test đuổi theo anh.** Đổi ý = sửa bản ghi ý định trước,
test tự chạy theo — đúng triết lý oracle của dự án.
