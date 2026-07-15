# BUG-LOG — quy trình log bug vào sổ hệ thống

> Sổ bug toàn hệ = `wtf-is-this/bug-he-thong.xlsx`, sinh từ `wtf-is-this/bug-he-thong.tcs.json`
> qua `build_bug_report.py`. **JSON là nguồn sự thật, Excel là bản in.**
> ⛔ **KHÔNG BAO GIỜ gõ tay vào Excel** — merge cell + shape neo theo dòng + COUNTIF theo range
> → sửa tay là lệch trang trí, sai số đếm. Sửa JSON rồi build lại, luôn.

Khác `build_evidence.py`: file kia in evidence **một spec** (Cover/Test Cases/Checklist).
`build_bug_report.py` in **sổ bug toàn hệ** (Tổng quan / Danh sách Bug / SPEC-GAP).

---

## 1. Có bug mới → thêm 1 object vào mảng `tcs`

Mở `wtf-is-this/bug-he-thong.tcs.json`, append:

```json
{
  "bug_id": "BUG-012",
  "id": "TC-15",
  "source": "TestCase-13",
  "screen": "Pro — Đặt lịch (double-book)",
  "pri": "High",
  "bug_type": "Function",
  "result": "FAIL",
  "title": "[1 câu: spec bảo X, màn làm Y]",
  "found_at": "2026-07-16",
  "status": "Mở",
  "fix_note": "",
  "retested_at": "",
  "pre": "...", "steps": "...", "expect": "...", "actual": "...", "note": "...",
  "before": null, "after": null
}
```

Phần lớn field copy thẳng từ file test `wtf-is-this/TestCase-XX/TestCase-XX.tcs.json` sang.

### Field — ý nghĩa

| Field | Bắt buộc? | Ghi gì |
|---|---|---|
| `bug_id` | ✅ (guard) | `BUG-NNN`, **duy nhất toàn sổ** |
| `found_at` | ✅ (guard) | ngày phát hiện, `YYYY-MM-DD` |
| `status` | ✅ (guard) | 1 trong **Mở / Chờ retest / Đã đóng / Tái phát** (xem §2) |
| `id` | | mã case gốc `TC-XX` (cột TC ref hyperlink về file evidence) |
| `source` | | spec **lộ ra** bug (`TestCase-XX`) — KHÔNG phải "của ai", chỉ là nơi soi thấy |
| `screen` | | màn/chức năng. Cột **Service** tự cắt từ đây (chữ trước ` — ` hoặc ` (`) |
| `pri` | | `High` / `Medium` / `Low` |
| `bug_type` | | `Function` / `UI` / `Text` |
| `result` | | `FAIL` (chấm được, sai spec) hoặc `SPEC-GAP` (spec im lặng → việc BA) |
| `title` | | mô tả 1 câu — báo **hành vi** (spec X / màn Y), KHÔNG file:line |
| `fix_note` | | để rỗng lúc mới; điền khi dev fix (xem §2) |
| `retested_at` | | để rỗng lúc mới; điền khi QA test lại (xem §2). **Bug age** tự tính từ 2 mốc này |
| `pre/steps/expect/actual/note` | | copy từ file test — chi tiết không in vào sổ (đã có ở TestCase-XX.xlsx) |
| `before/after` | | đường dẫn ảnh, hoặc `null` (test mức API không có ảnh) |

---

## 2. Vòng đời bug → chỉ đổi `status` (+ 2 field)

```
Mở  ──dev fix──▶  Chờ retest  ──QA test lại──▶  Đã đóng   (PASS)
                                            └──▶  Tái phát  (vẫn lỗi)
```

| Khi | Sửa trong JSON |
|---|---|
| Dev báo đã fix | `"status": "Chờ retest"` · `"fix_note": "dev fix gì"` |
| QA test lại **PASS** | `"status": "Đã đóng"` · `"retested_at": "2026-07-20"` |
| QA test lại **vẫn lỗi** | `"status": "Tái phát"` |

> **"Đã fix" là lời khai của dev** (→ Chờ retest). **"Đã pass" là QA quan sát lại thật** (→ Đã đóng).
> Đừng nhảy thẳng Mở → Đã đóng.

**SPEC-GAP** (`result: "SPEC-GAP"`): không phải bug dev, là lỗ hổng tài liệu → việc BA đính chính.
Tự nhảy sang **sheet SPEC-GAP** riêng trong sổ.

---

## 3. Build lại (mỗi lần sửa JSON)

```bash
python3 .claude/skills-scripts/testcase-evidence/build_bug_report.py \
  wtf-is-this/bug-he-thong.tcs.json wtf-is-this/bug-he-thong.xlsx
```

- Mọi số là COUNTIF/COUNTIFS — **0 ô hardcode**. Bất biến `Mở+Chờ retest+Đã đóng+Tái phát == tổng bug`;
  lệch → script **raise, không in file sai**.
- Chart chỉ vẽ khi dữ liệu đỡ nổi (ngưỡng ở `theme.json`); dưới ngưỡng → bảng/stat đứng thay.
- Mở xem **trên OneDrive / Excel Online** — Excel desktop hết-license render lỗi (View Only), làm tưởng file xấu.

## 4. Trang trí (trời/mây/kem/đồi cỏ)

Skin lấy từ file sếp vẽ, đã **nhúng vào script**: nền kem + banner trời + mặt trời/mây (neo cố định) +
đồi cỏ (tự tụt xuống đáy nội dung khi thêm bug) + data-bar xanh lá. Hình vector ở asset
`.claude/skills-scripts/testcase-evidence/bug_report_decor.xml`.

- Màu/mốc neo: `theme.json → labels.bug_report.decor`.
- **Tắt về bản pro sạch** (navy/trắng): `decor.enabled = false`.

---

**Tóm 1 dòng:** sửa `bug-he-thong.tcs.json` → chạy `build_bug_report.py` → sổ đẹp tự ra.
Không đụng Excel tay, không bịa field không có trong JSON.
