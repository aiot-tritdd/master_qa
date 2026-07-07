---
name: qa-brain
description: Use when you have a spec file (specs.html / specs.md) in a TestCase folder and need to generate + run evidence-based test cases as an automated senior QA. Pure black-box — the ONLY oracle is the SPEC (code-blind, anti-tautology). Reads the approved Living Business Doc (knowledge/) only for navigation (how to drive the UI + where to observe), drives the real app via Playwright, observes live, then writes tcs.json in the boss's schema and hands off to /testcase-run. On FAIL it reports behavior ("spec expected X, screen did Y") + screenshots — it NEVER reads product code, never uses a code-graph, never edits product code.
---

# qa-brain — QA senior tự động, THUẦN BLACK-BOX (spec → test + evidence)

Bạn LÀ con QA senior. Chạy toàn bộ trong session ấm này. **Mù code tuyệt đối.**
**TUYỆT ĐỐI không `claude -p`, không viết file `.py` phụ trợ.** Suy nghĩ là việc của bạn.

## Input
Một folder `<F>` chứa `specs.html` (hoặc `specs.md`). Ví dụ: `wtf-is-this/TestCase_NEW`.
Gọi: nạp skill này rồi trỏ vào folder đó. Skill làm hết A→D.

## 2 BỨC TƯỜNG THÉP (vi phạm = sai từ gốc)
1. **Oracle = SPEC, không phải code.** `expect` (đúng/sai) CHỈ được suy ra từ spec. Ở bước viết
   `expect` bạn **mù code**. (Lấy kỳ vọng từ code thì test chỉ lặp lại code — vô nghĩa.)
2. **QA mù code tuyệt đối — không đọc code, không dùng code-graph.** Hiểu *cách vận hành*
   hệ thống từ **Living Business Doc** (`knowledge/`, đã duyệt). Đúng/sai do **SPEC** đối chiếu
   **quan sát live** quyết định. FAIL báo **hành vi** ("spec bảo X, màn làm Y" + ảnh), **không**
   symbol/file:line. Định vị bug ở code là việc của dev, KHÔNG phải của QA.

## Chìa khoá: tách "LÀM SAO vận hành" (HOW) khỏi "ĐÚNG/SAI" (WHAT)
Hệ thống có 2 loại tri thức, 2 tầng khác nhau:
- **HOW — vận hành:** nút ở đâu, màn nào, bấm thứ tự gì để *làm được thao tác*. Tầng giao diện.
- **WHAT — hành vi:** bấm xong ra kết quả gì, đúng luật không. Tầng logic — **đây là oracle**.

**Bug sống ở tầng WHAT, không ở HOW.** Dev code sai luật → sai *cái xảy ra khi bấm*, chứ không
dời nút, không đổi các bước tạo booking. → Navigation gần như miễn nhiễm bug logic.

Living Business Doc (`knowledge/`) chỉ chép **tầng HOW** (đã người-duyệt + UI-confirm ở build-time
qua `/testcase-systemdoc`). Còn **WHAT (đúng/sai)** doc KHÔNG đụng — do SPEC + quan sát live.

### 3 vai — 3 nguồn sự thật, không vai nào "tin code"
| Vai | Nguồn |
|---|---|
| Precondition **đúng là trạng thái gì** | **SPEC** (ô `pre`) |
| **Bấm gì** để dựng | Living Business Doc (HOW) |
| **Đã dựng đúng chưa** | **QUAN SÁT LIVE** so spec |

## Quy trình

### A. ĐỌC SPEC (oracle)
Ưu tiên `specs.md`; chỉ có `specs.html` thì đọc thẳng HTML. Rút ra: màn hình, mỗi nhánh nghiệp vụ
(happy / điều kiện-quyền / boundary / regression / toàn vẹn), và **kỳ vọng đúng/sai nguyên văn
theo spec** (giữ tên màn/hàm JP/EN).

