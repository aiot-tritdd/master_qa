---
id: ticket-coupon-reports
status: approved
kind: flow
spans_repos: [ticket]
source_symbols:
  - "ticket: backoffice/urls.py (coupon-reports routes)"
  - "ticket: ReportService.get_coupon_metrics (CouponPack/CouponUsage/CouponTransaction)"
source_hash: efce575fd4e78cae
ui_confirmed_at: 2026-07-10
confidence: 🟢
verify_by: "Navigation UI-confirm LẠI live 2026/07/10 (probe thật ticket-dev đã deploy develop-aiot): sales/usage/timeline/branches/sales·snapshots = 200; staff = 400 (route có, cần param); dashboard = 404. route_map (code) khớp. OQ-01 coi như đóng: coupon model/service CÓ thật (coupon-sc.md code-verified)."
open_questions: [OQ-01]
grown_from: "GitNexus route_map(threease_ticket, coupon-reports) + UI-confirm (TestCase-11)"
---
# Flow: Coupon Report trên Ticket app (HOW — navigation only)

> ✅ Sinh từ **GitNexus route_map** (skeleton) + **UI-confirm** thật (TestCase-11, 2026-07-08).
> Firewall: chỉ ghi *cách vào + nơi quan sát + route nào tồn tại*. KHÔNG ghi đúng/sai (đó là SPEC).

**Access:** `getPage('ticket')` với **`TK_STAFF=ticket-admin`** (account `TESTSEED001/ticket-admin/password123`).
⚠️ Account thường (STAFF001) **KHÔNG có quyền report** → nav thiếu tab, `/reports/` redirect home.

**Route thực tế (route_map code develop-aiot + probe LIVE ticket-dev 2026/07/10):**
| Màn | Route | Live (ticket-dev) |
|---|---|---|
| チケットレポート | `/reports/` | ✅ (5 sub-tab: ダッシュボード/販売/消費/月次/店舗別) |
| クーポン・販売 | `/coupon-reports/sales/` | ✅ 200 |
| クーポン・消費 | `/coupon-reports/usage/` | ✅ 200 |
| クーポン・タイムライン | `/coupon-reports/timeline/` | ✅ 200 (**MỚI** — trước ghi "chưa build") |
| クーポン・店舗別 | `/coupon-reports/branches/` | ✅ 200 (**MỚI**) |
| クーポン・snapshot | `/coupon-reports/sales/snapshots/` (+ `/<pk>/download`) | ✅ 200 (**MỚI**) |
| クーポン・スタッフ別 | `/coupon-reports/staff/` | ⚠️ 400 (route CÓ nhưng vào trực tiếp lỗi — cần param) |
| クーポン・ダッシュボード | `/coupon-reports/dashboard/` | ❌ 404 (không có route) |
| クーポン・月次 | `/coupon-reports/monthly/` | ❌ không có trong route_map |

**Cách vào:** top-nav → 「クーポンレポート」 (chỉ hiện với ticket-admin) → landing `/coupon-reports/sales/`. ⚠️ Sub-tab bar giờ NHIỀU hơn 2 (đã thêm timeline/店舗別/snapshots) — nhãn tab cụ thể cần UI-confirm khi test tới (chỉ mới probe route, chưa chụp sub-tab bar).

**Nơi quan sát:** trực tiếp trên trang report (KPI card + bảng). 販売 = filter+KPI+販売記録; 消費 = filter+KPI+使用記録.

## Vì sao doc này giá trị (bài học TestCase-11)
Nếu tra `route_map` TRƯỚC, sẽ biết ngay chỉ `sales`+`usage` build → khỏi probe 404 mù 5-6 lượt.
→ **QA gặp report ticket lần sau: đọc doc này biết luôn route nào có, vào bằng account nào, khỏi mò.**

## Staleness
Code ticket đổi (thêm route coupon-report) → re-index → route_map đổi → cập nhật bảng route + re-confirm.
