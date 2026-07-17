---
id: lessons
status: approved
kind: lessons
spans_repos: [pro, ticket, backend]
source_symbols: []
source_hash: null
confidence: 🟢
verify_by: "Mỗi dòng là thứ QUAN SÁT ĐƯỢC lúc drive app. Nghi ngờ → drive lại; selector đổi → sửa + đổi ngày."
grown_from: "0119159:.claude-tester/knowledge/LESSONS.md (chỉ 9/11 mục — 2 mục code-derived đi sang knowledge/system/)"
---
# LESSONS — bẫy CƠ KHÍ khi drive app (tăng dần, có ngày)

> Sau mỗi `run`/`retest`, thêm bẫy mới ở **ĐẦU** danh sách. Format: `YYYY/MM/DD — [tag] bài học (→ hệ quả)`.

## ⚖️ LUẬT NHẬP — bài học này trả lời câu hỏi HOW hay WHAT?

| | Ví dụ | Vào đây? |
|---|---|:--:|
| **HOW** — cách drive / nơi quan sát | *"`fill` phải target `input[data-cy=…]`, không phải `div`"* | ✅ |
| **HOW** — thứ **quan sát được** | *"API xóa khi thiếu quyền trả **204**, dữ liệu không đổi"* | ✅ |
| **WHAT** — nguyên nhân | *"vé không thu hồi **vì** backend thiếu callback"* | ❌ |
| **WHAT** — phán quyết | *"coupon report **chưa build**"* | ❌ |

- **WHAT → `knowledge/system/*.md`** (build-time only). Ghi vào đây = đầu độc phiên sau, phá Tường thép #2.
- **Bug KHÔNG vào đây.** Bug thuộc `specs.md` (`BUG-xx`) + file Excel. `knowledge/` không phải nơi
  cất kết luận về sản phẩm.
- Không chắc HOW hay WHAT? → hỏi: *"câu này giúp tôi BẤM đúng, hay giúp tôi CHẤM đúng?"*
  Giúp **bấm** → vào. Giúp **chấm** → không (chỉ SPEC được giúp chấm).

- **2026/07/17 — [pro/auth] Pro KHÔNG dùng cookie phiên.** Auth = devise-token cất ở **localStorage key `user`**
  (`{"id":2,"accessToken":"…"}`), gửi lên qua **header** `access-token/client/uid/expiry/token-type`.
  Cookie duy nhất là analytics (`_ga`,`_gid`,`AMP_*`,`cwr_*`) — **không mang quyền**, server không hề `Set-Cookie`.
  ⇒ (a) họ **cookie-flags N/A** trên Pro; (b) cắm token giả vào key `_token`/`access-token` là **vô ích** —
  app không đọc 2 key đó (từng làm tui tưởng "token giả sống sót"); (c) logout = `DELETE /auth/sign_out`,
  sau đó token cũ trả **401**.
- **2026/07/17 — [pro/preset] Preset quyền = chỗ ghi data test AN TOÀN nhất trên Pro.**
  `GET/POST /permissions/presets` · `DELETE /permissions/presets/{id}` → **204**; `cleanup.js` quét prefix `AIOT-TEST`.
  Shape: `{id, name, default_preset, permission_slugs[]}`. Quan sát được: name rỗng → **422** · `permission_slugs: []` → **422** ·
  `id` lạ trong body → **422** · tạo hợp lệ → **201**.
- **2026/07/17 — [SPA/route/oracle] Nuxt trả 200 + CÙNG MỘT VỎ cho MỌI path** (pro, reservation — đo thật).
  `GET /../../../../etc/passwd` và `GET /reservation` trả body **giống HỆT nhau từng byte** (reservation 3526 ký tự,
  pro 4165); chữ `404 Not Found` / `リクエストページが存在しません` do **JS vẽ SAU khi render**, KHÔNG có trong body.
  ⇒ (a) **`context.request` (không chạy JS) không đủ để chấm** force-browse/IDOR trên SPA — phải `page.goto` + chờ
  rồi đọc `document.body.innerText`; (b) **status 200 trên SPA KHÔNG nghĩa là route tồn tại** — đừng dùng 200/404
  để kết luận "có/không có màn" (khác hẳn ticket-app Django: 404 thật là 404).
