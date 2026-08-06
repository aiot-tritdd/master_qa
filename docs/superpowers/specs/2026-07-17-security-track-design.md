# Security-gom track (`/testcase-security`) — Design

> Type-track thứ 3 cho master_qa (sau Accessibility, Visual). Gom các phép thử security
> đang nằm rải trong method functional của qa-brain (`SKILL.md` §"USER QUẬY PHÁ") thành **một
> track riêng, có hệ thống, oracle phổ quát, report riêng**. Cập nhật: 2026-07-17.

---

## 1. Vấn đề & mục tiêu

**Hiện trạng:** security testing (XSS, injection, IDOR, client-bypass, error-disclosure) ĐÃ được làm,
nhưng **rải rác trong từng test functional** — mỗi spec model tự nghĩ vài đòn quậy ad-hoc. Bằng chứng:
coupon list dev đầy `AIOT-TEST-XSS` (`<img src=x onerror="window.__XSS=1">`), `AIOT-TEST-CSVINJ`
(`=1+1+...`) do các lần test trước để lại. Không có: checklist chuẩn, report riêng, tính lặp lại,
độ phủ đo được.

**Mục tiêu:** track `/testcase-security` **quét security có hệ thống** cho các màn 1 TestCase đụng tới,
theo checklist kiểu OWASP-lite, chấm bằng **bất biến an ninh phổ quát**, xuất report + đẩy sổ bug —
**song song a11y/Visual**, cùng khuôn.

## 2. Nguyên tắc (2 tường thép — GIỮ NGUYÊN)

1. **Oracle = bất biến an ninh PHỔ QUÁT, KHÔNG phải SPEC, KHÔNG phải code.** Như WCAG với a11y:
   "XSS phải escaped", "tampering không được 500/lộ data", "IDOR phải 403/404", "UI chặn thì API phải
   chặn" — đúng/sai suy từ bất biến phổ quát + quan sát live, độc lập code-under-test → **không phá
   tường tautology**. `specs.md` chỉ dùng **chọn màn (scope)**, KHÔNG làm oracle.
2. **Mù code runtime.** Không đọc code sản phẩm / GitNexus / `knowledge/system/**`. Chỉ quan sát
   response + DOM render + trạng thái browser.

**Verdict:** `PASS` · `FAIL` · `未実施` (không probe được). **KHÔNG BAO GIỜ `SPEC-GAP`** — bất biến an ninh
luôn định nghĩa kỳ vọng (giống a11y với WCAG).

## 3. Phạm vi — 10 họ (phủ phần black-box của OWASP Top 10)

> **Sửa scope 2026-07-17 (user push-back):** v1 ban đầu chỉ 4 họ — scope quá dè dặt. Mở rộng thành
> **10 họ = TẤT CẢ phần OWASP Top 10 quét được kiểu black-box/mù-code.** Track này là **security scanner
> tập trung**, KHÔNG để functional làm rải rác nữa (xem §8 consolidation).

Oracle mỗi họ đều **quan sát được, mù code**:

| # | Họ (OWASP) | Probe | FAIL khi (bất biến bị phá) |
|---|---|---|---|
| 1 | **Injection / XSS** (A03) | Bơm `PAYLOADS.xss/sqli/template/csv` vào ô text (XSS marker `window.__SEC_XSS`) → `probeInjection` | payload **execute** · phản chiếu **chưa escaped** · **500** |
| 2 | **IDOR** (A01) | GET id người khác / khác institute / không tồn tại → `probeIDOR` | **200 kèm data thật** (thay vì 403/404) |
| 3 | **Client-bypass** (A01) | **Guard-parity:** quan sát UI guard (disabled/`max`/404) → gọi thẳng API → `probeBypass` | backend **KHÔNG chặn** (`!parityOk`) · số dư/tồn **âm** |
| 4 | **Error-disclosure** (A05) | input rác/param dị → `probeErrorDisclosure` | body lộ **Traceback/SQL/stack** · **500** |
| 5 | **Security-headers** (A05) | đọc response headers → `checkSecurityHeaders(headers,{https})` | thiếu **CSP / X-Frame / nosniff / Referrer-Policy / HSTS** |
| 6 | **Open-redirect** (A01) | param redirect (`?next/url/return`) = host ngoài → theo dõi final URL → `probeOpenRedirect` | final host = **host tấn công** |
| 7 | **CSRF** (A01/A05) | state-changing POST bỏ token/credential → `probeCsrf` | **2xx** dù thiếu token |
| 8 | **Mass-assignment** (A01) | POST field đặc quyền KHÔNG có trên form (`is_admin`/`role`/`institute_id`) → đọc lại → `probeMassAssignment` | field lạ **được persist** |
| 9 | **Force-browse / path-traversal** (A01) | GET URL admin/cấm hoặc `../` → `probeForceBrowse` | **200 kèm data thật** |
| 10 | **Session-after-logout** (A07) | logout → gọi lại request bảo vệ bằng session cũ → `probeSessionAfterLogout` | còn **200** sau logout |

