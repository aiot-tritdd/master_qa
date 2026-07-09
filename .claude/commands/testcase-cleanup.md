# Skill 5 — Dọn dữ liệu test trên dev

Xóa dữ liệu test tạo ra khi chạy `/testcase-run` / `/testcase-retest` trên **dev dùng chung**,
theo QUY ƯỚC ĐẶT TÊN (prefix). Mặc định **dry-run** (chỉ liệt kê), thêm `--apply` mới xóa.

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
   cd .claude/skills-scripts/testcase-evidence && BRANCH_ID=<n> node cleanup.js
   ```
   Env: `PRESET_PREFIX` (mđ `AIOT-TEST`), `STAFF_PREFIX` (mđ `AIOTTEST`), `BRANCH_ID`, `RESV_IDS=734,737`.

   ⚠️ **`BRANCH_ID` KHÔNG có mặc định đúng vĩnh viễn** — nó đổi theo phiên/data (đã ghi nhận
   TESTSEED001 map branch 4 → 2 → 3 qua các ngày). Không set → script tự bỏ qua Staff+Reservation
   và nhắc bạn xác nhận branch của **phiên hiện tại** trước. Đừng tin giá trị lịch sử.
2. **Rà soát** danh sách in ra (preset / staff / reservation).
3. **Thực thi xóa** (cần user duyệt — thao tác trên shared dev):
   ```
   node cleanup.js --apply
   ```
   - Xóa: **preset** khớp prefix + **reservation** trong `RESV_IDS`.
   - **Staff KHÔNG có API xóa** → chỉ liệt kê; user deactivate/xóa tay.
   - **Vé (ticket pack) phantom** do bug hủy-thanh-toán → chưa tự xóa; báo user + dev.
4. **Báo cáo**: đã xóa gì, còn tồn gì cần xử lý tay.

## Before final (checklist bắt buộc)
- [ ] Đã dry-run và được user duyệt trước khi `--apply` chưa? (shared dev — thao tác phá huỷ)
- [ ] `BRANCH_ID` là branch của **phiên hiện tại** hay giá trị lịch sử? (đổi theo phiên — đừng tin cũ)
- [ ] Có xoá nhầm dữ liệu **không mang prefix** `AIOT-TEST-*` / `AIOTTEST*` không?
- [ ] Bẫy mới khi dọn (thứ tự, mã lỗi) → đã ghi `knowledge/lessons.md` chưa?

## Booking đã thanh toán / có vé — xóa theo TẦNG (đúng thứ tự)
1. **Hủy giao dịch trước**: booking đã TT không DELETE được ngay →
   `PUT /branches/{b}/transactions/{id}` `{transaction:{status:'cancelled'}}` → rồi DELETE.
   (`cleanup.js` tự thử bước này khi gặp 422/409.)
2. **Xóa 2 vòng**: booking **phát hành** gói vé bị chặn `422「使用済みチケット」` khi gói còn vé đã dùng/giữ.
   Vòng 1 xóa booking **tiêu thụ vé** (nhả vé) → vòng 2 xóa booking **phát hành**.
3. **Không xóa được (by design / thiếu API)** — liệt kê để xử lý tay: vé đã quét trên Hệ thống Vé ·
   ticket master `AIOT-TEST-TK*` · khách hàng `AIOTTEST-KH*`.

## Lưu ý
- Chạy `npm i` 1 lần trong thư mục scripts trước — helper cần `playwright`.
- **KHÔNG auto-cleanup.** `/testcase-run` và `/testcase-retest` giữ nguyên dữ liệu test (để đối chiếu
  evidence / dev debug) và chỉ **liệt kê** thứ còn tồn. Cleanup là thao tác **chủ động chạy tay**
  khi user quyết định — thường sau khi evidence đã chốt.
- `--apply` là thao tác phá huỷ trên shared dev → luôn dry-run + xác nhận trước.
