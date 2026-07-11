---
id: system-coupon-sc
status: draft
kind: system-map
spans_repos: [ticket, backend, pro]
source_symbols:
  - "ticket: th/services/coupon_operation.py (CouponIssueService.issue / CouponUseService.use / reconcile_remaining_credits)"
  - "ticket: backoffice/views/coupons.py (CouponHistoryView / CouponIssueView / CouponUseView)"
  - "ticket: admin_api/data_sync/handlers.py (sync_coupon_pack / sync_coupon_sc_used / sync_coupon_sc_refunded)"
  - "backend: app/controllers/api/webhooks/threease_ticket/sync_controller.rb (handle_coupon_upserted/coupon_pack_issued/coupon_sc_used)"
source_hash: d1a56b9f9d4610a7
note: "MÔ TẢ code làm gì — KHÔNG phải oracle. Nav report ở knowledge/ticket-coupon-reports.md."
confidence: 🟢
verify_by: "Ticket-side CODE-VERIFIED 2026/07/10 (đọc coupon_operation.py + coupons.py + handlers.py trên branch develop-aiot / aiot-11). Backend reverse-sync table = derived 2026/07/08 (sync_controller.rb chưa đổi). Đọc lại khi 2 file này đổi."
grown_from: "0119159:.claude-tester/.claude-knowledge/REPORTING.md → re-derived từ code develop-aiot (aiot-11)"
---
# Domain: Coupon / SC (store credit) — ticket × backend × pro

> Coupon đếm theo **SC (store credit / クレジット)**, KHÁC 回数券 đếm theo **枚 (số vé)**.
> ✅ Ticket-side re-derived từ **code thật** (develop-aiot / aiot-11), 2026/07/10.

## Entities (ticket, verified từ code)
| Model | Vai trò | Field chính |
|---|---|---|
| `CouponPack` | 1 bản ghi phát hành (khách sở hữu) | `total_credits`, **`remaining_credits`** (cache số dư), `sales_price`/`sales_price_excluding_tax`/`sales_tax_amount`/`tax_rate`, `status` (ACTIVE/USED), `issued_at`, `pro_coupon_pack_id`, coupon/customer/branch/staff |
| `CouponTransaction` | sổ cái SC (nguồn sự thật) | `transaction_type` ∈ **CREDIT / DEBIT / REFUND**, `amount`, `coupon_pack`, `coupon_usage` |
| `CouponUsage` | 1 lượt dùng SC (FIFO qua nhiều pack) | `amount`, customer/branch/staff, `notes` |
| `Coupon` | master (cấu hình) | `sales_price`, `granted_credits`, `tax_rate`, `tax_type`, `available_quantity` |

## Cơ chế lõi (th/services/coupon_operation.py — CODE-VERIFIED)

### Phát hành — `CouponIssueService.issue()`
1. Tạo `CouponPack` (`total_credits = remaining_credits = coupon.granted_credits`, status ACTIVE).
2. Tạo `CouponTransaction(CREDIT, amount=granted_credits)`.
3. Nếu `coupon.available_quantity` không NULL → `available_quantity -= 1` (F()).
4. `on_commit` → sync sang Pro: `sync_coupon_pack_issued(pack)` (**FLOW 3B**) + `sync_coupon_upserted` (đồng bộ available_quantity).

### Dùng SC — `CouponUseService.use()` (FIFO)
1. `available = coupon_packs.usable().aggregate_remaining()`. **Nếu `amount > available` → `ValueError`** (chặn vượt số dư).
2. Tạo **1** `CouponUsage(amount)`.
3. **FIFO**: duyệt `usable().order_by_issued()` (= `order_by("issued_at","pk")`) — pack cũ trước; mỗi pack `remaining_credits -= deduct`, hết → `status=USED`.
4. Tạo **1** `CouponTransaction(DEBIT, amount)` (gộp cả lượt, `coupon_pack=None`, gắn `coupon_usage`).
5. `on_commit` → `sync_coupon_sc_used(usage)` (**FLOW 4B**).