- **2026/07/17 — [pro/route]** Route đặt lịch thật là **`/reservations`** (số nhiều, KHÔNG có prefix branch).
  `/branches/2/reservations/` trả **200 nhưng ra màn ホーム** (vỏ SPA) → tưởng vào đúng màn là sai.
  Calendar Nuxt cần **~7-8s** mới render (2.5s là chưa xong → quét axe/probe lúc đó = đo vỏ rỗng).
- **2026/07/17 — [reservation/route]** Widget đặt lịch ở **`/reservation`** (số ÍT). `/` ra `リクエストページが存在しません`
  (soft-404, HTTP 200). Widget **không có login** (chỉ basic-auth `BASIC_USER/BASIC_PASS`) → các họ cần cắt phiên
  (session-after-logout / session-fixation) **không áp dụng được**. Đặc trưng màn để chờ: `text=コース選択`.
- **2026/07/11 — [cleanup/coupon]** Coupon (Ticket **và** Pro) **KHÔNG có UI/API xoá**: list/detail/edit
  không có nút 削除, `/coupons/<id>/delete/` → 404, Pro modal chỉ có 更新/編集. ⇒ data test coupon
  (`AIOT-TEST-*`) + pack đã phát hành **không dọn được qua UI** → nhờ dev xoá ở DB (`name LIKE 'AIOT-TEST%'`).
  `cleanup.js` chỉ quét preset/reservation Pro, KHÔNG đụng coupon.
- **2026/07/10 — [ticket/coupon/create-edit]** Tạo coupon = route **`/coupons/add/`** (KHÔNG phải `/coupons/new/` → 404); sửa = `/coupons/<id>/edit/`. Vào bằng nút **登録** (list) / **編集** (detail). ⚠️ Nút 追加/更新 bị **thanh action (div.hstack) chắn pointer** → `page.click` retry vô hạn; phải `getByRole('button',{name:'追加'}).click({force:true})` (JS `.click()` submit KHÔNG ăn). Field form: name, branch_option(0=すべて/1=カスタム), custom_branches[], tax_category(included/excluded/none), tax_rate(0.08/0.10), sales_price, granted_credits, available_quantity, start_date, end_date, description.
- **2026/07/10 — [ticket/quyền]** Nút 登録/編集 coupon + tab report **ẩn theo QUYỀN account** → account thiếu quyền thấy như "feature không tồn tại" (route 404 + không có nút). ⚠️ **"không thấy nút" ≠ "chưa build"** — phải thử ĐÚNG account (account.txt) trước khi kết luận. (STAFF001 sau deploy 2026/07/10 đã đủ quyền coupon 設定/登録/編集 + report.)
- **2026/07/10 — [ticket/coupon/route]** Route coupon THẬT trên ticket-app khác URL trong mockup
  (`/backoffice/...`, `/coupons/new/`, `/coupons/1/edit/` đều **404/redirect** — chỉ là hình minh hoạ).
  Route thật: danh sách `/coupons/` · chi tiết `/coupons/<id>/` · khách `/customer/<id>/` (**số ít**) ·
  phát hành `/coupon-ops/issue/customer/<id>/` · dùng SC `/coupon-ops/use/customer/<id>/` ·
  lịch sử `/customers/<id>/coupon-history/` (**số NHIỀU** `customers`, khác với chi tiết khách số ít).

- **2026/07/10 — [ticket/login]** Màn quản lý coupon/顧客 cần `TK_STAFF=ticket-admin` (STAFF001 hạn chế,
  như report). Sau login trang hiện dải chọn 治療院 + banner "開発環境" nhưng **đã** đăng nhập (Django trả
  200/404 bình thường), không phải màn login.

- **2026/07/10 — [ticket/DOM]** `body.innerText` các trang ticket-app nuốt **toàn bộ option của 2 `<select>`
  khổng lồ** (danh sách 治療院 + staff バルク先生N) → dump text bị ngập. Khi đọc text: clone node rồi
  `querySelectorAll('select').forEach(remove)` trước, hoặc `grep -avE '治療院|先生'`.