**Guard-parity nói rõ (chốt brainstorm):** track **QUAN SÁT** trên màn thấy guard (đọc DOM: `disabled`,
`maxlength`, nút vắng mặt, 404) → test API có giữ **cùng ràng buộc quan sát được** đó không. Oracle =
"UI chặn X ⇒ API phải chặn X" — **không cần biết X là luật gì từ SPEC/code**, chỉ cần thấy UI đang chặn.

## 4. Thành phần (khuôn giống a11y)

Tất cả trong `.claude/skills-scripts/testcase-evidence/` (KHÔNG viết lại helper — tái dùng `pw_lib`).

### 4.1 `security_lib.js` (mới)
- **Payload banks** (hằng): `XSS[]`, `SQLI[]`, `TEMPLATE[]`, `CSV[]`. XSS dùng marker
  `window.__SEC_XSS` (bơm rồi đọc lại — mù code, chỉ quan sát browser).
- `probeInjection(page, fieldLocator, payload)` → điền + submit → trả `{fired, escaped, serverError, reflectedHtml}`.
- `probeIDOR(withApiFn, url)` → GET → trả `{status, looksLikeData, leakedFields}`.
- `probeBypass(page, withApiFn, guard, apiCall)` → đọc guard từ DOM + gọi API → trả `{uiBlocks, apiBlocks, parityOk}`.
- `probeErrorDisclosure(resp)` → quét body theo regex stack/SQL/traceback → trả `{disclosed, kind, snippet}`.
- Oracle helpers thuần: `xssFired(page)`, `isServerError(status)`, `looksLikeData(body)`, `hasStackLeak(body)`.
- Chuẩn hoá 1 finding: `{family, payloadClass, where, url, severity, observed, fix, evidenceShot}`.

### 4.2 `.claude/commands/testcase-security.md` (mới)
Quy trình (song song testcase-a11y):
1. **Scope:** `specs.md §3` → app/màn/field. Có `tcs.json` đã chạy → tái dùng màn/URL/field đã lái.
2. **Seam màn→URL/field:** `knowledge/*.md` approved (như functional). Flow chưa có → dừng, nhắc `/testcase-systemdoc`.
3. **Probe** (driver inline): mỗi màn × họ áp dụng được → gọi `security_lib`. Data ghi ra prefix
   **`AIOT-TEST-SEC-*`**. Evidence: khoanh chỗ (tái dùng pattern `shotViolation`) / lưu request+response.
4. **Verdict:** PASS (bất biến giữ) · FAIL (phá) · 未実施. Không SPEC-GAP.
5. **Viết `<folder>/security.results.json`**: `{meta, screens:[{name,app,url,result,findings:[...]}]}`.
6. **Build report:** `build_security_report.py`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/(màn×họ×payload-class)**, `bug_type:"Security"`, `pri`
   theo mức (XSS-fired/bypass-thành-công/IDOR-leak → High; error-disclosure/500 → Medium).
8. **Cleanup nhắc:** liệt kê id `AIOT-TEST-SEC-*` đã tạo → `/testcase-cleanup`.

### 4.3 `build_security_report.py` (mới — khuôn `build_a11y_report.py`)
`<Case>.security.xlsx`, 2 sheet:
- **Findings:** Màn · App · URL · Họ · Payload-class · Mức · Nơi (field/endpoint) · **Chi tiết (quan sát
  được)** · **Cách fix** (tách riêng, kiểu a11y) · **File ảnh** · Evidence (ảnh nhúng).
