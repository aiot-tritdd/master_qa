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

## 4 họ + oracle (FAIL khi bất biến bị phá)
| Họ | Probe | FAIL khi |
|---|---|---|
| Injection/XSS | `PAYLOADS.xss/sqli/template/csv` vào ô text → `probeInjection` | `fired` (XSS execute) / `serverError` (500) / phản chiếu chưa escaped |
| IDOR | GET id người khác/khác institute/không tồn tại → `probeIDOR` | `leak` (200 + data thật) |
| Client-bypass | quan sát UI guard (disabled/max/nút vắng) → gọi thẳng API → `probeBypass` | `!parityOk` (UI chặn mà API không) |
| Error-disclosure | input rác/param dị → `probeErrorDisclosure` | `disclosed` (500/traceback/SQL/stack) |

## Quy trình
1. **Scope:** đọc `specs.md §3` → app/màn/field. Có `tcs.json` đã chạy → tái dùng màn/URL/field.
2. **Seam màn→URL/field:** `knowledge/*.md` approved (như functional). Chưa có → dừng, nhắc `/testcase-systemdoc`.
3. **Probe** (driver inline như /testcase-run): mỗi màn × họ áp dụng được. Data GHI ra prefix **`AIOT-TEST-SEC-*`**.
   - Injection: lặp `PAYLOADS.*` vào từng ô text; `submit` = closure bấm nút gửi (trả `{status}` nếu quan sát được).
   - IDOR/Error: `withApi` (target Rails pro/backend) hoặc `context.request` (Django ticket, kèm cookie session) GET → đưa `{status,body}` vào probe.
   - Bypass: đọc guard trên DOM (disabled/max/404) → `uiBlocks`; gọi API bỏ guard → `apiStatus` → `probeBypass({uiBlocks,apiStatus})`.
   - Evidence: `shotViolation(page, [{target}], out)` khoanh chỗ / lưu request+response text.
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
