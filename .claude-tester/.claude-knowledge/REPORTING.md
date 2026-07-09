# REPORTING — Báo cáo / Export / Tính tiền-thuế-coupon (Hệ thống Vé)

> Gom lại các điều tra report/tax/coupon đã làm (No.11 và trước đó), để không phải grep/điều tra lại
> từ đầu mỗi lần có task liên quan báo cáo. Nguồn chính: `8.Tasks/specs/TestCase_No.11.Report/specs.md`
> (đọc 2026/07/08, độ ổn định 🟡 — đây là **spec cho tính năng đang làm**, có thể đổi khi review).
>
> ⚠️ **Đã verify code (2026/07/08)**: `grep -i coupon` trên `threease_ticket/th/models/` ra **RỖNG** —
> `CouponPack`/`CouponUsage`/`CouponTransaction` và `ReportService.get_coupon_metrics()` ở dưới đây
> **CHƯA TỒN TẠI TRONG CODE**, toàn bộ là **tên đề xuất trong spec (No.11 chưa code)**, KHÔNG phải
> hành vi đã implement. Model `Tickets::Pack` (tương tự Ticket, KHÔNG phải Coupon) thì có thật, chứa
> field `sales_price_excluding_tax`/`sales_tax_amount` (xác nhận tại
> [`tickets.py:708`](/Applications/Workspaces/threease/threease_ticket/th/models/tickets.py:708), field thứ 2 ở dòng 715)
> — spec No.11 có vẻ **mượn đặt tên tương tự** cho Coupon nhưng chưa build. Toàn bộ mục dưới đây đọc
> với tinh thần "theo spec, chưa verify code" trừ khi ghi rõ khác.

## Bối cảnh: 2 loại báo cáo khác bản chất nhau
**Nguồn**: `8.Tasks/specs/TestCase_No.11.Report/specs.md` mục 1 · Ngày đọc: 2026/07/08 · Ổn định: 🟢
(khái niệm nghiệp vụ, ít đổi hơn UI report).

- **チケットレポート (báo cáo Ticket/vé)** — màn hình sẵn có ở `/reports` (Hệ thống Vé), quản lý theo
  **số lượt (枚数)**.
- **クーポンレポート (báo cáo Coupon)** — đang được thêm mới (No.11), route đề xuất `/coupon-reports/`,
  quản lý theo **SC (ストアクレジット / store credit)** — khác hẳn cơ chế Ticket:
  - Nạp SC khi mua coupon (`CouponPack.total_credits`).
  - Tiêu SC theo **FIFO trên toàn tài khoản khách hàng** — KHÔNG gắn với 1 coupon cụ thể (khác Ticket,
    vốn tiêu theo từng gói/slip riêng biệt).

## Nguồn dữ liệu (model) cho báo cáo Coupon — 🔴 THEO SPEC, CHƯA VERIFY CODE (model chưa tồn tại)
| Model | Vai trò | Field quan trọng |
|---|---|---|
| `CouponPack` | Bản ghi phát hành coupon | `sales_price`, `sales_price_excluding_tax`, `sales_tax_amount`, `total_credits`, `remaining_credits`, `status` (active/used), `pro_coupon_pack_id` |
| `CouponUsage` | 1 lượt dùng SC (FIFO qua nhiều CouponPack) | liên kết `CouponTransaction`, `notes` |
| `CouponTransaction` | Giao dịch debit/refund SC | dùng phân biệt 使用 (debit) vs 返金 (refund) |

## Logic tính tiền/thuế — 🔴 THEO SPEC, CHƯA VERIFY CODE (đây là spec đề xuất, tránh suy đoán thêm
ngoài spec, nhưng cũng KHÔNG coi là hành vi đã chạy thật cho tới khi có code Coupon)
- **税込 (có thuế)**: `CouponPack.sales_price` — số tiền khách trả thực tế.
- **税抜 (chưa thuế)**: `sales_price_excluding_tax`.
- **消費税額 (tiền thuế)**: `sales_tax_amount` — cột riêng, không tự tính lại bằng công thức % (đọc
  thẳng field này để tránh sai lệch làm tròn).
