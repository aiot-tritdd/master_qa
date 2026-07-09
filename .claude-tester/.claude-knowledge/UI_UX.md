# UI/UX — Bản đồ giao diện các ứng dụng Threease (🟡 verify code trước khi dùng)

> Đọc trực tiếp code 2026/07/08. Fact volatile (màu/token) đổi theo release → kiểm lại `nuxt.config.js`/
> `variables.scss`/`colors.dart` trước khi tin tuyệt đối, nhất là khi cách xa ngày cập nhật.
> Dùng khi tạo mockup: chọn đúng theme theo app đang làm, KHÔNG dùng chung 1 màu cho tất cả.
> ⚠️ **Phạm vi**: chỉ khảo sát 4 app (Pro/Quản trị/Widget Đặt lịch/Di động Nhân viên) — **chưa khảo sát
> Hệ thống Vé** (`threease_ticket`, Django/HTMX). Cần mockup màn hình Hệ thống Vé → đọc thẳng
> template/CSS trong repo đó, xem [`REPORTING.md`](REPORTING.md) cho ví dụ (màn báo cáo No.11).

## Tổng quan — không có design-system dùng chung
3 app Nuxt (Ứng dụng Pro / Ứng dụng Quản trị / Widget Đặt lịch) **mỗi cái tự khai theme riêng**
(`nuxt.config.js` + `assets/variables.scss`) — KHÔNG có package theme/token dùng chung.
Không có Storybook/style guide thật nào tồn tại (chỉ có 1 build cache Storybook rỗng ở Ứng dụng Pro
và 1 link Figma dạng comment, chưa xác nhận truy cập được).

## Ứng dụng Pro & Ứng dụng Quản trị — cùng 1 "họ" thương hiệu nội bộ (nhân viên/admin)
**Nguồn**: [`threease_pro/nuxt.config.js:195-201`](/Applications/Workspaces/threease/threease_pro/nuxt.config.js:195),
[`threease_admin/nuxt.config.js:80-86`](/Applications/Workspaces/threease/threease_admin/nuxt.config.js:80),
[`threease_pro/assets/variables.scss:8-16`](/Applications/Workspaces/threease/threease_pro/assets/variables.scss:8)
· Ngày đọc: 2026/07/08 · Độ ổn định: ⭐ (đọc trực tiếp giá trị hex/hằng số) · Verify bằng: mở lại 3 file
trên nếu nghi màu đã đổi theo release.
- **Màu chủ đạo chung 2 app**: primary `#004adb`, secondary `#0A2046`, accent `#c9d1e2`
  (`nuxt.config.js:195-197` Pro, `:80-82` Admin).
- Khác nhau: Pro `error #C70020 / success #219653 / warning #F2994A` (`nuxt.config.js:199-201`); Quản
  trị `error #D90000 / success Vuetify green.accent3 / warning Vuetify amber.base` (`:84-86`) — nhạt
  hơn/mặc định hơn.
- **Ứng dụng Pro** đầu tư kỹ hơn: font riêng "Noto Sans" + `font-size-root: 15px`
  (`assets/variables.scss:8,14`), cấu trúc component chia `components/shared/` (Base*, HeaderBar,
  SideBar, TagLabel, TheConfirmWindow…) + `components/features/`; layout có TheHeaderBar (topbar) +
  TheSideBar/TheHQSideBar (sidebar, có mini-variant) + TheMobileBar riêng cho mobile web; nhiều layout
  khác nhau theo màn (`HQCrm`, `karte`, `login`, `open`).
- **Ứng dụng Quản trị** đơn giản hơn nhiều: không override font/spacing (dùng mặc định Vuetify/Roboto —
  verify by: `rg font-size-root threease_admin/assets/variables.scss` nếu nghi thay đổi), component để
  phẳng ngay `components/` (không chia shared/features), chỉ có layout `default/error/open` (không có
  layout mobile/HQ riêng) — vì phạm vi app hẹp (CRUD institute/branch/staff).
- Icon: cả 2 dùng font MDI (`mdi-*`), Pro dùng rất nhiều (~590 chỗ), Quản trị dùng ít (~11 chỗ) — đếm
  bằng `rg -c "mdi-" threease_pro/ threease_admin/` nếu cần số chính xác lại (số trên đếm 1 lần, có
  thể lệch khi code đổi).