- **2026/07/10 — [pw_lib/shot]** Trang chi tiết khách / lịch sử / use dài hơn viewport → `shot()` mặc định
  chỉ chụp viewport (mất bảng dưới fold). Truyền `opts.screenshot={fullPage:true}` cho các màn dài.

---

## Bẫy đã gặp

- **2026/07/09 — [selector/chung] Bảng selector Vuetify hay dùng** (nhập từ `0119159:.claude-tester/knowledge/SYSTEM.md`,
  ⚠️ code-derived, mới verify được phần đánh ✅):
  · Login: `input[data-cy=institute_code|therapist_code|password]`, nút `[data-cy=loginButton]` ✅
  · Input Vuetify: field bọc `div[data-cy=…]` → **phải target `input[data-cy=…]`** ✅
  · Dialog đang mở: `.v-dialog--active` (lấy **cái cuối** nếu chồng nhau) — chưa verify
  · Nút xoá booking: `.mdi-delete-outline` ✅ (×1 trong ReservationForm)
  · Màn quyền `/clinic_setting/permissions` ✅ · Đặt lịch `/reservations` ✅ · Kế toán `/accounting` (chưa verify)

- **2026/07/09 — [selector] Toạ độ chuột cứng là tri thức MỤC RỮA.** Doc cũ ghi `mouse.click(877, 68)`
  cho mũi tên "ngày sau". Dưới `ja-JP` nhãn ngày ngắn hơn → mũi tên thật ở **x=837** → 12 lần click rơi
  vào vùng trống, không báo lỗi, chỉ **im lặng không làm gì**.
  → Dùng selector ngữ nghĩa: `page.locator('.mdi-chevron-right').first()` (thanh ngày, y≈59).
  ⚠️ Trang có **7 chevron-right**: 1 ở thanh ngày + **6 ở header cột unit** (y≈117) — `.first()` mới đúng.

- **2026/07/09 — [selector] `exact:true` sai chuỗi = FAIL GIẢ âm thầm.**
  `getByText('削除', {exact:true})` → **0**. Nhãn thật là **`削除する`**. Tương tự `Remove` (bản EN) → 0.
  → Khi đếm ra 0, **đừng kết luận "không có nút"**. Chụp ảnh nhìn mắt trước.

- **2026/07/09 — [ui/cơ chế]** Nút `削除する` **luôn nằm trong DOM** (đếm ×2: dòng vé + dòng coupon),
  cả trước lẫn sau hover. Hover chỉ làm nó **nổi lên**. → Doc cũ mô tả *"hover mới hiện Remove"* là **sai
  cơ chế**: kiểm tồn tại thì không cần hover; chỉ **click** mới cần hover đúng dòng.

- **2026/07/09 — [ui/nav]** Mở booking → ReservationForm hiện ở **panel phải**, **URL KHÔNG đổi**
  (vẫn `/reservations`). → Đừng dùng URL để xác nhận form đã mở; dùng selector nội dung.

- **2026/07/09 — [knowledge/meta] ☠️ Doc navigation có thể ĐÓNG BĂNG một bug harness thành "sự thật".**
  `pro-open-booking.md` từng ghi *"app ở /en/ = ENGLISH nên tôi đổi keyword sang EN"* — phiên đó gặp
  bug thiếu `locale` rồi **chép bug vào knowledge** thay vì sửa harness. `source_hash` **không bắt được**
  (code sản phẩm không đổi dòng nào).
  → Đổi bất cứ gì ảnh hưởng cách app render (locale/viewport/DSF/auth) ⇒ **đánh `stale` MỌI doc `kind: flow`**
  + re-UI-confirm. Xem `docs/KNOWLEDGE-STRATEGY.md` §4b.

- **2026/07/09 — [locale] ☠️ BẪY NGUY HIỂM NHẤT: harness gây FAIL SAI.**
  App Pro **đổi ngôn ngữ UI theo `locale` của trình duyệt**. Playwright không set locale → app chạy
  **tiếng Anh** (`/en/shifts`, sidebar `Home/Reservation/Accounting`). Spec viết tiếng Nhật
  (`未払い`, `支払い済`, `請求書`, `キャンセル`, `権限設定`) sẽ **không match** → QA chấm **FAIL** trong khi
  sản phẩm **không có lỗi**.
  → `pw_lib` set `locale: 'ja-JP'` (đo: `ja-JP` → `/shifts`, sidebar `ホーム/予約/会計`).
  Muốn test bản EN thì `LOCALE=en-US`.

