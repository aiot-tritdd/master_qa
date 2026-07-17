# /testcase-security — Test Security (bất biến an ninh, black-box) một TestCase

Quét security các màn spec đang test đụng tới, theo checklist **13 họ** (tất cả đã live-verify trên ticket-dev
2026-07-17; 6 họ read-only re-verify trên pro + reservation). **Track RIÊNG**, KHÔNG trộn PASS/FAIL functional.
Oracle = **bất biến an ninh PHỔ QUÁT** (không phải spec). Mù code.

> ⚠️ Quét **app SPA** (pro / reservation / admin — Nuxt)? Đọc mục **"App SPA — BẮT BUỘC cấp `baselineBody`"**
> bên dưới TRƯỚC khi chạy. Bỏ qua = FAIL giả hàng loạt (đã cắn thật 2026-07-17).

## Cách dùng
`/testcase-security wtf-is-this/TestCase-XX`

## TIẾT KIỆM TOKEN
Dùng lại `.claude/skills-scripts/testcase-evidence/`: `pw_lib` (`getPage`,`shot`), `pw_api` (`withApi`),
`security_lib` (`PAYLOADS`, `probeInjection/probeIDOR/probeBypass/probeErrorDisclosure`, `finding`),
`a11y_lib` (`shotViolation` — dùng lại để khoanh chỗ), `build_security_report.py`. KHÔNG viết lại.
Setup 1 lần: `cd .claude/skills-scripts/testcase-evidence && npm i`.

## Nguyên tắc (2 tường)
- **Oracle = bất biến an ninh phổ quát.** `specs.md` chỉ chọn màn (scope), KHÔNG làm oracle.
- **Mù code.** Không đọc code / GitNexus / `knowledge/system/**`. Chỉ quan sát response + DOM + browser.

## 13 họ + oracle (phủ phần black-box của OWASP **2025**; FAIL khi bất biến bị phá)
> OWASP mapping = **Top 10 2025** (owasp.org/Top10/2025): A02 Misconfig lên cao, A03 = Supply-Chain
> (whitebox), A10 = Mishandling Exceptional Conditions, **SSRF gộp A01/A06** (không đứng riêng).
> Nhóm KHÔNG observable mù-code (A03 supply-chain/SCA, A04-crypto TLS/cipher sâu, A06 insecure-design,
> A08 integrity, A09 logging) → NGOÀI phạm vi, nhường con whitebox (ROADMAP §4).
> No-lockout & DoS: BỎ (thử sai pass nhiều lần dễ khoá account dùng chung — hại dev chung).

| # | Họ (OWASP 2025) | Probe | FAIL khi |
|---|---|---|---|
| 1 | Injection/XSS (A05) | `PAYLOADS.xss/sqli/template/csv` vào ô text → `probeInjection` | `fired` (XSS execute) / `serverError` (500) / chưa escaped |
| 2 | IDOR (A01) | GET id người khác/khác institute/không tồn tại → `probeIDOR` | `leak` (200 + data thật) |
| 3 | Client-bypass (A01) | UI guard (disabled/max/nút vắng) → gọi thẳng API → `probeBypass` | `!parityOk` (UI chặn mà API không) |
| 4 | Error-disclosure (A10) | input rác/param dị → `probeErrorDisclosure` | `disclosed` (500/traceback/SQL/stack) |
| 5 | Security-headers (A02) | đọc response headers → `checkSecurityHeaders(headers,{https})` | `missing` (thiếu CSP/X-Frame/nosniff/Referrer/HSTS) |
| 6 | Open-redirect (A01) | param redirect = host ngoài → theo dõi final URL → `probeOpenRedirect` | `vulnerable` (final host = host tấn công) |
| 7 | CSRF (A01) | state-changing POST bỏ token/credential → `probeCsrf` | `vulnerable` (2xx dù thiếu token) |
| 8 | Mass-assignment (A01) | POST field đặc quyền KHÔNG có trên form → quan sát ghi → `probeMassAssignment` | `vulnerable` (field lạ được persist) |
| 9 | Force-browse/path-traversal (A01) | URL admin/cấm hoặc `PAYLOADS.pathTraversal` → `probeForceBrowse` | `leak` (200 + data thật) |
| 10 | Session-after-logout (A07) | logout → gọi lại request bảo vệ → `probeSessionAfterLogout` | `vulnerable` (còn 200 sau logout) |
| 11 | **Cookie-flags** (A02/A04) *(v2)* | đọc Set-Cookie → `probeCookieFlags(setCookies,{https})` | `!ok` (cookie phiên thiếu HttpOnly/SameSite/Secure; cookie csrf được chừa HttpOnly) |
| 12 | **CORS misconfig** (A02) *(v2)* | gửi request kèm `Origin: evil` → đọc ACAO → `probeCors(headers,{attackerOrigin})` | `vulnerable` (echo origin lạ / `*`+credentials) |
| 13 | **Session-fixation** (A07) *(v2)* | **cắm session-id giả trước login** → so với id sau login → `probeSessionFixation({before,after})` | `vulnerable` (id KHÔNG xoay sau login) |

