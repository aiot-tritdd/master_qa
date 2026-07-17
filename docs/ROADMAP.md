# ROADMAP — threease_qa lớn lên theo hướng nào

> Bản đồ tầm nhìn (KHÁC `STATE.md` = việc-phiên-này). Mở file này để biết *đang đứng đâu trên bức
> tranh lớn, còn mở được gì, và vì sao*. Cập nhật khi hướng đổi, không phải mỗi phiên.
> Cập nhật: **2026-07-17** (sync sau đợt pro+reservation+compat+perf).
>
> 🔔 **Trạng thái 1 dòng:** con black-box **CẠN VIỆC** — 6/6 type xong · admin chốt bỏ · lỗ độ-phủ đáng vá đã đóng.
> Mở rộng thật sự **chỉ còn whitebox (§4)**, mà nó kẹt ở **quyền sở hữu** (cần sếp/dev đồng ý cho agent viết test
> vào 5 repo), không phải kẹt kỹ thuật. Việc-làm-được-ngay: **KHÔNG CÓ**. Xem `STATE.md` khối đầu.

---

## 1. Vision — QA tái dùng cho MỌI dự án, không riêng ThreeSides

Đích đến: con QA này là **engine dùng lại được across nhiều dự án**, không phải đồ đóng cứng cho ThreeSides.

Chìa khoá phân loại tri thức theo *độ tái dùng*:

| Phần | Tái dùng across dự án? |
|---|---|
| **Functional** (SPEC + navigation nghiệp vụ) | ❌ riêng từng dự án |
| **a11y / Visual / Performance / Compatibility** (engine phổ quát: axe, so-ảnh, đo-timing) | ✅ gần như 100% — chạy trên web app bất kỳ |

⇒ Mỗi **type-track** build một lần, xài cho mọi dự án sau. Phần dính-dự-án chỉ còn SPEC + nav.
Đây là lý do type-track ĐÁNG đầu tư theo vision này.

---

## 2. Lưới định vị — Level × Type

Hai trục vuông góc (xem `docs/.../Deep-Guide` hoặc README §"Tầng test"):
- **Level** = zoom (Unit → Integration → System/E2E). Con hiện tại kịch trần ở **E2E/System** — vì mù code, KHÔNG thể tụt xuống.
- **Type** = phẩm chất kiểm (Functional / a11y / Visual / Performance / Security / Compatibility).

### Đang đứng đâu (2026-07-17)

```
Level: E2E/System ─── con black-box hiện tại sống ở đây
                      Unit + Integration ─── TRỐNG (chỉ whitebox mới với tới, xem §4)

Type:  Functional      ✅ có
       Accessibility   ✅ DONE + live-verify (ticket · pro · reservation) — oracle=WCAG
       Security        ✅ DONE + live-verify (13 họ; đủ 13/13 trên pro) — oracle=bất biến an ninh
       Visual          ✅ DONE + live-verify — nhưng CHỈ hợp màn TĨNH (xem cảnh báo §3)
       Compatibility   ✅ DONE + live-verify (reservation widget) — oracle=WCAG 1.4.10 + parity engine
                       ≈67% ổn: 8/12 ô chạy, 8/8 PASS. Safari 未実施 — user CHỐT chấp nhận lỗ (2026-07-17)
       Performance     ✅ DONE + live-verify — oracle=Core Web Vitals (ngưỡng Google công bố)
                       ⚠️ LAB≠FIELD: đo 1 máy/1 mạng/trên dev = CẬN DƯỚI của mức tệ, không phải chứng nhận nhanh

⇒ **CẢ 6 TYPE ĐỀU XONG** — hết đường đi ngang. Trục ĐỘ PHỦ APP cũng đóng (**admin: user chốt bỏ hẳn 2026-07-17**).
⇒ **Mở rộng thật sự CHỈ CÒN trục LEVEL: whitebox (§4)** — mà nó kẹt ở **quyền sở hữu**, không phải kỹ thuật.
```

**Độ phủ app (2026-07-17)** — type-track ≠ app đã quét. Phủ **3/5** app; admin **bỏ có chủ ý**, backend không có UI:

