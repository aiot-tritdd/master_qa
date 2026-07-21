# /testcase-i18n — Test i18n / Localization (black-box) một TestCase

Soi bản dịch + encoding + parity giữa các locale trên các màn spec đụng tới. **Track RIÊNG**, KHÔNG trộn
PASS/FAIL functional. Oracle = **bất biến ngôn ngữ phổ quát** (không phải spec, không phải số ai đặt). Mù code.

## Cách dùng
`/testcase-i18n wtf-is-this/TestCase-XX`

## TIẾT KIỆM TOKEN
Dùng lại `.claude/skills-scripts/testcase-evidence/`: `pw_lib` (`getPage`, nạp `.env`),
`i18n_lib` (`probeKeyLeak`, `probeMojibake`, `probeParity`, `probeLocaleFormat`, `verdict`, `finding`),
`explorer` (`dynamic` → mask), `build_i18n_report.py`. KHÔNG viết lại. Setup 1 lần: `npm i`.

## Nguyên tắc (2 tường)
- **Oracle = bất biến ngôn ngữ phổ quát.** `specs.md` chỉ chọn màn (scope), KHÔNG làm oracle.
- **Mù code.** Chỉ đọc **text DOM đã render** — KHÔNG mở file locale/`i18n/*.json` trong repo (đó là code).

## 4 probe — oracle, KHÔNG tự chế
| Probe | Bắt lỗi | Verdict | Severity |
|---|---|---|---|
| **keyLeak** | key i18n thô lòi ra: `a.selectCourse`, `{{x}}`, `__MISSING__`, `[[k]]` | **FAIL** | High |
| **mojibake** | sai encoding: `Ã©`, `â€™`, `�` (U+FFFD) | **FAIL** | High |
| **parity** | trang locale-EN còn CJK ở text chrome ⇒ CHƯA DỊCH | **FAIL** (chỉ nơi có ≥2 locale) | Medium |
| **localeFormat** | ngày/tiền kanji (`2026年…円`) trên trang EN | **WARN-only** | Low |

> **0-setup, hợp vision đa dự án**: không cần ai đặt số, không cần baseline. Như WCAG với a11y.
> ⚠️ `parity` chỉ chạy được nơi màn có **≥2 locale** (reservation có `/en/2` và `/2`). App 1 ngôn ngữ
> (pro/ticket nếu không có bộ chuyển) → `parity` = **`未実施` + lý do**, KHÔNG được ép PASS.

## 🚨 BẮT BUỘC — MASK DATA TRƯỚC KHI SOI (nếu không: FAIL GIẢ hàng loạt)
**Data ≠ bản dịch.** Tên viện `AIoT院1`, tên khách, mã coupon là chữ Nhật **HỢP LỆ** trên trang EN.
Không mask → `probeParity`/`probeKeyLeak` bắt nhầm chúng là "chưa dịch"/"key thô" ⇒ **FAIL GIẢ** (đúng bẫy
Visual "màn data-heavy" + Security "SPA trả cùng vỏ"). Bắt buộc:
1. `node explorer.js dynamic --target <app> --url <path>` → lấy vùng ĐỘNG (đồng hồ/tên/số/mã).
2. Trích **chrome text** (`button,a,label,h1..h6,[role=tab],[role=button],nav,th`) rồi **LOẠI** text nằm
   trong vùng động. Chỉ text-khung mới đưa vào probe.

## Quy trình
1. **Scope:** `specs.md §3` → app/màn. Có `tcs.json` đã chạy → tái dùng màn/URL.
2. **Soi build-time có mấy locale:** reservation = `/en/2` + `/2` (đủ parity). pro/ticket = kiểm có bộ
   chuyển ngôn ngữ không; không có → chỉ keyLeak+mojibake, parity `未実施`.
3. **Vào ĐÚNG màn:** xác nhận bằng **API 200 + data thật hiện ra**, KHÔNG bằng HTTP 200 (SPA trả 200 mọi path).
   Chờ ĐIỀU KIỆN (`waitFor visible` + `networkidle`), KHÔNG chờ đồng hồ.
4. **Trích + mask + soi** (driver inline): với mỗi màn/locale → chrome text đã mask → 4 probe.
   Parity: chụp EN và ja **cùng lúc, cùng màn**.
5. **Chấm:** `verdict({reachable, keyLeak, mojibake, parity, localeFormat})` → PASS/FAIL/`未実施`.
   ⚠️ `localeFormat` là **WARN**, KHÔNG kéo verdict xuống FAIL. i18n **KHÔNG** bao giờ `SPEC-GAP`.
6. **Viết `<folder>/i18n.results.json`:**
   `{meta:{case,date,tester}, screens:[{name,app,url,locale,result,probes:{keyLeak,mojibake,parity,localeFormat},findings:[...],note}]}`
7. **Factcheck rồi build:** `python3 .../factcheck_report.py <folder>/i18n.results.json` →
   `python3 .../build_i18n_report.py <folder>/i18n.results.json <folder>/<Tên>.i18n.xlsx`.
8. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/(màn×probe)**. `bug_type:"i18n"`, `result:"FAIL"`,
   `pri`= keyLeak/mojibake→**High**, parity→**Medium**. `actual` = câu `observed` của `finding()`.
   `before:null`. Build lại sổ.
9. **Báo cáo:** bảng màn × probe + verdict. Ghi rõ probe nào `未実施` và VÌ SAO (app 1 ngôn ngữ).

## Before final (checklist)
- [ ] Có đọc source code / file locale trong repo / GitNexus không? **Đáp án đúng luôn là KHÔNG.**
- [ ] Có **mask data** trước khi soi không? (không mask = FAIL giả hàng loạt) **Phải là CÓ.**
- [ ] `parity` trên app 1 ngôn ngữ có bị ép PASS không? **Phải là `未実施` + lý do.**
- [ ] `localeFormat` có bị kéo thành FAIL không? **Phải KHÔNG — nó là WARN-only.**
- [ ] Vào đúng màn bằng **API 200 + data thật** chưa? (không phải HTTP 200 suông)
