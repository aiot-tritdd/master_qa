# STATE — điểm dừng & việc tiếp (đọc ĐẦU TIÊN mỗi phiên)

> File **sống** — cập nhật cuối mỗi phiên. Mục đích: mở phiên mới là biết ngay *đang ở đâu, làm gì tiếp*.
> Cập nhật: **2026-07-17**. Branch git: `qa-brain` (master_qa) — đã push hết, working tree sạch.
>
> ⚠️ **KHÔNG ghi commit hash vào file này.** Hash luôn SAI: commit ghi doc tạo ra hash mới *sau khi* đã ghi.
> (Đúng vậy thật — bản 2026-07-17 ghi `ba2018f`, thực tế đã là `ee3c434`.) Muốn biết đang ở đâu: `git log --oneline -1`.

---

# 🔔 MỞ SESSION MỚI → ĐỌC ĐÚNG KHỐI NÀY LÀ ĐỦ

## Cập nhật 2026-07-21: build thêm 3 track (i18n type-7 + load/stress grey-box). CÓ việc tự chạy được.

> Trạng thái "cạn việc" của 2026-07-17 KHÔNG còn đúng. Việc tự chạy được ngay (không kẹt ai):
> ① **i18n live-run** (`/testcase-i18n` — đã build+unit-verified, cần drive dev sống: reservation `/en/2` vs `/2`, pro, ticket).
> ② **Visual prove vòng-2** (chụp lại 3 màn ticket → so baseline đã commit → ra PASS thật; sửa `visual.results.json` thiếu màn `customer-700006`).
> load/stress **đã build xong nhưng RUN-GATED** — chỉ bắn khi user ra lệnh + khách/sếp gật (đổ tải lên AWS khách).

```
Trục TYPE (ngang):  6/6 live + i18n(type-7) BUILT chưa-live · load/stress (grey-box) BUILT run-gated
Trục APP  (ngang):  ĐÓNG       phủ 3/5 (ticket·pro·reservation) — admin user CHỐT BỎ HẲN
Trục LEVEL (dọc):   TRỐNG      Unit + Integration → chỉ WHITEBOX với tới (con đen mù code, cấu trúc không thể)
```

## ⛔ Cả 2 việc còn lại đều KẸT Ở NGƯỜI KHÁC — không phải kẹt kỹ thuật

| Việc | Kẹt gì | **Câu ông cần hỏi** |
|---|---|---|
| **Whitebox** (mở rộng thật sự duy nhất còn lại) | **quyền sở hữu** | Hỏi **sếp/dev**: *"Cho agent viết unit/integration test vào 5 repo sản phẩm không?"* Unit test xưa nay **dev tự viết trong repo họ** → đây là quyết định **tổ chức**, không phải kỹ thuật. Được đồng ý → làm **1 lát mỏng** (1 flow, tầng Integration/API-contract, oracle **vẫn SPEC**), đừng nuốt cả đáy pyramid × 5 repo. Chi tiết + 3 cục chặn: **ROADMAP §4**. |
| **IDOR** (họ security DUY NHẤT còn `未実施`) | **thiếu data** | Xin **dev/sếp**: **account institute THỨ HAI** (`TESTSEED002`). Hiện chỉ có `TESTSEED001` → không thử đọc-chéo-tenant được. Access-control là loại lỗ nặng nhất mà đang **mù**. |

> 💡 **Không hỏi được cái nào → KHÔNG CÓ VIỆC.** Đừng bịa việc ra làm. Đừng đề xuất lại mấy thứ ở
> mục **"Đã đề xuất → user BÁC"** (§3) — admin, giao bug, pro visual, webkit/Safari, PreToolUse hook.

## Ảnh chụp nhanh — hệ đang ở đâu
- **Sổ bug: 39** (Mở 39 · Đã đóng 0) — a11y 21 · Function 11 · Security 4 · Perf 3.
  🚫 **Giao bug = việc của USER** (tự đưa file lên Drive). `wtf-is-this/` giữ gitignore. **Đừng nhắc nữa.**
- **Test tự động của chính hệ QA: 97 JS `node --test` + 10 Python xanh** (thêm i18n_lib 13 + load_lib 13).
- **8 lib oracle**: `security_lib`(25) · `compat_lib`(12) · `perf_lib`(10) · `i18n_lib`(13) · `load_lib`(13, grey-box)
  · `a11y_lib` · `pw_lib` · `pw_api` + `factcheck_report.py`(7) gate mọi report trước khi build.
  k6 v1.0 đã cài (brew). Template `k6_load.js`/`k6_stress.js` inspect-verified, **chưa bắn**.
- **Dev sạch** — không còn data test (`AIOT-TEST-SEC-*` đã dọn, verify 0 preset rác).
- 📊 **Phát hiện to nhất chưa ai fix:** `pro` **TBT 1184ms** (đơ ~1.2s) vs `ticket` ~0ms vs `reservation` 106ms
  ⇒ **vấn đề tốc độ KHU TRÚ ở Pro**, không phải "hệ chậm". (Quan sát — không chẩn đoán, đó là việc dev.)

---

## 0. File này là gì

Đây là **điểm hồi phục**: mở phiên mới, đọc file này là biết *đang đứng đâu, làm gì tiếp*.
Nó **không** giải thích hệ thống — muốn hiểu hệ thống thì đọc [`README.md`](../README.md) (1 file, đủ).

QA senior **black-box** (skill `qa-brain` + commands `testcase-*`): SPEC → sinh+chạy test trên **dev** →
evidence PNG/xlsx. Oracle = SPEC + quan sát live. **Mù code.** GitNexus chỉ ở build-time (soạn knowledge).

