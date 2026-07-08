---
id: system-coupon-sc
status: draft
kind: system-map
spans_repos: [ticket, backend, pro]
source_symbols:
  - "backend: app/controllers/api/webhooks/threease_ticket/sync_controller.rb (handle_coupon_upserted/coupon_pack_issued/coupon_sc_used)"
  - "ticket: backoffice/urls.py (coupon-reports)"
source_hash: f84cd5e8d6f4a7de
note: "MÔ TẢ code làm gì — KHÔNG phải oracle. Nav report ở knowledge/ticket-coupon-reports.md."
---
# Domain: Coupon / SC (store credit) — ticket × backend × pro

> Coupon đếm theo **SC (store credit / クレジット)**, KHÁC 回数券 đếm theo **枚 (số vé)**.

## Entities
- `CouponPack` (phát hành: `sales_price`, `total_credits`, `remaining_credits`) · `CouponUsage` + `CouponTransaction`
  (dùng/返金 SC). Pro-issued: `pro_coupon_pack_id` NOT NULL → 発行元 "Pro"; NULL → "店頭".

## Đặc thù SC (khác vé)
- **FIFO toàn tài khoản khách:** 1 lần dùng = 1 `CouponUsage` (trừ credit qua nhiều pack theo FIFO), **không gắn 1 coupon/枚 cụ thể**.
- **Thuế tính lúc MUA** (không tính lúc dùng) → report 消費 **bỏ cột thuế**.
- 手続き chỉ **使用 / 返金** (返金 = SC âm, vd Pro hủy → `[refunded] pro_tx:*`).

## Reverse-sync (Django ticket → Rails backend) — từ sync_controller
| Event | Handler | Làm gì |
|---|---|---|
| `coupon_upserted` | `handle_coupon_upserted` | upsert `Therapists::Coupon` (dual-ID `django_coupon_id`) |
| `coupon_pack_issued` | `handle_coupon_pack_issued` | tạo `Payment::CouponTransaction(credit)` cho customer (idempotent theo `django_coupon_pack_id`) |
| `coupon_sc_used` | `handle_coupon_sc_used` | tạo `Payment::CouponTransaction(debit)` (idempotent theo `django_usage_id`) |

## Report (đã black-box — TestCase-11)
- Route: `/coupon-reports/{sales,usage}/` (2 sub-tab ĐÃ build); `dashboard/timeline/branch/snapshots` = **chưa build (404)**.
- 販売: 発行SC/消化SC/残SC/消化率 + 発行元(店頭/Pro). 消費: 使用SC/使用後残高/手続き/メモ/使用元. Nav approved ở `ticket-coupon-reports.md`.

## Điểm QA
- Quan sát: ticket-app `/customer/<id>/` (残クレジット) + coupon report. Access report cần `ticket-admin`.

## Draft — cần
- Đọc ticket models `CouponPack/Usage/Transaction` + `ReportService.get_coupon_metrics` xác nhận công thức SC. source_hash (`--update`).
