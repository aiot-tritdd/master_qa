---
id: pro-sc-pay-cancel
status: draft
kind: flow
spans_repos: [pro, backend, ticket]
source_symbols:
  - "pro: components/features/reservations/reservation_form/ReservationForm.vue (請求書/Invoice + Transactions)"
  - "ticket: admin_api/data_sync/handlers.py (sync_coupon_sc_used / sync_coupon_sc_refunded)"
source_hash: null
ui_confirmed_at: 2026-07-10
confidence: 🟡
verify_by: "Bước ⑴ mở 請求書 + ⑶ HỦY transaction + ⑷ quan sát Ticket 返金 = ĐÃ UI-confirm live 2026/07/10 (drive thật, locale ja-JP, khách PHUOC/院3, TC-26 PASS). Bước ⑵ THANH TOÁN BẰNG SC = dev dựng sẵn, selector CHƯA tự đo → còn draft. Muốn tự dựng precondition đầu-cuối thì cần confirm nốt ⑵."
grown_from: "/testcase-systemdoc pro-sc-pay-cancel — spec FLOW 4A/5 + pro-open-booking + GitNexus (ticket-side sync_coupon_sc_refunded)"
---
# Flow: Pro — thanh toán invoice bằng SC + hủy payment (HOW — navigation only)

> Mục tiêu: dựng precondition cho **FLOW 5 / TC-26** = 1 Invoice **Paid** đã dùng SC trên Pro, rồi **hủy** payment transaction đó để quan sát **hoàn SC** đồng bộ sang Ticket.
> ⚠️ **DRAFT** — mới có navigation tới bước mở 請求書 (từ `pro-open-booking`, approved). Các bước ⑵⑶ dưới lấy từ **spec mockup**, selector **CHƯA** UI-confirm.

## Điều kiện cần
- Khách có **số dư SC trên Pro** (SC đồng bộ Ticket→Pro khi phát hành coupon — xem TC-24). 
- 1 booking có **hóa đơn chưa thanh toán** (có item để trả tiền).

## ⑴ Mở hóa đơn (✅ đã confirm — theo `pro-open-booking.md`)
`getPage('pro')` (locale ja-JP) → `/reservations` (chờ ~7s) → điều hướng ngày (`.mdi-chevron-right` .first(), verification-driven) tới khách → click tên khách → ReservationForm mở panel phải → `button:has-text("請求書")` mở hóa đơn.

## ⑵ Thanh toán bằng SC (🔴 spec FLOW 4A — CHƯA UI-confirm)
Trên panel Invoice (spec mockup):
- Có ô **「Use Store Credit / ストアクレジット使用」** — nhập số SC dùng (spec: "Maximum applicable" = số dư SC khách).
- **Select Payment Method** (Cash/Card) → nút **Payment / 支払** → Invoice chuyển **Paid**.
- Sau thanh toán, bảng **Transactions** có dòng payment với **`ポイント: <số SC>`** (đây là giao dịch SC sẽ hủy ở bước ⑶).
- *(Selector thật cần đo: ô Use Store Credit, nút Payment, cột Transactions.)*

## ⑶ Hủy payment transaction (✅ UI-confirm 2026/07/10, ja-JP)
- Mở booking (院3, khách PHUOC) → ReservationForm → `button:has-text("請求書")` mở modal Invoice.
- Trong modal, bảng **Transactions** có dòng payment với **`ポイント: <SC>`** → dòng đó có nút **「キャンセル」** (locale ja-JP; bản EN = `CANCEL`). Bấm → (nếu có dialog) xác nhận.
- **Kết quả quan sát:** transaction → **キャンセル済**, invoice → **未払** (về chưa thanh toán). SC được hoàn + đồng bộ sang Ticket.
- ⚠️ Store Pro **không giữ** qua các phiên script → phải đổi store về đúng 院 **trong cùng script** (click `院X ▾` top-left → chọn `院3`) rồi mới mở booking.

## ⑷ Nơi quan sát hoàn SC (✅ UI-confirm 2026/07/10)
Trên Ticket (STAFF001, **đổi institute về 院3** qua `<select>` top): `/customers/<id>/coupon-history/`:
- Thêm dòng **入金（返金）** với 備考 **「Proキャンセル返金」**, SC変動 = **+X**.
- **使用済みクレジット giảm X** (使用済み = ΣDEBIT − ΣREFUND), **残クレジット合計 tăng X**.
- (Ví dụ TC-26: 出金 -1,400 → sau cancel: 入金返金 +1,400, 使用済み 1,400→0, 残 3,600→5,000.)

## Ghi chú build-time (KHÔNG dùng làm oracle)
Cơ chế phía ticket đã verify code (develop-aiot): `handlers.py sync_coupon_sc_refunded` tạo `CouponTransaction(REFUND)` + gọi `reconcile_remaining_credits`. Chi tiết ở `knowledge/system/coupon-sc.md`.

## Việc còn lại để approved (bước 3–4 /testcase-systemdoc)
1. Drive live 1 vòng ⑵⑶ → đo selector thật (Use Store Credit / Payment / delete-transaction).
2. Điền `ui_confirmed_at`, đổi `status: draft → approved`.
3. Rồi QA-runtime dùng doc này dựng precondition + chạy **TC-26**.
