---
id: playbook
status: draft
kind: flow
spans_repos: [pro, backend]
source_symbols: []
source_hash: null
confidence: 🟡
verify_by: "CHƯA UI-confirm dưới locale ja-JP. Mỗi công thức phải drive thật rồi mới approved. Nhãn UI trong file gốc của sếp được confirm dưới harness THIẾU locale → có thể sai (xem lessons.md 2026/07/09)."
ui_confirmed_at: null
grown_from: ".claude-tester/knowledge/PLAYBOOK.md"
---
# PLAYBOOK — công thức thao tác trên Threease dev (HOW)

> ⚠️ **`status: draft` — chưa UI-confirm.** File gốc (`.claude-tester/knowledge/PLAYBOOK.md`) được soạn
> khi harness **thiếu `locale`** → app chạy tiếng Anh. Doc `pro-open-booking.md` từng dính đúng lỗi đó
> (`Remove` thay vì `削除する`, `INVOICE` thay vì `請求書`, toạ độ chuột lệch 40px).
> **Drive thật từng công thức dưới đây rồi mới `approved`.** Đừng tin nhãn chưa kiểm.
>
> Firewall: chỉ ghi **cách làm** + **nơi quan sát**. KHÔNG ghi kết quả kỳ vọng (đó là SPEC).

## ✅ Chụp screenshot ĐÚNG (đã verify 2026-07-09)
Dùng `shot(page, path, readySelector)` — chờ selector đặc trưng + `networkidle` + đệm 500ms.
**KHÔNG** `waitForTimeout(6000)` + `page.screenshot()` trần.
Ảnh **PNG rõ** (`deviceScaleFactor: 2` → 2880×1800). Không nén JPG.

## ✅ Gọi API bằng phiên của app (đã verify 2026-07-09)
`withApi(async ({api}) => …)` (`pw_api.js`) — mở 1 trang có gọi API để **nghe lén** header devise-token,
rồi `api.get/post/put/del`. Trả `{status, body, ok}`.

## 🟡 Tạo đặt lịch `支払い済` có vé (để test toàn vẹn dữ liệu) — CHƯA re-confirm
1. Tạo đặt lịch + thêm item vé → trạng thái `未払い`.
2. Mở `請求書` → thanh toán đủ (`現金`) → `支払い済`; khi này khách **mới** được cấp vé (0 → N slip).
3. Kiểm số dư: `GET /branches/{b}/customers/{c}/ticket_packs` *(endpoint này **chưa gọi thật** —
   xem `knowledge/system/api-endpoints.md`)*.
4. Hủy: nút `キャンセル` trên dòng giao dịch → dialog xác nhận → bấm nút **`キャンセル`** (KHÔNG phải `閉じる`).

⚠️ **Precondition Protocol:** dựng trạng thái bằng **flow CŨ đã chạy ổn**, KHÔNG dùng feature đang test.
Dựng xong **verify bằng mắt** rồi mới chạy case.

## 🟡 Gán quyền để test ẩn/hiện nút — CHƯA re-confirm
- Ô quyền của preset **mặc định** bị `disabled` → phải tạo preset mới `AIOT-TEST-*` rồi gán cho staff,
  hoặc tạo staff `AIOTTEST*` gán preset đó.
- Gán preset: `PUT /staff/{id}` *(chưa gọi thật)* hoặc qua form `権限設定` (tab staff, có ô search).
- Màn quyền: `/clinic_setting/permissions` — ✅ đã verify (`shot()` bắt được `text=権限設定`).

## 🟡 Thứ tự XÓA khi cleanup booking đã TT / có vé — CHƯA re-confirm
1. **Hủy giao dịch trước:** booking đã TT không `DELETE` ngay →
   `PUT /branches/{b}/transactions/{id}` `status=cancelled` → rồi `DELETE`.
2. **Xóa 2 vòng:** booking **phát hành** gói vé bị `422「使用済みチケット」` khi gói còn vé đã dùng/giữ.
   Vòng 1 xóa booking **tiêu thụ** vé (nhả vé) → vòng 2 xóa booking **phát hành**.
3. **Không xóa được (by design / thiếu API)** → liệt kê xử lý tay: vé đã quét trên Hệ thống Vé ·
   ticket master `AIOT-TEST-TK*` · khách hàng `AIOTTEST-KH*`.

## Quy ước dữ liệu test (để `cleanup.js` quét được)
Preset `AIOT-TEST-*` · staff/account `AIOTTEST*` · ghi ID booking/vé tạo ra vào `note` của `tcs.json`.
