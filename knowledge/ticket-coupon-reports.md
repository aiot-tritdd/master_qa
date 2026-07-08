---
id: ticket-coupon-reports
status: approved
kind: flow
spans_repos: [ticket]
source_symbols:
  - "ticket: backoffice/urls.py (coupon-reports routes)"
  - "ticket: ReportService.get_coupon_metrics (CouponPack/CouponUsage/CouponTransaction)"
source_hash: null
ui_confirmed_at: 2026-07-08
grown_from: "GitNexus route_map(threease_ticket, coupon-reports) + UI-confirm (TestCase-11)"
---
# Flow: Coupon Report trên Ticket app (HOW — navigation only)

> ✅ Sinh từ **GitNexus route_map** (skeleton) + **UI-confirm** thật (TestCase-11, 2026-07-08).
> Firewall: chỉ ghi *cách vào + nơi quan sát + route nào tồn tại*. KHÔNG ghi đúng/sai (đó là SPEC).

**Access:** `getPage('ticket')` với **`TK_STAFF=ticket-admin`** (account `TESTSEED001/ticket-admin/password123`).
⚠️ Account thường (STAFF001) **KHÔNG có quyền report** → nav thiếu tab, `/reports/` redirect home.

**Route thực tế (GitNexus route_map — nguồn chính xác cho "đã build hay chưa"):**
| Màn | Route | Trạng thái (route_map) |
|---|---|---|
| チケットレポート | `/reports/` | ✅ có (5 sub-tab: ダッシュボード/販売/消費/月次/店舗別) |
| クーポン・販売 | `/coupon-reports/sales/` | ✅ có |
| クーポン・消費 | `/coupon-reports/usage/` | ✅ có |
| クーポン・ダッシュボード/月次/店舗別/snapshots | `/coupon-reports/{dashboard,timeline,branch,snapshots}/` | ❌ **KHÔNG có route** (route_map chỉ trả 2) → chưa build |

**Cách vào:** top-nav → 「クーポンレポート」 (chỉ hiện với ticket-admin) → landing `/coupon-reports/sales/`; sub-tab bar có **販売 | 消費** (2 tab).

**Nơi quan sát:** trực tiếp trên trang report (KPI card + bảng). 販売 = filter+KPI+販売記録; 消費 = filter+KPI+使用記録.

## Vì sao doc này giá trị (bài học TestCase-11)
Nếu tra `route_map` TRƯỚC, sẽ biết ngay chỉ `sales`+`usage` build → khỏi probe 404 mù 5-6 lượt.
→ **QA gặp report ticket lần sau: đọc doc này biết luôn route nào có, vào bằng account nào, khỏi mò.**

## Staleness
Code ticket đổi (thêm route coupon-report) → re-index → route_map đổi → cập nhật bảng route + re-confirm.
