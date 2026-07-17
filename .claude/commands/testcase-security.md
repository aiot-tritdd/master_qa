# /testcase-security — Test Security (bất biến an ninh, black-box) một TestCase

Quét security các màn spec đang test đụng tới, theo checklist 4 họ. **Track RIÊNG**, KHÔNG trộn
PASS/FAIL functional. Oracle = **bất biến an ninh PHỔ QUÁT** (không phải spec). Mù code.

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

## 10 họ + oracle (phủ phần black-box của OWASP; FAIL khi bất biến bị phá)
> Nhóm OWASP KHÔNG observable mù-code (A04 insecure-design, A06 vulnerable-components, A08 integrity,
> A09 logging, A02 crypto/TLS sâu) → NGOÀI phạm vi, nhường con whitebox tương lai (ROADMAP §4).
> No-lockout & DoS: BỎ (thử sai pass nhiều lần dễ khoá account dùng chung — hại dev chung).

| # | Họ (OWASP) | Probe | FAIL khi |
|---|---|---|---|
| 1 | Injection/XSS (A03) | `PAYLOADS.xss/sqli/template/csv` vào ô text → `probeInjection` | `fired` (XSS execute) / `serverError` (500) / chưa escaped |
| 2 | IDOR (A01) | GET id người khác/khác institute/không tồn tại → `probeIDOR` | `leak` (200 + data thật) |
| 3 | Client-bypass (A01) | UI guard (disabled/max/nút vắng) → gọi thẳng API → `probeBypass` | `!parityOk` (UI chặn mà API không) |
| 4 | Error-disclosure (A05) | input rác/param dị → `probeErrorDisclosure` | `disclosed` (500/traceback/SQL/stack) |
| 5 | Security-headers (A05) | đọc response headers → `checkSecurityHeaders(headers,{https})` | `missing` (thiếu CSP/X-Frame/nosniff/Referrer/HSTS) |
| 6 | Open-redirect (A01) | param redirect = host ngoài → theo dõi final URL → `probeOpenRedirect` | `vulnerable` (final host = host tấn công) |
| 7 | CSRF (A01/A05) | state-changing POST bỏ token/credential → `probeCsrf` | `vulnerable` (2xx dù thiếu token) |
| 8 | Mass-assignment (A01) | POST field đặc quyền KHÔNG có trên form → quan sát ghi → `probeMassAssignment` | `vulnerable` (field lạ được persist) |
| 9 | Force-browse/path-traversal (A01) | URL admin/cấm hoặc `../` → `probeForceBrowse` | `leak` (200 + data thật) |
| 10 | Session-after-logout (A07) | logout → gọi lại request bảo vệ → `probeSessionAfterLogout` | `vulnerable` (còn 200 sau logout) |

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
   - Evidence: `shotViolation(page, [{target}], out)` khoanh chỗ / lưu request+response text (header, status, body).
4. **Verdict/màn:** PASS (mọi bất biến giữ) · FAIL (≥1 phá) · 未実施 (không probe được).
   ⚠️ Security **KHÔNG BAO GIỜ** `SPEC-GAP` (bất biến an ninh luôn định nghĩa kỳ vọng).
5. **Viết `<folder>/security.results.json`**: `{meta:{case,date,tester}, screens:[{name,app,url,result,
   findings:[finding(...)]}]}`. XSS-fired / bypass-thành-công / IDOR-leak → severity `High`; error-disclosure/500 → `Medium`.
6. **Build report:** `python3 .../build_security_report.py <folder>/security.results.json <folder>/<Tên>.security.xlsx`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/(màn×họ×payload-class)** → append `bug-he-thong.tcs.json`
   (`bug_type:"Security"`, `result:"FAIL"`, `pri`=High cho XSS-fired/bypass/IDOR-leak, Medium cho error-disclosure/500,
   `screen`="<App> — <Màn>", `source`=TestCase-XX, `title`="<Họ>: <hành vi>", `before:null`+`note`, `after`=ảnh).
   Build lại `bug-he-thong.xlsx`.
8. **Cleanup:** liệt kê id `AIOT-TEST-SEC-*` đã tạo → nhắc `/testcase-cleanup`.
9. **Báo cáo:** bảng màn × họ × verdict; liệt kê FAIL + bug đã đẩy. Mô tả **hành vi** (payload + quan sát), KHÔNG file:line.

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG.**
- [ ] Verdict chỉ dựa bất biến an ninh + quan sát (không specs làm oracle, không SPEC-GAP)?
- [ ] Mọi data test đã prefix `AIOT-TEST-SEC-*` chưa? Đã nhắc cleanup id đã tạo chưa?
- [ ] Đã dedup 1 bug/(màn×họ×payload-class) trước khi append sổ chưa?
