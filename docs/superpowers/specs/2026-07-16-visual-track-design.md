# Track Visual (`/testcase-visual`) — Design

> Ngày: 2026-07-16 · Trạng thái: **draft, chờ review** · Branch: `qa-brain`
> Type test thứ 3 cho threease_qa: Visual regression, black-box, tách khỏi path functional.
> Đi sau a11y (`2026-07-16-a11y-track-design.md`) — tái dùng khuôn command đó.

---

## 1. Mục tiêu & phi-mục-tiêu

**Mục tiêu:** bắt lớp bug **UI vỡ/lệch** mà Functional mù (nút tràn khung, layout xô, font/màu đổi ngoài
ý muốn, ảnh vỡ) — bằng cách so ảnh màn hiện tại với **ảnh baseline đã người-duyệt**. Hợp dự án
**mature** như ThreeSides (chạy lặp nhiều lần, có baseline để gật).

**Bản chất — nói rõ:** Visual là công cụ **REGRESSION**, trả lời *"có ĐỔI so bản duyệt không"*, KHÔNG
phán *"UI có ĐÚNG không"*. Điểm neo là baseline người-duyệt.

**Phi-mục-tiêu (YAGNI — v1 KHÔNG làm):**
- So đa-viewport / đa-browser (để track Compatibility lo).
- Auto-update baseline hàng loạt (mỗi update chuẩn phải có người gật).
- So từng-component / DOM-level (chỉ so ảnh cả màn sau mask).

## 2. Vị trí trên lưới & 2 bức tường thép

- **Tọa độ:** Level = **E2E/System** (không đổi) · Type = **Visual** (mới).
- **Tường 1 (oracle = SPEC):** Visual oracle = **baseline PNG đã người-duyệt** — độc lập với code-under-test
  (giống WCAG cho a11y) → không phá chống-tautology. Track RIÊNG, không trộn PASS/FAIL functional.
  `specs.md` chỉ dùng **chọn màn cần chụp (scope)**, KHÔNG làm oracle.
- **Tường 2 (mù code):** chỉ đọc **pixel màn đã render**, không đọc code sản phẩm / GitNexus lúc runtime.

## 3. Baseline — nhà, git, vòng đời (quyết 2026-07-16)

- **Nhà:** `baselines/<app>/<màn-slug>.png` ở **gốc repo** (KHÔNG trong `.claude/skills-scripts/` — đó là
  tool, không chứa data). Key = `app` + slug từ URL/tên màn.
- **Git:** **COMMIT vào repo** = chuẩn chia sẻ toàn team/CI (ai chạy cũng so cùng 1 chuẩn). Baseline luôn là
  ảnh **đã mask** (không commit data dev thật).
- **Vòng đời:**
  ```
  chưa có baseline  →  chạy chụp masked  →  result NEW-BASELINE  →  NGƯỜI GẬT "nhìn đúng"  →  commit thành chuẩn
  đã có baseline    →  chụp masked → so pixel → PASS / FAIL(+diff)
  cố ý đổi UI       →  update baseline có chủ đích (gật lại) → commit đè
  ```
- **1 điểm người-chạm KHÔNG bỏ được:** baseline lần đầu (và mỗi lần cố ý đổi) **phải có người gật** — nếu
  không, ảnh chuẩn có thể đóng băng luôn cả bug. Nhưng chỉ **1 lần/màn**, sau đó tự động. (Auto-detect ở §4
  chỉ bỏ việc *vẽ mask*, KHÔNG bỏ việc *gật baseline* — đó là bản chất Visual.)

## 4. Mask vùng động — sinh Ở NƠI SINH TRI THỨC (không mask tay)

Màn có chỗ động (đồng hồ, tên khách, số dư) → phải che nhất quán mọi lần chụp, nếu không diff giả tràn.
Mask là tri thức **HOW** ("quan sát màn này sao cho ổn định") → sống trong knowledge nav doc + sinh ra ở
**build-time authoring**, KHÔNG nhét tay sau.

- **Nơi lưu:** thêm block `mask: [selector...]` vào `knowledge/*.md` của màn (approved qua UI-confirm).
- **Ai sinh (v1 scope — update authoring):** `/testcase-systemdoc` + `explorer.js` thêm bước auto-detect:
  - **Kỹ thuật:** chụp cùng 1 màn **2 lần cùng-trạng-thái** → diff pixel → vùng nào tự đổi = **vùng động** →
    map về selector bao vùng đó → đề xuất `mask:`. Người **chỉ liếc duyệt** (không vẽ tay), 1 lần/màn.
  - Deterministic (double-snapshot diff), hợp triết lý "script cơ khí".
  - ⚠️ Bắt được động **trong-phiên** (clock/animation/thứ-tự); động **xuyên-phiên** (số dư mai khác) thì
    người liếc bổ sung lúc duyệt — auto-detect lo phần lớn, không phải 100%.

## 5. Flow `/testcase-visual <folder>` (mỗi màn)

