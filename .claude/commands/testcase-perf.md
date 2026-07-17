# /testcase-perf — Test Performance (Core Web Vitals, black-box) một TestCase

Đo tốc độ các màn spec đụng tới bằng **Core Web Vitals**. **Track RIÊNG**, KHÔNG trộn PASS/FAIL functional.
Oracle = **ngưỡng Google công bố** (không phải spec, không phải số ai đó tự đặt). Mù code.

## Cách dùng
`/testcase-perf wtf-is-this/TestCase-XX`

## TIẾT KIỆM TOKEN
Dùng lại `.claude/skills-scripts/testcase-evidence/`: `pw_lib` (`getPage`, nạp `.env`),
`perf_lib` (`THRESHOLDS`, `rate`, `median`, `aggregate`, `verdict`, `findings`), `build_perf_report.py`.
KHÔNG viết lại. Setup 1 lần: `cd .claude/skills-scripts/testcase-evidence && npm i`.

## Nguyên tắc (2 tường)
- **Oracle = ngưỡng Google công bố.** `specs.md` chỉ chọn màn (scope), KHÔNG làm oracle.
- **Mù code.** Chỉ đo bằng `PerformanceObserver` trên trang đã render.

## Ngưỡng — Google công bố, KHÔNG tự chế, KHÔNG nới
| Chỉ số | good ≤ | poor > | Là gì | Nguồn |
|---|---|---|---|---|
| **LCP** | 2500ms | 4000ms | nội dung CHÍNH hiện ra | web.dev/articles/lcp |
| **CLS** | 0.1 | 0.25 | nội dung nhảy lung tung → bấm nhầm | web.dev/articles/cls |
| **TBT** | 200ms | 600ms | luồng chính bị CHẶN → bấm/gõ không ăn (**proxy LAB cho INP**) | web.dev/articles/tbt |
| FCP | 1800ms | 3000ms | pixel đầu tiên | web.dev/articles/fcp |
| TTFB | 800ms | 1800ms | server đáp nhanh không | web.dev/articles/ttfb |

> **Đây là lý do track này 0-setup, hợp vision đa dự án**: ngưỡng do W3C/Google công bố, ai cũng tra lại được —
> đúng vai trò WCAG với a11y. **Không cần chủ dự án đặt số nào.**
> (ROADMAP cũ ghi *"Performance vướng oracle, cần budget do người đặt"* → **SAI, đã gỡ 2026-07-17**. Budget
> riêng-dự-án kiểu "màn X < 800ms" là *thêm*, không phải *điều kiện cần*.)

## 🚨 4 điều PHẢI nói ra mỗi lần báo cáo — giấu là lừa người đọc
**① LAB ≠ FIELD.** Đây là đo *phòng thí nghiệm*: 1 máy, 1 đường mạng, không tải. Chuẩn CWV **thật** là
**phân vị 75 của NGƯỜI DÙNG THẬT** (CrUX) — điện thoại yếu, 4G. ⇒ Lab **"good" KHÔNG chứng minh** người dùng
thật thấy nhanh. Nhưng lab **"poor" thì CHẮC CHẮN** có vấn đề (thực tế còn tệ hơn).
**Kết quả track này = CẬN DƯỚI của mức tệ, KHÔNG phải chứng nhận nhanh.**

**② DEV ≠ PROD.** Không CDN, cache khác, data ít, có thể còn debug build. Số ở dev **không suy ra** production.

**③ INP không đo được ở LAB** (cần tương tác của người thật) → dùng **TBT** làm proxy, đúng khuyến nghị Google.
⛔ **Đừng bao giờ báo "INP = x ms" ở lab — đó là bịa.** `perf_lib` cố ý **không** có INP trong `THRESHOLDS`;
unit test khoá luôn điều này.

