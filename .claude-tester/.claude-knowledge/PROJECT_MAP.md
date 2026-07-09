# PROJECT_MAP — Bản đồ app/repo Threease

> Nguồn: đọc trực tiếp `Gemfile`/`package.json`/`pyproject.toml`/`pubspec.yaml` từng repo + route/config.
> Ngày đọc: 2026/07/08 · Độ ổn định: 🟢 (tech stack ít đổi) — riêng cột **Dev URL** đánh dấu 🟡 (đổi theo
> môi trường/release, verify lại `.env`/`nuxt.config.js` nếu nghi ngờ).
> Tên nghiệp vụ tra chéo bảng thuật ngữ ở `DOMAIN.md`.

| Tên nghiệp vụ | Repo | Tech stack | Vai trò | Nguồn sự thật dữ liệu? | Dev URL | Ghi chú |
|---|---|---|---|---|---|---|
| **Hệ thống Lõi** | `threease_backend` | Rails 6.1, Ruby 3.0.2, PostgreSQL (AWS RDS + 2 read replica), Redis + Sidekiq | API lõi — toàn bộ business logic, mọi app khác gọi vào đây | ✅ Có — nguồn sự thật cho Institute/Branch/Customer/Therapist/Reservation/Ticket | `api-dev.threease.com` | Auth = devise_token_auth; namespace theo app `/admin/*`, `/therapists/*`, `/home/*` |
| **Ứng dụng Pro** | `threease_pro` | Nuxt 2.15.8, Vue 2, Vuetify 1.11.3, TypeScript | Web nhân viên/chủ phòng khám — vận hành hàng ngày | ❌ Không — chỉ là UI, gọi API Hệ thống Lõi | `develop.pro.threease.com` (basic auth `threesides/threesides`) | Font riêng Noto Sans, layout sidebar+topbar, đầu tư UI kỹ nhất trong 3 app Nuxt |
| **Ứng dụng Quản trị** | `threease_admin` | Nuxt 2.15.8, Vue 2, Vuetify 1.11.2, TypeScript | Web Super Admin — quản lý tài khoản phòng khám, plugin | ❌ Không | 🟡 chưa xác nhận URL dev riêng — cần hỏi/tra `.env` khi cần | Cùng bảng màu navy với Pro nhưng đơn giản hơn (không custom font, component để phẳng) |
| **Widget Đặt lịch** | `threease_reservation` | Nuxt 2.15.8, Vue 2, Vuetify 1.12.1, TypeScript | Form đặt lịch nhúng — bệnh nhân tự đặt lịch qua web | ❌ Không | 🟡 chưa xác nhận URL dev riêng | Theme teal riêng biệt (khác hẳn Pro/Quản trị), layout topbar+footer không sidebar |
| **Ứng dụng Di động Nhân viên** | `threease_therapists` | Flutter/Dart (SDK ≥2.2.2) | Mobile nhân viên — xem lịch/nội dung trị liệu trong ngày | ❌ Không | N/A (mobile build, không có "dev URL" web) | Auth độc lập với Ứng dụng Pro (không share session); theme `#848cac`, không liên quan tông màu web |
| **Hệ thống Vé** | `threease_ticket` | Django ≥5.2, Python ≥3.13, HTMX, django-crispy-forms | Backoffice quản lý vé/coupon (回数券/クーポン) — tách biệt khỏi Hệ thống Lõi | ⚠️ Một phần — nguồn sự thật cho **thao tác trong Ticket app** (phát/hủy/chuyển vé), nhưng **không đồng bộ đầy đủ** với Hệ thống Lõi (xem `SYNC_MAP.md`) → số dư hiển thị có thể sai lệch | 🟡 chưa xác nhận URL dev riêng | Nhận sync 1 chiều (chưa đủ model) từ Hệ thống Lõi; có receiver cho chiều ngược nhưng sender chưa xác nhận (`SYNC_MAP.md`) |

## Ghi chú xác nhận còn thiếu (🟡/⚠️ trong bảng trên)
- Dev URL riêng cho Ứng dụng Quản trị, Widget Đặt lịch, Hệ thống Vé: chưa tìm thấy trong lần đọc
  2026/07/08 (không có trong `7.Tests/account.txt`, vốn chỉ ghi Pro dev). Cần hỏi team hoặc tra biến
  môi trường deploy khi cần test 3 app này.
- Không tìm thấy app mobile riêng cho **bệnh nhân** (đã ghi trong `DOMAIN.md`) — nếu tồn tại ở repo
  khác ngoài 6 repo đang quản lý, cần bổ sung dòng riêng vào bảng này.

## Liên kết
- Quan hệ nghiệp vụ chi tiết + thuật ngữ: [`DOMAIN.md`](DOMAIN.md)
- Đồng bộ dữ liệu giữa Hệ thống Lõi ↔ Hệ thống Vé: [`SYNC_MAP.md`](SYNC_MAP.md)
- UI/UX theo từng app: [`UI_UX.md`](UI_UX.md)
- Tính năng/màn hình cụ thể: [`FEATURES.md`](FEATURES.md)