```
đọc specs.md (chọn màn) → seam URL + đọc mask: từ knowledge/ → getPage(app) → goto → chờ render (shot-style)
   → captureMasked(page, masks)
        ├─ chưa có baselines/<app>/<slug>.png  → lưu ảnh làm candidate → result NEW-BASELINE (chờ gật)
        └─ có rồi → compareToBaseline → diffRatio
                        ├─ ≤ ngưỡng → PASS
                        └─ > ngưỡng → FAIL (+ ảnh diff tô đỏ)
```

**Verdict/màn:** `PASS` · `FAIL` · `未実施` (không vào được màn) · `NEW-BASELINE` (chưa có chuẩn).
Visual **KHÔNG BAO GIỜ** SPEC-GAP (oracle là baseline, luôn có/không — không có khoảng "spec im lặng").
Ngưỡng mặc định **≈ 0.1% pixel khác** (sau mask), chỉnh được.

## 6. Output

1. **`<Case>.visual.xlsx`** (build bằng `build_visual_report.py`, dùng lại `theme.json`): mỗi màn 1 dòng —
   **baseline | hiện tại | diff (tô đỏ)** + `diffRatio` + verdict + sheet "Màn quét" (per-screen verdict, như a11y).
2. **Sổ bug** — FAIL (diff > ngưỡng) → append `bug-he-thong.tcs.json`, `bug_type: "Visual"` (loại mới), theo
   `docs/BUG-LOG.md`. `result:"FAIL"` · `pri` theo `diffRatio` (lệch lớn → High) · `before`=baseline · `after`=ảnh diff.
   Dedup **1 bug/màn** (mỗi màn lệch = 1 bug, không tách theo vùng). `NEW-BASELINE`/`未実施` KHÔNG vào sổ bug.

## 7. Thành phần cần xây (7 mảnh — tái dùng khuôn a11y)

| Mảnh | File | Việc |
|---|---|---|
| Helper | `.claude/skills-scripts/testcase-evidence/visual_lib.js` | `captureMasked` · `detectDynamic` · `compareToBaseline` (pixelmatch) |
| Dep | `node_modules` | thêm `pixelmatch` + `pngjs` (đọc/ghi PNG cho diff) — black-box |
| Kho baseline | `baselines/` (gốc repo) | ảnh chuẩn đã mask, commit git |
| Report | `build_visual_report.py` | in `<Case>.visual.xlsx` (3 ảnh/màn + coverage sheet) |
| Command | `.claude/commands/testcase-visual.md` | điều phối flow §5 |
| Authoring | `/testcase-systemdoc` + `explorer.js` | auto-detect vùng động → emit `mask:` vào knowledge doc |
| Enum sổ bug | `build_bug_report.py` (tuple type) + `docs/BUG-LOG.md` | thêm `"Visual"` (giống cách thêm `"Accessibility"`) |

## 8. Test cho chính feature (nghiệm thu)

- `visual_lib`: fixture 2 ảnh PNG **giống hệt** → diffRatio 0 / PASS; 2 ảnh **khác 1 khối** → diffRatio > ngưỡng +
  diff img có vùng đỏ. `detectDynamic`: trang có 1 phần tử đổi text giữa 2 lần chụp → nhận đúng vùng đó.
- `build_visual_report.py`: results mẫu (1 màn FAIL + 1 NEW-BASELINE) → xlsx đúng 3 ảnh + coverage sheet.
- Sổ bug: append 1 bug `bug_type:"Visual"` vào bản real → guard không raise, Tổng quan hiện loại Visual.
- **Live-verify (cần Docker dev):** chạy `/testcase-visual` trên 1 màn Pro → NEW-BASELINE lần đầu; chạy lại →
  PASS; sửa gì đó (vd zoom) → FAIL + diff đỏ đúng chỗ. (Nếu dev down → DEFERRED như a11y.)

## 9. Rủi ro & câu hỏi mở

- **Noise là kẻ thù số 1.** Font rendering / anti-alias / sub-pixel khác giữa máy → diff giả. Giảm bằng:
  `deviceScaleFactor` cố định (đã có), threshold pixelmatch (`0.1` mặc định của lib), ngưỡng diffRatio.
  Nếu vẫn noise → siết mask, KHÔNG nới ngưỡng bừa (nới = mù bug thật).
- **Baseline chụp trên máy A, chạy trên máy B** → nếu render khác (OS font) có thể diff giả dù commit chung.
  v1 giả định team chạy cùng harness (Chromium Playwright pinned) → rủi ro thấp; theo dõi, chưa giải trước.
- **Động xuyên-phiên** (số dư đổi theo ngày) auto-detect không bắt hết → người bổ sung mask lúc duyệt (§4).
- **Update authoring đụng lại `explorer.js`** (vừa build tuần này) → làm cẩn thận, giữ FIREWALL HOW-only của nó
  (mask là HOW → hợp lệ, không phá tường).
