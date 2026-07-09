---
id: system-overview
status: draft
kind: system-map
spans_repos: [backend, ticket, pro, admin, reservation]
source: "GitNexus (5 repo index) + /Users/tritdd/Work/ThreeSides/CLAUDE.md + UI-confirm (phiên 2026-07)"
note: "MÔ TẢ code/hệ thống đang LÀM GÌ — KHÔNG phải oracle. Oracle = SPEC từng feature. ⛔ QA-runtime CẤM ĐỌC file này (và cả thư mục system/)."
source_hash: null
confidence: 🟡
verify_by: "Chạy list_repos + route_map (build-time). Số processes/nodes đo lại nếu nghi ngờ."
---
# System Business Map — ThreeSides (backbone để hiểu toàn hệ)

> Bản đồ **domain × flow × repo** của cả hệ. Mỗi domain sẽ có 1 file deep-dive `knowledge/system/<domain>.md`
> (dựng dần). File này là mục lục + wiring xuyên hệ. **draft** — grow/duyệt dần.

## Kiến trúc (nhắc — chi tiết ở /Users/tritdd/Work/ThreeSides/CLAUDE.md)
```
pro(Nuxt,8080) ─┐
admin(Nuxt,8081)├─HTTP▶ backend(Rails,3000, HUB) ─HTTP▶ ticket(Django,8000)
reservation ────┘        (mọi FE gọi hub)          (backend↔ticket đồng bộ 2 chiều HMAC)
(Nuxt,8082)
```
⚠️ Link là **HTTP**, không phải call-graph gộp. GitNexus **0 auto-link** cross-repo (§3) → wiring dưới lấy từ CLAUDE.md + UI-confirm.

## Danh mục DOMAIN (× repo × trạng thái hiểu biết)
| # | Domain | Repo chính | Trạng thái knowledge |
|---|---|---|---|
| 1 | **Customer/Master sync** (customer/institute/branch/staff) backend↔ticket | backend+ticket | 🟢 rõ (CLAUDE.md §8) — cần file deep-dive |
| 2 | **Ticket issue + sync** (Pro thanh toán → phát hành gói vé → sync ticket) | backend+pro+ticket | 🟢 deep-dive `system/ticket-issue-sync.md` (nav phát hành `issue-ticket-pack` draft) |
| 3 | **Payment / Invoice + Cancel** (cancel payment/booking/delete, guard vé-đã-dùng) | pro+backend | 🟢 deep-dive `system/payment-cancel.md` + nav `pro-open-booking` approved |
| 4 | **Coupon / SC** (CouponPack/Usage/Transaction, FIFO, reverse-sync Pro↔ticket) | ticket+backend+pro | 🟢 deep-dive `system/coupon-sc.md` + nav `ticket-coupon-reports` |
| 5 | **Reports** (ticket report + coupon report) | ticket | 🟢 route rõ (route_map) — `ticket-coupon-reports` approved |
| 6 | **Booking lifecycle** (tạo/xác nhận/hủy/xóa reservation) | pro+backend | 🟡 mở/hủy/xóa UI-confirmed; tạo mới chưa |
| 7 | **Reservation widget** (đặt lịch public → backend) | reservation+backend | 🔴 chưa đụng — `processes=0` → skeleton bằng `definitions` + **UI-confirm**. ✅ hết chặn (OQ-02 đóng: `reservation-dev.threease.com` sống) |
| 8 | **Admin panel** (super-admin) | admin+backend | 🔴 chưa đụng — `processes=0` → skeleton bằng `route_map` (20 route) + **UI-confirm**. ✅ hết chặn (`admin-dev.threease.com` sống) |

Chú: 🟢 hiểu tốt · 🟡 một phần · 🔴 chưa.

## ⚠️ Ngân sách GitNexus thật (đo `list_repos` 2026-07-09) — đừng kỳ vọng sai

| Repo | processes | nodes | Dùng được gì |
|---|---:|---:|---|
| backend | 227 | 15 813 | `query` → call-chain |
| ticket | 130 | 2 449 | `query` → call-chain |
| pro | 116 | 11 729 | `query` → call-chain |
| **admin** | **0** | 502 | `route_map` → **20 route + handler** (`/institutes`, `/accounts`, `/institutes/:id/plugins/:name`, `POST /customer_data/import`…) |
| **reservation** | **0** | 634 | `query` → `definitions`: `pages/_branchId/index.vue:bookReservation` · `guest_confirm.vue:submitGuestReservation` · `link_bookings.vue:fetchOrphans/claimAll` · `reservation-success.vue` |

- **473 = 227 + 130 + 116.** Đó là **tổng call-chain của 3 repo**, KHÔNG phải "473 business flow phải viết doc".
  Chúng gom thành **8 domain** ở bảng trên.