| App | Functional | a11y | Visual | Security | Compat | Perf |
|---|---|---|---|---|---|---|
| ticket | ✅ TestCase-11 | ✅ | ✅ (3 baseline) | ✅ 13 họ | 🔻 bỏ (app nội bộ) | ✅ 3 màn — **PASS** |
| pro | ✅ TestCase-12 | ✅ 2 màn | ❌ | ✅ **13/13 họ** | ❌ | ✅ 2 màn — **FAIL** |
| reservation | ⛔ **không có SPEC** → không chấm được | ✅ 1 màn | ❌ | ✅ 6 họ read-only | ✅ 2/3 engine × 4 cỡ (Safari bỏ) | ✅ 1 màn — PASS |
| ~~admin~~ | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 ← **user CHỐT BỎ HẲN 2026-07-17** (không test, không đề xuất lại) |
| backend | — (không có UI; quét gián tiếp qua API của pro) | — | — | — | — | — |

> ⚠️ **reservation không có SPEC** ⇒ functional **cấu trúc không chấm được** (không oracle → không bịa `expect`).
> Muốn test functional widget: phải có spec trước. Type-track thì chạy được vì oracle phổ quát.

**Sổ bug: 39 · Mở 39 · Đã đóng 0.** 🚫 **Giao bug = việc của user** (tự đưa file lên Drive; `wtf-is-this/` giữ
gitignore) — chốt 2026-07-17. Con QA **không lo khâu giao**; trách nhiệm dừng ở: sổ + report **đúng, sạch, đọc được**.
Vòng đời `Mở → Chờ retest → Đã đóng` + `/testcase-retest` vẫn **chưa chạy lần nào** — sẽ chạy khi dev bắt đầu fix.

---

## 3. Type-track — thứ tự & trạng thái

| Track | Trạng thái | Oracle (độc lập code) | Tận dụng |
|---|---|---|---|
| Functional | ✅ core | SPEC + quan sát live | qa-brain |
| **Accessibility** | ✅ **DONE — live-verified** (ticket 2026-07-17 · pro + reservation 2026-07-17) | WCAG (axe-core) | `shot()`, khuôn command |
| **Security (gom)** | ✅ **DONE — live-verified** (**13 họ**; ticket 13 · **pro đủ 13/13** · reservation 6 read-only) | bất biến an ninh phổ quát (XSS escaped, no 500/leak, IDOR 403/404, guard-parity, cookie/CORS/fixation) | `withApi`, khuôn a11y |
| **Visual** | ✅ **DONE — live-verified** (bless 3 baseline ticket) · ⚠️ CHỈ dùng cho màn **TĨNH** | baseline PNG đã người-duyệt | `shot()` sẵn + khuôn a11y |
| **Compatibility** | ✅ **DONE — live-verified** (`/testcase-compat`, 12 test, widget **8 PASS / 4 未実施 ≈ 67% phủ**) · Safari: **user chốt chấp nhận lỗ** | **WCAG 1.4.10 Reflow** (mốc 320px, W3C công bố) + parity affordance giữa engine + 0 `pageerror` | Playwright multi-context |
| **Performance** | ✅ **DONE — live-verified** (`/testcase-perf`, 8 test; widget PASS · **pro FAIL: TBT 1184ms = 6× ngưỡng**) | **Core Web Vitals** — LCP/CLS/TBT/FCP/TTFB < ngưỡng **Google công bố** (web.dev) | `PerformanceObserver` + `pw_lib` |

**🔬 Live-verify là thật, không phải thủ tục — 6 bug ORACLE + 1 bug URL bị bắt nhờ nó** (không có nó thì cả 4 đã lọt thành
bug bịa gửi cho dev, hoặc PASS rỗng che lỗi thật):

