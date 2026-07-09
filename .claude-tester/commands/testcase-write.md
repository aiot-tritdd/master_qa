# Skill 1 — Viết Test Case từ Spec (kế thừa template chính)

> **Nguyên tắc: Knowledge-first / source-on-demand** — luôn đọc knowledge (`.claude-tester/knowledge/`)
> trước để nắm bối cảnh, KHÔNG grep lại toàn bộ codebase; chỉ đọc thẳng source code/spec gốc khi
> knowledge không đủ chi tiết hoặc nghi ngờ đã lỗi thời.

Sinh file Test Case Evidence (.xlsx) từ spec user để trong 1 folder. Chưa chạy test —
chỉ THIẾT KẾ test case (result = `未実施`, evidence để trống). Skill 2 (`/testcase-run`)
sẽ chạy và điền evidence.

Bộ template chính ở `.claude-tester/scripts/`:
- `example.tcs.json` — khung 5 archetype (nội dung)
- `theme.json` — format/màu/layout (style)
- `build_evidence.py` — đọc 2 file trên → xuất .xlsx đẹp, đồng nhất

## Cách dùng
```
/testcase-write <folder>
```
Ví dụ: `/testcase-write 7.Tests/TestCase_No.10.5`

## Tri thức nền (đọc để thiết kế đủ góc — không grep lại code)
**Common trước (luôn đọc)**:
- `.claude-tester/knowledge/PROJECT_MAP.md` — task ảnh hưởng app/hệ nào (Pro/Admin/Hệ thống Vé...) →
  biết cần test qua mấy hệ.
- `.claude-tester/knowledge/DOMAIN.md` — nghiệp vụ (締め, 回数券, quyền) → biết **vì sao** là bug.
- `.claude-tester/knowledge/FEATURES.md` — tính năng liên quan đã có luồng/bẫy gì, tránh thiết kế case
  trùng hoặc bỏ sót bẫy đã biết.

**Common có điều kiện (đọc nếu task liên quan)**:
- `.claude-tester/knowledge/SYNC_MAP.md` — nếu task đụng tới vé/coupon/số dư đồng bộ Hệ thống Lõi ↔
  Hệ thống Vé (bắt buộc đọc trước khi viết case liên quan, tránh coi số dư 1 phía là chuẩn).
- `.claude-tester/knowledge/REPORTING.md` — nếu task liên quan báo cáo/export/tính tiền-thuế-coupon
  (No.11 và tương tự) — chú ý phần đã đánh dấu "chưa có code" trong file đó.

**Chuyên dụng tester (sau khi đã nắm common)**:
- `.claude-tester/knowledge/METHOD.md` — archetype + luật vàng (toàn vẹn dữ liệu sau hủy/xóa, permission matrix…).

## TIẾT KIỆM TOKEN — đọc trước
**KHÔNG viết lại generator, KHÔNG dựng lại cấu trúc test case từ số 0.** Chỉ:
(1) đọc spec, (2) `cp example.tcs.json → tcs.json` rồi chỉnh theo spec, (3) chạy build.
Không in nội dung script/không dán ảnh vào chat.

## Quy trình
1. **Tìm spec** — ưu tiên theo thứ tự (tên `<TênTask>` = tên `<folder>` bỏ phần `7.Tests/`, khớp với
   tên dùng ở `/task-spec-create`):
   1. **`8.Tasks/specs/<TênTask>/specs.md`** — nguồn chuẩn do `/task-spec-create` tạo, **tự động
      đọc từ đây trước tiên**, KHÔNG copy sang `<folder>` (đọc thẳng, tránh lệch bản khi spec update sau).
      Nếu tên `<folder>` không khớp chính xác tên trong `8.Tasks/specs/`, thử tìm theo số task
      (vd `No.10.6`) trước khi báo không tìm thấy.
   2. Nếu không có ở trên (task cũ, tạo trước khi có `.claude-task/`) → fallback `<folder>/specs.md`
      (hoặc `*.md` khác) như trước.
   3. Chỉ khi KHÔNG có `.md` nào mới fallback sang `specs*.png` / `.pdf` / `.xlsx` (OCR, tốn token hơn).
   - Bỏ qua file output: `.xlsx`, `tcs.json`, thư mục `shots/`.
   - Nếu chỉ có ảnh/pdf: gợi ý user chạy `/task-spec-create` để có `specs.md` chuẩn cho lần sau.
2. **KẾ THỪA khung template chính** (tiết kiệm thời gian — KHÔNG viết từ đầu):
   ```
   cp .claude-tester/scripts/example.tcs.json <folder>/tcs.json
   ```
   Khung có sẵn 5 archetype: (1) Happy path, (2) Biến thể điều kiện/quyền,
   (3) Boundary, (4) Regression, (5) Backend/API·toàn vẹn dữ liệu.
3. **Chỉnh khung theo spec** (tiếng Việt; giữ tên màn hình/hàm JP/EN):
   - Đổi `meta` (module = tên folder/task; env lấy từ `7.Tests/account.txt` URL Pro dev).
   - Với mỗi archetype: đổi `screen/title/pre/steps/expect` theo màn hình & thay đổi thật.
   - Mỗi màn hình trong spec ≥ 1 case; thêm/bớt case (copy 1 archetype phù hợp).
   - **Xoá mọi khoá bắt đầu bằng `_`** (`_huong_dan`, `_archetype`) khi hoàn thiện.
   - Giữ `result`=`"未実施"`, `actual`=`"未実施"`, `before`/`after`=`null` (Skill 2 sẽ điền).
   Schema mỗi tc: `id, screen, pri(High|Medium|Low), result, title, pre, steps, expect, actual, note, before, after`.
4. **Sinh Excel vào folder**:
   ```
   python3 .claude-tester/scripts/build_evidence.py \
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
- [ ] Đã đọc đúng knowledge theo routing (`.claude-knowledge/README.md` mục "Routing table") chưa?
- [ ] Có đọc source code không? Nếu có, vì sao?
- [ ] Có điểm nào knowledge thiếu/lỗi thời cần cập nhật lại không?
- [ ] Nếu task liên quan vé/coupon/report, đã cân nhắc `SYNC_MAP.md`/`REPORTING.md` đúng điều kiện chưa?

## Lưu ý
- File `.xlsx` và `tcs.json` **luôn để trong `<folder>`** cùng spec. Skill 2 đọc lại `tcs.json`.
- Format tự động theo `theme.json` (navy header, badge Priority, status, note vàng) — đồng nhất mọi lần build.
- Đổi màu/layout/nhãn file xuất = sửa `theme.json`. Đổi khung 5 case = sửa `example.tcs.json`.
  Cả hai KHÔNG cần đụng code/tcs cũ.
