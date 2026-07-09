# LESSONS — Bài học / bẫy (tăng dần, có ngày)

> Sau mỗi run/retest, thêm bẫy mới ở ĐẦU danh sách. Format: `YYYY/MM/DD — [tag] bài học (→ hệ quả)`.

- **2026/07/08 — [sync/vé]** Đọc trực tiếp code, xác nhận 2 việc quan trọng (chi tiết đầy đủ + file:line
  ở `.claude-knowledge/SYNC_MAP.md`, ĐỌC FILE ĐÓ thay vì tin tóm tắt này):
  (1) bên **Hệ thống Vé** hiện chỉ xử lý được đồng bộ Khách hàng/Nhân viên, **CHƯA xử lý được**
  Vé/Gói vé/Tùy chọn vé/Coupon;
  (2) phát hiện thêm: Hệ thống Lõi **đã có sẵn receiver** nhận sync chiều ngược (Hệ thống Vé → Hệ thống
  Lõi, 13 event) nhưng **chưa tìm thấy code phía Hệ thống Vé thực sự gọi tới** — nghĩa là claim "chỉ
  1 chiều" trước đây KHÔNG chính xác, cần hỏi dev thay vì tự kết luận.
  → Test tiêu thụ/hủy vé bên **Ứng dụng Pro** rồi xem giao diện **Hệ thống Vé** là **không đáng tin**.
  Phải đối chiếu API của **Hệ thống Lõi** (`GET /branches/{b}/customers/{c}/ticket_packs`) làm chuẩn.
- **2026/07/08 — [cleanup/branch]** Phiên staff `TESTSEED001` map branch = **3** (đổi từ 2 hôm 07/07).
  → Xác nhận: giá trị branch đổi theo phiên/data, không cố định — luôn set/verify `BRANCH_ID` đúng phiên
  trước khi gọi API theo branch, không tin theo lịch sử.
- **2026/07/07 — [cleanup/branch]** Phiên staff `TESTSEED001` map branch = **2**, không phải 4 (default cũ).
- **2026/07/07 — [cleanup/booking]** Booking **đã thanh toán** không DELETE được ngay → phải
  `PUT /transactions/{id}` status=cancelled trước.
- **2026/07/07 — [cleanup/ticket]** Xóa booking **phát hành gói vé** bị 422「使用済みチケット」khi gói còn vé
  đã dùng → xóa **2 vòng**: nhả vé (xóa booking tiêu thụ) trước, xóa booking phát hành sau.
- **2026/07/06 — [screenshot]** `sleep + screenshot` trần hay dính màn trắng/spinner → dùng
  `shot(page, path, readySelector)` chờ selector đặc trưng + networkidle.
- **2026/07/04 — [BUG No.10.5]** Hủy thanh toán đặt lịch có mua vé **KHÔNG thu hồi vé**: booking về `未払い`
  nhưng khách vẫn giữ nguyên số slip (vd 100). → Vi phạm toàn vẹn kế toán (đúng lo ngại 締め của spec).
  Đề nghị dev: hủy TT → refund/thu hồi vé.
- **2026/07/04 — [API/quyền]** API xóa đặt lịch đã TT khi không quyền trả **204** (không xóa gì, dữ liệu còn)
  thay vì 403. → Dữ liệu được bảo vệ nhưng nên trả mã lỗi quyền rõ ràng.
- **2026/07/04 — [Vuetify]** `data-cy` gắn ở cả `div` bọc lẫn `input` → `fill` phải target `input[data-cy=…]`.
  Dialog xác nhận có 2 nút gần giống (閉じる vs キャンセル) → chọn đúng nút hành động.
- **2026/07/04 — [preset]** Ô quyền của preset **mặc định** bị disabled → phải tạo preset mới để test ẩn/hiện nút.
