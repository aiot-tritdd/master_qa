# Sổ bug hệ thống + Báo cáo thống kê — Design

> Ngày: 2026-07-15 · Branch: `qa-brain` · Trạng thái: **chờ user duyệt**
> Nguồn gốc: sếp yêu cầu "thống kê bug"; mẫu tham khảo `wtf-is-this/{Project_Name}_テスト報告書・TestReports.xlsx`

## 1. Vấn đề

`wtf-is-this/bug-he-thong.tcs.json` hiện là **sổ ghi chết**: 11 bug (9 FAIL + 2 SPEC-GAP, đều
`source: TestCase-12`), có đủ *bug gì* + ảnh, nhưng **không có vòng đời**. Bug ghi vào là nằm im
vĩnh viễn — không ai biết nó đã fix chưa, fix thế nào, pass lại chưa, phát hiện từ bao giờ.

Sếp muốn 4 thứ: **bao nhiêu bug · bug gì · fix thế nào · pass chưa** — cộng thống kê theo
ngày/tuần/tháng. Ta có thứ 2, thiếu 1/3/4 và thiếu trục thời gian.

### 1.1 Bài học từ mẫu của sếp (bằng chứng, không phải ý kiến)

Mẫu `{Project_Name}_テスト報告書` là **mẫu tay** và nó **đang đếm sai**, đo được:

| Chỗ | Mẫu nói | Sự thật trong `List bug` | Nguyên nhân |
|---|---|---|---|
| §2a Bug theo loại | TOTAL = **13** | có **10 bug** | dòng 4-5 bị **gõ tay đè** lên công thức hỏng |
| §2b Bug theo severity | High/Mid/Low = **0/0/0** | **4/2/4** | `COUNTIF('List bug'!$I:$I,...)` — cột `I` là *Trình duyệt*, severity ở cột `J` |
| §1 cột Bug UI/Text/Function | 3 màn cuối = 0 | có bug | `COUNTIFS($B:$B, <tên màn>, $C:$C, "Bug UI")` — lệch đúng 1 cột (phải là `$C:$C` và `$D:$D`) |

**Kết luận thiết kế:** mẫu đó hỏng **vì nó được bảo trì bằng tay** — chèn cột làm lệch công thức,
không ai biết, rồi gõ tay đè lên để che. Luật `CLAUDE.md` (*"xlsx = bản in từ tcs.json"*,
*"CẤM sửa Excel tay"*) không phải cầu toàn — nó là thứ chặn đúng lỗi này.

## 2. Nguyên tắc bất di

1. **`bug-he-thong.tcs.json` là nguồn sự thật duy nhất.** `.xlsx` chỉ là **bản in**.
   Không một số nào trong xlsx được gõ tay; tất cả là `COUNTIF`/`COUNTIFS` hoặc do script sinh.
2. **Tương tác để ĐỌC = ✅ · Tương tác để GHI = ❌.** Lọc/sort/nhảy-link/tô-màu thoải mái.
   Dropdown, ô nhập → **không** (mời người sửa bản in = đúng tội đã giết mẫu của sếp). Ghi là việc của JSON.
3. **`status` là người gõ, `result` là máy chốt.** Dev báo "fix rồi" → `status: 🟡 Chờ retest`,
   nhưng `result` **vẫn `FAIL`** tới khi chạy lại và quan sát thấy PASS.
   *"Đã fix" là lời khai. "Đã pass" là bằng chứng.* Gộp 2 cột = mất ranh giới làm QA này đáng tin.
4. **Màu = `theme.json`.** Không bịa palette mới (nếu không Report đá với sheet Chi tiết cùng file,
   và mất tính chất "đổi màu = sửa 1 file").
5. **Chart chỉ vẽ khi dữ liệu đỡ nổi** (§6). Điều kiện nằm trong script, không nằm trong trí nhớ ai.

## 3. Ba file, ba vai

### 3.1 Bệnh hiện tại: `-update` là XOÁ, không phải chạy lại

Đo trên TestCase-12 (2026-07-15):

