# /testcase-visual — Test Visual regression (black-box) một TestCase

So ảnh các màn spec đang test với **baseline người-duyệt** (`baselines/<app>/<slug>.png`, commit git).
**Track RIÊNG**, KHÔNG trộn PASS/FAIL functional. Oracle = **baseline** (không phải spec). Mù code.

## Cách dùng
```
/testcase-visual wtf-is-this/TestCase-XX
```

## TIẾT KIỆM TOKEN
Dùng lại `.claude/skills-scripts/testcase-evidence/`: `pw_lib` (`getPage`), `visual_lib`
(`captureMasked`/`compareToBaseline`/`baselinePath`), `build_visual_report.py`. KHÔNG viết lại.
Setup 1 lần: `cd .claude/skills-scripts/testcase-evidence && npm i`.

## Nguyên tắc (2 tường)
- **Oracle = baseline người-duyệt.** `specs.md` chỉ để **chọn màn (scope)**, KHÔNG làm oracle.
- **Mù code.** Chỉ đọc pixel màn render. Không code / GitNexus / `knowledge/system/**`.

## Quy trình
1. **Chọn màn (scope):** đọc `<folder>/specs.md` mục "3. Ảnh hưởng hệ thống" → app/màn. Có `tcs.json` đã chạy → tái dùng màn/URL.
2. **Đọc `mask:`** của mỗi màn từ `knowledge/*.md` (approved). Màn chưa có `mask:` trong knowledge → chạy `/testcase-systemdoc <flow>` (build-time) để sinh, KHÔNG mask tay ở đây.
3. **Chụp + so** (driver inline):
   ```js
   const P='<repo>/.claude/skills-scripts/testcase-evidence/';
   const { getPage } = require(P+'pw_lib');
   const { captureMasked, compareToBaseline, baselinePath } = require(P+'visual_lib');
   const fs = require('fs');
   (async () => {
     const { browser, page, BASE } = await getPage('pro');
     await page.goto(BASE + '/reservations');
     // chờ render xong (như shot): chờ selector đặc trưng + networkidle
     const cur = '<folder>/shots/vis_reservations_cur.png';
     await captureMasked(page, cur, ['<mask selectors từ knowledge>']);
     const base = baselinePath('pro', '/reservations');
     if (!fs.existsSync(base)) {
       fs.mkdirSync(require('path').dirname(base), {recursive:true}); fs.copyFileSync(cur, base); // NEW-BASELINE
     } else {
       const r = compareToBaseline(cur, base, '<folder>/shots/vis_reservations_diff.png');
       // r.diffRatio > 0.001 => FAIL
     }
     await browser.close();
   })();
   ```
4. **Verdict/màn:** `PASS` (diffRatio ≤ 0.001) · `FAIL` (>) · `未実施` (không vào được màn) · `NEW-BASELINE` (chưa có baseline → vừa tạo).
   ⚠️ Visual **KHÔNG BAO GIỜ** `SPEC-GAP` (oracle là baseline, luôn có/không).
   ⚠️ **NEW-BASELINE cần NGƯỜI GẬT** "nhìn đúng" rồi mới `git add baselines/... && commit` — nếu ảnh xấu thì đừng commit, sửa app trước.
5. **Viết `<folder>/visual.results.json`** (schema ở `build_visual_report.py`): meta + screens[] {name,app,url,result,diff_ratio,baseline,current,diff}.
6. **Build report:** `python3 .../build_visual_report.py <folder>/visual.results.json <folder>/<Tên>.visual.xlsx`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/màn** → append `wtf-is-this/bug-he-thong.tcs.json` (`bug_type:"Visual"`, `result:"FAIL"`, `pri` theo diff_ratio, `screen`="<App> — <Màn>", `source`=TestCase-XX, `title`="Visual: <màn> lệch X% so baseline", `before`=baseline, `after`=ảnh diff), rồi build lại `bug-he-thong.xlsx`.
8. **Báo cáo:** bảng màn × verdict + diff%. Liệt kê NEW-BASELINE cần người gật/commit.

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG** (chỉ đọc pixel).
- [ ] Verdict chỉ dựa diff pixel với baseline (không tự bịa)? Không dùng specs.md làm oracle?
- [ ] NEW-BASELINE đã nhắc người GẬT trước khi commit chưa? (không auto-commit baseline chưa duyệt)
- [ ] Màn chưa có `mask:` → đã dừng + nhắc `/testcase-systemdoc`, KHÔNG mask tay?
