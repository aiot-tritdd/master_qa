# METHOD — Kỹ thuật test bất biến

Nguyên tắc thiết kế test case (không phụ thuộc hệ thống). Skill `/testcase-write` đọc để phủ đủ góc.

## Archetype phủ (khớp `example.tcs.json`)
1. **Happy path** — luồng chính mỗi màn hình bị ảnh hưởng.
2. **Biến thể điều kiện/quyền** — cùng thao tác, đổi quyền/trạng thái → hành vi khác (before/after).
3. **Boundary** — giá trị ngưỡng/giới hạn ghi trong spec.
4. **Regression** — chức năng liên quan KHÔNG bị ảnh hưởng.
5. **Backend/API · toàn vẹn dữ liệu** — kiểm tầng API/DB, chống bypass.

## Luật vàng (rút từ bug thật)
- **Toàn vẹn dữ liệu sau HỦY/XÓA**: với mọi thao tác cancel/delete/refund, PHẢI kiểm dữ liệu phái sinh
  được hoàn/thu hồi đúng (số dư vé, tồn kho, sổ kế toán). *(Gốc bug TC-09: hủy thanh toán không thu hồi vé.)*
- **Chống bypass tầng API**: quyền ẩn nút ở UI thì PHẢI có case gọi thẳng API để chắc backend cũng chặn
  (không chỉ ẩn nút). Kỳ vọng: 403/từ chối, dữ liệu không đổi.
- **State-transition**: liệt kê trạng thái (未払い/支払い済/キャンセル…) và kiểm hành vi ở từng trạng thái,
  đặc biệt các chuyển tiếp mà spec đổi logic.
- **Permission matrix**: quyền × trạng thái → 1 ô = 1 case (có quyền/không quyền × đã TT/chưa TT).
- **Negative**: nhập sai/thiếu quyền/gọi API không hợp lệ → phải báo lỗi đúng, không âm thầm nuốt (204 mà
  không làm gì cũng là mùi — nên trả mã lỗi rõ).

## Kết quả & đối chiếu
- `PASS` / `FAIL` / `未実施`; `actual` mô tả **quan sát được** (không suy diễn), bắt đầu bằng đúng từ đó.
- FAIL phải kèm: bằng chứng cụ thể (số liệu trước/sau) + đề nghị fix.
