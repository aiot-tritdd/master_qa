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
confidence: 🔴
verify_by: "Phần Coupon/SC theo SPEC No.11, CHƯA verify code. ⚠️ Claim 'coupon chưa tồn tại' đã bị black-box bác bỏ (9 PASS) — xem OPEN-QUESTIONS.md#OQ-01."
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

---

## 📥 Nhập từ `.claude-tester/.claude-knowledge/REPORTING.md` (2026-07-09, cửa WHAT)
> `grown_from: .claude-tester/.claude-knowledge/REPORTING.md` · ⛔ **QA-runtime CẤM đọc mục này.**

### ☠️ CẢNH BÁO PHẢN CHỨNG — đọc trước khi tin bất cứ dòng nào dưới đây
File gốc khẳng định (2026/07/08, phương pháp = `grep -i coupon` trên `threease_ticket/th/models/` → rỗng):
> *"`CouponPack`/`CouponUsage`/`CouponTransaction` và `ReportService.get_coupon_metrics()`
> **CHƯA TỒN TẠI TRONG CODE**."*

**Khẳng định này ĐÃ BỊ BÁC BỎ bằng quan sát live cùng ngày:** `TestCase-11` chạy black-box ra
**9 PASS / 8 FAIL**, khớp 100% list dev khai. Một tính năng "không tồn tại" không thể có 9 case PASS.
→ `grep` không thấy **≠** không tồn tại. Xem `OPEN-QUESTIONS.md#OQ-01` · `docs/SYSTEM-COMPARISON.md` Phần III.
**Giữ lại đây làm tư liệu build-time (để đi hỏi dev), TUYỆT ĐỐI không dùng làm oracle.**

### Model theo spec No.11 (🔴 theo spec, chưa verify code)
| Model | Vai trò | Field |
|---|---|---|
| `CouponPack` | bản ghi phát hành | `sales_price`, `sales_price_excluding_tax`, `sales_tax_amount`, `total_credits`, `remaining_credits`, `status`, `pro_coupon_pack_id` |
| `CouponUsage` | 1 lượt dùng SC (FIFO qua nhiều pack) | liên kết `CouponTransaction`, `notes` |
| `CouponTransaction` | giao dịch debit/refund SC | phân biệt 使用 (debit) vs 返金 (refund) |

### Thuế (🔴 theo spec)
- `税込` = `sales_price` (khách trả thật) · `税抜` = `sales_price_excluding_tax` ·
  `消費税額` = `sales_tax_amount` (**đọc thẳng field, không tự tính % — tránh lệch làm tròn**).
- Thuế chỉ tính **khi MUA coupon** (tab 販売). **Khi DÙNG SC (tab 消費) KHÔNG tính thuế lại.**
- `消化率` = `消化SC ÷ 発行SC × 100` (tính từ 2 field, không phải field riêng).
- ✅ Fact đã verify: `Tickets::Pack` (KHÔNG phải Coupon) có thật 2 field
  `sales_price_excluding_tax`/`sales_tax_amount` — `threease_ticket/th/models/tickets.py:708,715`.

### 発行元 vs 使用元 — hai trục ĐỘC LẬP (🔴 theo spec)
- **発行元 (nơi bán):** `pro_coupon_pack_id IS NULL` → `店頭`; `NOT NULL` → `Pro`
  (đồng bộ từ `ReservationCoupon`; khi đó cột 店舗名/販売スタッフ trống).
- **使用元 (nơi tiêu):** `notes LIKE '[pro]'`/`'[refunded]'` hoặc `branch/staff = NULL` → `Pro`; còn lại → `店頭`.
- Dòng `返金`: SC hiển thị **số âm** (đỏ), memo `[refunded] pro_tx:*`.
- ⚠️ Viết test case **đừng gộp 2 trục vào 1 điều kiện**.
