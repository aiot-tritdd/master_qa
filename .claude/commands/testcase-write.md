# Skill 1 — Viết Test Case từ Spec (kế thừa template chính)

Sinh file Test Case Evidence (.xlsx) từ spec user để trong 1 folder. Chưa chạy test —
chỉ THIẾT KẾ test case (result = `未実施`, evidence để trống). Skill 2 (`/testcase-run`)
sẽ chạy và điền evidence.

Bộ template chính ở `.claude/skills-scripts/testcase-evidence/`:
- `example.tcs.json` — khung 5 archetype (nội dung)
- `theme.json` — format/màu/layout (style)
- `build_evidence.py` — đọc 2 file trên → xuất .xlsx đẹp, đồng nhất

## Cách dùng
```
/testcase-write <folder>
```
Ví dụ: `/testcase-write wtf-is-this/TestCase_No.10.5`

## TIẾT KIỆM TOKEN — đọc trước
**KHÔNG viết lại generator, KHÔNG dựng lại cấu trúc test case từ số 0.** Chỉ:
(1) đọc spec, (2) `cp example.tcs.json → tcs.json` rồi chỉnh theo spec, (3) chạy build.
Không in nội dung script/không dán ảnh vào chat.

## Quy trình
1. **Tìm spec trong folder** (ưu tiên tiết kiệm token + chính xác):
   - **Ưu tiên `specs.md`** (hoặc `*.md`) — đọc text thẳng, rẻ, không OCR.
   - Chỉ khi KHÔNG có `.md` mới fallback sang `specs*.png` / `.pdf` / `.xlsx` (phải OCR ảnh, tốn token hơn).
   - Bỏ qua file output: `.xlsx`, `tcs.json`, thư mục `shots/`.
   - Nếu chỉ có ảnh/pdf: nên gợi ý user export spec sang `specs.md` để lần sau nhanh hơn.
2. **KẾ THỪA khung template chính** (tiết kiệm thời gian — KHÔNG viết từ đầu):
   ```
   cp .claude/skills-scripts/testcase-evidence/example.tcs.json <folder>/tcs.json
   ```
   Khung có sẵn 5 archetype: (1) Happy path, (2) Biến thể điều kiện/quyền,
   (3) Boundary, (4) Regression, (5) Backend/API·toàn vẹn dữ liệu.
3. **Chỉnh khung theo spec** (tiếng Việt; giữ tên màn hình/hàm JP/EN):
   - Đổi `meta` (module = tên folder/task; env lấy từ `wtf-is-this/account.txt` URL Pro dev).
   - Với mỗi archetype: đổi `screen/title/pre/steps/expect` theo màn hình & thay đổi thật.
   - Mỗi màn hình trong spec ≥ 1 case; thêm/bớt case (copy 1 archetype phù hợp).
   - **Xoá mọi khoá bắt đầu bằng `_`** (`_huong_dan`, `_archetype`, `_tuong_thep_*`) khi hoàn thiện.
   - Giữ `result`=`"未実施"`, `actual`=`"未実施"`, `before`/`after`=`null` (Skill 2 sẽ điền).
   Schema mỗi tc: `id, screen, pri(High|Medium|Low), result, title, pre, steps, expect, actual, note, source, before, after`.
   `result` hợp lệ: **`PASS` | `FAIL` | `未実施` | `SPEC-GAP`** (định nghĩa trong `theme.json`).

   ⚠️ **Oracle = SPEC.** `expect` CHỈ suy từ spec — lúc viết `expect` thì **mù code**.
   `knowledge/METHOD.md` quyết định **case nào phải tồn tại** (coverage), **không bao giờ** quyết định
   `expect`. Spec im lặng ở chỗ METHOD bảo phải kiểm → **KHÔNG bịa `expect`** → khi chạy sẽ ra `SPEC-GAP`
   (finding giá trị cao: bằng chứng spec chưa nghĩ tới), chứ không phải bịa ra một kỳ vọng rồi chấm FAIL.
4. **Sinh Excel vào folder**:
   ```
   python3 .claude/skills-scripts/testcase-evidence/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
   (không cần shots_dir vì chưa có ảnh)
5. **Tự đánh giá KPI số case** (bắt buộc, báo trong kết quả):
   - **Min** = số luồng chính (đối tượng × chiều + luồng đặc thù) — mỗi luồng ≥ 1 happy path.
   - **Max** = Min + validation/boundary + negative (retry/conflict) + biến thể theo app/màn hình,
     dừng trước khi case bắt đầu trùng cơ chế (không vét cạn ma trận).
   - **KPI mục tiêu = nhỉnh hơn trung bình, ~80% Max** (vd Max 10 → KPI 8; Min 14/Max 25 → KPI ~20).
   - Số case thiết kế phải **≥ KPI**; nếu dưới thì bổ sung nhóm validation/negative trước
     (đây là nhóm hay thiếu nhất), không đẻ thêm case trùng happy path để đủ số.
6. **Báo cáo**: liệt kê số case theo màn hình + **KPI (Min/Max/mục tiêu/thực tế)** + đường dẫn file .xlsx trong folder.

## Before final (checklist bắt buộc trước khi báo cáo xong)
- [ ] Có đọc source code không? **Ở bước viết `expect` đáp án đúng luôn là KHÔNG.** Lỡ đọc → khai ra.
- [ ] Có đọc `knowledge/system/**` hoặc dùng GitNexus không? (cả hai đều **CẤM**)
- [ ] Mọi `expect` đều truy được về 1 câu trong SPEC? Có chỗ nào tự bịa kỳ vọng không?
- [ ] Case nào `METHOD.md` bảo phải có mà spec im lặng → đã đánh dấu để chạy ra `SPEC-GAP` chưa?
- [ ] Flow dựng precondition có nằm trong `knowledge/` (approved) không? Nếu chưa → dừng,
      chạy `/testcase-systemdoc <flow>` (build-time), **KHÔNG** tự đọc code để bù.
- [ ] Có chạm `knowledge/OPEN-QUESTIONS.md` không? (case đụng OQ nào → ghi vào `note`)

## Lưu ý
- File `.xlsx` và `tcs.json` **luôn để trong `<folder>`** cùng spec. Skill 2 đọc lại `tcs.json`.
- Format tự động theo `theme.json` (navy header, badge Priority, status, note vàng) — đồng nhất mọi lần build.
- Đổi màu/layout/nhãn file xuất = sửa `theme.json`. Đổi khung 5 case = sửa `example.tcs.json`.
  Cả hai KHÔNG cần đụng code/tcs cũ.
