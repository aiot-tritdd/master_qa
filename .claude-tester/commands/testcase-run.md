# Skill 2 — Chạy Test Case & nhập Evidence

> **Nguyên tắc: Knowledge-first / source-on-demand** — luôn đọc knowledge (`.claude-tester/knowledge/`)
> trước để nắm bối cảnh, KHÔNG grep lại toàn bộ codebase; chỉ đọc thẳng source code/spec gốc khi
> knowledge không đủ chi tiết hoặc nghi ngờ đã lỗi thời.

Chạy test thật trên Threease dev (Playwright + API), chụp screenshot, rồi cập nhật
`result` + `actual` + ảnh Before/After vào file test case đã tạo bởi Skill 1.

## Cách dùng
```
/testcase-run <folder>
```
Ví dụ: `/testcase-run 7.Tests/TestCase_No.10.5`

## TIẾT KIỆM TOKEN — đọc trước
Dùng lại helper ở `.claude-tester/scripts/`:
`pw_lib.js` (đăng nhập/session), `pw_api.js` (gọi API), `build_evidence.py` (sinh Excel).
**KHÔNG viết lại** flow đăng nhập/generator. Đọc `<folder>/tcs.json` để biết case cần chạy.
Không in script, không dán base64/ảnh vào chat.

## Tri thức nền (đọc trước khi chạy — không grep lại code)
- `.claude-tester/knowledge/SYSTEM.md` — URL, auth, **branch (verify!)**, endpoint, selector.
- `.claude-tester/knowledge/PLAYBOOK.md` — công thức (tạo booking đã TT, số dư vé, `shot()`, thứ tự cleanup).
- `.claude-tester/knowledge/LESSONS.md` — bẫy đã gặp (branch 2, 422 vé, ảnh trắng…).
- **Điều kiện**: case liên quan số dư vé/coupon → đọc `.claude-tester/knowledge/SYNC_MAP.md` trước khi
  kết luận PASS/FAIL (đừng tin số dư hiển thị bên Hệ thống Vé làm bằng chứng duy nhất); case liên quan
  báo cáo/export/tính tiền → đọc `.claude-tester/knowledge/REPORTING.md`.

## Quy trình
1. **Đọc** `<folder>/tcs.json` (do Skill 1 tạo). Nếu thiếu → chạy `/testcase-write` trước.
   Khi cần đối chiếu hành vi mong đợi, đọc `specs.md` — ưu tiên
   `8.Tasks/specs/<TênTask>/specs.md` (nguồn chuẩn), fallback `<folder>/specs.md` cho task cũ
   (KHÔNG dùng ảnh spec — ưu tiên md cho rẻ + chính xác).
2. **Account đăng nhập**: lấy từ `7.Tests/account.txt`. Mặc định Pro dev đã đúng sẵn trong
   `pw_lib.js` (BASE=develop.pro.threease.com, basic `threesides/threesides`,
   login `TESTSEED001/STAFF001/password123`). Đổi hệ khác thì set env
   `BASE_URL, BASIC_USER/PASS, INST/THER/PW, API_BASE`.
3. **Chạy test từng case**, chụp screenshot vào `<folder>/shots/` (nén ~1080px JPG q90).
   Helper ở project (require bằng đường dẫn tuyệt đối tới project):
   ```js
   const P='/Applications/Workspaces/threease/.claude-tester/scripts/';
   const { getPage, shot } = require(P+'pw_lib');
   (async () => { const { browser, page, BASE } = await getPage();
     await page.goto(BASE + '/...');
     // BẮT BUỘC chụp bằng shot(): chờ selector đặc trưng màn hình + networkidle + đệm 500ms
     // → tránh chụp khi màn hình chưa load (spinner/màn trắng). KHÔNG dùng sleep cố định + screenshot trần.
     await shot(page, '<folder>/shots/TC-01_after.png', 'text=<element đặc trưng màn hình>');
     await browser.close(); })();
   ```
   Gọi API backend (token tự bắt): `const { withApi } = require(P+'pw_api');`
   **Setup 1 lần**: `cd .claude-tester/scripts && npm i` (cài playwright local
   → require chạy thẳng, KHÔNG cần NODE_PATH; Chromium đã cache ở `~/Library/Caches/ms-playwright`).
   Selector login: `input[data-cy=institute_code|therapist_code|password]`, `[data-cy=loginButton]`.
   Dữ liệu test tạo ra PHẢI có prefix `AIOT-TEST-*` (preset) / `AIOTTEST*` (staff) để cleanup quét được.
4. **Nén ảnh** trước khi nhúng:
   ```python
   from PIL import Image; im=Image.open(f).convert('RGB')
   w=1080; im=im.resize((w,int(im.height*w/im.width))) if im.width>w else im; im.save('<folder>/shots/'+name,'JPEG',quality=90)
   ```
5. **Cập nhật `<folder>/tcs.json`**: mỗi tc điền `result`(PASS|FAIL|未実施),
   `actual`(mô tả quan sát được, bắt đầu bằng PASS/FAIL/未実施), `before`/`after`(tên file trong shots),
   `note`(kỹ thuật/PR nếu có).
6. **Sinh lại Excel vào folder** (ảnh tự lấy ở `<folder>/shots` — cạnh `tcs.json`):
   ```
   python3 .claude-tester/scripts/build_evidence.py \
     <folder>/tcs.json <folder>/<TênFolder>.xlsx
   ```
7. **Báo cáo**: bảng PASS/FAIL/未実施, nêu rõ bug tìm được.
   Cuối báo cáo liệt kê **dữ liệu test còn tồn trên dev** (ID booking / khách / ticket master…)
   để user chủ động dọn sau bằng `/testcase-cleanup`.

## KHÔNG auto-cleanup
- Skill này **KHÔNG tự dọn dữ liệu test** sau khi chạy. Giữ nguyên dữ liệu để user
  đối chiếu evidence / dev debug bug vừa tìm được.
- Cleanup là thao tác **chạy tay, chủ động** khi cần: user tự gõ `/testcase-cleanup <folder>`.

## CAPTURE LESSONS (bắt buộc — vòng lặp học hỏi)
Sau khi chạy xong, cập nhật tri thức để lần sau "kinh nghiệm" hơn:
- Gặp bẫy mới (selector/timing/lỗi API…) → thêm 1 dòng vào `.claude-tester/knowledge/LESSONS.md` (có ngày).
- Endpoint/branch/selector khác với `SYSTEM.md` → sửa `SYSTEM.md` + đổi ngày.
- Bug lặp lại 1 pattern → nâng thành luật trong `METHOD.md`.

## Before final (checklist bắt buộc trước khi báo cáo xong)
- [ ] Đã đọc đúng knowledge theo routing (`.claude-knowledge/README.md` mục "Routing table") chưa?
- [ ] Có đọc source code không? Nếu có, vì sao?
- [ ] Có điểm nào knowledge thiếu/lỗi thời cần cập nhật lại không (đã làm ở bước CAPTURE LESSONS)?
- [ ] Nếu case liên quan vé/coupon/report, đã đối chiếu `SYNC_MAP.md`/`REPORTING.md` trước khi kết
  luận PASS/FAIL chưa?

## Lưu ý
- Thao tác phá huỷ (xoá đặt lịch, huỷ thanh toán) dùng dữ liệu test; tạo mới để test,
  tránh đụng dữ liệu người khác.
- Ảnh bind in-cell (co giãn theo ô). Excel để trong `<folder>`; upload Drive thì user tự kéo lên.
- Đổi màu/layout/nhãn file xuất = sửa `theme.json` (không đụng code/tcs).
