---
id: system-ui-theme
status: draft
kind: system-domain
spans_repos: [pro, admin, reservation]
source_symbols:
  - "pro: nuxt.config.js"
  - "pro: assets/variables.scss"
  - "admin: nuxt.config.js"
source_hash: af8e737769688b58
confidence: 🟡
verify_by: "Màu/token đổi theo release → mở lại nuxt.config.js / variables.scss / colors.dart trước khi tin."
grown_from: "0119159:.claude-tester/.claude-knowledge/UI_UX.md"
---
# UI/UX theme theo từng app (WHAT — chỉ dùng khi test/mockup giao diện)

> ⛔ **QA-runtime CẤM đọc.** Code-derived (đọc `nuxt.config.js` 2026/07/08), chưa UI-confirm.
> Chỉ mở khi build-time cần đối chiếu UI.

## Không có design-system dùng chung
3 app Nuxt (Pro / Quản trị / Widget Đặt lịch) **mỗi cái tự khai theme riêng**
(`nuxt.config.js` + `assets/variables.scss`). **Không** có package theme/token chung.
Không có Storybook/style-guide thật (chỉ 1 build cache rỗng ở Pro + 1 link Figma dạng comment, chưa truy cập được).

## Pro & Quản trị — cùng "họ" thương hiệu nội bộ
- **Màu chủ đạo chung:** primary `#004adb` · secondary `#0A2046` · accent `#c9d1e2`
  (`pro/nuxt.config.js:195-197`, `admin/nuxt.config.js:80-82`).
- Khác nhau: Pro `error #C70020 / success #219653 / warning #F2994A` (`:199-201`);
  Quản trị `error #D90000 / success green.accent3 / warning amber.base` (`:84-86`) — mặc định Vuetify hơn.
- **Pro đầu tư kỹ hơn:** font riêng *Noto Sans*, `font-size-root: 15px` (`assets/variables.scss:8,14`);
  chia `components/shared/` (Base*, HeaderBar, SideBar, TagLabel, TheConfirmWindow…) + `components/features/`;
  layout TheHeaderBar (topbar) + TheSideBar/TheHQSideBar (sidebar, có mini-variant) + TheMobileBar.

## Widget Đặt lịch
Theme **teal** riêng biệt (khác hẳn Pro/Quản trị), layout topbar + footer, **không sidebar**.

## Ứng dụng Di động Nhân viên
Flutter, theme `#848cac` — không liên quan tông màu web.

## ⚠️ Phạm vi — Hệ thống Vé CHƯA khảo sát
`threease_ticket` là Django/HTMX, **không** nằm trong khảo sát này.
Cần đối chiếu UI Hệ thống Vé → đọc thẳng template `.html`/CSS trong repo đó.
**KHÔNG** dùng bảng màu Vuetify ở trên làm chuẩn cho nó (khác nền tảng hoàn toàn).