### 9 lệnh test (mỗi lệnh 1 track riêng, oracle riêng)
| Lệnh | Oracle | Trạng thái |
|---|---|---|
| `/testcase-run` (qa-brain) | **SPEC** + quan sát live | ✅ |
| `/testcase-a11y` | **WCAG** (axe-core) | ✅ ticket·pro·reservation |
| `/testcase-visual` | baseline người-duyệt | ✅ — ⚠️ **CHỈ màn TĨNH** (màn có ngày/tiền → nhiễu). ⚠️ **CHƯA prove vòng-2** (baseline bless rồi, chưa chạy so-sánh ra PASS thật) |
| `/testcase-security` | bất biến an ninh (13 họ, OWASP 2025) | ✅ pro đủ 13/13 |
| `/testcase-compat` | **WCAG 1.4.10** + parity engine | ✅ ≈67% (Safari bỏ có chủ ý) |
| `/testcase-perf` | **Core Web Vitals** (ngưỡng Google) | ✅ ticket PASS · pro FAIL |
| `/testcase-i18n` (**type-7**, black-box) | bất biến ngôn ngữ (key-leak/mojibake/parity/format) | ✅ **BUILT + unit-verified** (13 test) · ⚠️ **CHƯA live-run** (cần dev sống; phủ reservation/pro/ticket) |
| `/testcase-load` (**grey-box/SRE**) | client-side k6 (error<1% · p95 placeholder) | ✅ **BUILT, RUN-GATED** — k6 cài sẵn, **chưa bắn** (cần user ra lệnh + khách gật) |
| `/testcase-stress` (**grey-box/SRE**) | knee + giả-thuyết nút-thắt (client-side) | ✅ **BUILT, RUN-GATED** — chưa bắn |

## 2. ĐÃ XONG (đừng làm lại)

- ✅ **`explorer.js`** (2026-07-14) — đồ **dò-đường build-time** cho UI-confirm: snapshot a11y-text + drive-by-name (role/label/text) + `nearLabel` + replay-nghiệm + emit HOW-only (tường WHAT ép bằng cấu trúc). Cắm vào `/testcase-systemdoc` bước 3. 13 unit test xanh (deterministic, fixture). ⚠️ **CÒN TREO: live smoke** (cần Docker dev + `.env`): `node explorer.js snapshot --target pro --url /reservations`. Spec/plan: `docs/superpowers/{specs,plans}/2026-07-14-build-time-explorer*`.
- ✅ **Redesign black-box:** SKILL.md · commands · `build_evidence.py` (3-sheet) ·
  `pw_lib.js` (5 target: pro/ticket/ticket_admin/reservation/admin) · docs · 2× CLAUDE.md.
- ✅ **Chuẩn evidence:** xlsx 3 sheet (Cover/Test Cases/Checklist+Nguồn), **mỗi case 2 ảnh before+after PNG rõ**.
- ✅ **Skill `/specs-md`** (html→md). ✅ **`/testcase-stale`** + `stale_check.py` + `source_hash` thật (GĐ-0).
- ✅ **Re-UI-confirm `pro-open-booking.md`** (2026-07-09, ja-JP) — phát hiện toạ độ cứng + nhãn EN đều mục rữa.
- ✅ **Test đã chạy:** `TestCase_NEW` (thu hồi vé) 7 case verified ·
  `TestCase-11` (coupon report) **9 PASS / 8 FAIL**, khớp 100% scope dev.
- ✅ **Phân tích + merge hệ của sếp** (`.claude-tester/`): xong Phase 0→4 (hồ sơ `SYSTEM-COMPARISON.md` đã gỡ — tra `git log`/`git show`).
- ✅ **Track Accessibility** (`/testcase-a11y`) — axe-core black-box, report `.a11y.xlsx` + sổ bug
  (`bug_type: Accessibility`). ✅ **LIVE-VERIFIED 2026-07-17** trên TestCase-11 (ticket): 3 màn FAIL, đẩy **BUG-012..019** vào sổ.
  Evidence nâng cấp: `shotViolation` chụp full-màn khoanh đỏ; report có cột giải-thích-lỗi (Lỗi gì→Chi tiết(failureSummary đo được)→Cách fix→Tài liệu→File ảnh). Spec/plan: `docs/superpowers/{specs,plans}/2026-07-16-a11y-track*`.
- ✅ **Track Visual** (`/testcase-visual`) — pixelmatch, baseline `baselines/<app>/<slug>.png` (commit git),
  report `.visual.xlsx` + sổ bug (`bug_type: Visual`). Mask sinh tự động ở build-time (explorer `dynamic`). Type test thứ 3.
  ✅ **LIVE-VERIFIED 2026-07-17**: capture/compare/NEW-BASELINE chạy e2e; **bless baseline 3 màn ticket** (`baselines/ticket/{coupons,customer-700006,coupon-reports-sales}.png`, commit). ⚠️ Giới hạn auto-mask (không bắt churn xuyên-phiên) đã ghi ROADMAP → 3 màn data-heavy này sẽ cần re-bless khi data đổi.
  Spec/plan: `docs/superpowers/{specs,plans}/2026-07-16-visual-track*`.
