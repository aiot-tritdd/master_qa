# threease_qa — con QA senior tự động, THUẦN BLACK-BOX (đọc trước)

Repo này KHÔNG chứa code sản phẩm. Nó chứa **skill `qa-brain`** (`.claude/skills/qa-brain/`) biến
session Claude này thành **QA senior mù code**: từ 1 file **SPEC** → sinh test → drive app dev bằng
Playwright → **quan sát live** → chấm PASS/FAIL + evidence. Cộng pipeline `.claude/commands/testcase-*.md`
(specs-md / write / run / cleanup / retest / upspecschange / systemdoc).

> 📘 **Hiểu hệ thống:** `README.md` (cửa vào — 1 file là đủ, có bảng "muốn biết X → mở file Y").
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
5. (tuỳ chọn) `/testcase-a11y wtf-is-this/TestCase-XX` → quét accessibility (WCAG) các màn → report + sổ bug.
   Track RIÊNG, oracle = WCAG, vẫn mù code (axe chỉ đọc DOM).
6. (tuỳ chọn) `/testcase-visual wtf-is-this/TestCase-XX` → so ảnh màn với baseline người-duyệt (regression UI).
   Track RIÊNG, oracle = baseline, mù code. Baseline ở `baselines/` (commit git), mask từ knowledge.
7. (tuỳ chọn) `/testcase-security wtf-is-this/TestCase-XX` → quét security **13 họ** (phủ phần black-box
   OWASP **2025**: Injection/XSS · IDOR · Client-bypass · Error-disclosure · Security-headers · Open-redirect · CSRF ·
   Mass-assignment · Force-browse/traversal · Session-after-logout · Cookie-flags · CORS · Session-fixation)
   → report + sổ bug. Track RIÊNG, oracle = **bất biến an ninh phổ quát**, mù code. Đây là NƠI TẬP TRUNG
   security (functional không làm rải rác nữa). Data test prefix `AIOT-TEST-SEC-*` → `/testcase-cleanup`.
   ⚠️ **App SPA (pro/reservation/admin — Nuxt): BẮT BUỘC cấp `baselineBody`** cho probe IDOR/force-browse,
   nếu không **FAIL giả hàng loạt** (server trả cùng vỏ cho mọi path, chữ 404 do JS vẽ sau). Xem command doc §"App SPA".

8. (tuỳ chọn) `/testcase-compat wtf-is-this/TestCase-XX` → quét **compatibility**: engine (chromium/firefox/webkit)
   × viewport (320/390/768/1280). Track RIÊNG, oracle = **WCAG 1.4.10 Reflow** (mốc 320px do W3C công bố) +
   **parity affordance giữa engine** + **0 lỗi JS**, mù code. KHÔNG cần baseline (so giữa engine cùng thời điểm).
   ⛔ Engine không chạy được → **`未実施` + lý do**, TUYỆT ĐỐI không giả lập bằng engine khác rồi báo "đã test".

9. (tuỳ chọn) `/testcase-perf wtf-is-this/TestCase-XX` → đo **Core Web Vitals** (LCP/CLS/TBT/FCP/TTFB),
   5 lần/màn lấy **trung vị**. Track RIÊNG, oracle = **ngưỡng Google công bố** (web.dev/vitals) — không cần
   ai đặt số. `needs-improvement` **cũng là FAIL** (good LÀ mốc đạt; nới = tự hạ chuẩn).
   ⚠️ **Báo cáo BẮT BUỘC nói: LAB ≠ FIELD + DEV ≠ PROD** — lab "good" không chứng minh user thật thấy nhanh;
   lab "poor" thì chắc chắn tệ. ⛔ **Không báo "INP" ở lab** (field-only) — dùng TBT proxy.

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
- **GitNexus CHỈ ở build-time** (`/testcase-systemdoc`, soạn knowledge — UI-confirm bằng `explorer.js` + duyệt).
  **QA-runtime KHÔNG đụng GitNexus, không đọc code, KHÔNG chạy `explorer.js`.** ⚠️ KHÔNG code-trace để phán "build/chưa-build"
  (đã từng SAI) — dùng `route_map` (build-time) + quan sát live.