> ✅ 3 họ **v2** (harvest qa-skills) đã vào `security_lib` + unit-test + **LIVE-VERIFIED 2026-07-17** (ticket: cả 3 PASS).
> Assert dùng **tập mã** (`isDenied(status)` / `statusIn(status,[400,403,404,422])`), KHÔNG ép 1 status.
> ⚠️ Cookie **csrf/xsrf** cố tình KHÔNG HttpOnly (double-submit cần JS đọc) → probe đã chừa; đừng báo bug.
> Session-fixation phải **cắm id giả** rồi xem server có xoay không (chỉ đọc id trước/sau chưa đủ nếu app không tạo session ẩn danh).

### 🚨 App SPA (Nuxt/Vue/React) — BẮT BUỘC cấp `baselineBody`, nếu không FAIL GIẢ HÀNG LOẠT
Oracle HTML của `probeIDOR`/`probeForceBrowse` là *"200 mà không phải trang deny ⇒ nghi lộ"*. Luật đó **VỠ trên SPA**:
server trả **cùng một vỏ** cho MỌI path (kể cả path cấm/không tồn tại), chữ "404 / không có quyền" do **JS vẽ sau**
→ vỏ không chứa deny-marker → **mọi path đều bị chấm leak**.
> 📌 Đã cắn thật **2026-07-17**: `../../../../etc/passwd` ra "200 + trả data" trên **cả pro lẫn reservation**,
> trong khi body **y HỆT** trang hợp lệ, **không** có `root:x:`, DOM sau render là **404** → app chặn ĐÚNG. FAIL giả 100%.
> (Cùng loại với dòng `IDOR attempt` 未実施 của TestCase-11 — trước phải ghi chú tay, nay có cơ chế chặn.)

```js
// ✅ ĐÚNG — baseline = body path HỢP LỆ; giống hệt byte ⇒ catch-all SPA ⇒ inconclusive
const baselineBody = await (await context.request.get(BASE + '/<path-hợp-lệ>')).text();
const r = probeForceBrowse({ status, body }, { baselineBody });
if (r.inconclusive) {                    // vỏ SPA → raw HTML vô nghĩa, PHẢI quan sát DOM đã render
  await page.goto(BASE + '/' + payload); await page.waitForTimeout(4000);
  const rendered = await page.evaluate(() => document.body.innerText.trim());
  // chấm lại trên `rendered`; traversal chỉ FAIL khi thấy dấu hiệu file hệ thống thật (root:x: / /bin/sh)
}
```
- **`baselineBody` (so byte) là cửa MẠNH NHẤT** — app-agnostic, không đoán. Luôn cấp khi có thể.
- `looksLikeSpaShell()` chỉ là **dự phòng** khi không có baseline, và **yếu hơn**: vỏ Pro có 56 ký tự text
  server-render (`…ログイン ワークスペースの準備が整うまでお待ちください。`) nên nó **trượt** — chỉ baseline bắt được.
  ⚠️ **Đừng nâng ngưỡng độ-dài để "chữa"**: ngưỡng cùn sẽ nuốt luôn trang lộ thật nhưng ngắn ⇒ **false-negative**
  (bỏ sót lỗ hổng — tệ hơn hẳn false-positive). Unit test đã khoá cả 2 chiều.
- Chỉ áp cho **HTML**; body **JSON** vẫn chấm bằng `looksLikeData` như cũ.