- **Đã quét:** coverage — mỗi màn × họ đã probe + verdict (phân biệt "quét sạch" vs "chưa probe").

### 4.4 `build_bug_report.py` (sửa nhỏ)
Thêm `"Security"` vào tuple `bug_type` hợp lệ (dòng ~380) — y hệt lúc thêm `Accessibility`/`Visual`.

## 5. An toàn trên dev chung (chốt brainstorm: active + mutating + cleanup)

- Được bắn payload GHI (tạo record, POST bypass) — NHƯNG mọi data test **bắt buộc prefix
  `AIOT-TEST-SEC-*`** để `/testcase-cleanup` quét sạch.
- Bypass POST mà backend **chặn đúng** (kỳ vọng) → không tạo data. Backend **nhận** (bug) → tạo data
  rác = chính là finding + phải cleanup (ghi id vào `note`).
- Không đụng account/data người thật; chỉ institute/khách test (`TESTSEED001`, khách `AIOT*`).
- IDOR probe chỉ **đọc** id lân cận trong phạm vi test; không sửa/xoá tài nguyên người khác.

## 6. Ngoài phạm vi — vì SAO (thật, không phải lười)

**Bỏ do BẢN CHẤT (không quét được mù-code từ ngoài) — nhường con whitebox tương lai (ROADMAP §4):**
- A04 Insecure Design (kiến trúc) · A08 Software/Data Integrity (deserialize/CI-CD) · A09 Logging & Monitoring
  (không observable từ ngoài) · A06 Vulnerable Components (cần SBOM/SCA = đọc dependency) · A02 Crypto/TLS sâu
  (cần soi config/cipher). → Đây là ranh giới THẬT của black-box, không phải cắt scope tuỳ tiện.

**Bỏ do AN TOÀN dev chung (không phải kỹ thuật):**
- No-lockout / credential-stuffing / brute-force: thử sai pass nhiều lần dễ **khoá account test dùng chung**
  (mini-DoS lên account) → BỎ. Rate-limit/DoS: cấm.

**Giữ nguyên (đã có ở §3):** mọi thứ CÒN LẠI của OWASP quét được black-box đều nằm trong 10 họ.

## 6b. Consolidation — security RA KHỎI qa-brain functional (chốt 2026-07-17)

Trước đây `qa-brain/SKILL.md` §"USER QUẬY PHÁ" bảo con **functional** tự improvise injection/IDOR/bypass
mỗi spec → rải rác, không hệ thống, không report riêng. **Dẹp.** Security **tập trung ở `/testcase-security`**:
- Sửa `SKILL.md`: rút Injection/IDOR/tampering/bypass/error-disclosure khỏi checklist functional →
  trỏ sang `/testcase-security`. Functional **chỉ giữ robustness nghiệp vụ** (input-rác, race/double-submit,
  state-transition, cross-field/business-rule — mấy cái đúng/sai *nghiệp vụ*, không phải security).
- Đụng nghi vấn security lúc test functional → GHI CHÚ chạy `/testcase-security`, KHÔNG improvise.

## 7. Kiểm thử (track tự test)

- `security_lib.test.js` (node:test): 15 test — oracle helpers thuần (10 họ: `xssFired`/`isServerError`/
  `looksLikeData`/`hasStackLeak`/`checkSecurityHeaders`/`probeOpenRedirect`/`probeCsrf`/`probeMassAssignment`/
  `probeForceBrowse`/`probeSessionAfterLogout`) + `probeInjection` trên fixture `setContent` (XSS-fired vs escaped) — không cần dev.
- `test_build_security_report.py`: cột đúng thứ tự · tách Chi tiết/Cách fix · File ảnh basename ·
  coverage sheet · empty-message.
- `test_bug_report_security_type.py` (hoặc mở rộng test type sẵn): `bug_type:"Security"` render được.
- **Live-verify** trên TestCase-11 (coupon, ticket) sau khi build — như a11y/Visual.

## 8. Độ phủ spec-coverage

Mọi họ ở §3 đều có: thành phần build (§4), oracle phổ quát (§2/§3), an toàn (§5), test (§7).
Track đứng độc lập, giao tiếp qua `security.results.json` (như a11y qua `a11y.results.json`).
