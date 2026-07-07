# threease_qa — con QA senior tự động (đọc trước)

Repo này KHÔNG chứa code sản phẩm. Nó chứa **1 skill** (`.claude/skills/qa-brain/`) biến
session Claude này thành **QA senior**: từ 1 file spec → sinh test → chạy Playwright lấy
evidence → khi FAIL thì định vị bug trong hệ thống ThreeSides (5 repo). Cộng với **pipeline
của sếp** ở `.claude/commands/testcase-*.md` (write / run / cleanup / retest / upspecschange).

## Cách xài (nhanh gọn)
1. Bỏ `specs.html` (hoặc `specs.md`) vào `wtf-is-this/TestCase_No.XX/`.
2. Bảo: **"dùng skill qa-brain cho folder wtf-is-this/TestCase_No.XX"** → skill đọc spec,
   viết case, gắn seam bằng 5 graph, ghi `tcs.json` + `.xlsx` (chưa chạy).
3. `/testcase-run wtf-is-this/TestCase_No.XX` → chạy thật + evidence + PASS/FAIL.
4. FAIL → skill dùng graph chỉ bug ở symbol/file nào (KHÔNG sửa code).

## 2 BỨC TƯỜNG THÉP (đọc kỹ, đừng phá)
1. **Oracle = SPEC, không phải code.** `expect` chỉ suy từ spec; lúc viết `expect` thì MÙ code.
   Lấy kỳ vọng từ code = test lặp lại code = vô nghĩa (tautology).
2. **Định vị bug, KHÔNG sửa code.** Đứng vai user. Chỉ ra bug ở đâu; không chỉnh 5 repo sản phẩm.

## Tri thức QA (black-box) — KHÔNG đọc code
- **Oracle = SPEC** (mỗi TestCase folder có `specs.md`). QA mù code tuyệt đối.
- **Chìa khoá — HOW vs WHAT:** navigation (bấm gì) tách khỏi đúng/sai (WHAT). Bug sống ở WHAT
  (logic), không ở HOW (nút/màn) → navigation miễn nhiễm bug logic.
- **Living Business Doc** (`knowledge/*.md`, đã duyệt) = *cách vận hành* (HOW/navigation) +
  kênh quan sát. **Không phải oracle.** Đúng/sai = SPEC + quan sát live.
- **Precondition Protocol:** định-nghĩa-từ-SPEC → dựng-bằng-flow-cũ (không dùng feature đang test)
  → verify-bằng-mắt (Pro + ticket-admin).
- **Kênh quan sát**: `knowledge/observation-channels.md` (Pro / ticket-admin / ticket-app).
- GitNexus **chỉ dùng ở build-time** (`/testcase-systemdoc`) để soạn Living Business Doc, bắt buộc
  UI-confirm + người duyệt. **QA-runtime KHÔNG đụng GitNexus, không đọc code.**
- Bối cảnh hệ thống (kiến trúc, HTTP link, DB, sync) ở `/Users/tritdd/Work/ThreeSides/CLAUDE.md`
  — chỉ dùng ở tầng build-time khi soạn Living Business Doc, không phải cho QA-runtime.

## Nguyên tắc token
1 session ấm nghĩ xuyên suốt + dùng graph tool + script sếp (xlsx/Playwright).
KHÔNG đẻ subprocess `claude -p`, KHÔNG viết file `.py` phụ trợ.
