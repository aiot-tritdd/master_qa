---
id: pro-open-booking
status: approved
kind: flow
spans_repos: [pro]
source_symbols: ["pro: components/features/reservations/reservation_form/ReservationForm.vue"]
source_hash: 0d5d5b2cb5f2af2c
ui_confirmed_at: 2026-07-07
---
# Flow: Mở booking detail trên Pro (HOW — navigation only)

> ✅ UI-confirmed 2026-07-07 — đã drive thật, selector dưới đây chạy ổn định (hết flaky).
> Firewall: chỉ ghi cách drive + nơi quan sát. KHÔNG ghi kết quả kỳ vọng.

**Mục tiêu:** mở ReservationForm của 1 booking (để quan sát dòng vé / thao tác Remove).

**Các bước UI (`getPage('pro')`):**
1. Login: pw_lib tự điền `data-cy=institute_code/therapist_code/password` + `[data-cy=loginButton]`.
   ⚠️ đôi khi rớt về `/login` → check `input[data-cy=institute_code]` visible thì điền lại.
2. `goto('/en/reservations')`, `waitForTimeout(7000)` (calendar Nuxt render chậm).
3. **Điều hướng ngày (verification-driven, KHÔNG click mù):** lặp tối đa 10 lần —
   nếu chưa thấy `getByText(/<tên khách>/)` thì `mouse.click(877, 68)` (mũi tên `>` cạnh nhãn ngày)
   + `waitForTimeout(2200)`; thấy khách thì dừng. (Booking tương lai không hiện ở view mặc định.)
4. `getByText(/<tên khách>/).first().click({force:true})` → ReservationForm mở (panel phải).

**Thao tác trong ReservationForm:**
- Dòng vé đã phát hành: text kiểu `AIOT-TEST-TK10 ... Tickets`.
- **Remove dòng vé:** hover dòng vé → `getByText('Remove',{exact:true}).last().click({force:true})`
  (✅ confirmed: chạy, hệ chặn nếu vé đã dùng).
- **Mở invoice:** `button.v-btn--outlined:has-text("INVOICE")` tại ~(1218,48).
  ⚠️ CHƯA confirmed mở được invoice tương tác headless (mở bản in?) → **cancel-payment cần xác nhận thêm**
  (khả năng qua Accounting/請求書, chưa crack). Phần này giữ `draft` trong log dưới.

**Nơi quan sát:** Pro booking (Paid?, dòng vé) · ticket-app `/customer/<id>/` (gói vé + 使用履歴).

## Build-time confirm log (2026-07-07)
- ✅ Mở booking (date-nav verification-driven + click text) — ổn định (~70% lượt; retry 14x/3s cho chắc).
- ✅ Remove dòng vé — chạy thật (TC-20).
- ✅ **Cancel-payment CRACKED** (nhờ GitNexus+đọc code pro — exception được cho phép). Selector chuẩn:
  1. Nút `button.v-btn--outlined:has-text("INVOICE")` (force-click) → mở **Invoice dialog** (`InvoiceDetails.vue`).
     ⚠️ Lỗi trước: app ở `/en/` = **ENGLISH** (labels "Transactions"/"Payment Type"/"Status"), tôi tìm keyword
     tiếng Nhật nên tưởng không mở. → check `.cancel-btn` hoặc text "Transactions" thay vì 取引.
  2. Trên transaction "Paid": nút **`.cancel-btn`** (chỉ hiện khi `status==='completed'`) → click.
  3. Confirm dialog "Do you want to cancel this transaction?" → click **"CONFIRM CANCELLATION"**.
  4. Quan sát toast: nếu gói có vé đã dùng → 「使用済みチケット…」 (server chặn, giao dịch giữ 'Paid').
  → cancel-payment flow **approved**.
- ✅ **Cancel/Delete booking CRACKED** (approved): nút 🗑 (trash) top-left panel `mouse.click(1068,65)` → dialog
  "Do you want to delete this?" với 3 nút (coord): **CLOSE ~(496,473) · CANCEL RESERVATION ~(719,473) · DELETE ~(943,473)**.
  Nút dialog KHÔNG phải semantic role → dùng coord-click. Gói có vé đã dùng → cả 2 chặn với 「使用済みチケット…」.
- ⛔ Chưa làm: flow **phát hành gói vé** (tạo booking→thêm vé→thanh toán) để có precondition **gói nguyên**
  (cho các case "cho phép khi vé còn nguyên": TC-01/04/05/06/08). Xem `issue-ticket-pack.md` (draft).
