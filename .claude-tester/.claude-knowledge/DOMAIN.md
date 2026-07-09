# DOMAIN — Nghiệp vụ Threease (vì sao 1 hành vi là bug)

## Bảng thuật ngữ (dùng khi trao đổi/báo cáo — KHÔNG dùng tên kỹ thuật với khách hàng)
Tên kỹ thuật (repo/công nghệ) chỉ dùng nội bộ để tra code; giao tiếp/viết report/họp khách hàng
**luôn dùng tên nghiệp vụ** ở cột trái.

| Tên nghiệp vụ (dùng khi nói/viết) | Vai trò | (tên kỹ thuật — chỉ để tra code, không nói ra ngoài) |
|---|---|---|
| **Hệ thống Lõi** | Nơi lưu toàn bộ dữ liệu gốc, xử lý nghiệp vụ chính | `threease_backend`, Rails |
| **Ứng dụng Pro** | Web nhân viên/chủ phòng khám thao tác hàng ngày | `threease_pro`, Nuxt |
| **Ứng dụng Quản trị** | Web dành cho Super Admin (vận hành Threease) | `threease_admin`, Nuxt |
| **Widget Đặt lịch** | Form đặt lịch nhúng trên web, bệnh nhân tự đặt | `threease_reservation`, Nuxt |
| **Ứng dụng Di động Nhân viên** | App mobile cho nhân viên (xem lịch/nội dung trị liệu) | `threease_therapists`, Flutter |
| **Hệ thống Vé** | Backoffice quản lý vé/gói buổi trị liệu (回数券), tách riêng khỏi Hệ thống Lõi | `threease_ticket`, Django |

## Hệ thống liên quan [nguồn: đọc repo trực tiếp, 2026/07/08]
- **Hệ thống Lõi** — nguồn sự thật (source of truth) cho toàn bộ dữ liệu: phòng khám/chi nhánh, khách hàng,
  nhân viên, đặt lịch, vé. Mỗi ứng dụng phía trên gọi vào đây qua API riêng theo vai trò (nhân viên/admin/
  bệnh nhân) — nghĩa là Ứng dụng Pro, Ứng dụng Di động Nhân viên **không tự lưu dữ liệu**, chỉ là giao diện.
- **Ứng dụng Di động Nhân viên** dùng phiên đăng nhập **độc lập** với Ứng dụng Pro (mỗi thiết bị tự có phiên
  riêng, không chia sẻ đăng nhập giữa web và mobile).
- **Hệ thống Vé** là hệ **tách biệt**, có giao diện quản trị riêng (phát/sử dụng/hủy/chuyển vé); nhận dữ liệu
  từ Hệ thống Lõi qua cơ chế đồng bộ (xem mục dưới) — **không phải cùng 1 database** với Hệ thống Lõi.
- Chưa xác nhận có ứng dụng mobile riêng cho **bệnh nhân** trong phạm vi 6 hệ thống đang quản lý — nếu tài
  liệu cũ có nhắc, cần kiểm lại vì hiện chưa thấy (⚠️ cần xác nhận).

## ⚠️ Đồng bộ dữ liệu Hệ thống Lõi ↔ Hệ thống Vé — xem chi tiết ở [`SYNC_MAP.md`](SYNC_MAP.md)
**Tóm tắt cho người không cần chi tiết kỹ thuật** (Nguồn: `SYNC_MAP.md`, đọc 2026/07/08, độ ổn định 🔴
vì có phần chưa xác nhận hết — xem file gốc để biết đúng chỗ nào chắc/chưa chắc). Diễn đạt cẩn thận,
KHÔNG khẳng định quá tay theo hướng nào:
- **Rails → Django** (`/admin-api/sync`): trong checkout code đang đọc, Django **chỉ xử lý được**
  2 loại dữ liệu là Khách hàng và Nhân viên — Vé/Gói vé/Coupon gửi sang sẽ không được nhận đúng.
