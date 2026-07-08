# Skill 3 — Cập nhật Specs Change / Bug

Ghi các **change request / bug mới** (phát sinh sau review) vào mục "Cập nhật Specs" trong
`<folder>/specs.md`, và (tuỳ chọn) thêm test case tương ứng vào `<folder>/tcs.json` rồi build lại.
KHÔNG chạy test — chỉ cập nhật tài liệu + khung case. Dùng `/testcase-retest` để chạy sau.

## Cách dùng
```
/testcase-upspecschange <folder>
<liệt kê change/bug, mỗi dòng 1 mục>
```
Ví dụ:
```
/testcase-upspecschange 7.Test/TestCase_No.10.5
- Change: đổi text quyền「会計後の修正・削除を許可」→「会計完了後の修正・削除」
- Bug: dời quyền mới về cuối danh sách
- Bug: chỉnh UI/UX nút キャンセル
```

## TIẾT KIỆM TOKEN — đọc trước
Chỉ **sửa text `specs.md` + `tcs.json`** rồi chạy `build_evidence.py`. KHÔNG chạy Playwright,
KHÔNG viết lại generator, KHÔNG dán ảnh. Đọc file `.md` (rẻ), tránh OCR ảnh spec.

## Quy trình
1. **Đọc `<folder>/specs.md`**. Nếu chưa có mục `## 4. Cập nhật Specs (Change requests & Bugs)`
   thì tạo mới ở cuối file (dạng **bảng changelog**). Cập nhật dòng "Cập nhật lần cuối" ở đầu file.
2. **Thêm từng mục là 1 DÒNG trong bảng** (cột: `ID | Ngày | Loại | Nội dung | Ảnh hưởng | Trạng thái`):
   - **Ngày = hôm nay** (bắt buộc — sẽ có nhiều đợt change nên phải truy vết theo ngày).
   - ID tự tăng: Change → `CHANGE-01,02,…` (🔧); Bug → `BUG-01,02,…` (🐞). Lấy số lớn nhất hiện có +1.
   - Trạng thái mới = `🔴`.
   - Ghi thêm dòng "Ghi chú liên quan" nếu biết mục này sẽ retest TC nào.
3. **(Tuỳ chọn) Thêm test case vào `<folder>/tcs.json`** cho mỗi change/bug cần verify:
   - Kế thừa archetype phù hợp từ `.claude/skills-scripts/testcase-evidence/example.tcs.json`.
   - `result="未実施"`, `before/after=null`, `note` trỏ tới ID (vd `CHANGE-01`).
   - ID test case tăng tiếp theo dãy TC hiện có.
4. **Build lại Excel** (nếu có sửa tcs.json):
   ```
   python3 .claude/skills-scripts/testcase-evidence/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
5. **Đánh giá lại KPI số case** (cùng phương pháp Skill 1): change/bug mới có thể mở rộng
   phạm vi → tính lại Min/Max; **KPI mục tiêu ≈ 80% Max** (nhỉnh hơn trung bình).
   Mỗi CHANGE/BUG cần verify ≥ 1 case; nếu tổng case < KPI mới thì bổ sung
   (ưu tiên validation/negative của phần thay đổi).
6. **Báo cáo**: liệt kê các ID vừa thêm (CHANGE/BUG) + test case mới (nếu có) + KPI mới (Min/Max/mục tiêu/thực tế).

## Lưu ý
- `specs.md` là **nguồn spec chuẩn** — luôn cập nhật ở đây, không sửa vào ảnh cũ.
- Trạng thái mục: `🔴 chưa xử lý` → `🟡 đang fix` → `✅ đã verify` (cập nhật khi retest xong).
- Không tự đổi các mục cũ trừ khi user yêu cầu.
