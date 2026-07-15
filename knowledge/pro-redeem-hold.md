---
id: pro-redeem-hold
status: approved
kind: flow
spans_repos: [pro, backend, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: 2026-07-14
confidence: 🟢
verify_by: "CONFIRMED 2026-07-14 bằng DRIVE THẬT ở tầng API (endpoint sniff từ request thật của app Pro, không đọc code) + QUAN SÁT LIVE 2 phía. Đã dựng hold thật (booking 819, 822) và quan sát ticket-app phản ánh đúng (見込残 giảm, 残 giữ, nhãn 使用予定回数 xuất hiện; hủy hold → 見込残 hoàn lại). ⚠️ Click-path UI trên Pro (bấm nút nào) lấy theo MÔ TẢ CỦA DEV (chủ dự án cung cấp 2026-07-14), CHƯA click-confirm từng nút bằng explorer — phần API-dressing thì đã drive thật. Approve theo uỷ quyền của chủ dự án."
grown_from: "Dev mô tả flow (2026-07-14) → dịch sang API + drive thật + quan sát live 2 phía"
---
# Flow: Giữ chỗ vé (HOLD) — gắn vé của gói CÓ SẴN vào item dịch vụ

> ⚠️ Firewall: doc này chỉ ghi **cách vận hành + nơi quan sát**. KHÔNG ghi kết quả kỳ vọng
> / luật nghiệp vụ (đó là SPEC + quan sát live).

**Mục tiêu:** dựng trạng thái vé「Đang giữ chỗ」= booking CHƯA thanh toán có tiêu vé của gói khách đang sở hữu.

## ⚠️ PHÂN BIỆT 2 CƠ CHẾ VÉ (nhầm chỗ này = mò cả buổi, đã bị)
| | **Phát hành gói mới** | **Tiêu vé của gói CÓ SẴN (hold/redeem)** |
|---|---|---|
| Field | `reservation.reservation_tickets[]` | `reservation.reservation_items[].ticket_packs[]` |
| Payload | `{ticket_option_id, price, ...}` (bắt buộc `option_id`) | `{id: <ticket_pack_id>, quantity: n}` |
| Nghĩa | khách MUA gói mới (vé sinh ra khi thanh toán) | khách DÙNG vé gói đang có, gắn vào 1 item dịch vụ |
| Nơi xem | `issue-ticket-pack.md` | doc này |

## Các bước UI (Pro) — theo mô tả dev 2026-07-14
1. Vào Pro → đặt 1 reservation (booking mới).
2. **Add-item**: thêm 1 **dịch vụ** bất kỳ (vd course `massage2`).
3. Chọn **customer đang SỞ HỮU gói vé**.
4. **Gắn vé của customer cho item vừa add** (chọn vé của gói cho dòng dịch vụ đó).
5. **Lưu** = nút **ADD màu xanh dương** (góc trên phải form).
6. **KHÔNG thanh toán** → booking ở trạng thái chưa trả ⇒ vé vào **HOLDING**.

## Đường API tương đương — ĐÃ DRIVE THẬT (kênh ổn định, thay UI flaky)
Kênh: `pw_api.withApi` (sniff devise-token từ request thật của app).

**Tạo hold** — booking CHƯA thanh toán + item dịch vụ có `ticket_packs`:
```js
POST /branches/2/reservations
{ reservation: {
    customer_id: 700006, unit_id: 4,
    start_time: '<ISO+09:00>', end_time: '<ISO+09:00>',
    status: 'confirmed',            // chưa thanh toán -> unpaid
    reservation_type: 'reservation', source: 'pro',
    comment_customer: '', comment_staff: '',
    reservation_items: [{
      item_id: 819, product_type: 'anma_self_payment', quantity: 30,
      price: 2000, discount: 0, tax_rate: 0.1, tax_type: 'included',
      ticket_packs: [{ id: <pack_id>, quantity: 1 }]   // <-- CHỖ TẠO HOLD
    }],
    reservation_tickets: [], reservation_coupons: []
} }
// -> 201; booking payment_status=unpaid
```
**Chuyển hold → đã dùng:** thanh toán invoice của booking đó
(`GET /branches/2/reservations/{id}/invoice` → `POST /branches/2/invoices/{invoice_id}/transactions`
`{transaction:{transaction_type:'regular',method:'cash',amount_paid:<total>,return_amount:0,store_credit:0}}`).

**Trả hold về khả dụng:** hủy booking
(`PUT /branches/2/reservations/{id}` với `status:'cancelled'`).

⚠️ **PUT reservation phải STRIP field read-only** nếu không sẽ 422 `customer_name: は入力しないでください`:
`customer_name, customer_code, customer_name_kana, customer_status, customer_reservation_count,
unit_name, staff_name, prices, relations, price, total_price, paid_amount, payment_methods,
payment_status, treatment_status`.

## Nơi quan sát (2 phía)
- **Rails/Pro (API):** `GET /branches/{b}/customers/{cid}/ticket_packs` → `redeemable_count` / `slip_count`.
  `redeemable_count` = **見込残** (số khả dụng, ĐÃ trừ phần đang giữ chỗ).
- **ticket-app (Django) — kênh sự thật hiển thị:** `getPage('ticket')` →
  **warm session bằng `/customer/` trước**, rồi `/customer/<id>/` (id **trùng** id Pro, vd 700006).
  - Cột **`枚数 (見込残回数 / 残回数 / 総回数)`** trên từng gói.
  - Nhãn **`使用予定回数 ・<ngày>：<n>回`** = có vé ĐANG GIỮ CHỖ cho booking ngày đó.
  - Thống kê: **`見込残枚数合計`** vs **`残り枚数合計`** (2 tổng tách nhau).
  - Nút thao tác/gói: `返金` / `譲渡` / `使用`.

## Các flow liên quan (đã sniff, cùng phiên)
- **Dùng vé thẳng trên ticket-app:** `/customer/<id>/` → nút `使用` → trang
  `/ticket-ops/use/customer/<id>/?pack=<pack_id>`: select **チケット** (chọn gói) + `quantity` + select **担当** →
  submit `使用` → `「使用しました。」`. Sync về Rails (`redeemable_count` giảm, `used_for_service=true`).
- **Transfer (譲渡):** `/customer/<id>/` → nút `譲渡` → `/ticketpack/<pack_id>/transfer/`:
  `quantity` + `receiver` (**内部ID** người nhận) → `確認画面へ` → nút `譲渡を実行` → `「譲渡が完了しました。」`.
  Sync Rails: gói người gửi giảm, người nhận có gói mới.

## Ghi chú vận hành
- Pack issuance/reclaim/sync là **ASYNC** — chờ ~4–6s rồi mới đọc lại, đừng đọc ngay.
- Customer 700006 (AIOTTEST-KH3) là **seed dùng chung, 373+ booking** → **KHÔNG quét calendar** để tìm
  booking; luôn thao tác theo **id** qua API.
- Pro UI (Nuxt/Vuetify) flaky (customer-autocomplete ~20%/lần) → nếu buộc dùng UI thì bọc retry-loop;
  ưu tiên kênh API cho mutation.
- Dữ liệu test PHẢI prefix `AIOTTEST*` / `AIOT-TEST-*` để `/testcase-cleanup` quét được.