| File | Số case | Kết quả |
|---|---|---|
| `TestCase-12/tcs.json` | **54** | 43 PASS · 9 FAIL · 2 SPEC-GAP |
| `TestCase-12/tcs-update.json` | **43** | **43 PASS · 0 FAIL** |
| Chênh | **−11** | đúng 11 con đã sang `bug-he-thong` (đối chiếu từng ID: khớp 100%) |

Không con nào được chạy lại. Không con nào FAIL→PASS. **Chúng bị gỡ khỏi file.**
⇒ `TestCase-12-update.xlsx` nói **"43/43 PASS — 100%"**. Ai mở nó một mình sẽ tưởng spec 12 sạch bong.
Thông tin không mất (nằm ở sổ bug), nhưng **file đó tự nó không hé răng**.

Đây **cùng cơ chế với `⛔ Won't fix`** đã bị cắt ở §5.1: làm số đẹp lên bằng cách **bỏ bớt cái xấu**,
không phải bằng cách sửa nó.

**Gốc rễ:** `-update` gộp **hai việc khác hẳn nhau** vào cùng thao tác "xoá dòng":
1. **Gỡ case ngoài scope** — sửa phạm vi, làm **1 lần**, ngay sau khi dev confirm
2. **Chạy lại sau khi dev fix** — kiểm chứng, làm **sau**, làm **nhiều lần**

Hai cái cho ra file trông y hệt (toàn PASS) nhưng **nghĩa ngược nhau**.

### 3.2 Chốt vai

| File | Vai | Số case | Sửa? |
|---|---|---|---|
| `TestCase-XX/tcs.json` | **Biên bản đóng băng** — lần chạy #1, quan sát thô | đủ (54) | ❌ không bao giờ. Sửa = gian lận evidence. |
| `TestCase-XX/tcs-update.json` | **Bản sống của spec đó** — trạng thái spec XX *bây giờ* + phân loại scope | **đủ (54)** | ✅ mỗi lần retest |
| `bug-he-thong.tcs.json` | **Sổ sống của toàn hệ** — vòng đời từng con bug | chỉ bug | ✅ liên tục |

Ba file trả lời **ba câu hỏi khác nhau**, nên không mâu thuẫn dù cùng chứa 1 con bug:
*"hôm đó chạy ra sao?"* (quá khứ) · *"spec 12 giờ sạch chưa?"* (hiện tại, theo spec) ·
*"hệ còn bug gì?"* (hiện tại, toàn hệ).

> **Luật đếm:** *"TestCase-12 có bao nhiêu bug"* **luôn** đếm ở **sổ bug** (`COUNTIF(source)`),
> không bao giờ đếm ở biên bản. Một con số, một nhà.

### 3.3 `-update` đổi nghĩa: KHÔNG xoá case nào

`tcs-update.json` giữ **đủ 54 case**. Case ngoài scope được **đánh cờ, không gỡ**:

```json
{ "id": "TC-25", "result": "FAIL", "out_of_scope": true, "bug_id": "BUG-002", ... }
```

Cover của `-update` đếm **hai khối riêng**:
```
TRONG SCOPE   43 case  →  43 PASS · 0 FAIL          Pass rate 100%
NGOÀI SCOPE   11 case  →  9 FAIL · 2 SPEC-GAP       → đã chuyển sổ bug (BUG-001..BUG-011)
```
Vẫn ra được con số **100%** đẹp để nộp, nhưng **file tự nói ra** là có 11 phát hiện khác.
Đây cũng là chỗ khoe: *"spec 13 pass hết, tiện thể lòi thêm 11 bug hệ thống"* — thứ QA tay không làm được.

**Pass rate chỉ tính trên case trong scope.** Spec 13 không bị chấm điểm xấu vì lỗi không phải của nó.

### 3.4 `out_of_scope` sống ở `-update`, KHÔNG ở `tcs.json`

Phân loại scope là **phán đoán của dev, biết được SAU khi chạy** — nó là *diễn giải*, không phải
*quan sát*. Biên bản `tcs.json` chỉ chứa quan sát ⇒ giữ đóng băng tuyệt đối, không thêm cờ vào đó.
Diễn giải sống ở bản sống (`-update`). Đây chính là ranh giới §2.3 (*"đã fix" là lời khai · "đã pass"
là bằng chứng*) áp cho scope: **"ngoài scope" là lời khai của dev, phải nằm ở nơi sửa được.**