- `processes = 0` **≠ graph rỗng**: admin/reservation vẫn cho route + file + method → đủ dựng `draft`.
  Chỉ thiếu **call-chain** → phần UI-confirm nặng hơn. **Không phải** "GitNexus vô dụng với 2 repo này".
- Cả hai đều `consumers: []`, `flows: []` → đúng cảnh báo `CLAUDE.md` §3: catalog có, **cross-link không**.

## Wiring xuyên hệ then chốt (từ CLAUDE.md — graph không thấy)
- **Sync backend↔ticket = 2 tầng: direct-first, outbox-fallback.** `ThreeaseTicketSyncable` (after_commit)
  → `ThreeaseTicketSyncJob` → ticket khỏe: HMAC webhook `/admin-api/sync` (INSTANT) · ticket down: outbox
  (`rake threease_ticket:flush_outbox`). Reverse: ticket `pro_backend_sync.py` + `SyncOutboxEvent`.
- **Guard "vé đã dùng"** (phiên này UI-confirm): chặn cancel payment/booking/delete/remove khi gói có vé đã dùng;
  message JP đúng ở A/B, raw i18n key ở Remove (bug).
- **Coupon SC:** đếm theo SC (store credit), FIFO toàn tài khoản; report `/coupon-reports/{sales,usage}` (2/5 sub-tab build).

## Cách dựng deep-dive mỗi domain (lặp)
1. `query({repo:"@threease", search_query:"<domain>"})` + `context` → symbol + flow.
2. Đọc code tại pinpoint + trám cross-repo bằng CLAUDE.md.
3. Viết `knowledge/system/<domain>.md`: entities · flows · rules · state-machine · cross-repo wiring · `source_symbols`+`source_hash`. status: draft → người duyệt.
4. (Nếu domain cần cho QA dựng precondition → UI-confirm phần navigation → tách sang `knowledge/<flow>.md` approved.)

## Thứ tự đề xuất (giá trị cao trước)
① Customer/Master sync (đã rõ, viết nhanh) → ② Payment/Cancel (đã UI-confirm) → ③ Ticket issue+sync →
④ Coupon/SC → ⑤ Reports → ⑥ Booking → ⑦ Reservation widget → ⑧ Admin.

---

## 📥 Nhập từ `.claude-tester/.claude-knowledge/PROJECT_MAP.md` (2026-07-09, cửa WHAT)
> `grown_from: .claude-tester/.claude-knowledge/PROJECT_MAP.md` · Nguồn gốc: đọc `Gemfile`/`package.json`/
> `pyproject.toml`/`pubspec.yaml` từng repo, 2026/07/08. ⛔ **QA-runtime CẤM đọc.**
> Tên nghiệp vụ ↔ tên kỹ thuật: `knowledge/GLOSSARY.md` (file đó QA **được** đọc).

| Hệ | Repo | Tech stack | Nguồn sự thật dữ liệu? | Dev URL (✅ xác nhận 2026-07-09) |
|---|---|---|---|---|
| Hệ thống Lõi | `threease_backend` | Rails 6.1, Ruby 3.0.2, PG (RDS + 2 read replica), Redis + Sidekiq | ✅ **Có** — Institute/Branch/Customer/Therapist/Reservation/Ticket | `api-dev.threease.com` |
| Ứng dụng Pro | `threease_pro` | Nuxt 2.15.8, Vue 2, Vuetify 1.11.3, TS | ❌ chỉ UI | `develop.pro.threease.com` (basic `threesides/threesides`) |
| Ứng dụng Quản trị | `threease_admin` | Nuxt 2.15.8, Vuetify 1.11.2 | ❌ | `admin-dev.threease.com` |
| Widget Đặt lịch | `threease_reservation` | Nuxt 2.15.8, Vuetify 1.12.1 | ❌ | `reservation-dev.threease.com` |
| Ứng dụng Di động NV | `threease_therapists` | Flutter/Dart ≥2.2.2 | ❌ | N/A (mobile) |
| Hệ thống Vé | `threease_ticket` | Django ≥5.2, Python ≥3.13, HTMX, crispy-forms | ⚠️ **một phần** — sự thật cho thao tác TRONG ticket app, nhưng sync chưa đủ model | `ticket-dev.threease.com` |

- Auth Hệ thống Lõi = `devise_token_auth`; namespace theo app `/admin/*`, `/therapists/*`, `/home/*`.
- Ứng dụng Di động NV có **phiên đăng nhập độc lập** với Ứng dụng Pro.
- Đăng nhập chéo sang Hệ thống Vé = link đăng nhập 1 lần (`quick_login`), **không** dùng chung phiên Pro.
