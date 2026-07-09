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
/testcase-retest wtf-is-this/TestCase_No.10.5 TC-01 TC-06        # retest theo TC id
/testcase-retest wtf-is-this/TestCase_No.10.5 CHANGE-01 BUG-02   # retest theo change/bug
/testcase-retest wtf-is-this/TestCase_No.10.5                    # retest mọi mục còn 🔴/🟡 trong specs.md
```

## TIẾT KIỆM TOKEN — đọc trước
Dùng lại helper `.claude/skills-scripts/testcase-evidence/pw_lib.js` (`getPage` + **`shot()`**),
`pw_api.js` (`withApi`, sniff devise-token), `build_evidence.py`.
**KHÔNG viết lại** flow đăng nhập/generator. **Chỉ chạy các case được chỉ định** — không chạy cả suite.
Không in script, không dán base64/ảnh.
Tri thức nền: `knowledge/*.md` (approved) + `knowledge/lessons.md` + `knowledge/OPEN-QUESTIONS.md`.
⛔ **CẤM** `knowledge/system/**`, code, GitNexus (xem `SKILL.md` § danh sách cấm).

## Quy trình
1. **Xác định phạm vi retest**:
   - Có tham số → đúng các TC-id đó, hoặc map CHANGE/BUG-id → TC liên quan (theo `note` trong tcs.json).
   - Không tham số → mọi mục còn `🔴 chưa xử lý` / `🟡 đang fix` trong `<folder>/specs.md`
     và các TC liên quan.
   Đối chiếu hành vi mong đợi bằng **`<folder>/specs.md`** (không dùng ảnh).
2. **Đăng nhập/chạy live** chỉ các case đó (như Skill 2). **Setup 1 lần**:
   `cd .claude/skills-scripts/testcase-evidence && npm i` (playwright local → không cần NODE_PATH).
   Account từ `wtf-is-this/account.txt` (Pro dev mặc định đúng trong `pw_lib.js`).
   Ảnh mới lưu `<folder>/shots/` (**PNG rõ**, không nén JPG) — **chụp bằng `shot(page, path, readySelector)`**,
   KHÔNG `waitForTimeout` + screenshot trần. Thao tác phá huỷ → tạo dữ liệu test mới
   (prefix `AIOT-TEST-*`/`AIOTTEST*`), tránh đụng dữ liệu người khác.
3. **Cập nhật `<folder>/tcs.json`** cho các case retest: `result` (**PASS|FAIL|未実施|SPEC-GAP**),
   `actual` (mô tả mới, bắt đầu bằng đúng từ đó), `before`/`after` (ảnh mới).
   Không đụng các case ngoài phạm vi.
4. **Cập nhật trạng thái mục trong `specs.md`**:
   `✅ đã verify` nếu retest PASS · giữ `🔴/🟡` + ghi chú nếu vẫn FAIL.
5. **Build lại Excel**:
   ```
   python3 .claude/skills-scripts/testcase-evidence/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
6. **Báo cáo diff**: mỗi case retest ghi `trước → sau` (vd `未実施 → PASS`, `FAIL → PASS`),
   nêu bug đã hết hay còn. Liệt kê **dữ liệu test còn tồn** trên dev.
7. **KHÔNG auto-cleanup.** Giữ dữ liệu để đối chiếu evidence / dev debug; user tự gõ `/testcase-cleanup`.

## CAPTURE LESSONS (bắt buộc)
Bẫy **cơ khí** mới (selector/timing/mã HTTP quan sát được) → thêm 1 dòng có ngày vào `knowledge/lessons.md`.
⛔ **Cấm ghi** nguyên nhân / phán quyết "đã-chưa build" (đó là WHAT → đầu độc phiên sau).
Bug **không** vào knowledge — bug thuộc `specs.md` (`BUG-xx`) + Excel.

## Before final (checklist bắt buộc)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG.**
- [ ] `expect` của case retest có bị sửa không? (**không được sửa** — oracle đã frozen từ `/testcase-write`)
- [ ] FAIL nào còn ghi symbol/file:line không? (phải mô tả hành vi thuần)
- [ ] Đã Capture Lessons chưa? Có mục nào lẫn WHAT vào không?

## Lưu ý
- Chỉ chạm các case trong phạm vi — giữ nguyên kết quả/evidence các case khác.
- Nếu 1 change/bug chưa có TC → gợi ý chạy `/testcase-upspecschange` để thêm TC trước khi retest.
