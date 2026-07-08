# Skill 2 — Chạy Test Case & nhập Evidence

Chạy test thật trên Threease dev (Playwright + API), chụp screenshot, rồi cập nhật
`result` + `actual` + ảnh Before/After vào file test case đã tạo bởi Skill 1.

## Cách dùng
```
/testcase-run <folder>
```
Ví dụ: `/testcase-run 7.Test/TestCase_No.10.5`

## TIẾT KIỆM TOKEN — đọc trước
Dùng lại helper ở `.claude/skills-scripts/testcase-evidence/`:
`pw_lib.js` (đăng nhập/session), `pw_api.js` (gọi API), `build_evidence.py` (sinh Excel).
**KHÔNG viết lại** flow đăng nhập/generator. Đọc `<folder>/tcs.json` để biết case cần chạy.
Không in script, không dán base64/ảnh vào chat.

## Quy trình
1. **Đọc** `<folder>/tcs.json` (do Skill 1 tạo). Nếu thiếu → chạy `/testcase-write` trước.
   Khi cần đối chiếu hành vi mong đợi, đọc **`<folder>/specs.md`** (KHÔNG dùng ảnh spec —
   ưu tiên md cho rẻ + chính xác).
2. **Account đăng nhập**: lấy từ `7.Test/account.txt`. Mặc định Pro dev đã đúng sẵn trong
   `pw_lib.js` (BASE=develop.pro.threease.com, basic `threesides/threesides`,
   login `TESTSEED001/STAFF001/password123`). Đổi hệ khác thì set env
   `BASE_URL, BASIC_USER/PASS, INST/THER/PW, API_BASE`.
3. **Chạy test từng case**, chụp **PNG RÕ** vào `<folder>/shots/` — **KHÔNG nén JPG**, KHÔNG resize nhỏ.
   Chuẩn evidence = như folder mẫu `TestCase_No.10.1~3/shots/` (PNG ~150KB, tên `TC-XX_before/after/confirm.png`).
   Helper ở project (require bằng đường dẫn tuyệt đối tới project):
   ```js
   const P='/Applications/Workspaces/threease/.claude/skills-scripts/testcase-evidence/';
   const { getPage } = require(P+'pw_lib');
   (async () => { const { browser, page, BASE } = await getPage();
     await page.goto(BASE + '/...'); await page.waitForTimeout(6000);
     await page.screenshot({ path: '<folder>/shots/TC-01_after.png' }); await browser.close(); })();
   ```
   Gọi API backend (token tự bắt): `const { withApi } = require(P+'pw_api');`
   **Setup 1 lần**: `cd .claude/skills-scripts/testcase-evidence && npm i` (cài playwright local
   → require chạy thẳng, KHÔNG cần NODE_PATH; Chromium đã cache ở `~/Library/Caches/ms-playwright`).
   Selector login: `input[data-cy=institute_code|therapist_code|password]`, `[data-cy=loginButton]`.
   Dữ liệu test tạo ra PHẢI có prefix `AIOT-TEST-*` (preset) / `AIOTTEST*` (staff) để cleanup quét được.
4. **Ảnh giữ nguyên PNG rõ** (generator tự scale khi nhúng — không cần nén tay).
   **BẮT BUỘC 2 ảnh/case: `before` + `after`** (template sếp có 2 cột Evidence). Chụp rõ vùng quan trọng.
   - Case **thao tác** (create/cancel/pay…): before = TRƯỚC thao tác · after = SAU (kết quả/thông báo).
   - Case **hiển thị/report** (verify cột/label/tab): before = điểm vào / filter / sub-tab bar (context) ·
     after = kết quả quan sát (KPI+bảng, hoặc 404 nếu chưa build).
5. **Cập nhật `<folder>/tcs.json`**: mỗi tc điền `result`(PASS|FAIL|未実施),
   `actual`(mô tả quan sát được, bắt đầu bằng PASS/FAIL/未実施), `before`/`after`(tên file trong shots),
   `note`(kỹ thuật/PR nếu có).
6. **Sinh lại Excel vào folder** (ảnh tự lấy ở `<folder>/shots` — cạnh `tcs.json`):
   ```
   python3 .claude/skills-scripts/testcase-evidence/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
7. **Báo cáo**: bảng PASS/FAIL/未実施, nêu rõ bug tìm được.
8. **Dọn dữ liệu test**: chạy `/testcase-cleanup` (hoặc `node cleanup.js`) để xóa preset/account/đặt lịch
   test đã tạo trên dev.

## Lưu ý
- Thao tác phá huỷ (xoá đặt lịch, huỷ thanh toán) dùng dữ liệu test; tạo mới để test,
  tránh đụng dữ liệu người khác.
- Ảnh bind in-cell (co giãn theo ô). Excel để trong `<folder>`; upload Drive thì user tự kéo lên.
- Đổi màu/layout/nhãn file xuất = sửa `theme.json` (không đụng code/tcs).