- **Django → Rails**: Rails **có sẵn code nhận** (receiver) cho chiều này — nhưng **CHƯA xác nhận được**
  Hệ thống Vé có thực sự gửi request tới đó trong môi trường hiện tại hay không (không tìm thấy code
  phía Django gọi tới, có thể do chưa triển khai, triển khai nơi khác, hoặc đã tắt). **Không khẳng định
  "có" hay "không" — cần hỏi dev.**
- → Hệ quả cho test: số dư vé/coupon hiển thị bên Hệ thống Vé **KHÔNG đáng tin làm bằng chứng test duy
  nhất** dù xét theo chiều nào, phải đối chiếu API Hệ thống Lõi (nguồn sự thật) trước.
- **Đăng nhập chéo sang Hệ thống Vé**: có cơ chế đăng nhập nhanh riêng (link đăng nhập 1 lần từ Hệ
  thống Lõi sang Hệ thống Vé) — không dùng chung phiên đăng nhập với Ứng dụng Pro.
- Chi tiết endpoint/model/dòng code/câu hỏi cần hỏi dev → đọc thẳng `SYNC_MAP.md`, đừng suy diễn lại
  từ tóm tắt này.

## Khái niệm cốt lõi
**Nguồn**: đối chiếu spec/bug thật No.10.1, No.10.5 · **Ngày đọc**: 2026/07/04–07 · **Độ ổn định**: 🟢
(khái niệm nghiệp vụ ổn định, không đổi theo release UI) · **Verify bằng**: đối chiếu spec gốc trong
`8.Tasks/specs/` của task liên quan nếu nghi ngờ.
- **締め / Kết sổ**: chốt sổ kế toán theo kỳ. Sau khi kết sổ, số liệu quá khứ KHÔNG được biến động.
  → Xóa/sửa đặt lịch đã thanh toán sau kết sổ = **mất tin cậy số dư vé + biến động tiền ngoài kiểm soát**.
  Đây là lý do gốc của No.10.5 (kiểm soát quyền sửa/xóa sau thanh toán).
- **回数券 / Ticket pack**: gói vé (vd 100 slip). Khách mua qua đặt lịch → khi **支払い済** mới cấp vé.
  Hủy thanh toán → PHẢI thu hồi vé (xử lý như **返金/refund**). *(No.10.1 đã thống nhất; bug TC-09 = chưa làm.)*
- **Trạng thái đặt lịch**: `確認待ち → 本予約 → 受付済 → 進行中 → 完了` / `キャンセル済`;
  thanh toán: `未払い → 一部支払済 → 支払い済`.

## Quy tắc nghiệp vụ đang test (No.10.5)
**Nguồn**: `8.Tasks/specs/TestCase_No.10.5/specs.md` · **Ngày đọc**: 2026/07/07 · **Độ ổn định**: 🟡
(đang trong quá trình test/fix, có thể đổi theo change/bug mới) · **Verify bằng**: đọc mục "Cập nhật
Specs" trong specs.md của task này trước khi tin — có thể đã có change mới hơn ngày đọc ở trên.
- Quyền mới điều khiển sửa/xóa **chỉ với đặt lịch「支払い済」**; `未払い`/`受付済`/quá giờ giữ nguyên.
- Màn Hóa đơn: nút thao tác giao dịch là **「キャンセル」(hủy thanh toán)** — khác nút xóa (thùng rác) ở màn Đặt lịch.

## Vì sao quan trọng khi test
- Đụng tới **tiền + vé + sổ** → mọi thao tác hủy/xóa phải kiểm **cả 3 phía**: Ứng dụng Pro (đặt lịch), hóa đơn
  (giao dịch), Hệ thống Vé (số dư vé). Chỉ nhìn UI Ứng dụng Pro là thiếu — nhất là với khoảng trống đồng bộ
  ở trên, số dư bên Hệ thống Vé có thể không đáng tin.