| # | Ngày | Probe bịa gì | Sự thật | Vá |
|---|---|---|---|---|
| 1 | 07-17 | `csrftoken` thiếu HttpOnly = yếu | CSRF cookie **cố tình** để JS đọc (double-submit) | chừa csrf khỏi luật HttpOnly |
| 2 | 07-17 | IDOR/force-browse "200 + lộ data" (ticket) | oracle HTML sai | vá HTML-oracle |
| 3 | 07-17 | **`/etc/passwd` lộ trên pro + reservation** | body path cấm **=== body path hợp lệ từng byte**; không có `root:x:`; DOM sau render = **404** ⇒ app chặn ĐÚNG. SPA trả cùng vỏ cho mọi path, `context.request` không chạy JS | `probeIDOR(r,{baselineBody})` → giống baseline = `inconclusive`; + `looksLikeSpaShell()` dự phòng |
| 4 | 07-17 | error-disclosure "không rò" (pro) | 422 rò `Couldn't find Therapists::Preset … WHERE "therapists_presets"."institute_id"` = **model + bảng + cột tenant**. Oracle cũ chỉ tìm **tên class** exception nên trượt | +2 pattern `rails-record-not-found`, `sql-fragment` |
| 5 | 07-17 | compat: chromium FAIL / firefox PASS (6 "lỗi JS") | 6 "lỗi" là **resource-404**, mà chromium ghi ra console còn **firefox KHÔNG** ⇒ đang đo *cách browser ghi log*, không phải app vỡ | `probeConsole` chỉ nhận `pageerror`; 404 tách sang `networkFailures` (chuyện functional) |
| 6 | 07-17 | compat parity: firefox lệch nút `閉じる` | Lúc firefox **thiếu** (320px), lúc **thừa** (390px) — **tự mâu thuẫn** ⇒ dialog chớp nhoáng, không phải khác biệt engine | `detectTransient()` (vừa-thiếu-vừa-thừa) + `probeParity(…,{transient})`, luôn báo `ignored` |
| 🎯 | 07-17 | **a11y/security widget: đo SAI URL suốt** | `/reservation` **không phải** đường vào — app hiểu path là **slug phòng khám** → đi tìm院 tên "reservation" → **404 toàn bộ API** → đo widget **rỗng data**. Đúng là **`/2`** (5 API 200, hiện `AIoT院1`) | Đo lại: **BUG-033 (link-name) là bug MA** của trang lỗi → xoá; BUG-031 color-contrast **3→5**. Sổ 37→36 |

⇒ **Luật rút ra:** ① *unit-test khoá oracle, live-verify khoá "probe có chạm app thật"* — thiếu vế nào cũng chết.
② **PASS không có đối chứng = PASS vô nghĩa** (mass-assignment lần đầu ra 422 vì gửi kèm `id` lạ → bị chặn vì
lý do KHÁC; phải tách biến: A hợp lệ→201, B chỉ thêm `default_preset:true`→201 nhưng field bị bỏ qua).
③ **Vá false-positive rất dễ đẻ false-negative** — bản vá SPA đầu tiên (chỉ đo độ dài text) bị chính unit test
bắt vì nó nuốt luôn trang lộ thật nhưng ngắn. Ở security, **bỏ sót nguy hiểm hơn báo nhầm**.
④ **HTTP 200 + màn có render ≠ vào ĐÚNG màn.** Bẫy đắt nhất đợt này: quét cả a11y lẫn security trên `/reservation`
suốt, widget *có* hiện `コース選択` nên tưởng đúng — thật ra API 404 hết, đang đo **trạng thái lỗi**. ⇒ Xác nhận vào
đúng bằng **API 200 + DATA thật hiện ra** (tên phòng khám), KHÔNG bằng status/“nhìn thấy chữ gì đó”.
⑤ **Chờ ĐIỀU KIỆN, không chờ ĐỒNG HỒ** — `waitForTimeout(7000)` chấm 未実施 OAN cho desktop (giây 7 vẫn đang
loading). Luật này `pw_lib.shot()` đã ghi từ lâu mà vẫn phạm lại.

**⚡ Performance — ROADMAP cũ nói "vướng oracle, cần người đặt budget". SAI, đã gỡ (2026-07-17):**
**Core Web Vitals** (LCP < 2.5s · CLS < 0.1 · INP < 200ms) là ngưỡng **Google công bố công khai** — phổ quát,
không phụ thuộc dự án, **y hệt vai trò WCAG với a11y**. Không cần ông chủ dự án đặt số nào. ⇒ Performance
**đủ điều kiện oracle-phổ-quát/0-setup**, ngang hàng a11y — không còn lý do hoãn vì oracle.
(Cái *thật sự* cần người quyết chỉ là budget **riêng-dự-án** kiểu "màn X phải < 800ms" — đó là *thêm*, không phải *điều kiện cần*.)