## 4. Schema — thêm 6 field vào mỗi phần tử `tcs[]`

| Field | Ví dụ | Ai điền | Bắt buộc |
|---|---|---|---|
| `bug_id` | `BUG-001` | script cấp khi append | ✅ |
| `found_at` | `2026-07-14` | script, lúc bug vào sổ | ✅ |
| `status` | `🔴 Mở` \| `🟡 Chờ retest` \| `✅ Đã đóng` \| `🔁 Tái phát` | **người**, khi dev báo | ✅ (mặc định `🔴 Mở`) |
| `fix_note` | "dev thêm validate quantity ở API hold" | dev / user | ❌ |
| `retested_at` | `2026-07-20` | script, lúc `/testcase-retest` chạy | ❌ |
| `bug_type` | `Function` \| `UI` \| `Text` | script (mặc định `Function`) | ✅ |

Field cũ giữ nguyên hết: `id, source, screen, pri, result, title, pre, steps, expect, actual,
before, after, note`.

### 4.1 `bug_id` — vì sao BẮT BUỘC phải có, tách khỏi `id`

Sổ đang dùng `id` = ID test case gốc (`TC-09`, `TC-25`…). Nhưng **TestCase-11 có `TC-01`→`TC-59`
và TestCase-12 có `TC-01`→`TC-54`** — **cùng dải ID**.

⇒ Ngày TestCase-11 góp bug đầu tiên vào sổ, sổ sẽ có **hai dòng cùng tên `TC-09`**, hai con bug
hoàn toàn khác nhau. Dev hỏi *"TC-09 fix chưa?"* → không ai trả lời được. Đây **không phải rủi ro
xa xôi**: 11/11 bug hiện tại đều từ TestCase-12, tức **lần thứ hai đổ bug vào sổ là dính**.

Lỗi gốc: **mượn ID của phạm vi này (1 spec) làm ID cho phạm vi khác (toàn hệ)**.

**Sửa:**
- `bug_id` = `BUG-001`, `BUG-002`… — danh tính riêng của sổ, **cấp tăng dần, không bao giờ tái sử dụng**
  (kể cả khi bug bị xoá — đảm bảo link/hội thoại cũ không trỏ nhầm con khác).
- `tc_ref` (hiển thị, script sinh từ `id` + `source`) = `"TC-09 @ TestCase-12"` — con trỏ ngược.
- Migration: 11 bug hiện có được cấp `BUG-001`..`BUG-011` theo đúng thứ tự đang nằm trong mảng `tcs`.

## 5. Output — `wtf-is-this/bug-he-thong.xlsx`, 3 sheet

| Sheet | Ai đọc | Nội dung |
|---|---|---|
| `Report` | **Sếp** | Thống kê. Mở ra thấy hết, không cần cuộn. |
| `List bug` | **Dev** | 1 dòng = 1 bug. Lọc/sort được. |
| `Chi tiết` | Dev khi fix | Sheet `Test Cases` hiện có — pre/steps/expect/actual + ảnh before/after. **Giữ nguyên.** |

### 5.1 Sheet `Report`

```
BÁO CÁO BUG HỆ THỐNG — Threease                 [banner navy 1F3864]
dev · QA-Server · cập nhật 2026-07-15

① TÌNH TRẠNG HIỆN TẠI                    ← KPI row, stat tile
  ┌────────┬──────────┬──────────────┬──────────┬───────────┐
  │   11   │    9     │      0       │    2     │     0     │
  │Tổng bug│🔴 Đang mở│🟡 Chờ retest │✅ Đã đóng│🔁 Tái phát│
  └────────┴──────────┴──────────────┴──────────┴───────────┘
  Bất biến: `Đang mở + Chờ retest + Đã đóng + Tái phát = Tổng bug`.
  Script assert điều này; lệch = có `status` sai chính tả trong JSON → **build FAIL, không in ra
  file sai**. (Thà không có file còn hơn có file nói dối — xem §1.1.)

  **Không có `⛔ Won't fix`** — cố ý. Nó là **nút rửa số**: gạt bug khó sang đó thì ô "🔴 Đang mở"
  tụt xuống mà không sửa gì cả, tức xây lại đúng căn bệnh §1.1 nhưng "hợp lệ theo thiết kế".
  Bug không định fix thì hoặc **không phải bug** (đừng cho vào sổ), hoặc **là nợ đang gánh**
  (phải để `🔴 Mở` cho nhức mắt). Không nhánh nào cần status thứ 5.
