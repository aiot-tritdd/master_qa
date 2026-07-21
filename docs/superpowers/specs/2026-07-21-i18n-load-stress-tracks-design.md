# Design — 3 track mới: i18n (type-7) + load + stress

> Ngày 2026-07-21. Duyệt qua brainstorming (user OK 2026-07-21). Chia **2 spec** vì bản chất khác
> nhau, gộp trong 1 file design này cho gọn. Tuân đúng khuôn type-track cũ (compat/perf):
> `X_lib.js` (probe = hàm thuần) + `X_lib.test.js` (`node --test`) + `build_X_report.py` + command doc.

## Bối cảnh / vì sao

- Trục TYPE ngang đã 6/6. i18n là **type-7 black-box** hợp lệ vì app **song ngữ** (reservation có
  `/en/2` và `/2`; pro/ticket là ja-JP). Oracle = **bất biến ngôn ngữ phổ quát** (như WCAG với a11y).
- load/stress user **muốn có**. Chúng KHÔNG phải black-box: là **grey-box/SRE**, bắn k6 vào API
  (path EC2→RDS), oracle một phần cần số business. Build đầy đủ nhưng **run-gated**.

---

## SPEC 1 — `/testcase-i18n` (type-7, black-box, chạy được ngay)

### Files
`i18n_lib.js` + `i18n_lib.test.js` + `build_i18n_report.py` + `test_build_i18n_report.py`
+ `test_bug_report_i18n_type.py` + `.claude/commands/testcase-i18n.md`
+ thêm `"i18n"` vào tally sổ bug (`build_bug_report.py:380` list 6 type → 7).

### Oracle = 4 probe (hàm thuần trên text đã trích + đã mask)
| Probe | Bắt lỗi | Verdict | Ghi chú |
|---|---|---|---|
| `probeKeyLeak(texts)` | key i18n thô: dotted-ident hiển thị (`reservation.title`), `{{x}}`, `__MISSING__`, `[[ ]]` | **FAIL** | universal |
| `probeMojibake(texts)` | `�` (U+FFFD), double-encoded UTF-8 (`Ã©`,`â€`,`ã‚`), control chars | **FAIL** | universal |
| `probeParity(enTexts, jaTexts)` | element chrome **cùng vị trí** có text **giống hệt** + chứa CJK trên trang EN → chưa dịch | **FAIL** | chỉ nơi có locale-2; không có → `未実施` |
| `probeLocaleFormat(texts, locale)` | ngày `YYYY/MM/DD` / tiền `円` xuất hiện trên trang locale EN | **WARN-only** (v1) | probe nhiễu nhất; KHÔNG cho thành FAIL cho tới khi tin |

- **Verdict tổng:** `PASS` (mọi probe áp dụng đều sạch) · `FAIL` (≥1 probe FAIL) · `未実施` (không probe nào
  chạy được) · **KHÔNG bao giờ `SPEC-GAP`** (chuẩn ngôn ngữ luôn định nghĩa kỳ vọng — như perf).
- Severity: keyLeak/mojibake = **High** (lỗi hiển thị rõ ràng); parity = **Medium**.

### Data-mask = AUTO (user chốt)
Driver inline (trong command) gọi `explorer.js dynamic` → `visual_lib.detectDynamic(page)` để lấy vùng
động (đồng hồ/tên/số/mã) → **loại text trong các vùng đó** trước khi đưa vào probe. Lý do bắt buộc:
**data ≠ bản dịch** — tên viện `AIoT院1`, tên khách, mã coupon là chữ Nhật HỢP LỆ trên trang EN, không
mask thì `probeParity`/`probeKeyLeak` **FAIL giả hàng loạt** (đúng bẫy Visual data-heavy + `/etc/passwd`).

### Phủ 3 app
- **reservation**: `/en/2` (EN) vs `/2` (ja) → đủ 4 probe kể cả parity.
- **pro / ticket**: **soi build-time** xem có bộ chuyển ngôn ngữ không.
  - Có locale-2 → chạy đủ.
  - Chỉ ja-JP → `probeKeyLeak` + `probeMojibake` (soi 1 locale vẫn bắt được key thô/mojibake),
    `probeParity` = **`未実施` + lý do** ("app chỉ 1 ngôn ngữ, không có locale để so").