**Vì sao HOÃN Visual — quyết 2026-07-16, GIỮ NGUYÊN (dù track đã build xong):** Visual là track **kém "drop-in" nhất**,
ngược vision "engine đa dự án ít setup":
- Cần **baseline curated PER-PROJECT** (chụp + gật + mask data động + maintain) → setup lặp mỗi dự án.
- **Regression-only** — dự án mới chưa có baseline thì chưa nói được gì (mà QA generic hay rơi vào "dự án mới đúng spec không" — chỗ Visual mù).
- **Noise cao nhất** (font/anti-alias/data động) → người không rành tune sẽ ngó lơ → track chết.
- Đối chiếu a11y: WCAG = oracle tuyệt đối + phổ quát + **0 setup** → đó mới là hình mẫu "reusable".
⇒ Visual **đáng cho dự án trưởng thành/ổn định chạy lặp nhiều** (ThreeSides về sau), KHÔNG phải track kế tiếp
cho vision đa-dự-án. Ưu tiên trước: **Performance · Compatibility · Security-gom** (0 setup per-project, oracle phổ quát).

**⚠️ Giới hạn auto-mask (live-verify 2026-07-17):** `explorer.js dynamic`/`detectDynamic` chỉ bắt **động
TRONG-phiên** (đồng hồ/spinner/animation tự nhảy giữa 2 snapshot cùng-trạng-thái). Nó **KHÔNG thấy
"động XUYÊN-phiên"**: dữ liệu bảng đổi khi tester thêm/xoá data, số dư đổi theo ngày. Trên màn data-heavy
(vd coupon list, 顧客詳細) auto-mask trả `[]` (tưởng tĩnh) nhưng baseline vẫn **FAIL-giả** khi data đổi →
phải re-bless. Muốn hết noise phải **mask vùng-data tay** (điều user không thích) hoặc chỉ bless màn UI ổn định.
Đây là lý do thực nghiệm củng cố "Visual = dự án mature/ổn định".

**❌ QUYẾT 2026-07-17: KHÔNG chạy Visual cho pro/reservation.** Đề xuất chạy → **user bác, đúng.** Hai lý do:
1. Lần đầu chỉ sinh **NEW-BASELINE** → **0 verdict, 0 bug** hôm nay; giá trị chỉ đến từ lần *sau*.
2. Cả 3 màn đều **đổi theo NGÀY**: calendar Pro hiện `2026/07/17 (金)`, widget hiện dãy `17→23`, 会計 có
   số tiền/giao dịch. Mai chụp là khác ⇒ diff đỏ mỗi ngày. Đúng loại **"động XUYÊN-phiên"** mà auto-mask
   **không thấy** (cảnh báo ngay trên). ⇒ Visual ở đây = **máy đẻ nhiễu**, không phải máy bắt bug.
⇒ **Luật dùng Visual:** chỉ bless màn **TĨNH** (form, cài đặt, login). Màn có ngày/tiền/danh sách → **đừng**.

**Bỏ qua (quyết 2026-07-16 · rà lại 2026-07-17):**
- **Analyzer** (gom cụm bug) — ⚠️ *lý do cũ đã lỗi thời*: viết khi sổ "11 bug/1 nguồn"; **nay 39 bug / 4 loại**
  (a11y 21 · Function 11 · Security 4 · Perf 3). Rà lại 2026-07-17: **vẫn hoãn** — dedup hiện làm bằng tay lúc
  đẩy sổ (1 bug/(màn×họ×payload-class), gom site-wide cho headers) và vẫn ổn. Mốc xét lại: **sổ > ~80 bug**
  hoặc khi cụm trùng bắt đầu lọt.
- **PreToolUse hook** (biến tường thép thành cơ chế) — OQ-09. **User bác lại 2026-07-17** khi được đề xuất → giữ hoãn.
  ⚠️ Rủi ro còn nguyên: "QA mù code" hiện **chỉ là chữ**, không có gì chặn kỹ thuật.

---

## 3b. Bước kế — xếp theo GIÁ TRỊ BIÊN (chốt 2026-07-17)

> Xếp theo *"làm cái này thì thay đổi được gì"*, KHÔNG theo "cái nào vui".