## Access dev + evidence
- Account: `wtf-is-this/account.txt`. `pw_lib` targets: `getPage('pro'|'ticket'|'ticket_admin'|'reservation'|'admin')`.
- **Report ticket cần** `TESTSEED001/ticket-admin/password123` (env `TK_STAFF=ticket-admin`) — STAFF001 không có quyền.
- Dữ liệu test tạo ra: prefix `AIOT-TEST-*`/`AIOTTEST*` → `/testcase-cleanup` quét.
- **Evidence chuẩn:** xlsx **3 sheet** (Cover/Test Cases/Checklist+Nguồn) · **mỗi case 2 ảnh (before+after) PNG rõ**.

## Sổ bug hệ thống — `wtf-is-this/bug-he-thong.xlsx` (append qua JSON, CẤM sửa Excel tay)
> 📘 **Quy trình đầy đủ (field, vòng đời status, build, trang trí): `docs/BUG-LOG.md`.** Dưới đây chỉ là bản rút gọn.

Bug + SPEC-GAP đã **confirm với dev là bug hệ thống** (out-of-scope spec đang test) thì chuyển vào sổ này,
file update của spec chỉ giữ PASS (vd `TestCase-12-update.xlsx` sinh từ `TestCase-12/tcs-update.json`).
Sổ bug là **bản in từ `bug-he-thong.tcs.json`** qua **`build_bug_report.py`** (KHÁC `build_evidence.py` —
file kia in evidence 1 spec). Nguồn sự thật là JSON, không phải Excel.
- **Append bug mới:** thêm object vào mảng `tcs` của `wtf-is-this/bug-he-thong.tcs.json`. Bắt buộc:
  `bug_id` (BUG-NNN duy nhất) · `found_at` (YYYY-MM-DD) · `status` ∈ {Mở, Chờ retest, Đã đóng, Tái phát}.
  `source` = spec lộ ra bug. Thiếu/sai → guard **raise, không in file**.
- **Vòng đời:** Mở →(dev fix: `fix_note`)→ Chờ retest →(QA test lại)→ Đã đóng (`retested_at`) / Tái phát.
  "Đã fix" là lời khai dev; "Đã pass" là QA quan sát lại thật.
- **In lại:** `python3 .claude/skills-scripts/testcase-evidence/build_bug_report.py wtf-is-this/bug-he-thong.tcs.json wtf-is-this/bug-he-thong.xlsx`
- **Vì sao cấm sửa Excel trực tiếp:** merge cell + shape trang trí neo theo dòng + COUNTIF theo range →
  chèn dòng tay là lệch trang trí, sai số đếm. Sửa JSON rồi build lại, luôn.
- **Trang trí** (trời/kem/đồi cỏ) đã nhúng trong script; tắt về bản sạch: `theme.json → …bug_report.decor.enabled=false`.
- Mở xem trên **OneDrive/Excel Online** — Excel desktop hết-license render lỗi (View Only).

## Grow tri thức (demand-driven — đừng grow trước)
Spec mới cần 1 flow để dựng precondition → **có** trong `knowledge/` (approved) thì dùng luôn; **chưa có**
thì **DỪNG, KHÔNG tự đọc code để bù** → `/testcase-systemdoc <flow>` (build-time: GitNexus ra draft →
UI-confirm → approved) → quay lại chạy test. Chỉ viết doc cho flow **thực sự test tới**. Chi tiết: `README.md` §10.

## Maintenance khi 5 repo update
`refresh-gitnexus.sh` (graph tươi — CHỈ graph) → **stale-check `source_hash`** (`/testcase-stale`, hoặc
`python3 .claude/skills-scripts/testcase-evidence/stale_check.py`) → re-confirm CHỈ doc drift.
(refresh KHÔNG tự update knowledge/ — luôn cần nhịp stale-check.) Lệnh đầy đủ + `confidence`: `docs/KNOWLEDGE-STRATEGY.md` §3 GĐ-2.

## Nguyên tắc token
1 session ấm nghĩ xuyên suốt + script sếp (xlsx/Playwright). KHÔNG `claude -p`, KHÔNG viết `.py` phụ trợ.
