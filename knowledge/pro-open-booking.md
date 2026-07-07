---
id: pro-open-booking
status: approved
kind: flow
spans_repos: [pro]
source_symbols: ["pro: components/features/reservations/reservation_form/ReservationForm.vue"]
source_hash: null
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
- ⛔ **Cancel-payment CHƯA CRACK được headless.** Đã thử & đều TRƠ (không mở invoice tương tác có 取引/キャンセル):
  - Nút `button.v-btn--outlined:has-text("INVOICE")` (1218,48): force-click, real-click, coord-click → không mở gì, không tab mới, không dialog invoice.
  - Chip `Paid (Cash)` → trơ.
  - `View Invoice` (cuối panel, cần scroll drawer) → force-click trơ; scrollIntoView không tới.
  → **Cần headed-session** (người thấy + click chính xác, scroll drawer tới View Invoice) HOẶC biết **route invoice**
    (vd `/en/accounting` → 請求書 → 取引 キャンセル) để crack. Headless-blind không đủ.
  → cancel-payment flow giữ **draft**; các case Part A/B (cancel payment / cancel booking) chưa run được.