| # | Việc | Vì sao đứng đây | Chặn gì |
|---|---|---|---|
| **1** | **Whitebox — 1 lát mỏng** (§4) | **Thứ DUY NHẤT còn lại thực sự mở rộng hệ.** Trục ngang (Type) đã 6/6; chỉ còn trục dọc (Level): Unit + Integration — con đen **cấu trúc không thể** với tới | ⛔ **cần sếp/dev đồng ý** cho agent viết test vào 5 repo sản phẩm (§4 cục chặn #3) |
| **2** | **IDOR** | Họ duy nhất còn `未実施`. Access-control là loại nặng nhất mà đang **mù** | ⛔ cần **account institute #2** (`TESTSEED002`) |
| ✅ | ~~`ticket` — Perf~~ | **XONG 2026-07-17: 3/3 màn PASS, 0 bug** (TBT 0–4ms). Lỗ độ-phủ đáng vá cuối cùng → đã đóng | — |
| 🔻 | `ticket` — Compat | Giá trị thấp: app **nội bộ**, nhân viên dùng desktop/Chrome máy công ty. Compat đáng cho app **công khai** (đã làm widget) | không — nhưng đừng ưu tiên |
| 🚫 | ~~Admin app~~ · ~~`pro` Visual~~ · ~~giao bug~~ · PreToolUse hook · Analyzer | **user đã BÁC** — xem `STATE.md §3 "Đã đề xuất → user BÁC"`. Đừng đề xuất lại | — |

**Con đen coi như XONG.** 6/6 type · admin chốt bỏ · lỗ độ-phủ đáng vá cuối (ticket perf) đã đóng
⇒ mở rộng thật sự **chỉ còn whitebox**, mà whitebox kẹt ở **quyền sở hữu**, không phải kỹ thuật.

**📊 Vấn đề tốc độ KHU TRÚ ở Pro, không phải "hệ chậm"** (quan sát 2026-07-17, không chẩn đoán nguyên nhân —
đó là việc dev): `ticket` **TBT ≈ 0ms** · `reservation` **TBT 106ms** · `pro` **TBT 1184ms** (đơ ~1.2s).

---

## 4. Kiến trúc 2-con — black-box (nay) + whitebox (tương lai)

**Ý tưởng cần build, ghi lại kẻo rơi.**

Con hiện tại mù code ⇒ **cấu trúc không thể** phủ đáy pyramid (Unit/Integration). Muốn phủ ⇒ **con thứ hai**:

```
threease_qa (black_box)      Level E2E/System · MÙ code · oracle = SPEC + quan sát live
threease_qa_whitebox (MỚI)   Level Unit + Integration · ĐỌC code · GitNexus lúc RUNTIME
```

Tách đôi = giữ **linh hồn mỗi con sạch**: tường chống-tautology của black-box không bị nhiễm; con whitebox
tự do đọc code. GitNexus đã index 5 repo → whitebox có code-graph sẵn.

**Mô hình 2-con hồi sinh mấy nguồn đã "khai tử" cho black-box:**

| Nguồn (khảo sát 2026-07-16) | Vai trong whitebox |
|---|---|
| test-automator (VoltAgent) | lõi: dựng framework unit/IT, coverage, CI |
| security-auditor (VoltAgent) | nhánh security white-box (SAST, audit code) |
| qa-skills: `unit-testing`, `api-testing`, `database-testing`, `contract-testing`, `coverage-analysis` | bị CẤM ở black-box, HỢP LỆ ở whitebox |
| qa-expert | strategy chung 2 con |

**🔐 Bàn giao SECURITY cho whitebox (chốt sau live-verify `/testcase-security` 2026-07-17):**
Track black-box `/testcase-security` phủ **phần OWASP quét-được-từ-ngoài** (A01 access-control · A05 injection ·
A02 misconfig · A07-phần session · A10 exceptional-conditions) — **13 họ** (OWASP **2025** mapping).
**Những category sau BẤT KHẢ với black-box → whitebox PHẢI ôm:**
| OWASP còn thiếu | Vì sao black-box không tới | Whitebox làm gì |
|---|---|---|
| **A02** Cryptographic Failures | cần soi TLS/cipher/thuật toán/nơi lưu secret | đọc config + code crypto |
| **A04** Insecure Design | thuộc kiến trúc, không có "đòn" quan sát được | review threat-model + data-flow trên code-graph |
| **A06** Vulnerable Components | cần đọc dependency/lockfile (SCA/SBOM) | quét `Gemfile.lock`/`package-lock`/`requirements` vs CVE |
| **A08** Integrity Failures | deserialize/CI-CD/pipeline — không lộ ra UI | audit code deserialize + pipeline config |
| **A09** Logging & Monitoring | không observable từ ngoài | kiểm code có log/alert sự kiện bảo mật |
| **A10** SSRF | chỉ test được NẾU có feature fetch-URL (coupon không có) | trace sink `fetch/open(url)` trên code-graph |
- **Giới hạn ĐỘ SÂU đã biết:** black-box probe là **1-shot heuristic** (không chuỗi vuln, không fuzz sâu như
  ZAP/Burp). Whitebox + SAST bù phần sâu. **IDOR object-level** black-box cũng yếu (cần id cross-tenant thật)
  → whitebox có id/quan hệ từ DB-schema, test IDOR chính xác hơn.
- **Giới hạn kiểu app (đo thật 2026-07-17):** trên **SPA client-render** (Nuxt/Vue/React), oracle "đọc HTML từ
  raw request" **vô dụng** — server trả cùng vỏ cho mọi path, verdict nằm trong DOM sau JS. ⇒ black-box **buộc**
  phải drive browser thật; công cụ chỉ-HTTP (curl/ZAP baseline không-JS) sẽ báo bừa. Whitebox không dính vấn đề này.
- **Cửa đã đóng nhờ black-box (đừng whitebox lại từ đầu):** trên pro đã xác nhận **mass-assignment** (server bỏ
  qua field đặc quyền), **client-bypass** (server ép cùng ràng buộc UI), **session-after-logout/fixation** (token
  chết sau logout; token cắm sẵn → 401), **password-leak** (không rò qua response/URL/localStorage; login chỉ đi https).
- **Neo oracle:** security whitebox vẫn KHÔNG được "code nói an toàn nên an toàn" — oracle = chuẩn an ninh
  (OWASP/CWE) + threat-model, code chỉ để *biết chỗ cần soi* (đúng cạm bẫy tautology §dưới).

**🍞 Breadcrumb cho whitebox/chiến-lược (chốt 2026-07-17, ĐÃ đọc file skill thật):**
Mấy nguồn dưới đây khảo rồi, **cố tình KHÔNG bê cho con đen** vì là whitebox/strategy — để sẵn cho con sau nhặt,
khỏi khảo lại:
| Nguồn (đã đọc) | Món cụ thể bê được | Cho ai |
|---|---|---|
| `qa-skills/security-testing` (references: `scanning-and-ci.md`, `auth-tests.md`, `owasp-tests.md`) | **ZAP (DAST)** baseline scan · **OSV-Scanner (SCA/gate)** + SBOM/provenance (A03) · **Semgrep `p/owasp-top-ten` (SAST)** · secret-scan (TruffleHog) · JWT tests (`alg:none`/expiry/wrong-key) · 5-layer CI pipeline | whitebox — security |
| **security-auditor** (VoltAgent) | audit config/policy/log theo SOC2/ISO/PCI/HIPAA/NIST (Read/Grep/Glob) | whitebox — security/compliance |
| **test-automator** (VoltAgent) | dựng framework unit/IT/perf + CI, mục tiêu >80% coverage, flaky <1% | whitebox — lõi |
| `qa-skills` nhánh trắng: `unit-testing`·`coverage-analysis`·`database-testing`·`contract-testing` | test tầng đáy pyramid theo runner từng repo | whitebox — lõi |
| **qa-expert** (VoltAgent) | test-strategy/plan · quality-metrics (defect-density, coverage, quality-score) · điều phối test-automator/security-auditor | **chiến-lược** — trùm 2 con |
- ⚠️ **Neo lại tautology:** whitebox bê mấy cái trên vẫn phải giữ oracle = SPEC/chuẩn (OWASP/CWE), KHÔNG để "test sinh từ code". Chi tiết 3 cạm bẫy ở cuối §4.
- Bản đối chiếu đầy đủ + phần ĐÃ bê cho con đen: xem **§5 Harvest log (2026-07-17)**.

**3 cạm bẫy phải giải trước khi build whitebox:**
1. **Tautology áp thẳng vào whitebox.** Test sinh từ code = "code làm đúng cái code làm" = vô nghĩa (đúng cái
   README black-box chửi). ⇒ whitebox vẫn phải neo oracle vào **SPEC** (test tầng unit/IT nhưng kỳ vọng từ spec);
   code chỉ để *biết đường test tới đâu*, KHÔNG để *quyết đúng/sai*.
2. **Scope ×5 repo.** Unit/IT sống TRONG từng repo, bằng ngôn ngữ repo (RSpec/pytest/Jest) — 3 test-runner,
   không phải "Claude lái Playwright". Gần như 1 QA-engineer-in-a-box cho 5 codebase.
3. **Ownership.** Unit/IT thường DEV tự viết trong repo. Agent riêng viết test vào 5 repo sản phẩm = mô hình
   sở hữu khác → cần sếp/dev đồng ý, không chỉ là quyết định kỹ thuật.

**Khuyến nghị khi khởi động:** làm **1 lát mỏng trước** (vd chỉ Integration/API-contract cho 1 flow, oracle vẫn SPEC)
để thử mô hình — đừng nuốt cả đáy pyramid × 5 repo ngay.

---

## 5. Khảo sát nguồn tham khảo (2026-07-16) — dùng gì cho đâu

| Nguồn | Cho black-box | Cho whitebox |
|---|---|---|
| **petrkindlmann/qa-skills** | a11y ✅ · visual/security/perf (seed) | unit/api/db/contract/coverage |
| VoltAgent **ui-ux-tester** | seed persona Visual/UX | — |
| VoltAgent **test-automator** | — (white-box, sai tool) | 🟢 lõi |
| VoltAgent **security-auditor** | — (white-box) | 🟢 nhánh security |
| VoltAgent **qa-expert** | metrics (đã có breakdown xlsx) | strategy |
| **Testsigma** | ý 5-agent (đã rút) | — |

### Harvest log (2026-07-17) — đọc file skill thật rồi mới chốt
> ✅ **Queue harvest cho con đen: ĐÓNG.** 3 món đã bê + verify xong (dưới). 4 nguồn còn lại park cho whitebox/strategy.
Sau khi **đọc nội dung thật** (không đoán mô tả) 3 skill của `qa-skills` (kindlmann, MIT):
- ✅ **BÊ NGAY — con đen:** `exploratory-testing` → **HICCUPS/FEW HICCUPS** đã nhét vào `qa-brain` §3.4
  (bộ 10 oracle-lens nhận diện bug; Claims=SPEC, Standards=WCAG, World=Compatibility — code-blind, không phá tường).
- ✅ **BÊ RỒI — con đen (đã live-verify / test):**
  - `security-testing` → nâng `security_lib` **v2 (LIVE-VERIFIED 2026-07-17)**: **OWASP remap 2021→2025** (A03=Supply-Chain, A10=Exceptional-Conditions,
    SSRF gộp A01/A06), thêm probe **cookie-flags / path-traversal / CORS / session-fixation** (3 họ v2 đều PASS), đổi sang
    **acceptable-status-set** (`expect([...]).toContain`), **meta-verify bằng OWASP Juice Shop** (chĩa probe vào app
    cố-tình-lỗi để chứng minh probe bắt thật, không PASS rỗng).
  - ✅ `qa-report-humanizer` → **`factcheck_report.py`** (+7 test): GATE filler/AI-tell + tally-bịa (số PASS/FAIL summary khớp đếm thật), WARN passive/vague. Chạy TRƯỚC build mọi report-source JSON (BUG-LOG §3 + command doc).
- 🔵 **PARK cho whitebox/chiến-lược (KHÔNG bê cho con đen):**
  - **security-auditor** (VoltAgent) → nhánh security con whitebox (đọc config/SAST/compliance) — đã có ở §4.
  - **test-automator** (VoltAgent) → lõi con whitebox (framework unit/API/CI, coverage) — đã có ở §4.
  - **qa-expert** (VoltAgent) → lớp **strategy/metrics** trùm 2 con (test-plan, defect-density, quality-score) — dùng khi dựng chiến lược, không phải track.
  - **testsigma** → chỉ khái niệm (5-agent, Healer/Analyzer) — đã rút, không có code bê được.
