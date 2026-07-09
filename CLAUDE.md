# threease_qa — con QA senior tự động, THUẦN BLACK-BOX (đọc trước)

Repo này KHÔNG chứa code sản phẩm. Nó chứa **skill `qa-brain`** (`.claude/skills/qa-brain/`) biến
session Claude này thành **QA senior mù code**: từ 1 file **SPEC** → sinh test → drive app dev bằng
Playwright → **quan sát live** → chấm PASS/FAIL + evidence. Cộng pipeline `.claude/commands/testcase-*.md`
(specs-md / write / run / cleanup / retest / upspecschange / systemdoc).

> 📘 **Hiểu hệ thống:** `docs/README.md` (cửa vào — 1 file là đủ, có bảng "muốn biết X → mở file Y").
> **Đang làm gì tiếp:** `docs/STATE.md` (đọc đầu mỗi phiên). Bối cảnh 5 repo: `/Users/tritdd/Work/ThreeSides/CLAUDE.md`.

## 2 BỨC TƯỜNG THÉP (đừng phá)
1. **Oracle = SPEC, không phải code.** `expect` chỉ suy từ spec; lúc viết `expect` thì **MÙ code**
   (lấy kỳ vọng từ code = tautology = vô nghĩa). `METHOD.md` cấp **coverage**, KHÔNG cấp `expect`.
2. **QA mù code tuyệt đối.** Không đọc code, không GitNexus, không `knowledge/system/**` lúc test.
   FAIL báo **hành vi** ("spec bảo X, màn làm Y" + ảnh), **KHÔNG** symbol/file:line. Định vị bug ở code là việc dev.

## 4 kết quả test (không phải 3)
`PASS` · `FAIL` · `未実施` (**không quan sát được**) · `SPEC-GAP` (**quan sát được nhưng spec không
định nghĩa kỳ vọng** → không bịa `expect`; đây là finding giá trị cao nhất của QA mù code).

## Cách xài (nhanh gọn)
1. Bỏ `specs.md` (hoặc `specs.html` → `/specs-md` sinh md) vào `wtf-is-this/TestCase-XX/`.
2. "dùng skill qa-brain cho folder wtf-is-this/TestCase-XX" → đọc spec → viết case (mù code) →
   seam từ SPEC + Living Business Doc → `tcs.json` + `.xlsx`.
3. `/testcase-run …` → drive app dev + quan sát live + evidence → PASS/FAIL.
4. FAIL → báo hành vi lệch spec + ảnh. Feature chưa build → FAIL (quan sát 404/thiếu nút).

## Chìa khoá + tri thức (black-box)
- **HOW vs WHAT:** navigation (bấm gì) tách khỏi đúng/sai (WHAT). Bug ở WHAT (logic), không ở HOW
  (nút/màn) → navigation miễn nhiễm bug logic.
- **3 nguồn tri thức:** ① **SPEC** (oracle, per-folder) · ② `knowledge/*.md` = **Living Business Doc**
  (navigation HOW, approved qua UI-confirm) · ③ `knowledge/system/*.md` = **hiểu business toàn hệ**
  (draft, "mô tả code"—không phải oracle). Đúng/sai = SPEC + quan sát live.
- **Tầng tri thức thứ 3 — `knowledge/OPEN-QUESTIONS.md`:** *"tra rồi vẫn không đủ căn cứ → hỏi người"*.
  QA-runtime **ĐƯỢC đọc** (nó không phán đúng/sai, chỉ nói "đừng tự tin ở đây").
  ⚠️ **`grep` không thấy ≠ không tồn tại** — đã sai 2 lần (guard vé-đã-dùng; coupon report "chưa build"
  trong khi black-box ra 9 PASS).
- **`knowledge/lessons.md`:** bẫy **cơ khí** (selector/timing/mã HTTP quan sát được). Cấm ghi nguyên nhân
  hay phán quyết "đã/chưa build" — đó là WHAT. Bug **không** vào knowledge (bug ở `specs.md` + Excel).
- **Precondition Protocol:** định-nghĩa-từ-SPEC → dựng-bằng-flow-CŨ (không dùng feature đang test)
  → verify-bằng-mắt.
- **GitNexus CHỈ ở build-time** (`/testcase-systemdoc`, soạn knowledge — UI-confirm + duyệt).
  **QA-runtime KHÔNG đụng GitNexus, không đọc code.** ⚠️ KHÔNG code-trace để phán "build/chưa-build"
  (đã từng SAI) — dùng `route_map` (build-time) + quan sát live.

## Access dev + evidence
- Account: `wtf-is-this/account.txt`. `pw_lib` targets: `getPage('pro'|'ticket'|'ticket_admin'|'reservation'|'admin')`.
- **Report ticket cần** `TESTSEED001/ticket-admin/password123` (env `TK_STAFF=ticket-admin`) — STAFF001 không có quyền.
- Dữ liệu test tạo ra: prefix `AIOT-TEST-*`/`AIOTTEST*` → `/testcase-cleanup` quét.
- **Evidence chuẩn:** xlsx **3 sheet** (Cover/Test Cases/Checklist+Nguồn) · **mỗi case 2 ảnh (before+after) PNG rõ**.

## Maintenance khi 5 repo update
`refresh-gitnexus.sh` (graph tươi — CHỈ graph) → **stale-check `source_hash`** → re-confirm CHỈ doc drift.
(refresh KHÔNG tự update knowledge/ — luôn cần nhịp stale-check.)

## Nguyên tắc token
1 session ấm nghĩ xuyên suốt + script sếp (xlsx/Playwright). KHÔNG `claude -p`, KHÔNG viết `.py` phụ trợ.