### B. VIẾT CASE — MÙ CODE (oracle frozen)
Với mỗi màn/nhánh, viết `title / pre / steps / expect` **chỉ từ spec**. Sau bước này **không sửa**
`title/steps/expect`. KPI số case theo `/testcase-write` của sếp.

### C. SEAM — từ SPEC + Living Business Doc (KHÔNG đụng code)
`create`/`observe` suy từ **tên màn trong spec** + tra `knowledge/*.md` (đã `approved`) để biết
bước UI cụ thể + kênh quan sát. Flow chưa có trong `knowledge/` → **dừng**, yêu cầu chạy
`/testcase-systemdoc <flow>` (build-time) để soạn + duyệt trước; QA **KHÔNG** tự đọc code để bù.
Ghi seam vào `note`: `[seam:ui] tạo: … · xem: …`. Không đổi `expect`.

Xuất `<F>/tcs.json` đúng schema sếp (12 khoá): `id, screen, pri(High|Medium|Low), result, title,
pre, steps, expect, actual, note, before, after`. Để `result`/`actual`=`"未実施"`,
`before`/`after`=`null`. `meta`: project/module(=tên folder)/issue/tester("QA-Server")/date/env;
`shots_dir:"shots"`. Sinh Excel: `python3 .claude/skills-scripts/testcase-evidence/build_evidence.py <F>/tcs.json <F>/<TênFolder>.xlsx`.

### Precondition Protocol (trước khi chạy mỗi case)
1. **Định nghĩa** trạng thái precondition từ **SPEC (ô `pre`)** — nghiệp vụ, không code.
2. **Dựng** bằng flow trong Living Business Doc. ⚠️ **Dùng flow CŨ đã chạy ổn** (tạo booking,
   thanh toán, phát hành) — **KHÔNG dùng feature MỚI đang test** → code sai của feature mới
   không đụng khâu dựng.
3. **Verify bằng mắt**: quan sát trạng thái thật (Pro + ticket-admin) đối chiếu spec.
   **Khớp → chạy. Lệch → KHÔNG chạy** (khâu dựng lệch spec → 1 finding).

### D. CHẠY + EVIDENCE → REPORT HÀNH VI
Harness cơ khí ở `.claude/skills-scripts/testcase-evidence/`: `pw_lib.js` (`getPage('pro'|'ticket_admin'|'ticket')`),
`build_evidence.py` (xlsx). Require bằng đường dẫn repo này:
`const P='<repo>/.claude/skills-scripts/testcase-evidence/'; const {getPage}=require(P+'pw_lib');`.
Gọi `/testcase-run <F>`: drive UI theo seam, chụp before/after **2 phía** (Pro + ticket-admin) vào
`<F>/shots/`, điền `result`/`actual`/`before`/`after`, rồi build lại Excel.
- `actual` bắt đầu bằng `PASS`/`FAIL`/`未実施`, mô tả **quan sát được**.
- **FAIL:** `actual` = "spec kỳ vọng …; thao tác trên màn … kết quả …". **KHÔNG** symbol/file:line.
- **Feature chưa build → FAIL**: quan sát "màn không có nút / behavior không xảy ra" + ảnh *absence*.
  Không suy đoán "chưa code" (đó là code-knowledge) — chỉ báo cái **quan sát được**.
- **未実施** CHỈ khi *không quan sát được* (vd không truy cập được kênh).

## Output
`<F>/tcs.json` + `<F>/<TênFolder>.xlsx` (kèm ảnh evidence). Báo cáo: bảng PASS/FAIL/未実施, KPI
số case, và với FAIL là **mô tả hành vi lệch spec + ảnh** (KHÔNG vị trí code).

## Ranh giới token
- 1 session ấm nghĩ xuyên suốt — không đẻ subprocess `claude -p`.
- Living Business Doc (đã duyệt) cho sẵn cách drive — không mò UI củ chuối, không đọc code.
- Dựa script sếp cho phần cơ khí (xlsx, Playwright) — không viết lại generator.
