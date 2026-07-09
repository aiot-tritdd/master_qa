# Skill 5 — Dọn dữ liệu test trên dev (CHẠY TAY, không auto)

> **Nguyên tắc: Knowledge-first / source-on-demand** — luôn đọc knowledge (`.claude-tester/knowledge/`)
> trước để nắm bối cảnh, KHÔNG grep lại toàn bộ codebase; chỉ đọc thẳng source code/spec gốc khi
> knowledge không đủ chi tiết hoặc nghi ngờ đã lỗi thời.

Xóa dữ liệu test tạo ra khi chạy `/testcase-run` / `/testcase-retest` trên **dev dùng chung**,
theo QUY ƯỚC ĐẶT TÊN (prefix). Mặc định **dry-run** (chỉ liệt kê), thêm `--apply` mới xóa.

> **Nguyên tắc**: cleanup là thao tác **chủ động chạy bằng tay khi cần** — các skill run/retest
> KHÔNG tự gọi cleanup. Dữ liệu test được giữ lại sau khi test để đối chiếu evidence / dev debug;
> chỉ dọn khi user quyết định.

## Cách dùng
```
/testcase-cleanup [<folder>]
```

## QUY ƯỚC ĐẶT TÊN DỮ LIỆU TEST (bắt buộc)
Mọi skill khi tạo dữ liệu test PHẢI đặt prefix cố định để cleanup quét được:
- **Preset**: `AIOT-TEST-*` (vd `AIOT-TEST-105`)
- **Staff / account**: `AIOTTEST*` (vd `AIOTTEST105`)
- Đặt lịch/vé tạo để test → ghi lại **ID** vào phần Note của tcs.json để cleanup theo id.

## Quy trình
1. **Dry-run trước** (an toàn, chỉ liệt kê):
   ```
   cd .claude-tester/scripts && node cleanup.js
   ```
   Env tuỳ chỉnh: `PRESET_PREFIX`, `STAFF_PREFIX`, `BRANCH_ID`, `RESV_IDS=734,737`.
2. **Rà soát** danh sách in ra (preset / staff / reservation).
3. **Thực thi xóa** (cần user duyệt — thao tác trên shared dev):
   ```
   node cleanup.js --apply
   ```
   - Xóa: **preset** khớp prefix + **reservation** trong `RESV_IDS`.
   - **Staff KHÔNG có API xóa** → chỉ liệt kê; user deactivate/xóa tay.
   - **Vé (ticket pack) phantom** do bug hủy-thanh-toán → chưa tự xóa; báo user + dev.
4. **Báo cáo**: đã xóa gì, còn tồn gì cần xử lý tay.

## Booking đã thanh toán / có vé (kinh nghiệm No.10.1~3, 2026/07/07)
Xóa booking trên dev bị chặn theo tầng — làm đúng thứ tự:
1. **Hủy giao dịch trước**: booking đã thanh toán không DELETE được ngay.
   `PUT /branches/{branch}/transactions/{id}` với `transaction.status=cancelled` → rồi mới DELETE.
2. **Xóa 2 vòng**: booking PHÁT HÀNH gói vé bị chặn 422「使用済みチケット…」khi gói còn vé
   đã dùng/giữ chỗ. Vòng 1 xóa các booking **tiêu thụ vé** (nhả vé) → vòng 2 xóa booking phát hành.
3. **Không xóa được (by design / thiếu API)** — liệt kê để xử lý tay:
   - Booking có vé đã **quét trực tiếp trên threease_ticket** (không hoàn tác được).
   - **Ticket master** (`AIOT-TEST-TK*`): không có API/UI xóa sau khi đã bán option.
   - **Khách hàng** (`AIOTTEST-KH*`): chưa có API xóa.
4. **Branch**: xác nhận branch của phiên đăng nhập (dev hiện tại staff TESTSEED001 → branch **2**,
   không phải 4 như default cũ) — set `BRANCH_ID` cho đúng.

## Before final (checklist bắt buộc trước khi báo cáo xong)
- [ ] Đã đọc đúng knowledge theo routing (`.claude-knowledge/README.md` mục "Routing table") chưa?
- [ ] Có đọc source code không? Nếu có, vì sao?
- [ ] Có điểm nào knowledge thiếu/lỗi thời cần cập nhật lại không (vd branch/prefix đổi)?
- [ ] Vé phantom hoặc dữ liệu liên quan sync (`SYNC_MAP.md`) có cần cảnh báo riêng cho user/dev không?

## Lưu ý
- Chạy `npm i` 1 lần trong thư mục scripts trước (xem README) — helper cần `playwright`.
- Chạy khi nào? **Khi user chủ động yêu cầu** — thường là sau khi evidence đã chốt,
  dev không còn cần dữ liệu để debug. KHÔNG chạy tự động sau run/retest.
- `--apply` là thao tác phá huỷ trên shared dev → luôn dry-run + xác nhận trước.