② THEO SPEC          Spec │Bug góp│🔴 Mở│🟡 Chờ│✅ Đóng│⚠️ Gap    [+ data bar cột "Bug góp"]
③ THEO MỨC ĐỘ        High 6 · Mid 3 · Low 2                      [+ 🍩 doughnut]
④ THEO LOẠI          Function 9 · UI 0 · Text 0 · ⚠️ Spec-Gap 2
⑤ THEO THỜI GIAN     Kỳ │Phát hiện│Đã đóng│Tồn cuối kỳ           [+ 📈 line khi ≥4 kỳ]
⑥ BUG ĐỂ LÂU NHẤT    top 5 theo bug age (High + đang mở lên đầu)
⑦ MÔI TRƯỜNG & PHẠM VI
```

- **Mọi ô số = `COUNTIF`/`COUNTIFS` trỏ vào sheet `List bug`.** Zero hardcode. (Đây là điều kiện
  chống đúng bệnh §1.1.)
- Mục ⑤ chạy được **chỉ nhờ** `found_at` + `retested_at`. Kỳ = ISO week (`2026-W29`) và tháng (`2026-07`).
- Mục ⑥ **bug age** = `hôm nay − found_at` (ngày). Tô `pri_high` khi `pri=High` **và** `status=🔴 Mở`
  **và** age > 14 ngày. Đây là con số các template tracker ngoài kia đều có và sếp sẽ hỏi nhiều nhất.

### 5.2 Sheet `List bug` — Excel Table thật

Cột: `STT · Bug ID · TC ref · Spec · Màn/Chức năng · Loại · Mức độ · Tiêu đề · Hiện tượng quan sát ·
Status · Fix note · Ngày phát hiện · Ngày retest · Bug age · Ghi chú`

- **`Table` + AutoFilter** (`TableStyleMedium2`) → dropdown lọc mọi cột + banded row.
  Lọc `Spec=TestCase-12` + `Status=🔴 Mở` = backlog của dev. **Đây là "tương tác" thật.**
- **Freeze pane** ở header → cuộn 100 bug vẫn thấy tên cột.
- **Hyperlink `Bug ID` → sheet `Chi tiết`** (nhảy tới ảnh before/after). Mẫu sếp phải mở Google Drive
  (link chết = mất chứng cứ); ta bấm 1 phát, ảnh nằm trong file.
- **Conditional formatting:** `Mức độ` → `pri_high/medium/low`; `Status` → chip màu.
  **Luôn kèm chữ** (xem §7).
- **KHÔNG data-validation dropdown** — xem nguyên tắc §2.2.

## 6. Chart — điều kiện vẽ nằm trong script

| Chart | Dạng | Điều kiện vẽ | Hiện tại |
|---|---|---|---|
| Bug theo mức độ | 🍩 doughnut | ≥2 mức có bug | ✅ vẽ (6/3/2) |
| Theo spec × status | 📊 stacked bar **ngang** | ≥2 spec có bug | ✅ vẽ |
| Bug tồn cuối kỳ | 📈 line | **≥4 kỳ** | ⏳ chưa — stat tile ⑤ đứng thay |

Dưới ngưỡng thì **không vẽ**, bảng/stat tile đứng thay. Hệ quả: file **tự đẹp lên** khi dữ liệu dày —
không ai phải nhớ bật gì.

**Căn cứ (skill `dataviz`):**
- Doughnut hợp lệ: part-to-whole, **3 ≤ 6 segment**, giá trị cách nhau rõ (6/3/2) → không dính
  *"donut for comparing close values"*.
- Line 1 điểm = *"one-bar bar chart"* → phải là stat tile. Nên chặn ở 4 kỳ.
- Bar ngang vì tên category dài (`TestCase-12`).
- **Bar theo spec: một màu duy nhất cho mọi cột** (spec là nominal) — cấm *"value-ramp on nominal
  categories"*.
- Legend luôn hiện khi ≥2 series.

## 7. Ràng buộc màu — đo được, không phải ý kiến

Chạy `dataviz/scripts/validate_palette.js` trên `theme.json`:

| Bộ màu | Kết quả | Hệ quả |
|---|---|---|
| `pri_high/medium/low` (`C00000,BF8F00,548235`) | **ALL PASS** — CVD worst adjacent **ΔE 23.1** (deutan) | 🍩 doughnut tô thoải mái. *(Nghi ngờ ban đầu "đỏ/xanh-lá không an toàn" là **SAI** — vàng ở giữa gánh.)* |
| `pri_medium` `BF8F00` | ⚠️ WARN contrast **2.86:1** (<3:1) — *"not dismissable"* | phải có nhãn chữ nhìn thấy. Hiện đã có (chữ "Medium"). |
| status **text** (`375623,9C0006,7F6000,5B3E96`) | ⚠️ CVD **ΔE 8.4** (`7F6000↔9C0006`) — dải sàn 8–12 | *"legal ONLY with secondary encoding"* → **stacked bar bắt buộc có nhãn số trên từng khúc + khe hở 2px.** |
| status **chip bg** (`E2EFDA,FCE4E4,FFF2CC,EAE3F7`) | CVD **ΔE 4.3** (`PASS↔FAIL`) | **Không sao hiện tại** (chip luôn có chữ PASS/FAIL). **Thành lỗi ngay khi** dùng màu-không-chữ. |

> **Luật rút ra:** mọi con số/khúc có màu **bắt buộc** đi kèm icon + chữ. Không bao giờ mã hoá bằng
> màu đơn độc. (Đây cũng đúng luật `dataviz`: *status ships with an icon + label, never color alone*.)

`theme.json` được thêm khoá mới cho Report (`status_lifecycle`, `report` layout). **Không sửa khoá cũ**
→ 4 file `tcs.json` cũ build lại phải ra y hệt (§9).

## 8. Script — `build_bug_report.py` (mới, KHÔNG nhét vào `build_evidence.py`)

`build_evidence.py` (257 dòng) sinh format evidence 3-sheet cho **mọi** `tcs.json`. Nhét Report bug
vào đó ⇒ mỗi `TestCase-XX.xlsx` cũng mọc ra sheet Report bug → sai.

⇒ File mới `.claude/skills-scripts/testcase-evidence/build_bug_report.py`:
- Input: `wtf-is-this/bug-he-thong.tcs.json` (+ `theme.json`)
- Output: `wtf-is-this/bug-he-thong.xlsx` (3 sheet)
- Sheet `Chi tiết` **tái dùng hàm dựng của `build_evidence.py`** (import, không copy-paste)
- Chỉ đọc **1 file JSON** — không quét `TestCase-XX/` (xem §10)

Đây là **script hạ tầng thường trú** (cùng loại `build_evidence.py`), không phải `.py` phụ trợ
throwaway — không vi phạm luật token trong `CLAUDE.md`.

## 9. Verify — điều kiện nghiệm thu

1. `build_bug_report.py` chạy sạch trên `bug-he-thong.tcs.json` (11 bug) → xlsx 3 sheet.
2. **Con số khớp đếm tay:** Tổng 11 · FAIL 9 · SPEC-GAP 2 · High/Mid/Low khớp `pri`.
   **Không ô nào là hằng số** — mở xlsx bằng openpyxl (`data_only=False`) kiểm mọi ô số ở `Report`
   phải bắt đầu bằng `=`.
3. **Regression `theme.json`:** build lại 4 `tcs.json` cũ (17/34/25/44 case) bằng `build_evidence.py`
   → output phải **y hệt bản cũ**: mọi ô số/nhãn không đổi, ảnh nhúng khớp (34↔34, 7↔7).
   Thêm khoá mới vào `theme.json` **không được** làm đổi bất kỳ output cũ nào.
4. **Test đụng ID:** thêm 1 bug giả `source: TestCase-11`, `id: TC-09` → sổ phải ra `BUG-012`
   (không đụng `BUG-001`/`TC-09` cũ), `tc_ref` phân biệt được 2 con.
5. **Test ngưỡng chart:** dữ liệu 1 kỳ → **không có** line chart; nhồi 4 kỳ giả → line xuất hiện.
6. Mở file thật bằng mắt: không vỡ layout, không nhãn bị cắt, ảnh không dính spinner.

## 10. Cố tình CẮT (YAGNI — ghi lại để khỏi bàn lại)

| Cắt | Vì sao | Khi nào làm |
|---|---|---|
| **Thống kê theo màn hình** (như mẫu sếp) | Nhu cầu thật của user là *"TestCase-12 có bao nhiêu bug"* = theo **spec** → `COUNTIF(source)` là xong. Gom theo màn đòi `screen` phải là **từ vựng chuẩn** (hiện là chữ tự do: `"Pro — Hóa đơn (Regression Hủy/Xóa)"`) ⇒ phải dựng danh mục màn trong `GLOSSARY.md` + sửa lại `screen` của 11 bug cũ. Công lớn, chưa ai cần. | Khi sếp thật sự hỏi "màn nào yếu nhất" |
| **`Pass rate` theo spec** | Sổ bug không biết spec 12 chạy 54 case → phải đọc thêm `TestCase-XX/tcs.json`, biến script từ "đọc 1 file" thành "quét cả thư mục". | Khi cần báo cáo độ phủ |
| **Data-validation dropdown** | Vi phạm §2.2 (mời sửa bản in) | Không bao giờ |
| **Slicer / Sparkline** | `openpyxl 3.1.5` **không hỗ trợ** (đo trực tiếp). AutoFilter thay được slicer. | Nếu đổi sang xlsxwriter — không đáng |
| **Lịch sử tái phát** (event log thay vì 1 `retested_at`) | Bug đóng rồi mở lại sẽ ghi đè `retested_at` → mất lịch sử. Chưa có ca nào. | Khi có con `🔁 Tái phát` đầu tiên |

## 11. Quy trình vận hành — vòng đời 1 con bug

Hiện việc append là **gõ JSON bằng tay** (`CLAUDE.md`: *"thêm case vào mảng `tcs`"*). 5 con còn được;
30 con thì cấp trùng `bug_id` là chuyện sớm muộn. ⇒ phải có lệnh.

```
① /testcase-run TestCase-13
     → TestCase-13/tcs.json: 40 PASS / 6 FAIL / 2 SPEC-GAP
     → ĐÓNG BĂNG. Không đụng lại bao giờ.