## Quy trình
1. **Scope:** đọc `specs.md §3` → app/màn/field. Có `tcs.json` đã chạy → tái dùng màn/URL/field.
2. **Seam màn→URL/field:** `knowledge/*.md` approved (như functional). Chưa có → dừng, nhắc `/testcase-systemdoc`.
3. **Probe** (driver inline như /testcase-run): mỗi màn × họ áp dụng được. Data GHI ra prefix **`AIOT-TEST-SEC-*`**.
   - Injection: lặp `PAYLOADS.*` vào từng ô text; `submit` = closure bấm nút gửi (trả `{status}` nếu quan sát được).
   - IDOR/Error: `withApi` (target Rails pro/backend) hoặc `context.request` (Django ticket, kèm cookie session) GET → đưa `{status,body}` vào probe.
   - Bypass: đọc guard trên DOM (disabled/max/404) → `uiBlocks`; gọi API bỏ guard → `apiStatus` → `probeBypass({uiBlocks,apiStatus})`.
   - Security-headers: `response.headers()` (hoặc `context.request` HEAD/GET) → `checkSecurityHeaders(headers,{https:true})`.
   - Open-redirect: tìm param redirect (`?next=`/`?url=`/`?return=`) → set host ngoài (vd `evil.example`) → theo dõi `page.url()`/`response` final → `probeOpenRedirect({finalUrl, attackerHost})`.
   - CSRF: state-changing POST bỏ header/token CSRF (hoặc origin lạ) qua `context.request` → `probeCsrf({status})`.
   - Mass-assignment: POST kèm field đặc quyền KHÔNG có trên form (vd `is_admin`, `role`, `institute_id` khác) → đọc lại record xem có persist → `probeMassAssignment({accepted})`.
   - Force-browse/traversal: GET URL admin/cấm hoặc `../` → `probeForceBrowse({status,body})`.
   - Session-after-logout: logout xong, gọi lại 1 request bảo vệ bằng session cũ → `probeSessionAfterLogout({status})`.
   - **Cookie-flags:** lấy các dòng `Set-Cookie` từ response login (`response.headersArray()` lọc `set-cookie`) → `probeCookieFlags(list,{https:true})`.
   - **CORS:** `context.request.get(url,{headers:{Origin:'https://evil.example'}})` → `probeCors(resp.headers(),{attackerOrigin:'https://evil.example'})`.
   - **Session-fixation:** đọc cookie phiên TRƯỚC login (context tươi) + SAU login → `probeSessionFixation({before,after})`. Thiếu 1 vế = `inconclusive` → `未実施`.
   - Evidence: `shotViolation(page, [{target}], out)` khoanh chỗ / lưu request+response text (header, status, body).
4. **Verdict/màn:** PASS (mọi bất biến giữ) · FAIL (≥1 phá) · 未実施 (không probe được).
   ⚠️ Security **KHÔNG BAO GIỜ** `SPEC-GAP` (bất biến an ninh luôn định nghĩa kỳ vọng).
5. **Viết `<folder>/security.results.json`**: `{meta:{case,date,tester}, screens:[{name,app,url,result,
   findings:[finding(...)]}]}`. XSS-fired / bypass-thành-công / IDOR-leak → severity `High`; error-disclosure/500 → `Medium`.
6. **Factcheck rồi build report:** `python3 .../factcheck_report.py <folder>/security.results.json` (gate: filler/AI-tell + tally bịa; sạch mới build) → `python3 .../build_security_report.py <folder>/security.results.json <folder>/<Tên>.security.xlsx`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/(màn×họ×payload-class)** → append `bug-he-thong.tcs.json`
   (`bug_type:"Security"`, `result:"FAIL"`, `pri`=High cho XSS-fired/bypass/IDOR-leak, Medium cho error-disclosure/500,
   `screen`="<App> — <Màn>", `source`=TestCase-XX, `title`="<Họ>: <hành vi>", `before:null`+`note`, `after`=ảnh).
   Build lại `bug-he-thong.xlsx`.
8. **Cleanup:** liệt kê id `AIOT-TEST-SEC-*` đã tạo → nhắc `/testcase-cleanup`.
9. **Báo cáo:** bảng màn × họ × verdict; liệt kê FAIL + bug đã đẩy. Mô tả **hành vi** (payload + quan sát), KHÔNG file:line.

## Meta-verify probe (chống "PASS rỗng" — harvest qa-skills)
Một probe bug (sai selector/URL/oracle) sẽ **luôn PASS** dù app có lỗi — nguy hiểm hơn không test. Định kỳ
(hoặc khi sửa `security_lib`) chĩa probe vào app **cố-tình-lỗi OWASP Juice Shop** → probe PHẢI báo FAIL:
```bash
docker run --rm -d -p 4200:3000 bkimminich/juice-shop   # container RIÊNG, KHÔNG phải dev — an toàn
# rồi chạy 1 script probe (như sec_*.js) với BASE=http://localhost:4200:
#   IDOR/injection/security-headers PHẢI ra FAIL. Nếu toàn PASS → probe KHÔNG chạm app → sửa selector/URL trước khi tin.
docker stop $(docker ps -q --filter ancestor=bkimminich/juice-shop)
```
Đây là kiểm-định-công-cụ (build-time), KHÔNG phải test dev — nên chạy Juice Shop cục bộ là hợp lệ. Unit-test
`security_lib.test.js` đã khoá phần oracle thuần; Juice-Shop khoá phần "probe có thật sự chạm app".

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG.**
- [ ] Verdict chỉ dựa bất biến an ninh + quan sát (không specs làm oracle, không SPEC-GAP)?
- [ ] Mọi data test đã prefix `AIOT-TEST-SEC-*` chưa? Đã nhắc cleanup id đã tạo chưa?
- [ ] Đã dedup 1 bug/(màn×họ×payload-class) trước khi append sổ chưa?