- Vuetify version: Pro `1.11.3`, package `@nuxtjs/vuetify` (`threease_pro/package.json:93`).

## Widget Đặt lịch — thương hiệu khác hẳn, hướng khách hàng (bệnh nhân)
**Nguồn**: [`threease_reservation/nuxt.config.js:86-93`](/Applications/Workspaces/threease/threease_reservation/nuxt.config.js:86),
[`threease_reservation/assets/variables.scss:4`](/Applications/Workspaces/threease/threease_reservation/assets/variables.scss:4)
· Ngày đọc: 2026/07/08 · Độ ổn định: ⭐ · Verify bằng: mở lại 2 file trên.
- **Màu hoàn toàn khác** 2 app trên: primary `#31AFBA`, accent `#DFF5F7`, secondary `#575965`,
  `background: '#F0F6F7'` (không thấy ở 2 app kia), error `#D21E1E`, success `#0E9E2E`
  (`nuxt.config.js:86-93`). → Đúng vì đây là **giao diện công khai cho bệnh nhân**, không phải nội bộ.
- `font-size-root: 18px` (`variables.scss:4`) — to hơn 2 app kia (15px/mặc định), hợp lý cho đối tượng
  người dùng phổ thông.
- Layout khác hẳn: **topbar + footer** (`TheAppBar`/`TheFooter`), KHÔNG có sidebar — vì là trang public,
  không phải dashboard quản trị.
- Icon: ít dùng font MDI (~18 chỗ), thay bằng **SVG component riêng** trong `components/icons/`
  (vd `SuccessIcon.vue`) — nhìn "thiết kế" hơn là dùng icon font thô.
- Có vài component đặt tên kiểu "design-system" (`BaseButton.vue`, `BaseRadioInput.vue`) — dấu hiệu app
  này được đầu tư UI kỹ hơn 2 app kia dù nhỏ hơn về chức năng.

## Ứng dụng Di động Nhân viên (Flutter) — theme tối giản
**Nguồn**: [`threease_therapists/lib/colors.dart:3`](/Applications/Workspaces/threease/threease_therapists/lib/colors.dart:3),
[`threease_therapists/lib/main_production.dart:45`](/Applications/Workspaces/threease/threease_therapists/lib/main_production.dart:45)
· Ngày đọc: 2026/07/08 · Độ ổn định: ⭐ · Verify bằng: mở lại 2 file trên.
- `colorPrimary = 0xff848cac` (xanh xám trầm, `colors.dart:3`), có light/dark variant, chữ trên nền
  primary màu trắng. Áp dụng qua `_buildTheme()` (`main_production.dart:45`).
- Không có design-system widget riêng, dùng thẳng Material widget mặc định của Flutter — không có file
  token mở rộng ngoài `colors.dart`.
- ⚠️ Tông màu này **không khớp với bất kỳ app web nào** (không phải navy của Pro/Quản trị, không phải
  teal của Widget Đặt lịch) — khi làm mockup cho app này, không tham khảo màu từ 2 nhóm kia.

## Áp dụng khi tạo mockup
1. Xác định **đang mockup cho app nào** trước tiên (nội bộ nhân viên/admin vs công khai bệnh nhân vs mobile)
   — không có theme "Threease chung" để dùng mặc định.
2. Nội bộ (Pro/Quản trị) → nền tảng màu navy `#004adb`/`#0A2046`, Vuetify/Material Design, icon MDI.
   Nếu mockup cho Pro cụ thể → thêm font Noto Sans + layout sidebar; nếu cho Quản trị → giữ đơn giản,
   không cần sidebar phức tạp.
3. Công khai bệnh nhân (Widget Đặt lịch) → teal `#31AFBA`, layout topbar+footer không sidebar, ưu tiên
   icon SVG tùy chỉnh thay vì icon font, cỡ chữ lớn hơn.
4. Mobile nhân viên (Flutter) → tông `#848cac`, Material mặc định, không bê theme web sang.
5. Không có Figma/style guide truy cập được trong repo — nếu cần độ chính xác cao hơn cho 1 màn cụ thể,
   nên đọc trực tiếp file Vue/route tương ứng trong repo đó (xem [[FEATURES.md]] để biết vào đâu) thay vì
   suy diễn từ bảng màu này.