### Trích text (driver)
- `page.locator(sel).allInnerTexts()` trên tập selector **chrome**: `button, a, label, h1..h6,
  [role=tab], [role=button], nav, th`. KHÔNG lấy vùng data (đã mask).
- Chờ ĐIỀU KIỆN không chờ đồng hồ (`waitFor visible` + `networkidle`). Xác nhận vào ĐÚNG màn bằng
  **API 200 + data thật** (bài học `/2` vs `/reservation`).

### Report + bug
- `<folder>/i18n.results.json` → factcheck → `build_i18n_report.py` → `<Case>.i18n.xlsx`
  (Sheet "Ngôn ngữ" app×probe + Sheet "Findings"). `bug_type:"i18n"`, chỉ FAIL vào sổ.

---

## SPEC 2 — `/testcase-load` + `/testcase-stress` (grey-box, RUN-GATED)

### Files
`load_lib.js` (oracle chung) + `load_lib.test.js` + `k6_load.js` + `k6_stress.js` (template k6)
+ `build_load_report.py` + `test_build_load_report.py` + 2 command doc (`testcase-load.md`, `testcase-stress.md`).
k6 **đã cài** (brew, 2026-07-21) — nhưng **KHÔNG tự bắn**.

### Ranh giới (ghi RÕ đầu mỗi command doc)
- ⛔ **KHÔNG code-blind. Đây là track grey-box/SRE riêng**, không thuộc "con đen".
- ⛔ **GUARD 2 LỚP trước khi chạy:** (a) user ra lệnh chạy tường minh **và** (b) khách/sếp gật cho tạo
  tải lên dev. Mặc định = **chỉ build/chuẩn bị, KHÔNG bắn.** Bắn tải = đổ tải thật lên hạ tầng KHÁCH.
- **Target = API endpoint** widget `/2` gọi (path EC2→RDS). **KHÔNG bắn trang Amplify** (CDN, vô nghĩa).
  **Chỉ endpoint READ** (GET) — không tạo booking rác.

### `load` vs `stress`
- **load** = giữ tải ở **VU mục tiêu** (mặc định 200) trong 1 khoảng (vd 3 phút) → PASS/FAIL so ngưỡng.
- **stress** = **ramp tăng dần** (10→50→100→200→…) tới khi gãy → tìm **điểm gãy (knee)**, báo **sức chịu**
  (không pass/fail cứng — là số năng lực, không phải đúng/sai).

### Oracle (`load_lib.js`, hàm thuần trên k6 summary JSON)
| Chỉ số | Ngưỡng | Nguồn |
|---|---|---|
| `http_req_failed` (error rate) | < 1% | universal-ish |
| `http_req_duration` p95 | < 2500ms (trang) / 800ms (API) | mặc định từ CWV — **PLACEHOLDER, cần SLA business** |
| throughput (req/s) | báo ra | — |

- `verdict(summary, thresholds)` → PASS/FAIL (load) · `knee(stages)` → mức VU đầu tiên p95 vượt / error tăng (stress).
- **Phân loại nút thắt từ hình đường cong** (phần "đoán why" client-side, không cần AWS):
  `classifyBottleneck(stages)` → `latency tuyến tính`→CPU/worker · `bậc thang`→pool DB · `5xx`→worker chết ·
  `timeout`→DB lock. Trả **giả thuyết**, không phải kết luận (không nhìn được ruột server).
- ⚠️ Report **bắt buộc** ghi: **client-side only** (không thấy RDS/EC2 — không đụng AWS khách) +
  **DEV≠PROD** + ngưỡng p95 là **placeholder cho tới khi có SLA business**.

### Report + bug
- k6 xuất `summary.json` → `build_load_report.py` → `<Case>.load.xlsx` (Sheet "Kết quả" + "Findings" +
  cảnh báo). `bug_type:"Performance"` (tái dùng họ; capacity finding), chỉ khi thật sự FAIL và user duyệt.

---

## Thứ tự build
1. **i18n trước** (chạy được ngay, giá trị liền).
2. **load+stress** (build-only, run-gated).

## Không làm (YAGNI)
- Không tự bắn load/stress. Không đọc AWS. Không bắn endpoint ghi. Không thêm INP-kiểu-bịa.
- i18n: không auto-fix bản dịch, không đọc file locale trong repo (mù code — chỉ đọc DOM render).