### ⭐ `reconcile_remaining_credits(customer)` — MỚI (aiot-11), quan trọng cho FLOW 5
- **Sổ cái = nguồn sự thật**: `ledger_balance = ΣCREDIT + ΣREFUND − ΣDEBIT` (đây là con số khớp Pro).
- **Vấn đề vá**: Pro hủy thanh toán → xóa pack (+ CREDIT ledger) → khách re-pay → pack tạo lại đủ SC, nhưng DEBIT cũ còn lại → **cache `remaining_credits` lệch sổ cái**.
- **Cách vá**: `consumed = max(0, Σtotal_credits − ledger_balance)`, phân bổ theo **FIFO** (cùng thứ tự `use()`) để tính lại `remaining_credits`/`status` từng pack. **Idempotent** (khớp rồi → no-op).
- **Gọi ở**: `handlers.py` sau mỗi `sync_coupon_pack` (upsert **và** delete — capture owner trước khi xóa), `sync_coupon_sc_used`, `sync_coupon_sc_refunded`.

## History view — công thức số dư (coupons.py, aiot-11)
- `総付与クレジット (total_granted)` = **ΣCREDIT**.
- `使用済みクレジット (total_used)` = **ΣDEBIT − ΣREFUND** (net — refund do hủy thanh toán làm giảm 使用済み).
- ⇒ **`総付与 − 使用済み = 残高`** luôn đúng; khớp `remaining_credits` sau reconcile.
- `CouponIssueView`/`CouponUseView`: coupon đã **USED vẫn giữ** trong danh sách "現在保有中" (hiện券面SC), không lọc bỏ.

## Reverse-sync (Django ticket → Rails backend) — từ sync_controller (derived 2026/07/08)
| Event | Handler (Rails) | Làm gì |
|---|---|---|
| `coupon_upserted` | `handle_coupon_upserted` | upsert `Therapists::Coupon` (dual-ID `django_coupon_id`) |
| `coupon_pack_issued` | `handle_coupon_pack_issued` | tạo `Payment::CouponTransaction(credit)` (idempotent theo `django_coupon_pack_id`) |
| `coupon_sc_used` | `handle_coupon_sc_used` | tạo `Payment::CouponTransaction(debit)` (idempotent theo `django_usage_id`) |

## 発行元 vs 使用元 — hai trục ĐỘC LẬP (report)
- **発行元 (nơi bán):** `pro_coupon_pack_id IS NULL` → `店頭`; `NOT NULL` → `Pro`.
- **使用元 (nơi tiêu):** `notes LIKE '[pro]'`/`'[refunded]'` hoặc branch/staff NULL → `Pro`; còn lại → `店頭`.
- Dòng `返金 (REFUND)`: SC hiển thị **số âm** (đỏ). ⚠️ Test đừng gộp 2 trục vào 1 điều kiện.

## Điểm QA
- Quan sát: ticket-app `/customer/<id>/` (残クレジット合計) · `/coupon-ops/{issue,use}/customer/<id>/` · `/customers/<id>/coupon-history/` · report `/coupon-reports/...`. Access backoffice cần `ticket-admin`.
- **Boundary dùng SC**: vượt `available` → `ValueError` (code chặn, không chỉ HTML max).

## Ghi chú lịch sử (KHÔNG dùng làm oracle)
File gốc (REPORTING.md, 2026/07/08, `grep -i coupon` rỗng) từng khẳng định *"CouponPack/Usage/Transaction + get_coupon_metrics CHƯA TỒN TẠI"* — **SAI**: đã bị black-box bác (TestCase-11: 9 PASS) và nay đọc code thấy đủ các model/service. Giữ làm bài học *"grep không thấy ≠ không tồn tại"* (OPEN-QUESTIONS.md#OQ-01).