② [CỔNG NGƯỜI] ông + dev soi 8 con FAIL/GAP:
     · "spec 13 viết sai, không phải bug"      → bỏ, không vào sổ
     · "bug hệ thống, ngoài scope spec 13"     → vào sổ
   ⚠️ KHÔNG tự động hoá được: máy không biết "ngoài scope" — đó là phán đoán
      nghiệp vụ + phải hỏi dev. Đây là cổng người DUY NHẤT của quy trình.

③ /testcase-bugbook TestCase-13          ← LỆNH MỚI
     → liệt kê FAIL/SPEC-GAP của TestCase-13 CHƯA có trong sổ (so bằng id+source)
     → ông tick chọn (vd 5 con)
     → script append vào bug-he-thong.tcs.json, tự điền:
         bug_id: BUG-012..BUG-016   (cấp tiếp từ max hiện có, không tái dùng)
         found_at: hôm nay · status: 🔴 Mở · source: TestCase-13
         bug_type: Function (mặc định)
         (copy nguyên pre/steps/expect/actual/before/after từ tcs.json)
     → build lại bug-he-thong.xlsx

   → ĐỒNG THỜI sinh TestCase-13/tcs-update.json = bản sống của spec 13:
       đủ 48 case (KHÔNG xoá con nào), 5 con vừa vào sổ được gắn
       out_of_scope: true + bug_id: BUG-012..016