- **2026/07/09 — [screenshot/nét]** `deviceScaleFactor: 2` → ảnh **2880×1800** thay vì 1440×900
  (267KB vs 67KB). Chuẩn giao hàng là "PNG rõ" → luôn bật. Ghi đè bằng `DSF=1` nếu cần ảnh nhẹ.

- **2026/07/09 — [login/race] Ba cách SAI để hỏi "đã đăng nhập chưa".**
  App **luôn render form login một nhịp** rồi mới xác thực xong và unmount nó. Nên:
  · `count()` → đếm cả node **ẩn** → tưởng cần login → treo 30s.
  · `url().includes('login')` → **race**: app ghé `/login` rồi mới sang `/shifts`.
  · `waitFor({state:'visible'})` sớm → form **có** visible thật một nhịp **kể cả khi session hợp lệ**.
  → Đúng: **chờ `networkidle` + đệm 2.5s** cho auth-check + redirect xong, **rồi mới** `isVisible()`.

- **2026/07/09 — [login/state]** Lưu `storageState` **ngay khi URL đổi** là SAI — app chưa kịp ghi
  devise-token vào `localStorage` → file cache có nhưng **rỗng session** → lần sau vẫn bị đá về `/login`.
  → Chờ `networkidle` + 1.5s rồi mới `storageState()`.

- **2026/07/09 — [login/vuetify]** Form Vuetify + i18n **re-render** khi nạp locale → `fill` giữa chừng
  báo `element was detached from the DOM`. → `fillSafe()`: chờ visible + retry 3 lần trước mỗi `fill`.

- **2026/07/09 — [dev/URL]** Cả 5 dev URL **đều sống** (đo `curl` + `<title>`):
  `develop.pro` (`threease_pro`) · `api-dev` · `ticket-dev` (`threeaseチケット`) ·
  `admin-dev` (`threease_admin`) · `reservation-dev` (`Threease`). → giá trị đoán trong `pw_lib` là ĐÚNG.

- **2026/07/09 — [screenshot]** `waitForTimeout(6000)` + `page.screenshot()` trần hay dính spinner/màn trắng.
  → Luôn dùng `shot(page, path, readySelector)` (`pw_lib.js`): chờ selector đặc trưng + `networkidle` + đệm 500ms.

- **2026/07/09 — [api/auth]** Hệ thống Lõi **không** dùng `Authorization: Bearer`. Nó dùng devise-token:
  5 header `access-token, client, uid, expiry, token-type`.
  → `pw_api.withApi()` **nghe lén** header từ request thật của app (`page.on('request')`) rồi tái dùng.
  KHÔNG tự dựng token, KHÔNG đọc code để biết cách auth. `api.get/post/...` trả `{status, body, ok}` —
  dùng `status` cho case chống-bypass (403 vs 204).

- **2026/07/08 — [access/report]** Report Hệ thống Vé (`/reports`, `/coupon-reports/*`) cần quyền riêng:
  account **`TESTSEED001 / ticket-admin / password123`** (env `TK_STAFF=ticket-admin`).
  `STAFF001` **không** vào được (nav thiếu tab, `/reports` redirect về home).
  → Nhầm account sẽ tưởng "chưa build" trong khi chỉ là thiếu quyền.

- **2026/07/08 — [cleanup/branch]** Branch của phiên staff `TESTSEED001` **đổi theo phiên/data**
  (đã thấy 4 → 2 → 3 qua các ngày).
  → **Luôn xác nhận `BRANCH_ID` của phiên hiện tại** trước khi gọi API theo branch. Không tin giá trị lịch sử.
  (`cleanup.js` không set thì tự bỏ qua Staff+Reservation thay vì đoán bừa.)

