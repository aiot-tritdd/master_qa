# Track Accessibility (`/testcase-a11y`) — Design

> Ngày: 2026-07-16 · Trạng thái: **draft, chờ review** · Branch: `qa-brain`
> Thêm **Type test thứ 2** cho master_qa: Accessibility (WCAG), black-box, tách khỏi path functional.

---

## 1. Mục tiêu & phi-mục-tiêu

**Mục tiêu:** con QA hiện chỉ test **Functional** ở tầng E2E/System. Thêm khả năng quét
**Accessibility** (WCAG) trên các màn đang test — bắt lớp lỗi hiện đang **mù hoàn toàn**
(nút/icon không nhãn, input không label, tương phản thấp, thiếu heading…). Nhiều lỗi a11y
đồng thời là **bug UX/chất lượng thật**, nên giá trị không phụ thuộc việc có theo đuổi chuẩn WCAG hay không.

**Phi-mục-tiêu (YAGNI — v1 KHÔNG làm):**
- Crawl toàn site (chỉ quét màn trong scope của spec đang test).
- Mô phỏng screen-reader / giả lập điều hướng bàn phím.
- Triage moderate/minor (chỉ liệt kê, không thành bug).
- Tự sửa lỗi. Kỳ vọng "phủ hết WCAG" — axe tự-chấm chỉ bắt phần máy kiểm được (~1/3–1/2).

## 2. Vị trí trên lưới & 2 bức tường thép

- **Tọa độ:** Level = **E2E/System** (không đổi) · Type = **Accessibility** (mới).
- **Tường 1 (oracle = SPEC):** a11y oracle = **WCAG** — chuẩn ngoài, **độc lập với code-under-test**
  → *không* phá nguyên tắc chống-tautology. Là **track RIÊNG**, không trộn vào PASS/FAIL functional.
  `specs.md` chỉ dùng để **chọn màn cần quét (scope)**, **KHÔNG** làm oracle a11y.
- **Tường 2 (mù code):** axe-core **chỉ đọc DOM đã render** → không đọc code sản phẩm, không GitNexus.
  Runtime-safe, không cần PreToolUse hook.

## 3. Input — tái dùng đúng 1 spec người dùng vốn đưa

```
/testcase-a11y wtf-is-this/TestCase-XX
```

**Không có file mới do người dùng viết.** Nguồn "quét màn nào":
1. Đọc `wtf-is-this/TestCase-XX/specs.md`, mục **"3. Ảnh hưởng hệ thống"** → danh sách app/màn feature đụng.
2. Map **màn → URL** bằng `knowledge/*.md` (nav, approved) — đúng cơ chế **seam** qa-brain đã dùng cho functional.
3. Nếu folder đã có `tcs.json` **đã chạy** → tái dùng luôn màn/URL đã lái (khỏi seam lại — rẻ hơn).

> specs.md ở đây đóng vai **scope** (giống lúc functional dùng nó để biết test màn nào), **không** đóng vai oracle.

## 4. Flow (mỗi màn)

```
getPage(app)  →  goto url (seam từ knowledge/)  →  chờ readySelector  →  runAxe()
     login sẵn                                     (như shot())         →  nhóm vi phạm theo impact
                                                                        →  shot() chụp phần tử lỗi (evidence)
```

**Verdict mỗi màn** (song song 4-verdict functional, nhưng cho a11y):
| Verdict | Khi nào |
|---|---|
| `PASS` | 0 vi phạm mức **critical/serious** |
| `FAIL` | ≥1 vi phạm **critical/serious** |
| `未実施` | không quan sát được màn (login fail / 404 / thiếu quyền) |

moderate/minor: **liệt kê trong report, KHÔNG làm FAIL, KHÔNG vào sổ bug.**

## 5. Output

1. **`<Case>.a11y.xlsx`** — report riêng, build bằng `build_a11y_report.py` (dùng lại `theme.json`).
   Mỗi vi phạm: `rule · impact · phần tử (selector/HTML) · WCAG ref · gợi ý fix` (axe cho sẵn) + ảnh evidence.
2. **Sổ bug** — critical+serious → append `wtf-is-this/bug-he-thong.tcs.json`, theo đúng quy trình `docs/BUG-LOG.md`.

### Flow đưa vào sổ bug (đã verify với `build_bug_report.py`)

**Guard KHÔNG chặn** (dòng 730–739 chỉ ép `bug_id` unique + `found_at` + `status` hợp lệ; `bug_type` không bị guard).
Map mỗi finding a11y → 1 object bug:

| field | giá trị a11y |
|---|---|
| `bug_id` | `BUG-NNN` kế tiếp (max hiện có +1) |
| `found_at` / `status` | ngày / `"Mở"` |
| `bug_type` | **`"Accessibility"`** (loại mới) |
| `result` | **luôn `"FAIL"`** — a11y không bao giờ SPEC-GAP (WCAG luôn định nghĩa kỳ vọng) |
| `pri` | critical → `High` · serious → `Medium` |
| `source` | `TestCase-XX` (spec lộ ra) |
| `screen` | `"<App> — <Màn>"` (cột Service tự cắt tiền tố trước ` — `) |
| `title` | *"WCAG `<rule>`: `<màn>` — `<mô tả hành vi>`"* (hành vi, không file:line) |
| `expect` | trích **WCAG rule** (không phải spec) — vì đây là bản ghi bug, không phải bước write-oracle |
| `actual` | *"axe rule `<id>`, impact `<mức>`, N phần tử"* + gợi ý fix axe cho sẵn |
| `before` / `after` | `before=null` (kèm `note` giải thích N/A) · `after` = ảnh phần tử lỗi |
| `id` (TC-ref) | hyperlink trỏ `<Case>.a11y.xlsx` (evidence a11y, không phải TestCase-XX.xlsx) |

**Chống ngập — dedup bắt buộc:** gom **1 bug / (màn × axe-rule)**. 8 nút cùng lỗi `button-name` trên 1 màn
= **1 bug** (`actual` ghi "8 phần tử", detail liệt kê selector), KHÔNG phải 8 dòng.

## 6. Thành phần cần xây (6 mảnh — tái dùng phần lớn hạ tầng)

| Mảnh | File | Việc |
|---|---|---|
| Helper quét | `.claude/skills-scripts/testcase-evidence/a11y_lib.js` | nhét axe-core vào trang + `runAxe(page, opts)` → trả vi phạm nhóm theo impact; cạnh `pw_lib`/`pw_api` |
| Skill điều phối | `.claude/commands/testcase-a11y.md` | đọc specs.md → seam màn → chạy `runAxe` → verdict → viết `a11y.results.json` → build xlsx → đẩy sổ bug |
| Report builder | `.claude/skills-scripts/testcase-evidence/build_a11y_report.py` | in `<Case>.a11y.xlsx` |
| Enum sổ bug | `build_bug_report.py` | **sửa tuple hardcode dòng ~380** `("Function","UI","Text")` → thêm `"Accessibility"` (nếu không, a11y bug vào list nhưng KHÔNG hiện ở bảng breakdown-theo-loại). Guard KHÔNG cần đổi. `theme.json` không giữ list này. |
| Dependency | `skills-scripts/node_modules` | thêm `axe-core` (hoặc `@axe-core/playwright`) — black-box, không đụng code SP |
| **Doc quy trình** | `docs/BUG-LOG.md` | thêm `Accessibility` vào bảng `bug_type` (dòng ~49) + 1 dòng note a11y: *result luôn FAIL · `before=null`+`after`=ảnh phần tử lỗi · dedup 1 bug/(màn×rule) do lệnh a11y lo* — giữ "1 tri thức 1 nhà" |

## 7. axe-core lấy từ đâu

npm `axe-core` (thư viện quét, chạy trong trình duyệt) inject qua Playwright, hoặc `@axe-core/playwright`
(wrapper tiện). Đã có `playwright` local trong `skills-scripts/node_modules` → chỉ thêm 1 dep. Thuần black-box.

## 8. Test cho chính feature (nghiệm thu)

- Chạy trên **1 màn Vuetify đã biết** (vd Pro `/reservations`) → verify axe bắt vi phạm `button-name`
  (dự đoán CÓ thật vì Vuetify icon-button hay thiếu accessible name — xem `knowledge/lessons.md` các `.mdi-*`).
- Verify `build_a11y_report.py` ra xlsx sạch, ảnh nhúng đúng.
- Verify guard sổ bug **pass** với `bug_type: "Accessibility"` mới (không raise).
- Verify verdict: màn 0 crit/serious → PASS; màn có → FAIL + đẩy sổ bug.

## 9. Rủi ro & câu hỏi mở

- **specs.md không liệt kê màn rõ** → fallback: reuse `tcs.json` đã chạy, hoặc hỏi người (không mò code).
- **Thời điểm quét:** axe phải chạy **sau khi trang render xong** — tái dùng logic chờ của `shot()`
  (readySelector + networkidle + đệm), không `runAxe` trên màn còn spinner.
- **Màn cần quyền** (report ticket cần `ticket-admin`) → reuse `getPage` targets + env như functional.
- **Nội dung động:** v1 quét 1 snapshot/màn — đủ. Multi-state (mở dialog rồi quét) để sau.
- **Ngưỡng critical/serious** theo phân loại mặc định của axe; nếu nhiễu → tinh chỉnh rule-set sau (không phải v1).
- **Sổ bug trộn functional + a11y:** số liệu Tổng quan (High đang mở, theo Service, xu hướng) sẽ gộp cả 2 loại.
  Chấp nhận ở v1 (1 bảng bug chung, `bug_type` phân biệt). Muốn tách chart theo loại → sau.
- **Dedup xuyên lần chạy:** v1 gom trong-1-lần-chạy (màn × rule). Cùng lỗi tái xuất ở lần chạy sau có thể tạo BUG mới trùng
  → đây là việc của **Analyzer** (hạng mục #2 trong roadmap), KHÔNG giải trong v1 a11y.
