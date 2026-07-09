# FEATURES — Sổ tay tính năng (kinh nghiệm dùng thật)

> Góc nhìn người dùng/tester: tính năng này dùng để làm gì, vào đâu, chuẩn bị data thế nào.
> Khác `.claude-tester/knowledge/SYSTEM.md` (fact khô: route/endpoint/selector) và
> `.claude-tester/knowledge/PLAYBOOK.md` (công thức thao tác kỹ thuật) — 2 file đó **chỉ tồn tại bên
> `.claude-tester/`**, KHÔNG có trong `.claude-task/knowledge/` (file này là shared, đọc từ cả 2 phía).
> Mỗi tính năng test lần đầu → thêm 1 mục theo khung dưới. Không cần viết hết 1 lần.
> Fact confidence: mỗi mục nên có 1 dòng **Nguồn** (spec/code đã đọc) · **Ngày đọc** · **Độ ổn định**
> (⭐/🟢/🟡/🔴) · **Verify bằng** (cách tự kiểm khi nghi ngờ) — xem ví dụ ở 3 mục dưới.

## Khung mẫu (copy khi thêm tính năng mới)
```
## <Tên tính năng>
- **Vào đâu**: route + đường bấm (menu/nút) tới đó
- **Mục đích / luồng chính**: 2-4 bước theo đúng thứ tự thao tác thật
- **Chuẩn bị data trước khi test**: cần gì (khách hàng/preset/quyền…), cách tạo nhanh
- **Phụ thuộc**: chức năng/màn hình nào bị ảnh hưởng qua lại
- **Bẫy hay gặp khi thao tác**: quen tay (không phải bug) — nút dễ nhầm, thứ tự bấm sai bị kẹt UI…
- **Liên kết**: [[DOMAIN.md]] (shared) · `.claude-tester/knowledge/SYSTEM.md` (tester-only, nếu áp dụng)
  · `.claude-tester/knowledge/PLAYBOOK.md` (tester-only, nếu áp dụng)
```

---

## Đặt lịch có mua vé (回数券) — No.10.1 / No.10.5
Nguồn: spec No.10.1/10.5 + test thật · Ngày đọc: 2026/07/07 · Ổn định: 🟢 · Verify bằng: chạy lại
`/testcase-run` case liên quan nếu nghi thay đổi.
- **Vào đâu**: `/reservations` → tạo đặt lịch → thêm item vé.
- **Mục đích / luồng chính**:
  1. Tạo đặt lịch + thêm item vé → trạng thái `未払い`.
  2. Mở「請求書」→ thanh toán đủ (現金) → `支払い済` → khách được cấp vé (0 → N slip).
  3. Kiểm số dư vé qua API `GET /branches/{b}/customers/{c}/ticket_packs`.
- **Chuẩn bị data trước khi test**: cần khách hàng test + item vé (Linh ticket) có sẵn trong hệ thống.
- **Phụ thuộc**: Kế toán (giao dịch), Hệ thống Vé (số dư vé — đồng bộ có khoảng trống, KHÔNG tin số dư
  hiển thị bên Hệ thống Vé làm bằng chứng, xem [`SYNC_MAP.md`](SYNC_MAP.md)).
- **Bẫy hay gặp khi thao tác**: hủy thanh toán dùng nút「キャンセル」trên dòng giao dịch (màn Hóa đơn),
  KHÁC nút xóa (thùng rác) ở màn Đặt lịch — dễ nhầm 2 nút này vì tác dụng khác nhau.
