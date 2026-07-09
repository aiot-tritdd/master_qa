---
id: glossary
status: approved
kind: glossary
spans_repos: [backend, ticket, pro, admin, reservation]
source_symbols: []
source_hash: null
confidence: 🟢
verify_by: "Tên nghiệp vụ do người đặt, không đổi theo code. Chỉ cập nhật khi hệ thống mới xuất hiện."
ui_confirmed_at: null
grown_from: ".claude-tester/.claude-knowledge/DOMAIN.md#bảng-thuật-ngữ"
---
# GLOSSARY — thuật ngữ nghiệp vụ (dùng khi VIẾT REPORT)

> **Luật:** tên kỹ thuật (repo/công nghệ) **chỉ dùng nội bộ**. Khi viết `actual`, báo cáo FAIL,
> hoặc nói chuyện với khách hàng/BA → **luôn dùng tên nghiệp vụ** ở cột trái.
>
> Đây là **HOW/naming**, không phải WHAT — nó không nói cái gì đúng/sai. QA-runtime đọc được.

## Hệ thống

| Tên nghiệp vụ (dùng khi nói/viết) | Vai trò | *(tên kỹ thuật — chỉ để tra cứu nội bộ)* |
|---|---|---|
| **Hệ thống Lõi** | Nơi lưu toàn bộ dữ liệu gốc, xử lý nghiệp vụ chính. **Nguồn sự thật** | `threease_backend`, Rails |
| **Ứng dụng Pro** | Web nhân viên/chủ phòng khám, thao tác hàng ngày | `threease_pro`, Nuxt |
| **Ứng dụng Quản trị** | Web Super Admin (vận hành Threease) | `threease_admin`, Nuxt |
| **Widget Đặt lịch** | Form đặt lịch nhúng, bệnh nhân tự đặt | `threease_reservation`, Nuxt |
| **Ứng dụng Di động Nhân viên** | App mobile nhân viên (xem lịch/nội dung trị liệu) | `threease_therapists`, Flutter |
| **Hệ thống Vé** | Backoffice quản lý vé/gói buổi trị liệu (回数券), tách riêng khỏi Hệ thống Lõi | `threease_ticket`, Django |

## Nghiệp vụ

| Thuật ngữ | Nghĩa |
|---|---|
| **締め / Kết sổ** | Chốt sổ kế toán theo kỳ. Sau kết sổ, số liệu quá khứ không được biến động |
| **回数券 / Gói vé (ticket pack)** | Gói nhiều buổi trị liệu (vd 100 slip). Khách mua qua đặt lịch |
| **SC / Store credit** | Đơn vị của Coupon. Tiêu theo **FIFO trên toàn tài khoản** — khác vé (tiêu theo từng gói) |
| **発行元** | Nơi **bán** (店頭 = tại quầy / Pro) |
| **使用元** | Nơi **tiêu** (店頭 / Pro). ⚠️ Hai trục **độc lập** với 発行元 — đừng gộp |

## Trạng thái (dùng nguyên văn tiếng Nhật trong `expect`/`actual`)

- **Đặt lịch:** `確認待ち → 本予約 → 受付済 → 進行中 → 完了` · `キャンセル済`
- **Thanh toán:** `未払い → 一部支払済 → 支払い済`

## Kết quả test (4 trạng thái — xem `theme.json`)

| | Nghĩa |
|---|---|
| `PASS` | quan sát khớp `expect` |
| `FAIL` | quan sát lệch `expect` |
| `未実施` | **không quan sát được** (không vào được kênh quan sát) |
| `SPEC-GAP` | **quan sát được** nhưng spec không định nghĩa kỳ vọng → không chấm được |

## Ví dụ viết report

❌ *"`ThreeaseTicketSyncJob` không gọi `flush_outbox` nên `th_customer` chưa upsert."*
✅ *"Spec kỳ vọng sau khi thanh toán, khách được cấp 100 vé. Quan sát trên **Ứng dụng Pro**: số dư vé
vẫn 0. Đối chiếu **Hệ thống Lõi** (API `ticket_packs`): cũng 0. Ảnh: TC-05_before/after.png."*

> FAIL báo **hành vi**, không báo **vị trí code**. Định vị bug là việc của dev.
