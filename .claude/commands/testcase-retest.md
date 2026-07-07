# Skill 4 — Retest (chạy lại case bị ảnh hưởng)

Chạy lại **chỉ các test case bị ảnh hưởng** bởi change/bug (sau khi dev fix), chụp evidence mới,
cập nhật `result` + `actual` + ảnh, đổi trạng thái mục trong `specs.md`, rồi build lại Excel.
Tránh chạy lại toàn bộ suite (đỡ token + đỡ phá dữ liệu dev).

## Cách dùng
```
/testcase-retest <folder> [<TC-id|CHANGE/BUG-id ...>]
```
Ví dụ:
```
/testcase-retest 7.Test/TestCase_No.10.5 TC-01 TC-06        # retest theo TC id
/testcase-retest 7.Test/TestCase_No.10.5 CHANGE-01 BUG-02   # retest theo change/bug
/testcase-retest 7.Test/TestCase_No.10.5                    # retest mọi mục còn 🔴/🟡 trong specs.md
```

## TIẾT KIỆM TOKEN — đọc trước
Dùng lại helper `.claude/skills-scripts/testcase-evidence/pw_lib.js`/`pw_api.js`/`build_evidence.py`.
**KHÔNG viết lại** flow đăng nhập/generator. **Chỉ chạy các case được chỉ định** — không chạy cả suite.
Không in script, không dán base64/ảnh.

## Quy trình
1. **Xác định phạm vi retest**:
   - Có tham số → đúng các TC-id đó, hoặc map CHANGE/BUG-id → TC liên quan (theo `note` trong tcs.json).
   - Không tham số → mọi mục còn `🔴 chưa xử lý` / `🟡 đang fix` trong `<folder>/specs.md`
     và các TC liên quan.
   Đối chiếu hành vi mong đợi bằng **`<folder>/specs.md`** (không dùng ảnh).
2. **Đăng nhập/chạy live** chỉ các case đó (như Skill 2). **Setup 1 lần**:
   `cd .claude/skills-scripts/testcase-evidence && npm i` (playwright local → không cần NODE_PATH).
   Account từ `7.Test/account.txt` (Pro dev mặc định đúng trong `pw_lib.js`).
   Ảnh mới lưu `<folder>/shots/` (**PNG rõ**, không nén JPG). Thao tác phá huỷ → tạo dữ liệu test mới
   (prefix `AIOT-TEST-*`/`AIOTTEST*`), tránh đụng dữ liệu người khác.
3. **Cập nhật `<folder>/tcs.json`** cho các case retest: `result`(PASS|FAIL|未実施),
   `actual` (mô tả mới, bắt đầu bằng PASS/FAIL/未実施), `before`/`after` (ảnh mới).
   Không đụng các case ngoài phạm vi.
4. **Cập nhật trạng thái mục trong `specs.md`**:
   `✅ đã verify` nếu retest PASS · giữ `🔴/🟡` + ghi chú nếu vẫn FAIL.
5. **Build lại Excel**:
   ```
   python3 .claude/skills-scripts/testcase-evidence/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
6. **Báo cáo diff**: mỗi case retest ghi `trước → sau` (vd `未実施 → PASS`, `FAIL → PASS`),
   nêu bug đã hết hay còn.
7. **Dọn dữ liệu test**: chạy `/testcase-cleanup` sau khi retest.

## Lưu ý
- Chỉ chạm các case trong phạm vi — giữ nguyên kết quả/evidence các case khác.
- Nếu 1 change/bug chưa có TC → gợi ý chạy `/testcase-upspecschange` để thêm TC trước khi retest.