- **Quan trọng**: thuế chỉ tính **khi MUA coupon** (ở tab 販売/bán) — khi **DÙNG SC** (tab 消費/tiêu thụ)
  **KHÔNG tính thuế lại** (cột thuế bị bỏ hẳn ở bảng 使用記録). Nếu thấy UI có radio 税込/税抜ở tab 消費
  mà tưởng nó ảnh hưởng số liệu — *(cần làm rõ logic, spec ghi nhận đây là điểm chưa rõ, actual dev
  trả lời)*.
- **消化率 (tỷ lệ tiêu thụ)** = 消化SC ÷ 発行SC × 100 (tính từ 2 field khác, không phải field riêng).

## Phân biệt nguồn phát hành/tiêu thụ (店頭 vs Pro) — 🔴 THEO SPEC, CHƯA VERIFY CODE — hay nhầm khi test
- **発行元 (nơi bán)**: `pro_coupon_pack_id IS NULL` → **店頭** (bán trực tiếp qua Hệ thống Vé);
  `NOT NULL` → **Pro** (đồng bộ từ `ReservationCoupon` bên Ứng dụng Pro) — khi đó cột 店舗名/販売スタッフ
  hiển thị trống vì giao dịch gốc không thuộc chi nhánh nào trong Hệ thống Vé.
- **使用元 (nơi tiêu — KHÁC nơi bán)**: xác định qua `notes LIKE '[pro]'`/`'[refunded]'` hoặc
  `branch/staff = NULL` → **Pro**; còn lại → **店頭**. Đây là 2 trục độc lập (nơi bán ≠ nơi tiêu) —
  khi viết test case đừng gộp chung 1 điều kiện.
- Dòng **返金 (refund)**: SC hiển thị **số âm** (đỏ), memo dạng `[refunded] pro_tx:*`.

## Cấu trúc màn hình báo cáo Coupon (No.11, đang làm — verify lại UI thật trước khi mockup/test)
- 2 sub-tab: **販売** (bán) / **消費** (tiêu thụ) — KHÔNG có dashboard/tháng/theo cửa hàng ở phase 1.
- Tab 販売: filter (kỳ, chi nhánh bán, coupon, khoảng 残SC, hạn dùng, staff bán, 発行元, hiển thị
  税込/税抜) + 8 KPI card + bảng phân trang 50 dòng/trang + nút CSV export.
- Tab 消費: filter (kỳ, chi nhánh dùng, staff xử lý, loại thủ tục: 使用/返金, 使用元, hiển thị
  税込/税抜) + 3 KPI card + bảng phân trang + CSV export.
- Backend dự kiến: `ReportService.get_coupon_metrics()` — **đã verify: KHÔNG có trong code**
  ([`reports.py:101`](/Applications/Workspaces/threease/threease_ticket/th/services/reports.py:101)
  `class ReportService`, có 18 method, `grep -i coupon` ra rỗng — chỉ có method cho Ticket). Đây là
  tên hàm đề xuất trong spec, chưa tồn tại. Verify lại bằng: `rg -i coupon threease_ticket/th/services/reports.py`.

## Điểm chưa rõ (spec đã đánh dấu, KHÔNG tự suy đoán khi test/mockup)
1. KPI「消化SC」ở tab 販売: lọc theo kỳ **mua** hay kỳ **dùng**? (mockup có 2 tab ra cùng 1 số
   414,400 — nghi ngờ đang tính sai hoặc trùng do dùng chung 1 query).
2. Radio 表示形式 税込/税抜 ở tab 消費 có tác dụng thật không, khi cột thuế đã bị bỏ khỏi bảng đó?

## Liên kết
- Spec đầy đủ (nguồn chính, có changelog cập nhật): `8.Tasks/specs/TestCase_No.11.Report/specs.md`
- Investigation gốc (ước lượng effort, tiếng Nhật): `Investigations/no11_coupon_report_2reports_estimation_ja.html`
- Thuật ngữ business dùng khi viết report cho khách: [`DOMAIN.md`](DOMAIN.md)
- Nếu cần mockup màn hình report: **`UI_UX.md` chưa khảo sát Hệ thống Vé** (chỉ có 4 app Nuxt/Flutter,
  không có Django/HTMX) — ưu tiên đọc thẳng template `.html`/`.py` trong `threease_ticket/` thay vì suy
  đoán theo bảng màu Vuetify của 3 app kia (khác nền tảng hoàn toàn).
