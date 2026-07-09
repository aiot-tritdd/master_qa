# PLAYBOOK — Công thức thao tác

Cách làm cụ thể trên Threease dev. Helper ở `.claude-tester/scripts/` (`pw_lib.js`, `pw_api.js`).

## Chụp screenshot ĐÚNG (bắt buộc)
Dùng `shot(page, path, readySelector)` của `pw_lib.js` — chờ selector đặc trưng + networkidle + đệm 500ms
→ tránh ảnh trắng/spinner. **KHÔNG** dùng `sleep cố định + page.screenshot` trần.
Ảnh nén ~1080px JPG q90.

## Lấy token gọi API
`withApi(async ({api}) => …)` (pw_api.js) — mở 1 trang có gọi API để tự bắt header, rồi `api('GET','/…')`.

## Tạo đặt lịch「支払い済」có vé (để test toàn vẹn dữ liệu)
1. Tạo đặt lịch + thêm item vé (Linh ticket) → trạng thái `未払い`.
2. Mở「請求書」→ thanh toán đủ (現金) → `支払い済`; khi này khách mới **được cấp vé** (0 → N slip).
3. Kiểm số dư: `GET /branches/{b}/customers/{c}/ticket_packs`.
4. Hủy: nút「キャンセル」trên dòng giao dịch → dialog xác nhận, bấm nút **キャンセル** (không phải 閉じる).
   → Kỳ vọng: vé thu hồi về 0. (Bug hiện tại: vẫn giữ N — xem LESSONS.)

## Gán quyền để test ẩn/hiện nút
- Không sửa được ô quyền của **preset mặc định** (disabled). → Tạo preset mới `AIOT-TEST-*` rồi gán cho staff,
  hoặc tạo staff `AIOTTEST*` gán preset đó. Gán preset: `PUT /staff/{id}` hoặc qua form 権限設定 (tab staff, có search).

## Thứ tự XÓA khi cleanup booking đã TT / có vé  [LESSONS 2026/07/07]
1. **Hủy giao dịch trước**: booking đã TT không DELETE ngay → `PUT /transactions/{id}` status=cancelled → rồi DELETE.
2. **Xóa 2 vòng**: booking phát hành gói vé bị 422「使用済みチケット」khi gói còn vé đã dùng/giữ.
   Vòng 1 xóa booking **tiêu thụ vé** (nhả vé) → vòng 2 xóa booking **phát hành**.
3. Không xóa được (thiếu API/by design) → liệt kê xử lý tay: vé đã quét trên threease_ticket,
   ticket master, khách hàng.

## Quy ước dữ liệu test (để cleanup quét)
Preset `AIOT-TEST-*` · staff/account `AIOTTEST*` · (ghi ID đặt lịch/vé tạo ra vào `note` của tcs.json).
