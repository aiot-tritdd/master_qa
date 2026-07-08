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
   cd .claude/skills-scripts/testcase-evidence && node cleanup.js
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

## Lưu ý
- Chạy `npm i` 1 lần trong thư mục scripts trước (xem README) — helper cần `playwright`.
- Nên chạy cleanup **sau mỗi phiên** `/testcase-run` để dev không tích rác.
- `--apply` là thao tác phá huỷ trên shared dev → luôn dry-run + xác nhận trước.