- **2026/07/13 — [pro/nav]** Mũi tên đổi NGÀY ở `/reservations` là 2 icon **cạnh nhãn ngày** (đo bbox:
  `.mdi-chevron-left` x≈684/y≈59 · `.mdi-chevron-right` x≈837/y≈59). Các `.mdi-chevron-*` ở **y≈120** là
  nút cuộn CỘT unit/bed trên lưới — click chúng KHÔNG đổi ngày. `.first()` của chevron-left tình cờ trúng
  cái đúng, nhưng nên lọc theo y≈59 cho chắc.

- **2026/07/13 — [pro/store]** Bộ chọn store ở toolbar: click phần tử `.v-toolbar__content *` có text khớp
  `/院\d/` (KHÔNG `getByText(/AIOT院/)` — trúng logo, timeout). Menu ra list `AIoT院1..4 / テスト院5.. / threease院1..`.
  ⚠️ Store hiển thị ở toolbar KHÔNG map 1-1 với `branch_id` API: phiên hiện tại luôn phát request
  `/branches/2/reservations` dù đổi store sang AIoT院1/院3 → xác định branch bằng cách nghe request thật, đừng suy từ tên 院.

- **2026/07/13 — [pro/api]** `GET /branches/{b}/reservations?start_date=YYYYMMDD&end_date=YYYYMMDD&session=all`
  trả `{reservations:[...]}` (OBJECT, không phải array trần) — parse `body.reservations`. Thêm `&per=200`
  → trả **rỗng** (giới hạn per); range > ~1 tháng cũng trả rỗng → query từng tháng, đừng set per lớn.
  Detail: `GET /branches/{b}/reservations/{id}`; item vé nằm ở `reservation_items[].ticket_packs=[{id,quantity}]`
  (booking DÙNG vé) — pack id ticket-app ≥ **200000**. Phiên đo: branch có booking vé = **4, 5** (branch 2 không có).

- **2026/07/08 — [observe/vé]** Số dư vé hiển thị bên **Hệ thống Vé** không đủ làm bằng chứng duy nhất.
  → Đối chiếu thêm **Hệ thống Lõi** (`GET /branches/{b}/customers/{c}/ticket_packs`). Quan sát **2 phía**.
  *(Vì sao 2 phía có thể lệch → `knowledge/system/`, không ghi ở đây.)*

- **2026/07/07 — [cleanup/booking]** Booking **đã thanh toán** không `DELETE` được ngay
  → `PUT /branches/{b}/transactions/{id}` `{transaction:{status:'cancelled'}}` trước, rồi mới `DELETE`.

- **2026/07/07 — [cleanup/vé]** Xóa booking **phát hành** gói vé bị `422「使用済みチケット」` khi gói còn vé
  đã dùng/giữ → xóa **2 vòng**: vòng 1 xóa booking **tiêu thụ** vé (nhả vé), vòng 2 xóa booking **phát hành**.

- **2026/07/07 — [pro/login]** Form login Pro là Vue render động → phải chờ
  `input[data-cy=institute_code]` **visible** rồi mới `fill` (race condition, hay rớt về `/login`).

- **2026/07/07 — [pro/nav]** Booking tương lai **không** hiện ở view mặc định của `/reservations`.
  → Điều hướng ngày **verification-driven**: lặp tối đa 10 lần, mỗi lần click mũi tên `>` rồi kiểm
  `getByText(/<tên khách>/)` — **không click mù N lần**.

- **2026/07/04 — [Vuetify]** `data-cy` gắn ở **cả** `div` bọc lẫn `input` → `fill` phải target
  `input[data-cy=…]`. Dialog xác nhận có 2 nút gần giống (`閉じる` = đóng · `キャンセル` = hành động hủy)
  → bấm nhầm `閉じる` tưởng đã hủy nhưng chưa.

- **2026/07/04 — [preset]** Ô quyền của preset **mặc định** bị `disabled` → muốn test ẩn/hiện nút
  phải tạo preset mới (`AIOT-TEST-*`) rồi gán cho staff (`AIOTTEST*`).

- **2026/07/04 — [api/quyền]** API xóa đặt lịch đã TT khi **không có quyền** trả **`204`** (không xóa gì,
  dữ liệu còn nguyên) thay vì `403`. → Quan sát được: dữ liệu **được bảo vệ**. Mã lỗi thì không rõ ràng.
  *(Đây có phải bug không → SPEC quyết định, không phải file này.)*
