# /testcase-a11y — Test Accessibility (WCAG, black-box) một TestCase

Quét accessibility các màn mà spec đang test đụng tới, bằng axe-core. **Track RIÊNG**, KHÔNG trộn
vào PASS/FAIL functional. Oracle = **WCAG** (không phải spec). Mù code — axe chỉ đọc DOM đã render.

## Cách dùng
```
/testcase-a11y wtf-is-this/TestCase-XX
```

## TIẾT KIỆM TOKEN — đọc trước
Dùng lại helper `.claude/skills-scripts/testcase-evidence/`: `pw_lib.js` (`getPage`+`shot`),
`a11y_lib.js` (`runAxe`), `build_a11y_report.py`. KHÔNG viết lại. Không in script/ảnh vào chat.
**Setup 1 lần:** `cd .claude/skills-scripts/testcase-evidence && npm i`.

## Nguyên tắc (2 tường)
- **Oracle = WCAG.** `specs.md` chỉ dùng để **chọn màn cần quét (scope)**, KHÔNG làm oracle.
- **Mù code.** Không đọc code sản phẩm / GitNexus / `knowledge/system/**`. axe chỉ đọc DOM.

## Quy trình
1. **Chọn màn (scope):** đọc `<folder>/specs.md` mục "3. Ảnh hưởng hệ thống" → danh sách app/màn.
   Nếu folder đã có `tcs.json` **đã chạy** → tái dùng luôn màn/URL đã lái (rẻ hơn).
2. **Seam màn → URL:** tra `knowledge/*.md` (approved) đúng như qa-brain functional. Flow chưa có trong
   `knowledge/` → **dừng**, KHÔNG tự đọc code; báo user chạy `/testcase-systemdoc <flow>` trước.
3. **Quét từng màn** (viết driver inline như /testcase-run):
   ```js
   const P='<repo>/.claude/skills-scripts/testcase-evidence/';
   const { getPage, shot } = require(P+'pw_lib');
   const { runAxe } = require(P+'a11y_lib');
   (async () => {
     const { browser, page, BASE } = await getPage('reservation'); // app theo màn
     await page.goto(BASE + '/booking');
     await shot(page, '<folder>/shots/a11y_booking_context.png', 'text=<đặc trưng màn>'); // chờ render xong
     const { violations, counts } = await runAxe(page);
     // với mỗi violation critical/serious: chụp phần tử lỗi làm evidence
     // await page.locator(v.nodes[0].target).first().screenshot({path:'<folder>/shots/a11y_<màn>_<rule>.png'});
     await browser.close();
   })();
   ```
   ⚠️ Chỉ `runAxe` **sau khi trang render xong** (dùng `shot()`/chờ selector + networkidle), không quét lúc còn spinner.
4. **Verdict mỗi màn:** `PASS` (0 critical/serious) · `FAIL` (≥1) · `未実施` (không vào được màn).
   ⚠️ a11y **KHÔNG BAO GIỜ** dùng `SPEC-GAP` — WCAG luôn định nghĩa kỳ vọng, nên mọi vi phạm chấm được là FAIL. (Đừng mang mental-model "SPEC-GAP là finding cao nhất" của qa-brain sang đây.)
5. **Viết `<folder>/a11y.results.json`** đúng schema (xem `build_a11y_report.py`): meta + screens[] với
   violations[] = {rule, impact, wcag (từ tag `wcagXYZ`), help, nodes[{target,html}], shot}.
6. **Build report:** `python3 .claude/skills-scripts/testcase-evidence/build_a11y_report.py \
   <folder>/a11y.results.json <folder>/<TênFolder>.a11y.xlsx`.
7. **Đẩy sổ bug** (chỉ critical+serious): **dedup 1 bug/(màn×rule)** → mỗi nhóm 1 object append vào
   `wtf-is-this/bug-he-thong.tcs.json` (theo `docs/BUG-LOG.md`): `bug_type:"Accessibility"`, `result:"FAIL"`,
   `pri`= critical→High/serious→Medium, `screen`="<App> — <Màn>", `source`=TestCase-XX, `title`="WCAG <rule>: …",
   `actual`="axe <rule>, impact <mức>, N phần tử", `before:null` (+`note` lý do N/A), `after`=ảnh phần tử,
   `bug_id`=BUG-NNN kế tiếp, `found_at`=hôm nay, `status`="Mở". Rồi build lại:
   `python3 .../build_bug_report.py wtf-is-this/bug-he-thong.tcs.json wtf-is-this/bug-he-thong.xlsx`.
8. **Báo cáo:** bảng màn × verdict + số vi phạm theo mức; liệt kê bug đã đẩy (BUG-NNN). Mô tả **hành vi**
   (rule + phần tử), KHÔNG file:line.

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG** (axe chỉ đọc DOM).
- [ ] Mọi verdict chỉ dựa vi phạm WCAG do axe trả (không tự bịa)? Không dùng specs.md làm oracle a11y?
- [ ] Đã dedup 1 bug/(màn×rule) trước khi append sổ bug chưa?
- [ ] moderate/minor CHỈ nằm trong report, KHÔNG đẩy sổ bug?
