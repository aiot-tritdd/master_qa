# Skill 2 — Chạy Test Case & nhập Evidence

Chạy test thật trên Threease dev (Playwright + API), chụp screenshot, rồi cập nhật
`result` + `actual` + ảnh Before/After vào file test case đã tạo bởi Skill 1.

## Cách dùng
```
/testcase-run <folder>
```
Ví dụ: `/testcase-run wtf-is-this/TestCase_No.10.5`

## TIẾT KIỆM TOKEN — đọc trước
Dùng lại helper ở `.claude/skills-scripts/testcase-evidence/`:
`pw_lib.js` (đăng nhập/session), `pw_api.js` (gọi API), `build_evidence.py` (sinh Excel).
**KHÔNG viết lại** flow đăng nhập/generator. Đọc `<folder>/tcs.json` để biết case cần chạy.
Không in script, không dán base64/ảnh vào chat.

## Quy trình
1. **Đọc** `<folder>/tcs.json` (do Skill 1 tạo). Nếu thiếu → chạy `/testcase-write` trước.
   Khi cần đối chiếu hành vi mong đợi, đọc **`<folder>/specs.md`** (KHÔNG dùng ảnh spec —
   ưu tiên md cho rẻ + chính xác).
2. **Account đăng nhập**: lấy từ `wtf-is-this/account.txt`. Mặc định Pro dev đã đúng sẵn trong
   `pw_lib.js` (BASE=develop.pro.threease.com, basic `threesides/threesides`,
   login `TESTSEED001/STAFF001/password123`). Đổi hệ khác thì set env
   `BASE_URL, BASIC_USER/PASS, INST/THER/PW, API_BASE`.
3. **Chạy test từng case**, chụp **PNG RÕ** vào `<folder>/shots/` — **KHÔNG nén JPG**, KHÔNG resize nhỏ.
   Chuẩn evidence = như folder mẫu `TestCase_No.10.1~3/shots/` (PNG ~150KB, tên `TC-XX_before/after/confirm.png`).
   Helper ở project (require bằng đường dẫn tuyệt đối tới project):
   ```js
   const P='<repo>/.claude/skills-scripts/testcase-evidence/';
   const { getPage, shot } = require(P+'pw_lib');
   (async () => { const { browser, page, BASE } = await getPage('pro');
     await page.goto(BASE + '/...');
     // BẮT BUỘC chụp bằng shot(): chờ selector đặc trưng của màn + networkidle + đệm 500ms.
     // KHÔNG dùng `waitForTimeout(6000) + page.screenshot()` — 6s là con số cầu may, dễ dính spinner/màn trắng.
     await shot(page, '<folder>/shots/TC-01_after.png', 'text=<element đặc trưng màn hình>');
     await browser.close(); })();
   ```
   Gọi API Hệ thống Lõi: `const { withApi } = require(P+'pw_api');` — **tự sniff devise-token** từ request
   thật của app (KHÔNG tự dựng token, KHÔNG đọc code). Trả `{status, body, ok}` → dùng `status` cho
   case chống-bypass (403 vs 204). Targets: `getPage('pro'|'ticket'|'ticket_admin'|'reservation'|'admin')`.
   ⚠️ Report ticket cần `TK_STAFF=ticket-admin` (STAFF001 không có quyền).
   **Setup 1 lần**: `cd .claude/skills-scripts/testcase-evidence && npm i` (cài playwright local
   → require chạy thẳng, KHÔNG cần NODE_PATH; Chromium đã cache ở `~/Library/Caches/ms-playwright`).
   Session được cache ở `.state.<target>.json` (đặt `NO_STATE=1` khi cần login sạch/đổi account).
   Dữ liệu test tạo ra PHẢI có prefix `AIOT-TEST-*` (preset) / `AIOTTEST*` (staff) để cleanup quét được.
4. **Ảnh giữ nguyên PNG rõ** (generator tự scale khi nhúng — không cần nén tay).
   **BẮT BUỘC 2 ảnh/case: `before` + `after`** (template có 2 cột Evidence). Chụp rõ vùng quan trọng.
   - Case **thao tác** (create/cancel/pay…): before = TRƯỚC thao tác · after = SAU (kết quả/thông báo).
   - Case **hiển thị/report** (verify cột/label/tab): before = điểm vào / filter / sub-tab bar (context) ·
     after = kết quả quan sát (KPI+bảng, hoặc 404 nếu chưa build).