**④ Nhiễu cao → PHẢI chạy nhiều lần lấy TRUNG VỊ** (mặc định **5**), không phải trung bình (1 lần dính
GC/mạng lag là kéo lệch). `aggregate()` gắn cờ **`unstable`** khi dao động > trung vị → **báo ra**, đừng giấu:
nó nói "đừng tin con số chính xác này".

## Quy trình
1. **Scope:** `specs.md §3` → app/màn. Có `tcs.json` đã chạy → tái dùng màn/URL.
2. **Seam màn→URL:** `knowledge/*.md` approved. ⚠️ **URL SAI = số vô nghĩa** — xác nhận vào ĐÚNG màn bằng
   **API 200 + data thật hiện ra**, KHÔNG bằng HTTP 200 (SPA trả 200 cho mọi path).
3. **Đo** (driver inline) — **N=5 lần/màn**:
   - Cắm `PerformanceObserver` bằng **`context.addInitScript(...)`** → phải cắm **TRƯỚC khi trang chạy JS**,
     nếu không **hụt event sớm** (LCP/FCP bắn rất sớm). Dùng `buffered: true`.
   - LCP `largest-contentful-paint` · CLS `layout-shift` (**bỏ `hadRecentInput`** — shift do user bấm không tính) ·
     TBT `longtask` (cộng `max(0, duration-50)` = phần CHẶN) · FCP `paint` · TTFB `navigation.responseStart - requestStart`.
   - **Chờ ĐIỀU KIỆN, không chờ đồng hồ**: `getByText(<đặc trưng màn>).waitFor({state:'visible'})` +
     `waitForLoadState('networkidle')` + đệm ngắn để LCP/CLS chốt sổ.
   - Mỗi lần chạy **context MỚI** (cache ấm sẽ làm số đẹp giả).
4. **Chấm:** `aggregate(runs)` → `verdict(agg)`. `PASS` (mọi chỉ số **good**) · `FAIL` (có ≥1 không good) ·
   `未実施` (không đo được chỉ số nào — **KHÔNG được PASS**).
   ⚠️ **`needs-improvement` cũng là FAIL.** Ngưỡng "good" LÀ mốc đạt; nới cho qua = **tự hạ chuẩn công bố
   xuống theo ý mình** — đúng cái bệnh track này sinh ra để tránh. Muốn nới phải là quyết định của NGƯỜI, ghi rõ.
   ⚠️ Perf **KHÔNG BAO GIỜ** `SPEC-GAP` (chuẩn luôn định nghĩa kỳ vọng).
5. **Viết `<folder>/perf.results.json`**:
   `{meta:{case,date,tester}, thresholds:{...}, screens:[{name,app,url,result,metrics:<agg>,findings:[...],note}]}`
6. **Factcheck rồi build:** `python3 .../factcheck_report.py <folder>/perf.results.json` → `python3 .../build_perf_report.py <folder>/perf.results.json <folder>/<Tên>.perf.xlsx`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/(màn×chỉ số)**. `bug_type:"Performance"`, `result:"FAIL"`,
   `pri`= poor→**High**, needs-improvement→**Medium**. `before:null` + `note` **bắt buộc chứa cảnh báo LAB≠FIELD**.
   `actual` = câu `observed` của `findings()` (đã có số đo + ngưỡng + dao động). Build lại sổ.
8. **Báo cáo:** bảng màn × chỉ số + verdict. **Luôn kèm cảnh báo LAB≠FIELD và DEV≠PROD.**

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG.**
- [ ] Có báo "INP = x" ở lab không? **Phải là KHÔNG** — INP là field-only, lab dùng TBT proxy.
- [ ] Có chạy ≥3 lần và lấy **trung vị** không? Có báo cờ `unstable` khi số nhiễu không?
- [ ] Có tự nới ngưỡng / cho `needs-improvement` qua thành PASS không? **Phải là KHÔNG.**
- [ ] Báo cáo có nói rõ **LAB ≠ FIELD** + **DEV ≠ PROD** chưa? (không nói = để người đọc hiểu nhầm)