- ✅ **Track Security** (`/testcase-security`) — **13 họ phủ phần black-box OWASP 2025** (Injection/XSS · IDOR · Client-bypass guard-parity ·
  Error-disclosure · Security-headers · Open-redirect · CSRF · Mass-assignment · Force-browse/traversal · Session-after-logout),
  oracle = **bất biến an ninh phổ quát** (code-blind, no SPEC-GAP). `security_lib.js` (**25 test**) + `build_security_report.py` + `bug_type:Security`. Type track thứ 4.
  **Consolidation:** security RÚT khỏi qa-brain functional (SKILL.md) → tập trung ở track này.
  ✅ **LIVE-VERIFIED 2026-07-17** (10 họ trên TestCase-11 ticket): **6 PASS** (error-disclosure/force-browse/injection-escaped/CSRF-403/session-logout-302/**client-bypass end<start chặn server-side**) · 1 FAIL security-headers CSP+HSTS → **BUG-020** · 4 未実施 (IDOR *hoãn — account chỉ 1 institute TESTSEED001, cần institute thứ 2* · mass-assignment *whitebox — cần model* · open-redirect *không có param* · SSRF *N/A — scope coupon không có feature fetch-URL*). KHÔNG data rác (mutating bị reject). Live lộ + vá 3 probe (IDOR/force-browse HTML-oracle, session-logout cần POST). Whitebox handoff (OWASP A02/04/06/08/09/10) ghi ROADMAP §4.
  Spec/plan: `docs/superpowers/{specs,plans}/2026-07-17-security-track*`.
- ✅ **Harvest qa-skills** (kindlmann, MIT — 2026-07-17, ĐÃ đọc file skill thật):
  - **HICCUPS** → `qa-brain/SKILL.md §3.4`: bộ 10 kính oracle nhận diện bug (code-blind; Claims=SPEC chốt đúng/sai, Standards=a11y, World=Compatibility).
  - **`security_lib` v2** (+5 test → 21): 3 probe mới **cookie-flags · CORS · session-fixation** (họ 11-13) + `PAYLOADS.pathTraversal` + helper **acceptable-status-set** (`isDenied`/`statusIn`). Command doc remap **OWASP 2025** + recipe **Juice-Shop meta-verify** (chống PASS rỗng).
  - ✅ **LIVE-VERIFIED 3 họ v2 2026-07-17** (ticket-dev, read-only, không cleanup): **cả 3 PASS** — cookie-flags (sessionid HttpOnly+Secure+SameSite; csrftoken Secure+SameSite) · session-fixation (cắm id giả → server xoay sang id mới) · CORS (không phản chiếu Origin lạ). Live **bắt + vá 1 false-positive**: probe đòi HttpOnly trên csrftoken (SAI — CSRF cookie by-design để JS đọc) → chừa csrf khỏi luật HttpOnly. TestCase-11 security = **16 dòng: 9 PASS / 3 FAIL (=BUG-020 headers) / 4 未実施**.
  - ✅ **Fact-preservation checker** (`factcheck_report.py` + 7 test) — bê phần mechanical của qa-report-humanizer: GATE **filler/AI-tell** + **tally bịa** (số PASS/FAIL trong summary phải khớp đếm thật), WARN passive/vague. Chạy trên MỌI report-source JSON TRƯỚC build (pointer ở BUG-LOG §3 + command doc). Data thật (security.results + sổ 20 bug) đều 0 lỗi.
  - **Breadcrumb whitebox/chiến-lược** vào ROADMAP §4 + harvest log §5 (security-auditor/test-automator/qa-expert + phần DAST/SCA/SAST của qa-skills security-testing = whitebox; không bê cho con đen).
  - ✅ **Queue harvest con đen ĐÓNG**: HICCUPS + security_lib v2 (live-verified) + fact-check. 3 nguồn whitebox/strategy đã park (ROADMAP §4).
- ✅ **Type-track trên Pro + Reservation** (2026-07-17) — lần đầu ra ngoài ticket-app:
  - **a11y**: 3 màn quét, **cả 3 FAIL** → **BUG-021..034 → còn 13 bug** (BUG-033 link-name bị XOÁ, xem dưới). Pro `/reservations` (aria-allowed-attr×4, button-name×16, color-contrast×14, nested-interactive) · Pro `/accounting` (button-name×9, label×4, color-contrast×7, nested-interactive×4) · Reservation **`/2`** (button-name×3 = **hamburger + 2 mũi tên đổi ngày** → screen-reader không đặt lịch nổi, label×2, aria-command-name, color-contrast×5). Report: `TestCase-12.a11y.xlsx` + `Reservation-widget.a11y.xlsx`.
  - **security Reservation** (6 họ read-only — widget công khai, KHÔNG ghi data): headers **FAIL** → **BUG-036** (thiếu cả 5; widget CÔNG KHAI nên thiếu X-Frame-Options = clickjack được luồng đặt lịch). CORS/error-disclosure/open-redirect/force-browse PASS. Họ cần login (session-*) = **N/A** (widget không có login). Họ mutating **chưa chạy** (ghi = đẻ booking rác, user chốt chỉ chạy Pro).
  - **security Pro — ĐỦ 13 họ** (user chốt "A": cho ghi data trên Pro). **14 PASS / 3 FAIL / 4 未実施**:
    · **FAIL**: headers ×2 màn → **BUG-035** (thiếu CẢ 5) · **error-disclosure tầng API** → **BUG-037**.
    · **PASS**: injection/xss (3 payload lưu được nhưng render escaped, `window.__SEC_XSS` không set) · mass-assignment · client-bypass · csrf · session-after-logout (token cũ → 401) · session-fixation (token cắm sẵn → server 401) · CORS · open-redirect · force-browse.
    · **未実施**: cookie-flags (**N/A** — Pro auth = devise-token ở localStorage/header, không cookie phiên) · IDOR (chờ institute #2).
    · **Ghi data**: chỉ preset `AIOT-TEST-SEC-*` (5 cái) → **đã dọn ngay trong script, verify còn 0** ✅ dev sạch.
  - 🐞 **Live bắt + vá bug oracle #2** (`security_lib`, 24→**25 test**): `hasStackLeak` **trượt** rò kiểu Rails. POST preset với `id` lạ → 422 kèm `Couldn't find Therapists::Preset with 'id'=999999 [WHERE "therapists_presets"."institute_id" = $1]` — lộ **model + tên bảng + cột phân tách tenant**, nhưng body KHÔNG chứa tên class exception (`ActiveRecord::…`) nên 5 pattern cũ đều trượt. Thêm 2 pattern: `rails-record-not-found` (rò qua *message*) + `sql-fragment` (`WHERE "bảng"."cột" =`). → **BUG-037**.
  - ⚠️ **Bài học phương pháp**: mass-assignment lần đo đầu ra **422 = PASS may rủi** (gửi kèm `id`/`institute_id` lạ nên bị chặn vì lý do KHÁC). Test lại **tách biến + có đối chứng** (A hợp lệ→201 / B chỉ thêm `default_preset:true`→201 nhưng field bị bỏ qua) mới là PASS có căn cứ. **Không có đối chứng thì PASS vô nghĩa.**
  - 🐞 **Live bắt + vá 1 bug oracle THẬT** (`security_lib`, 21→**24 test**): probe force-browse/IDOR chấm `../../../../etc/passwd` = **"200 + lộ data" trên CẢ pro lẫn reservation** → **FAIL GIẢ**. Bằng chứng: body path cấm **===** body path hợp lệ (từng byte), không có `root:x:`, DOM sau render = **404** ⇒ app chặn đúng. Nguyên nhân: SPA trả cùng vỏ cho mọi path, `context.request` không chạy JS. Vá: `probeIDOR/probeForceBrowse(result, {baselineBody})` → giống baseline ⇒ `inconclusive` (so byte, app-agnostic, **cửa mạnh nhất**) + `looksLikeSpaShell()` dự phòng. ⚠️ Bản vá đầu (chỉ đo độ dài text) bị **chính unit test bắt**: nuốt luôn trang lộ thật nhưng ngắn ⇒ false-NEGATIVE → phải đòi thêm vân tay hydration SPA. Vỏ Pro có 56 ký tự text nên heuristic **trượt**, chỉ baseline bắt được. Doc: `/testcase-security` §"App SPA".
  - Bẫy cơ khí SPA (route thật, thời gian render, soft-404, 200≠tồn-tại) → `knowledge/lessons.md`.
  - **Sổ bug: 20 → 36** (13 a11y + BUG-035/036 headers + BUG-037 error-disclosure). Data test đã dọn trong script, dev verify sạch → không cần `/testcase-cleanup`.
- ✅ **Track Compatibility** (`/testcase-compat`) — **type track thứ 5**, 2026-07-17. `compat_lib.js` (**12 test**) +
  `build_compat_report.py` (sheet **Ma trận** engine × viewport) + `bug_type:"Compatibility"`.
  **3 oracle, 0 setup, KHÔNG cần baseline** (khác Visual — vì so giữa các engine **cùng thời điểm**, không so ảnh cũ
  ⇒ không mục rữa theo ngày): ① **WCAG 1.4.10 Reflow** (mốc **320 CSS px** do W3C công bố) · ② **parity affordance**
  giữa engine · ③ **0 `pageerror`**. Engine: chromium · firefox · webkit. Viewport: 320/390/768/1280.
  ✅ **LIVE-VERIFIED 2026-07-17** (reservation widget `/2`): **8 PASS / 4 未実施** — chromium + firefox **4/4 viewport
  PASS** (reflow ok @320px, parity **19 affordance khớp y hệt** cả 4 cỡ, 0 lỗi JS). **0 bug.**
  ✅ **CHỐT 2026-07-17 (user quyết): CHẤP NHẬN LỖ Safari — KHÔNG phủ webkit, KHÔNG đề xuất lại.**
  webkit/Safari = **`未実施` vĩnh viễn** trên setup này: `playwright 1.61` + **macOS 13.7.8** → `does not support
  webkit on mac13`. Đã đề xuất Docker/CI để phủ → **user bác, chấp nhận lỗ**.
  ⛔ **KHÔNG giả lập** bằng chromium+UA rồi báo "đã test Safari" (giả lập đổi viewport/UA, KHÔNG đổi engine ⇒ PASS rỗng).
  ⚠️ **Báo cáo compat PHẢI ghi rõ "chưa test Safari"** — không được để người đọc tưởng đã phủ.
  📊 **Trạng thái thật: Compat ≈ 67% ổn** = 8/12 ô chạy (2/3 engine × 4 viewport), **8/8 ô chạy đều PASS**, 1 màn.
  Lưu ý trung thực khi đọc con số "0 bug": chromium + firefox là 2 engine **ÍT vỡ nhất**; Safari (engine hay vỡ:
  flexbox, `<input type=date>`, scroll iOS) nằm ngoài phạm vi. "0 bug" = 0 bug **trên phần dễ**, không phải "widget
  chạy ngon trên mọi máy".
  - 🐞 **Live bắt + vá 2 bug oracle nữa**: ① `probeConsole` đếm **resource-404** là lỗi JS → chromium ghi 404 ra
    console, **firefox KHÔNG** ⇒ chromium FAIL/firefox PASS = **bịa** (đang đo *cách browser ghi log*). Vá: chỉ nhận
    `pageerror`; 404 tách sang `networkFailures` (chuyện functional). ② `probeParity` nhiễu vì **dialog chớp nhoáng**:
    `button::閉じる` lúc firefox *thiếu* (320px) lúc *thừa* (390px) — tự mâu thuẫn ⇒ `detectTransient()` + `{transient}`,
    luôn báo `ignored` (dao 2 lưỡi: nhét bừa = nuốt diff thật).
  - 🎯 **BẪY ĐẮT NHẤT ĐỢT NÀY — đo SAI URL suốt**: `/reservation` **KHÔNG phải** đường vào widget. App hiểu path là
    **slug phòng khám** → đi tìm院 tên "reservation" → **404 toàn bộ API** → widget render vỏ nhưng **rỗng data**.
    Đúng là **`/2`** (5 API 200, hiện `AIoT院1` + SĐT). Vì `コース選択` có mặt ở CẢ trạng thái lỗi nên nó **không**
    phân biệt được → tưởng vào đúng. ⇒ **Đo lại a11y trên `/2`: BUG-033 (link-name) là bug MA của trang lỗi → XOÁ;
    BUG-031 color-contrast 3→5.** Sổ 37→36. **Luật: xác nhận vào đúng màn bằng API 200 + DATA THẬT hiện ra, KHÔNG
    bằng HTTP 200 / "thấy chữ gì đó".**
  - ⚠️ Phạm lại luật cũ: `waitForTimeout(7000)` → desktop bị chấm **未実施 OAN** (giây 7 vẫn đang loading, spinner +
    lớp phủ). Sửa: chờ **điều kiện** (`waitFor visible` + `networkidle`). `pw_lib.shot()` đã ghi luật này từ lâu.
- ✅ **Track Performance** (`/testcase-perf`) — **type track thứ 6, ĐÓNG TRỌN 6/6 TYPE**, 2026-07-17.
  `perf_lib.js` (**8 test**) + `build_perf_report.py` (sheet **Chỉ số** màn × metric, có dòng ngưỡng + cảnh báo
  LAB≠FIELD ngay đầu) + `bug_type:"Performance"`.
  **Oracle = Core Web Vitals, ngưỡng GOOGLE CÔNG BỐ** (web.dev/vitals) — LCP ≤2500ms · CLS ≤0.1 · **TBT ≤200ms**
  (proxy LAB cho INP) · FCP ≤1800ms · TTFB ≤800ms. **Không cần ai đặt số** ⇒ 0-setup, đúng vai trò WCAG với a11y.
  📌 **Gỡ 1 quyết định SAI của ROADMAP cũ**: *"Performance vướng oracle, cần budget do người đặt"* → **SAI**.
  `needs-improvement` **cũng FAIL** (good LÀ mốc đạt; nới cho qua = tự hạ chuẩn công bố).
  ✅ **LIVE-VERIFIED 2026-07-17** (5 lần/màn → **trung vị**, chromium, dev):
  · **Reservation `/2` = PASS** — cả 5 chỉ số good (LCP 1324ms · CLS 0.046 · TBT 106ms · FCP 1324ms · TTFB 184ms).
  · **Pro `/reservations` = FAIL** → **BUG-039 (High): TBT 1184ms = 6× ngưỡng 200ms** ⇒ luồng chính bị chặn ~1.2s,
    user bấm/gõ không ăn · **BUG-038 (Medium): CLS 0.18** (dao động 0.109–0.495, cờ `unstable` — nhưng **mọi lần
    chạy đều > 0.1** nên vẫn kết luận được là không đạt).
  · **Pro `/accounting` = FAIL** → **BUG-040 (Medium): TBT 480ms = 2.4× ngưỡng**.
  ⚠️ **4 điều BẮT BUỘC nói khi báo cáo** (giấu = lừa người đọc): ① **LAB ≠ FIELD** — chuẩn CWV thật là phân vị 75
  của người dùng THẬT (CrUX, máy yếu/4G); lab "good" **không** chứng minh user thật thấy nhanh, nhưng lab "poor"
  thì **chắc chắn** tệ ⇒ kết quả = **CẬN DƯỚI của mức tệ**. ② **DEV ≠ PROD** (không CDN, data ít). ③ **INP
  KHÔNG đo được ở lab** → TBT proxy; `perf_lib` cố ý **không** có INP trong `THRESHOLDS`, **unit test khoá luôn**
  (thêm INP vào = chuẩn bị bịa số). ④ **Nhiễu cao** → 5 lần lấy **TRUNG VỊ** (không phải trung bình); cờ
  `unstable` (dao động > trung vị) phải **báo ra**, không giấu.
  **Sổ bug: 36 → 39.**
  ✅ **Vá lỗ `ticket` perf 2026-07-17 — 3/3 màn PASS, 0 bug** (`/coupons/` · `/customer/700006/` · `/coupon-reports/sales/`,
  account `ticket-admin`). Mọi chỉ số good, **TBT = 0–4ms** (LCP 376–604ms · CLS 0–0.007 · TTFB 168–495ms).
  Đã **verify probe vào ĐÚNG màn** (DOM render `クーポン設定`/`顧客詳細`/`クーポン販売記録レポート`) — không phải PASS rỗng;
  `ready` selector ban đầu (`クーポン`/`顧客`/`レポート`) quá lỏng nên phải kiểm lại bằng dump DOM.
  📊 **Đối chiếu quan sát được (KHÔNG chẩn đoán nguyên nhân — đó là việc dev):** `ticket` **TBT ≈ 0ms** vs `pro`
  **TBT 1184ms**. Cùng một sản phẩm, chênh nhau ~1.2 giây chặn luồng chính. ⇒ Vấn đề tốc độ **khu trú ở Pro**,
  không phải "hệ chậm".
  - ⚠️ **Reservation KHÔNG có SPEC** → functional **không chạy được** (không oracle, không bịa). Chỉ type-track (oracle phổ quát). Folder `wtf-is-this/Reservation-widget/` chứa evidence type-track, không phải folder spec.

### ✅ MERGE Phase 0 — vá lệnh chết (2026-07-09, đã verify)
Trước đó 4 lệnh trỏ vào file **không tồn tại**. Nay:
- ✅ `theme.json` (mới) — single source of truth cho format. `build_evidence.py` đọc nó, hết hardcode palette.
- ✅ `example.tcs.json` (mới) — khung 5 archetype thành **dữ liệu**, không còn là trí nhớ của model.
- ✅ `cleanup.js` (mới) — `/testcase-cleanup` lần đầu chạy được. `BRANCH_ID` **không** hardcode.
- ✅ `shot(page, path, readySelector)` trong `pw_lib.js` — hết ảnh dính spinner.
- ✅ `pw_api.js` viết lại: **sniff devise-token** từ request thật (bỏ `Bearer API_TOKEN` sai auth).
  Trả `{status, body, ok}` → case chống-bypass phân biệt được 403 vs 204.
- ✅ `storageState` cache theo target (`.state.<target>.json`, đã gitignore).
- ✅ **`SPEC-GAP` = result thứ tư** (Q1 chốt hướng A). Cover đếm riêng, Checklist đếm riêng, `result` lạ → WARN.
- **Verify:** 4 tcs.json cũ (17/34/25/44 case) build lại sạch · ảnh nhúng khớp bản cũ (34↔34, 7↔7) ·
  `SPEC-GAP` chạy end-to-end · `node --check` sạch 3 file JS.

### ✅ MERGE Phase 1 — vệ sinh tri thức (2026-07-09)
- ✅ **`knowledge/OPEN-QUESTIONS.md`** (mới) — **tầng tri thức thứ ba**: *"tra rồi vẫn không đủ căn cứ"*.
  8 câu (OQ-01..08). QA-runtime **đọc được** (nó không phán đúng/sai).
- ✅ **`knowledge/GLOSSARY.md`** (mới) — thuật ngữ nghiệp vụ, để report FAIL không lộ tên repo.
- ✅ **`knowledge/lessons.md`** (mới) — 12 bẫy **cơ khí**, có luật nhập HOW-vs-WHAT ngay đầu file.
- ✅ `confidence:` + `verify_by:` vào front-matter mọi doc `knowledge/`.
- ✅ **Routing table + ⛔ danh sách CẤM đọc** trong `SKILL.md`.
- ✅ **Checklist "Before final"** vào cả 5 command (câu tripwire: *"Có đọc source code không? Nếu có, vì sao?"*
  — ở QA-runtime đáp án đúng luôn là **KHÔNG**).
- ✅ **Capture Lessons** (bắt buộc) vào `/testcase-run` + `/testcase-retest`.
- ✅ Luật **"1 tri thức = 1 nhà"** + **"dot-folder không chứa deliverable"** vào `KNOWLEDGE-STRATEGY.md`.

### ✅ REGRESSION TEST cho chính hệ QA (2026-07-09) — merge KHÔNG phá black-box
Thước đo thành công của merge: chạy lại TestCase-11 phải vẫn ra **9 PASS / 8 FAIL**. → ✅ **ĐÚNG**.
- `200`: top-tab `チケットレポート`+`クーポンレポート` · `/reports/` · `/coupon-reports/sales/` (filter, KPI,
  `CSVエクスポート`, cột `発行元`) · `/coupon-reports/usage/`
- `404`: `/coupon-reports/` (dashboard) · `/monthly/` · `/by-store/` · `/csv-snapshots/`; nút `過去のCSV` = 0
- Sub-tab クーポンレポート thật = **2** (`販売`,`消費`), spec đòi 5 → TC-04 FAIL.
- ⚠️ **Chốt OQ-01:** coupon report **CÓ tồn tại**, mới build 2/5 sub-tab. Khẳng định `grep` của sếp
  (*"CHƯA TỒN TẠI TRONG CODE"*) **sai**. Model nằm chỗ khác/tên khác.
- 📌 Bẫy tự bắt: selector `.nav-link,[role=tab]` hốt cả top-nav → ra 9. Số thật là 2.
  Tin thẳng số 9 ⇒ TC-04 PASS **sai**. Luôn nhìn ảnh khi con số lạ.

### ✅ LIVE-VERIFY harness (2026-07-09) — cổng chặn đã MỞ
Chạy thật trên dev, không phải syntax check:
- ✅ `pw_api` sniff devise-token: `GET /permissions/presets` → **200**, 7 preset. Id không tồn tại → **404**
  ⇒ `api.status` dùng được cho archetype #5 (chống bypass).
- ✅ `shot()` bắt được `text=権限設定`, ảnh **2880×1800 / 267KB**, không phải màn trắng.
- ✅ Cache `.state.pro.json` hoạt động cả 2 chiều (sạch → có).
- 🐞 **Tìm + vá 4 bug harness** (chi tiết `knowledge/lessons.md`): thiếu `locale:'ja-JP'` (**gây FAIL SAI**
  vì spec tiếng Nhật không match UI tiếng Anh) · thiếu `deviceScaleFactor:2` · lưu `storageState` quá sớm
  (cache rỗng session) · 3 cách sai để hỏi "đã đăng nhập chưa" (`count()` / `url()` / `visible` sớm).
- 🗑️ ~~Rác trên dev: preset `AIOT-TEST-105`~~ → ✅ **đã sạch** (đo 2026-07-17: `GET /permissions/presets` trả
  đúng **6 preset gốc** `本社/マネージャー/院長/施術者/受付/チケット管理者`, **0 preset `AIOT*`**).

## 3. VIỆC TIẾP (ưu tiên trên xuống — rà lại 2026-07-17)

> 🧹 Dọn 2026-07-17: các mục MERGE Phase 1-4 · live-verify `pw_api`/`shot()` · re-UI-confirm `pro-open-booking`
> **đã XONG** → chuyển hết lên §2, không còn nằm ở "việc tiếp" nữa. Bảng đầy đủ + lý do xếp hạng: **`ROADMAP.md` §3b**.

1. 🔵 **[Whitebox — 1 lát mỏng] Thứ DUY NHẤT còn lại thực sự MỞ RỘNG hệ.** Trục ngang (Type) đã **6/6**, admin
   đã chốt bỏ ⇒ con đen **hết đường đi ngang**. Chỉ còn trục dọc (Level): **Unit + Integration** — con đen
   **cấu trúc không thể** với tới (mù code). Chi tiết + 3 cục chặn: **ROADMAP §4**.
   ⛔ **Chặn KHÔNG phải kỹ thuật mà là QUYỀN SỞ HỮU**: unit test thường **dev tự viết trong repo họ**; agent lạ
   ghi test vào 5 repo sản phẩm → **cần sếp/dev đồng ý**. Hỏi được thì mới bắt đầu.
   Khuyến nghị ROADMAP: làm **1 lát mỏng** (1 flow, tầng Integration/API-contract, oracle **vẫn là SPEC**) —
   đừng nuốt cả đáy pyramid × 5 repo.
2. **[Security] IDOR** — họ DUY NHẤT còn `未実施` trên cả ticket lẫn pro. Access-control là loại nặng nhất mà đang **mù**.
   ⛔ **Chặn: cần account institute THỨ HAI** (`TESTSEED002`) → xin dev/sếp.
3. **[Grow knowledge/system]** Còn 2 domain: **6 Booking** · **7 Reservation widget** (~~8 Admin~~ — đã chốt bỏ).
   ⚠️ Chỉ grow khi **thực sự test tới** (demand-driven).
7. **[Nav doc]** Nâng `issue-ticket-pack.md` `draft → approved`: UI-confirm khâu tạo booking → thanh toán → phát hành vé.
8. **[Optional]** `TestCase_NEW`: 6 case còn `未実施` cần precondition **gói vé còn nguyên** (KH3 đã dùng 2 vé).

### Đã đề xuất → user BÁC (đừng đề xuất lại nếu không có lý do mới)
- **PreToolUse hook** (OQ-09) — biến "QA mù code" từ *chữ* thành *cơ chế chặn thật*. Đề xuất 2026-07-17 → **bác**.
  ⚠️ Rủi ro còn nguyên: hiện **không có gì** chặn kỹ thuật việc đọc code lúc test.
- **Visual cho pro/reservation** — bác, **đúng**: 3 màn đều đổi theo ngày (calendar/dãy ngày/số tiền) ⇒ baseline
  hỏng mỗi ngày = máy đẻ nhiễu. Visual chỉ dùng cho màn **TĨNH**.
- **Reservation — họ security mutating** — bác: ghi data = đẻ booking rác trên widget công khai.
- **Phủ webkit/Safari cho Compat** (Docker/CI hoặc macOS ≥14) — đề xuất 2026-07-17 → **bác, CHẤP NHẬN LỖ**.
  ⇒ Compat đứng ở **≈67%** (8/12 ô; 8/8 ô chạy đều PASS) và **dừng ở đó**. Báo cáo phải ghi rõ "chưa test Safari".
  Đừng đề xuất lại trừ khi có lý do MỚI (vd: khách báo lỗi trên iPhone).
- **Whitebox / Analyzer** — hoãn (ROADMAP §3, §4).
- 🚫 **ADMIN app — user chốt 2026-07-17: BỎ HẲN, "từ nay luôn".** KHÔNG test admin, **KHÔNG đề xuất lại**.
  ⇒ Độ phủ app dừng ở **3/5** (ticket · pro · reservation). Admin = vùng trắng **có chủ ý**, không phải thiếu sót.
- 🚫 **Giao bug cho team** — user tự lo (đưa file lên Drive). `wtf-is-this/` **giữ gitignore**. Đừng đề xuất kênh giao,
  đừng nhắc "bug chưa tới tay dev" nữa. Việc của con QA dừng ở: sổ + report đúng, sạch, đọc được.
- 🚫 **`pro` — Visual**: cùng lý do đã bác cho reservation (calendar `2026/07/17`, 会計 có số tiền → baseline hỏng
  mỗi ngày = máy đẻ nhiễu). Visual chỉ dùng cho màn **TĨNH**.
- 🔻 **`ticket` — Compat**: giá trị thấp (app **nội bộ**, nhân viên dùng desktop/Chrome máy công ty). Compat đáng cho
  app **công khai** (khách xài đủ loại máy) — đã làm cho widget rồi. Không cấm, nhưng đừng ưu tiên.

## 3b. 📓 Nhật ký phiên 2026-07-17 — phiên DÀI, tóm cho phiên sau

**Làm được:** test pro + reservation (a11y+security) · build **2 track mới** (Compat, Perf) → đóng 6/6 type ·
vá lỗ ticket perf · sync toàn bộ doc về đúng thực tế · sổ bug **20 → 39**.

**🐞 Live-verify bắt 7 lỗi CỦA CHÍNH CON QA** (không có nó thì cả 7 đã thành bug bịa gửi dev / PASS rỗng):

| Probe bịa gì | Sự thật |
|---|---|
| `csrftoken` thiếu HttpOnly = yếu | CSRF cookie **cố tình** để JS đọc (double-submit) |
| **`/etc/passwd` lộ trên pro + reservation** | body path cấm **=== body path hợp lệ từng byte**, không có `root:x:`, DOM sau render = **404** ⇒ app chặn ĐÚNG. SPA trả cùng vỏ mọi path, `context.request` không chạy JS |
| error-disclosure "không rò" (pro) | 422 rò `Couldn't find Therapists::Preset … WHERE "therapists_presets"."institute_id"` — oracle cũ chỉ tìm **tên class** exception nên trượt → **BUG-037** |
| "chromium FAIL / firefox PASS" (compat) | 6 "lỗi" là **resource-404**; chromium ghi ra console, firefox KHÔNG ⇒ đang đo **cách browser ghi log** |
| firefox lệch nút `閉じる` | lúc **thiếu** (320px) lúc **thừa** (390px) — **tự mâu thuẫn** ⇒ dialog chớp nhoáng |
| mass-assignment "PASS" (422) | PASS **may rủi** — gửi kèm `id` lạ nên bị chặn vì **lý do KHÁC**. Tách biến + đối chứng mới ra PASS thật |
| `CLS = 0.1804399642965267` | số máy nhả, không phải số để báo cáo → `fmt()` |

**🎯 Bẫy ĐẮT NHẤT — đo SAI URL suốt nửa phiên:** quét a11y + security trên `/reservation` mà nó **không phải**
đường vào widget (app hiểu path là **slug phòng khám** → tìm院 tên "reservation" → **404 toàn bộ API** → đo
widget **rỗng data**). Đúng là **`/2`** (5 API 200, hiện `AIoT院1`). Bẫy: `コース選択` có mặt ở **CẢ trạng thái lỗi**
nên **không phân biệt được** → tưởng vào đúng. Hậu quả: **BUG-033 là bug MA** → xoá; BUG-031 đếm sai 3→5.

**5 luật rút ra (đã nhét vào §6 NGUYÊN TẮC BẤT DI — đọc mục đó):**
1. Vào đúng màn = **API 200 + DATA THẬT hiện ra**, KHÔNG phải HTTP 200 / "thấy chữ gì đó".
2. **PASS không có ĐỐI CHỨNG = PASS vô nghĩa.**
3. **Unit-test và live-verify khoá 2 thứ KHÁC nhau** — thiếu vế nào cũng chết.
4. Vá false-positive **rất dễ đẻ false-negative** → test cả 2 chiều.
5. **Chờ ĐIỀU KIỆN, không chờ ĐỒNG HỒ** (phạm lại luật `pw_lib.shot()` đã ghi từ lâu).

**Quyết định user chốt phiên này** (xem đầy đủ ở mục "Đã đề xuất → user BÁC"):
bỏ hẳn **admin** ("từ nay luôn") · **giao bug** là việc user · **pro visual** không làm ·
**Safari/webkit** chấp nhận lỗ · security mutating trên reservation không chạy · chỉ ghi data trên **Pro**.

## 4. Cách maintain khi 5 repo update

`refresh-gitnexus.sh` (graph tươi — **CHỈ graph**) → **`/testcase-stale`** (so `source_hash`) →
re-derive + re-confirm **CHỈ doc drift**.
⚠️ refresh KHÔNG tự update `knowledge/`. Graph hiện **đang tươi** (index 2026-07-06/08, không repo nào
báo `commitsBehind`) → chỉ chạy refresh khi 5 repo thực sự có commit mới.
Ngân sách GitNexus thật (processes/repo) + 3 loại stale: [`KNOWLEDGE-STRATEGY.md`](KNOWLEDGE-STRATEGY.md) §1, §4b.

## 5. Access nhanh (dev) — để chạy ngay

- Creds: `wtf-is-this/account.txt`. `pw_lib`: `getPage('pro'|'ticket'|'ticket_admin'|'reservation'|'admin')`.
- **Report ticket cần** `TESTSEED001/ticket-admin/password123` → env `TK_STAFF=ticket-admin`.
- Chụp ảnh: **`shot(page, path, readySelector)`**. Gọi API: `withApi()` (tự sniff token).
- Data test: prefix `AIOT-TEST-*`/`AIOTTEST*` → `/testcase-cleanup` (cần `BRANCH_ID=<phiên hiện tại>`).
- **Branch phiên `TESTSEED001` hiện = `3`** (đo 2026-07-09; branch sai → API trả 404).
- Booking mẫu để drive: **`Jenny` 07/09 14:20, branch 3, id=774, `一部支払済み`, có vé `AIOT-TEST-TK1` + coupon**.
  ❌ `AIOTTEST-KH3` booking 07/13 **không còn tồn tại** (đã bị dọn) — ghi chú cũ đã sai.
- 🗑️ Rác còn trên dev (đo lại **2026-07-17**): preset ✅ **SẠCH** (6 preset gốc, 0 `AIOT*` — mục `AIOT-TEST-105`
  cũ đã hết). Chưa đo lại: staff `AIOT Test105`, ticket master `AIOT-TEST-TK1` (2 cái này **không có API xoá** → nhờ dev xoá DB).
- **Pro auth = devise-token ở `localStorage.user`** (`{"id":..,"accessToken":".."}`), gửi qua **header**
  `access-token/client/uid/expiry/token-type`. **KHÔNG có cookie phiên** (cookie chỉ là GA/AMP/cwr).
  Logout = `DELETE /auth/sign_out` → token cũ thành **401**.
- **Chỗ ghi data test AN TOÀN nhất trên Pro = preset quyền**: `POST /permissions/presets` →201 ·
  `DELETE /permissions/presets/{id}` →204 · `cleanup.js` quét prefix `AIOT-TEST`. Shape `{id,name,default_preset,permission_slugs[]}`.
- **Route thật**: pro đặt lịch = **`/reservations`** (KHÔNG phải `/branches/N/reservations/` — cái đó ra vỏ ホーム) ·
  pro kế toán = `/accounting` · reservation widget = **`/reservation`** (số ít; `/` ra soft-404). Nuxt cần **~7-8s** render.
- Build xlsx: `python3 .claude/skills-scripts/testcase-evidence/build_evidence.py <F>/tcs.json <F>/<Tên>.xlsx`.
- Factcheck TRƯỚC mọi build: `python3 .../factcheck_report.py <file>.json` (gate filler + tally bịa).
- Session cache: `.state.<target>.json` — `NO_STATE=1` để login sạch.

## 6. NGUYÊN TẮC BẤT DI (đừng phá — đã từng trả giá)

1. Oracle = **SPEC**; viết `expect` MÙ code. `METHOD.md` cấp **coverage**, KHÔNG cấp `expect`.
2. QA-runtime **mù code, không GitNexus, không `knowledge/system/**`**; FAIL báo **hành vi + ảnh**,
   không symbol/file:line.
3. **KHÔNG code-trace để phán "đã build/chưa"** — đã SAI **2 lần** (guard vé-đã-dùng; coupon report).
   Dùng `route_map` (build-time) + quan sát live.
4. `knowledge/` = navigation (HOW), KHÔNG phải oracle. Graph→`draft`; UI-confirm→`approved`.
5. **`grep` không thấy ≠ không tồn tại** → `OPEN-QUESTIONS.md`, không ép thành "có"/"không".
6. Spec im lặng ở chỗ METHOD bảo phải kiểm → **`SPEC-GAP`**, KHÔNG bịa `expect`.
7. Specs sau này = **tinh chỉnh/update** business đã map, không build lại từ 0.
8. **PASS không có ĐỐI CHỨNG = PASS vô nghĩa.** (2026-07-17) mass-assignment ra `422` → tưởng server phòng thủ
   tốt; thật ra bị chặn vì **lý do khác** (gửi kèm `id` lạ). Phải **tách biến**: A hợp lệ→201 (baseline chứng minh
   thao tác chạy được) rồi B chỉ thêm **đúng 1** field đặc quyền. Không có A thì B nói lên **con số không**.
9. **Unit-test và live-verify khoá HAI thứ KHÁC NHAU — thiếu vế nào cũng chết.** Unit-test khoá *oracle đúng
   logic*; live-verify khoá *probe có thật sự chạm app*. **4 bug oracle** (2026-07-17) đều chỉ lộ khi chạy thật:
   csrftoken-HttpOnly · IDOR HTML-oracle · **SPA trả cùng vỏ mọi path** (`/etc/passwd` FAIL giả trên pro+reservation) ·
   **rò Rails qua message** (`Couldn't find Therapists::Preset … WHERE "bảng"."cột"` — oracle chỉ tìm tên class nên trượt).
10. **Vá false-positive rất dễ đẻ false-negative.** Bản vá SPA đầu (chỉ đo độ dài text) bị **chính unit test bắt**:
   nó nuốt luôn trang lộ thật nhưng ngắn. Ở security, **bỏ sót nguy hiểm hơn báo nhầm** → mọi bản vá phải có
   test **cả hai chiều** (bắt được ca thật + không nuốt ca thật).
11. **Số lạ → MỞ ẢNH / đọc body.** `200` trên SPA **không** nghĩa là route tồn tại (Nuxt trả cùng vỏ cho mọi path).
   Đừng dùng status để phán "có/không có màn" — chỉ Django/Rails mới 404 thật.

## 7. Trạng thái git / task nền

- Branch `qa-brain` — **local == remote**, working tree **sạch** (chốt 2026-07-17).
- `wtf-is-this/` đã gitignore (evidence + sổ bug = **LOCAL ONLY**, user tự đưa lên Drive). `.state.*.json` đã gitignore.
- ✅ `.claude-tester/` **đã xoá** (archive `0119159`, xoá `822d5dd`). Tra nguồn: `git show 0119159:.claude-tester/<path>`.
- Đống transition Python→skill (`D qa/ api/ web/ tests/`) còn trong index — **để user tự xử**.
- Không có background task đang chạy.

**Chạy lại toàn bộ test của hệ QA (nên làm đầu phiên nếu đụng lib):**
```bash
cd .claude/skills-scripts/testcase-evidence && NODE_PATH="$PWD/node_modules" node --test   # 71 xanh
python3 .claude/skills-scripts/testcase-evidence/test_factcheck_report.py                   # 7 xanh
```
⚠️ **Playwright:** chỉ có **chromium + firefox**. **webkit KHÔNG cài được** (macOS 13.7.8) — đã chốt chấp nhận.
Cài browser phải dùng binary LOCAL (`./node_modules/.bin/playwright install`), `npx playwright` lấy bản khác → lệch version.

---

## 📌 TODO cũ (INFRA, ngoài QA) — "phân tách" claude-mem observer

> Ghi 2026-07-08. Chưa làm. Không chặn việc QA.

- Đo thật: **claude-mem observer (Haiku) = ~2.3% tổng token** → **KHÔNG phải thủ phạm**.
  Thủ phạm = 1 session QA marathon (peak 863k ctx → cache_read 200M). Fix: `/compact`/`/clear` **sớm**.
- Bash đã được skip đúng trong `~/.claude-mem/settings.json`.
- Việc còn: xem 32 observer session/ngày có dư không · gọn nền mỗi phiên (MCP registry ~52k deferred).
- Ruflo: **đã gỡ sạch** 2026-07-08.