5. **Cập nhật `<folder>/tcs.json`**: mỗi tc điền `result` (**PASS | FAIL | 未実施 | SPEC-GAP**),
   `actual` (mô tả quan sát được, bắt đầu bằng đúng từ đó), `before`/`after` (tên file trong shots),
   `note` (seam/kỹ thuật nếu có).

   **4 trạng thái — đừng nhầm:**
   | result | Khi nào | `actual` viết gì |
   |---|---|---|
   | `PASS` | quan sát khớp `expect` | mô tả cái quan sát được |
   | `FAIL` | quan sát lệch `expect` | "spec kỳ vọng X; màn hình làm Y" + ảnh. **KHÔNG** symbol/file:line |
   | `未実施` | **KHÔNG quan sát được** (không vào được kênh quan sát) | lý do không quan sát được |
   | `SPEC-GAP` | **quan sát được** nhưng spec **không định nghĩa kỳ vọng** ở chỗ `METHOD.md` bảo phải kiểm | cái quan sát được + "không chấm được → hỏi BA/dev" |

   ⚠️ **Feature chưa build → `FAIL`** (quan sát 404/thiếu nút + ảnh *absence*). KHÔNG suy đoán
   "chưa code" — đó là code-knowledge. ⚠️ **Không bịa `expect`** để lấp chỗ spec im lặng → dùng `SPEC-GAP`.
6. **Sinh lại Excel vào folder** (ảnh tự lấy ở `<folder>/shots` — cạnh `tcs.json`):
   ```
   python3 .claude/skills-scripts/testcase-evidence/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
7. **Báo cáo**: bảng PASS/FAIL/未実施/SPEC-GAP, nêu rõ bug tìm được (mô tả **hành vi**, không vị trí code).
8. **KHÔNG auto-cleanup.** Giữ nguyên dữ liệu test để đối chiếu evidence / dev debug. Cuối báo cáo
   **liệt kê dữ liệu test còn tồn trên dev** (ID booking/khách/ticket master) để user chủ động gõ
   `/testcase-cleanup` khi cần.

## CAPTURE LESSONS (bắt buộc — vòng lặp học hỏi)
Sau khi chạy xong, ghi lại bẫy **CƠ KHÍ** vào `knowledge/lessons.md` (có ngày):
- ✅ Được ghi: selector đổi, timing, mã HTTP **quan sát được**, thứ tự thao tác, branch của phiên này.
- ❌ **Cấm ghi**: nguyên nhân ("vé không thu hồi *vì* backend thiếu callback"), phán quyết
  ("coupon chưa build"). Đó là WHAT → phá Tường thép #2, đầu độc phiên sau.
- **Bug KHÔNG vào knowledge** — bug thuộc về `specs.md` (`BUG-xx`) và file Excel.

## Before final (checklist bắt buộc trước khi báo cáo xong)
- [ ] Có đọc source code không? **Ở QA-runtime đáp án đúng luôn là KHÔNG.** Nếu lỡ đọc → khai ra.
- [ ] Có đọc `knowledge/system/**` hoặc dùng GitNexus không? (cả hai đều **CẤM** ở runtime)
- [ ] Mọi `expect` đều truy được về SPEC? Có chỗ nào tôi tự bịa kỳ vọng không? (→ phải là `SPEC-GAP`)
- [ ] FAIL nào còn ghi symbol/file:line không? (phải mô tả hành vi thuần)
- [ ] Đã Capture Lessons chưa? Có mục nào lẫn WHAT vào không?

## Lưu ý
- Thao tác phá huỷ (xoá đặt lịch, huỷ thanh toán) dùng dữ liệu test; tạo mới để test,
  tránh đụng dữ liệu người khác.
- Ảnh bind in-cell (co giãn theo ô). Excel để trong `<folder>`; upload Drive thì user tự kéo lên.
- Đổi màu/layout/nhãn file xuất = sửa `theme.json` (không đụng code/tcs).