- **Liên kết**: [[DOMAIN.md#回数券--ticket-pack]] (shared) ·
  `.claude-tester/knowledge/PLAYBOOK.md#tạo-đặt-lịch支払い済-có-vé` (tester-only) ·
  `.claude-tester/knowledge/LESSONS.md` (tester-only)

## Quyền / Preset (権限設定)
Nguồn: test thật No.10.5 · Ngày đọc: 2026/07/07 · Ổn định: 🟢 · Verify bằng: mở màn hình trực tiếp,
UI ít khi đổi cấu trúc preset/staff.
- **Vào đâu**: `/clinic_setting/permissions` — bảng preset + bảng gán staff.
- **Mục đích / luồng chính**: tạo preset quyền → gán preset cho staff → preset quyết định staff thấy/thao tác được gì.
- **Chuẩn bị data trước khi test**: preset **mặc định** không sửa được ô quyền (disabled) → phải tạo preset mới
  (`AIOT-TEST-*`) rồi gán cho staff test (`AIOTTEST*`) mới bật/tắt được quyền để test ẩn/hiện nút.
- **Phụ thuộc**: mọi màn hình có kiểm soát quyền theo preset (Kế toán, Đặt lịch…).
- **Bẫy hay gặp khi thao tác**: quên là preset mặc định disabled → tưởng bug khi không sửa được.
- **Liên kết**: `.claude-tester/knowledge/SYSTEM.md#selector-ui-vuetify` (tester-only) ·
  `.claude-tester/knowledge/PLAYBOOK.md#gán-quyền-để-test-ẩnhiện-nút` (tester-only)

## Hóa đơn / Kế toán (会計)
Nguồn: test thật No.10.5 · Ngày đọc: 2026/07/07 · Ổn định: 🟢 · Verify bằng: chạy lại case liên quan
`支払い済`/hủy giao dịch nếu nghi ngờ hành vi đổi.
- **Vào đâu**: `/accounting` — tab 取引履歴 (lịch sử giao dịch) / 予約履歴 (lịch sử đặt lịch); hóa đơn mở qua
  nút「請求書」trong chi tiết đặt lịch.
- **Mục đích / luồng chính**: xem/thao tác giao dịch thanh toán gắn với đặt lịch; hủy giao dịch bằng nút
  「キャンセル」(không xóa hẳn, chuyển trạng thái `cancelled`).
- **Chuẩn bị data trước khi test**: cần đặt lịch đã ở trạng thái có giao dịch (`支払い済`/`一部支払済`).
- **Phụ thuộc**: Đặt lịch (booking), Hệ thống Vé (số dư vé nếu giao dịch có mua vé — xem `SYNC_MAP.md`
  về độ tin cậy đồng bộ), 締め (kết sổ — sau kết sổ số liệu quá khứ không được biến động).
- **Bẫy hay gặp khi thao tác**: dialog hủy có 2 nút gần giống nhau (閉じる = đóng, キャンセル = hành động hủy
  thật) — bấm nhầm 閉じる tưởng đã hủy nhưng chưa.
- **Liên kết**: [[DOMAIN.md#khái-niệm-cốt-lõi]] (shared) ·
  `.claude-tester/knowledge/LESSONS.md` (tester-only)

## Báo cáo Coupon/Ticket (レポート) — No.11, đang làm
Nguồn: `8.Tasks/specs/TestCase_No.11.Report/specs.md` · Ngày đọc: 2026/07/08 · Ổn định: 🟡 (spec đang
review, có điểm chưa rõ) · Verify bằng: đọc mục 4 "Cập nhật Specs" của specs.md trước khi tin.
- **Vào đâu**: Hệ thống Vé (Django backoffice) → `/reports` (Ticket, có sẵn) sắp thêm `/coupon-reports/`.
- **Mục đích / luồng chính**: xem chi tiết đầy đủ ở [`REPORTING.md`](REPORTING.md) — khác bản chất
  giữa báo cáo Ticket (số lượt) và Coupon (SC/store credit, tiêu theo FIFO toàn tài khoản).
- **Chuẩn bị data trước khi test**: cần `CouponPack`/`CouponUsage`/`CouponTransaction` có dữ liệu mẫu
  đủ cả 発行元 (店頭/Pro) và 使用元 (店頭/Pro) để test đúng ma trận phân loại.
- **Phụ thuộc**: Hệ thống Lõi (`ReservationCoupon` nếu phát hành từ Pro), tính thuế lúc mua coupon.
- **Bẫy hay gặp khi thao tác**: đừng nhầm 発行元 (nơi bán) với 使用元 (nơi tiêu) — 2 trục độc lập.
- **Liên kết**: [`REPORTING.md`](REPORTING.md) · [[DOMAIN.md]]
