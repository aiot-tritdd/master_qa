# Skill 4 — Retest (chạy lại case bị ảnh hưởng)

> **Nguyên tắc: Knowledge-first / source-on-demand** — luôn đọc knowledge (`.claude-tester/knowledge/`)
> trước để nắm bối cảnh, KHÔNG grep lại toàn bộ codebase; chỉ đọc thẳng source code/spec gốc khi
> knowledge không đủ chi tiết hoặc nghi ngờ đã lỗi thời.

Chạy lại **chỉ các test case bị ảnh hưởng** bởi change/bug (sau khi dev fix), chụp evidence mới,
cập nhật `result` + `actual` + ảnh, đổi trạng thái mục trong `specs.md`, rồi build lại Excel.
Tránh chạy lại toàn bộ suite (đỡ token + đỡ phá dữ liệu dev).

## Cách dùng
```
/testcase-retest <folder> [<TC-id|CHANGE/BUG-id ...>]
```
Ví dụ:
```
/testcase-retest 7.Tests/TestCase_No.10.5 TC-01 TC-06        # retest theo TC id
/testcase-retest 7.Tests/TestCase_No.10.5 CHANGE-01 BUG-02   # retest theo change/bug
/testcase-retest 7.Tests/TestCase_No.10.5                    # retest mọi mục còn 🔴/🟡 trong specs.md
```

## TIẾT KIỆM TOKEN — đọc trước
Dùng lại helper `.claude-tester/scripts/pw_lib.js`/`pw_api.js`/`build_evidence.py`.
**KHÔNG viết lại** flow đăng nhập/generator. **Chỉ chạy các case được chỉ định** — không chạy cả suite.
Không in script, không dán base64/ảnh.
Tri thức nền: đọc `.claude-tester/knowledge/SYSTEM.md` + `PLAYBOOK.md` + `LESSONS.md` trước khi chạy.
Điều kiện: case liên quan vé/coupon → thêm `SYNC_MAP.md`; liên quan báo cáo → thêm `REPORTING.md`.
Sau retest: **Capture Lessons** — bẫy mới → `LESSONS.md`; thay đổi hệ → `SYSTEM.md` (có ngày).

## Quy trình
1. **Xác định phạm vi retest**:
   - Có tham số → đúng các TC-id đó, hoặc map CHANGE/BUG-id → TC liên quan (theo `note` trong tcs.json).
   - Không tham số → mọi mục còn `🔴 chưa xử lý` / `🟡 đang fix` trong `specs.md` (`8.Tasks/specs/<TênTask>/specs.md`, fallback `<folder>/specs.md`)
     và các TC liên quan.
   Đối chiếu hành vi mong đợi bằng **`specs.md` (`8.Tasks/specs/<TênTask>/specs.md`, fallback `<folder>/specs.md`)** (không dùng ảnh).
2. **Đăng nhập/chạy live** chỉ các case đó (như Skill 2). **Setup 1 lần**:
   `cd .claude-tester/scripts && npm i` (playwright local → không cần NODE_PATH).
   Account từ `7.Tests/account.txt` (Pro dev mặc định đúng trong `pw_lib.js`).
   Ảnh mới lưu `<folder>/shots/` (nén ~1080px JPG q90). **Chụp bằng `shot(page, path, readySelector)`
   của `pw_lib.js`** (chờ màn hình load xong mới chụp) — không dùng sleep + screenshot trần.
   Thao tác phá huỷ → tạo dữ liệu test mới
   (prefix `AIOT-TEST-*`/`AIOTTEST*`), tránh đụng dữ liệu người khác.
3. **Cập nhật `<folder>/tcs.json`** cho các case retest: `result`(PASS|FAIL|未実施),
   `actual` (mô tả mới, bắt đầu bằng PASS/FAIL/未実施), `before`/`after` (ảnh mới).
   Không đụng các case ngoài phạm vi.
4. **Cập nhật trạng thái mục trong `specs.md`**:
   `✅ đã verify` nếu retest PASS · giữ `🔴/🟡` + ghi chú nếu vẫn FAIL.
5. **Build lại Excel**:
   ```
   python3 .claude-tester/scripts/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
6. **Báo cáo diff**: mỗi case retest ghi `trước → sau` (vd `未実施 → PASS`, `FAIL → PASS`),
   nêu bug đã hết hay còn. Liệt kê dữ liệu test còn tồn trên dev để user dọn sau.

## KHÔNG auto-cleanup
- Skill này **KHÔNG tự dọn dữ liệu test** sau khi retest.
- Cleanup chạy tay khi cần: user tự gõ `/testcase-cleanup <folder>`.

## Before final (checklist bắt buộc trước khi báo cáo xong)
- [ ] Đã đọc đúng knowledge theo routing (`.claude-knowledge/README.md` mục "Routing table") chưa?
- [ ] Có đọc source code không? Nếu có, vì sao?
- [ ] Có điểm nào knowledge thiếu/lỗi thời cần cập nhật lại không?
- [ ] Nếu case liên quan vé/coupon/report, đã đối chiếu `SYNC_MAP.md`/`REPORTING.md` chưa?

## Lưu ý
- Chỉ chạm các case trong phạm vi — giữ nguyên kết quả/evidence các case khác.
- Nếu 1 change/bug chưa có TC → gợi ý chạy `/testcase-upspecschange` để thêm TC trước khi retest.
