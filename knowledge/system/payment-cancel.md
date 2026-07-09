---
id: system-payment-cancel
status: draft
kind: system-map
spans_repos: [pro, backend, ticket]
source_symbols:
  - "backend: app/services/payment/invoice_items_update_service.rb"
  - "backend: app/use_cases/therapists/branch/reservations/destroy_case.rb"
  - "backend: app/use_cases/therapists/branch/reservations/update_case.rb"
  - "backend: app/controllers/api/webhooks/threease_ticket/sync_controller.rb (handle_pack_cancelled)"
  - "pro: components/features/invoices/TransactionDetails.vue"
  - "pro: components/features/reservations/reservation_form/ReservationForm.vue"
source_hash: 84418ad68623e2bd
note: "MÔ TẢ code làm gì — KHÔNG phải oracle. Navigation approved ở knowledge/pro-open-booking.md."
confidence: 🟢
verify_by: "Guard 'vé đã dùng' đã black-box verify. Navigation chi tiết → knowledge/pro-open-booking.md (approved)."
---
# Domain: Payment / Invoice + Cancel/Delete + Remove vé (Pro × backend × ticket)

> 4 thao tác "ngược" trên booking đã phát hành gói vé: **Cancel payment · Hủy booking · Xóa booking · Remove vé**.
> Tất cả có **guard "vé đã dùng"** (UI-confirm phiên 2026-07-08).

## Entities
- `Invoice` + `Transaction` (status: completed/cancelled) · `ReservationTicket`/`Tickets::Pack` (gói vé phát hành).

## 4 thao tác + nơi bấm (navigation chi tiết → `knowledge/pro-open-booking.md` approved)
| Thao tác | UI (Pro) | Backend |
|---|---|---|
| **Cancel payment** | booking → INVOICE → dialog Invoice → `.cancel-btn` trên 取引 → CONFIRM CANCELLATION | `TransactionDetails.updateTransaction(status:'cancelled')` · `Payment::InvoiceItemsUpdateService` |
| **Hủy booking (Cancel)** | trash 🗑 → dialog → CANCEL RESERVATION | `UpdateCase` (status=cancelled) → invoice update |
| **Xóa booking (Delete)** | trash 🗑 → dialog → DELETE | `DestroyCase` (soft-delete deleted_at + release slips + sync_remaining) |
| **Remove vé** | booking → hover dòng vé → Remove | (guard chặn nếu vé đã dùng) |

## Guard "vé đã dùng" — HÀNH VI THẬT (black-box verified)
- Gói vé có ≥1 vé đã dùng → **CHẶN cả 4 thao tác** + thông báo.
- **Message:** Cancel payment / Hủy / Xóa → nguyên văn `使用済みチケットが含まれているため、支払キャンセル・削除はできません。` ✅
  **Remove → lộ RAW i18n key** `reservations.used_ticket_cannot_remove` ❌ (BUG — dev cần dịch key).
- ⚠️ **Guard NÀY code-trace GitNexus KHÔNG thấy** (Rails index yếu — từng kết luận SAI "chưa build").
  → chỉ black-box mới xác nhận đã build + chạy đúng.

## Sync sang ticket (khi thu hồi)
`handle_pack_cancelled` (webhook Django→Rails) → `Tickets::Pack.destroy`. Recall gói vé → `ThreeaseTicketSyncJob` sync.

## Điểm QA (precondition)
- Cần booking **đã thanh toán + có gói vé phát hành**. Vé **còn nguyên** → thao tác cho phép (thu hồi+sync);
  vé **đã dùng** → bị chặn. Test data: `AIOTTEST-KH3` (gói 8/10 = có vé đã dùng → dùng test nhánh CHẶN).

## Draft — cần
- Đọc code xác nhận đủ nhánh recall (intact) + refund record. source_hash (chạy `--update`).