④ Dev fix BUG-013 → báo ông
     → ông sửa 1 dòng JSON:  status: 🟡 Chờ retest
       (+ fix_note nếu dev có nói fix thế nào)

⑤ RETEST — hai mức, tuỳ ông đang cần trả lời câu nào:

   ⑤a /testcase-retest bug-he-thong      ← dev vừa fix vài con
        → chạy lại CHỈ mấy con status = 🟡 Chờ retest (không chạy cả sổ)

   ⑤b /testcase-retest TestCase-13       ← muốn báo cáo "spec 13 giờ sạch chưa"
        → chạy lại CẢ 48 case → ghi đè tcs-update.json (lần chạy #2)

   Cả hai: MÁY chốt, người không gõ:
        quan sát PASS  → result: PASS · status: ✅ Đã đóng · retested_at: hôm nay
        vẫn FAIL       → status: 🔴 Mở  (dev fix hụt) + ảnh mới đè ảnh cũ
   → build lại xlsx (bug-he-thong.xlsx, + TestCase-13-update.xlsx nếu là ⑤b)
```

**Một lần chạy = một quan sát = cập nhật cả hai nơi.** ⑤b chạy lại spec 13 thì vừa sinh
`tcs-update.json` (báo cáo cho **BA/sếp**: spec 13 pass chưa) vừa lật `status` mấy con bug
`source=TestCase-13` trong sổ (theo dõi cho **dev**). Cùng một quan sát đẻ ra 2 output
⇒ **không bao giờ có 2 số cãi nhau.**

**Vì sao chỉ chạy lại mấy con 🟡, không chạy cả sổ:** precondition mục rữa. `STATE.md` §5 ghi data
test bị dọn định kỳ (`AIOTTEST-KH3` đã biến mất); `TestCase_NEW` đang có 6 case `未実施` đúng vì lý do
đó. Chạy cả sổ ⇒ một đống `未実施` giả → sổ nhiễu, sếp đọc không ra.

**Bước ③ và ⑤ nằm ngoài phạm vi spec này** (spec này chỉ lo *file* + *schema*). Ghi ở đây để plan
biết đường và để không ai tưởng quy trình tự chạy. → tách spec riêng sau khi file chạy được.

## 12. Migration — dữ liệu đang có

| Việc | Chi tiết |
|---|---|
| Cấp `bug_id` | 11 bug trong sổ → `BUG-001`..`BUG-011`, theo đúng thứ tự đang nằm trong mảng `tcs` |
| Điền `found_at` | = `2026-07-14` (ngày `bug-he-thong.tcs.json` được tạo) cho cả 11 |
| Điền `status` | = `🔴 Mở` cho cả 11 (dev chưa fix con nào) |
| Điền `bug_type` | = `Function` cho cả 11 (đọc qua 11 title: không con nào là UI/Text) |
| **Dựng lại `TestCase-12/tcs-update.json`** | **43 → 54 case**: nhét lại 11 con đã bị gỡ, gắn `out_of_scope: true` + `bug_id`, giữ nguyên `result` FAIL/SPEC-GAP (dev chưa fix ⇒ chạy lại cũng vẫn FAIL, **không được** giả vờ PASS) |
| In lại xlsx | `bug-he-thong.xlsx` + `TestCase-12-update.xlsx` |

⚠️ **Cảnh báo hệ quả nhìn thấy được:** sau migration, `TestCase-12-update.xlsx` **không còn nói
"43/43 PASS — 100%"** nữa. Nó sẽ nói:
```
TRONG SCOPE   43/43 PASS  (100%)
NGOÀI SCOPE   11 phát hiện → BUG-001..BUG-011 (9 FAIL · 2 SPEC-GAP)
```
Con số 100% **vẫn còn** và vẫn đúng — nhưng file thôi im lặng về 11 con kia.
**Nếu file cũ đã gửi cho ai rồi thì phải báo họ bản mới**, vì nó nhìn khác hẳn.
Đây là chủ đích, không phải tác dụng phụ.

## 13. Việc tiếp

Sang `writing-plans` → kế hoạch triển khai.

**Không đụng tới:** `SKILL.md` qa-brain · bức tường thép (OQ-09 vẫn là việc lớn nhất còn lại,
độc lập với spec này) · `TestCase-XX/tcs.json` cũ.
