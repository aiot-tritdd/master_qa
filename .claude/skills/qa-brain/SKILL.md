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

## ROUTING TABLE — bước nào nạp gì (đọc đúng, không grep bừa)

| Bước | Nạp | KHÔNG được nạp |
|---|---|---|
| **A. Đọc spec** | `<F>/specs.md` (oracle) | mọi thứ khác |
| **B. Viết case** (`expect`) | **CHỈ spec** + `knowledge/METHOD.md` (coverage) | knowledge/ · code · GitNexus |
| **C. Seam** (create/observe) | `knowledge/*.md` (**approved**) · `observation-channels.md` · `pro-open-booking.md` · `OPEN-QUESTIONS.md` | `knowledge/system/**` · doc `draft` |
| **D. Chạy + chấm** | như C + `lessons.md` · `GLOSSARY.md` (viết report) | `knowledge/system/**` · code · GitNexus |

⚠️ Doc `status: draft` (`playbook.md`, `features.md`, `issue-ticket-pack.md`) = **chưa UI-confirm** →
dùng để **định hướng**, KHÔNG tin selector/nhãn trong đó. Cần dùng thật → UI-confirm rồi `approved`.

### ⛔ DANH SÁCH CẤM ĐỌC Ở QA-RUNTIME
- `knowledge/system/**` — WHAT (mô tả code làm gì). Đọc = gián tiếp đọc code.
- Mọi file trong 5 repo sản phẩm (`threease_backend|ticket|pro|admin|reservation`).
- Mọi tool GitNexus (`query`/`context`/`impact`/`route_map`/…).
- *(`.claude-tester/` đã bị xoá 2026-07-09 — không còn tồn tại để grep trúng. Tra nguồn gốc:
  `git show 0119159:.claude-tester/<path>` — **build-time only**.)*

`knowledge/OPEN-QUESTIONS.md` **ĐƯỢC đọc**: nó không phán đúng/sai, nó nói *"chỗ này chưa ai biết
chắc — đừng suy diễn"*. Đó là thuốc giải cho suy diễn, không phải nguồn của suy diễn.

## Quy trình

### A. ĐỌC SPEC (oracle)
**A0 — Chuẩn hoá oracle TRƯỚC.** Nếu `<F>` chỉ có `specs.html` / file mockup `*.html` (chưa có
`specs.md`): **chạy logic `/specs-md` trước** (`.claude/commands/specs-md.md`) → sinh `<F>/specs.md`
sạch, business-level (giữ nguyên văn tên màn + thông báo JP, bảng state/so sánh, để sẵn `## 4`
changelog rỗng cho `/testcase-upspecschange`). Rồi mới đọc `specs.md` làm oracle.
→ ĐỪNG bỏ bước này rồi đọc thẳng HTML: mất artifact oracle tái dùng được + `/testcase-upspecschange`
mất chỗ bám. (Chỉ đọc thẳng khi KHÔNG thể sinh md — vd spec là ảnh/PDF thuần.)

**A1 — Đọc oracle.** Từ `specs.md` rút ra: màn hình, mỗi nhánh nghiệp vụ (happy / điều kiện-quyền /
boundary / regression / toàn vẹn), và **kỳ vọng đúng/sai nguyên văn theo spec** (giữ tên màn/hàm JP/EN).

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
Harness cơ khí ở `.claude/skills-scripts/testcase-evidence/`: `pw_lib.js`
(`getPage('pro'|'ticket'|'ticket_admin'|'reservation'|'admin')` + **`shot()`**), `pw_api.js`
(`withApi` — sniff devise-token từ request thật, trả `{status, body}`), `build_evidence.py` (xlsx),
`theme.json` (format), `example.tcs.json` (khung 5 archetype), `cleanup.js`.
Require: `const P='<repo>/.claude/skills-scripts/testcase-evidence/'; const {getPage, shot}=require(P+'pw_lib');`
Gọi `/testcase-run <F>`: drive UI theo seam, chụp before/after **2 phía** (Pro + ticket-app/admin) vào
`<F>/shots/` (**PNG rõ**, không nén JPG), điền `result`/`actual`/`before`/`after`, build lại Excel.
- **Chụp BẮT BUỘC bằng `shot(page, path, readySelector)`** — chờ selector đặc trưng + networkidle + đệm.
  KHÔNG `waitForTimeout(6000)` + screenshot trần (dính spinner/màn trắng).
- `actual` bắt đầu bằng `PASS`/`FAIL`/`未実施`/`SPEC-GAP`, mô tả **quan sát được**.
- **FAIL:** `actual` = "spec kỳ vọng …; thao tác trên màn … kết quả …". **KHÔNG** symbol/file:line.
- **Feature chưa build → FAIL**: quan sát "màn không có nút / behavior không xảy ra" + ảnh *absence*.
  Không suy đoán "chưa code" (đó là code-knowledge) — chỉ báo cái **quan sát được**.
- **未実施** CHỈ khi *không quan sát được* (vd không truy cập được kênh).
- **SPEC-GAP** khi *quan sát được* nhưng **spec không định nghĩa kỳ vọng** ở chỗ `METHOD.md` bảo phải
  kiểm → **KHÔNG bịa `expect`**. Đây là finding **giá trị cao nhất** của QA mù code (bằng chứng spec
  chưa nghĩ tới). `actual` = cái quan sát được + "không chấm được → hỏi BA/dev".

> ⚠️ `METHOD.md` quyết định **case nào phải tồn tại** (coverage). Nó **không bao giờ** quyết định
> `expect` (oracle). Nhầm chỗ này = phá Tường thép #1.

## Output
`<F>/tcs.json` + `<F>/<TênFolder>.xlsx` (kèm ảnh evidence). Báo cáo: bảng PASS/FAIL/未実施, KPI
số case, và với FAIL là **mô tả hành vi lệch spec + ảnh** (KHÔNG vị trí code).

## Kết thúc phiên — NHẮC command vòng đời (skill KHÔNG tự chạy)
Skill này chỉ lo **A→D (specs.md → write → run → evidence)**. Các thao tác vòng đời là command RIÊNG,
**cố ý KHÔNG auto** (vài cái phá huỷ / cần người duyệt). User hay không nhớ → **cuối MỖI báo cáo phải
NHẮC** (chỉ nhắc, không tự gõ), theo điều kiện quan sát được trong phiên:

| Điều kiện trong phiên | Nhắc |
|---|---|
| Đã tạo dữ liệu test `AIOT-TEST-*` / `AIOTTEST*` trên dev | `/testcase-cleanup` (khi hết cần đối chiếu evidence) |
| Có FAIL / bug / SPEC-GAP | Ghi `specs.md ## 4` (BUG-xx/CHANGE-xx); spec đổi → `/testcase-upspecschange` |
| Spec vừa có bản mới | `/testcase-upspecschange` → rồi `/testcase-retest` |
| Muốn chạy lại sau khi dev fix | `/testcase-retest` |
| Case ra `未実施`/`SPEC-GAP` vì flow dựng precondition CHƯA có trong `knowledge/` | `/testcase-systemdoc <flow>` (build-time, có người duyệt) |
| 5 repo vừa refresh / nghi `knowledge/` lỗi thời | `/testcase-stale` |

Format nhắc: 1 cụm ngắn cuối báo cáo — **"Bước tiếp có thể cần: …"** — chỉ liệt kê ĐÚNG điều kiện khớp
phiên này + 1 dòng vì sao. KHÔNG liệt kê máy móc cả 6 khi không khớp.

## CHẤT LƯỢNG TEST CASE (BẮT BUỘC — dev + Codex sẽ review lại)

### 1. Đóng vai USER QUẬY PHÁ — không chỉ happy path
Bộ case mà **toàn PASS + toàn happy path = YẾU**. QA giỏi **cố tình phá cho gãy**. Với mỗi feature
PHẢI có nhóm **adversarial** (ngoài happy/permission/boundary/regression/integrity của METHOD):
- **Input rác:** số âm, 0, thập phân, chữ, cực lớn, rỗng, khoảng trắng, emoji.
- **Injection:** `<script>`/`<img onerror>` (XSS), `'; DROP`/`${}` vào MỌI ô text → phải escaped.
- **Race / double-submit:** double-click nút, gửi 2 lần cực nhanh → không nhân đôi/âm.
- **Chống-bypass:** bỏ guard client (xoá `max`/`disabled`, sửa value qua JS) hoặc gọi thẳng API →
  **backend phải chặn** (METHOD golden). Số dư/tồn kho **không được âm**.
- **Tampering / IDOR:** URL với id không tồn tại / của người khác / khác institute → 404/403 sạch,
  **không 500/traceback/lộ dữ liệu**.
- **State ngược đời:** ngày kết thúc < bắt đầu, hủy 2 lần, dùng khi hết hạn, sửa khi đang có người giữ.
- ⚠️ Nhiều đòn quậy spec **im lặng** kỳ vọng → ra **`SPEC-GAP`** (finding giá trị cao nhất). ĐỪNG bịa
  `expect`; ghi cái quan sát được + "hỏi BA/dev". Tìm được `SPEC-GAP`/`FAIL` ở nhóm này = QA đang làm đúng việc.

### 2. Viết để DEV TÁI HIỆN ĐƯỢC BẰNG TAY (reproducibility)
Dev/Codex sẽ mở file đọc + test lại tay. Mỗi case phải **tự đủ** — không bắt người đọc đoán:
- **`pre`:** ghi RÕ precondition cần gì + **dựng thế nào** (account nào + URL login, institute/store nào,
  khách/coupon nào + **giá trị số cụ thể**, dựng bằng flow nào). Không viết "khách có SC" chung chung →
  ghi "khách 222 (院1), 残クレジット合計 = 10,151 SC (đọc ở /customer/222/)".
- **`steps`:** đánh số, mỗi bước 1 hành động cụ thể: **URL đầy đủ + tên ô/nút chính xác + giá trị nhập**.
- **`expect`:** kỳ vọng cụ thể + **trích spec** (mục nào). Spec im lặng → nói rõ "spec không định nghĩa → SPEC-GAP".
- **`actual`:** bắt đầu bằng `PASS/FAIL/未実施/SPEC-GAP` + **số liệu THẬT** (trước→sau, mã HTTP, thông báo
  nguyên văn JP, id bản ghi). Không mô tả mơ hồ.
- **`note`:** seam (`[seam:ui] tạo:… xem:…`) + tên ảnh + cảnh báo data test cần cleanup (id nào).
- **`before`/`after`:** ảnh PNG rõ. **Case có THAO TÁC (create/edit/issue/use/cancel) BẮT BUỘC có `before`** (trạng thái/số liệu TRƯỚC) + `after` (SAU) — thiếu `before` cho case mutation = evidence yếu, dev/Codex không đối chiếu được. Case chỉ QUAN SÁT (nav/list/detail) có thể `before=null` (build_evidence để N/A) nhưng nên chụp điểm-vào làm context nếu có ý nghĩa.
  - ⚠️ **Chụp `before` NGAY trong lúc chạy case** (đừng để lấp sau — trạng thái đổi thì không tái hiện trung thực được, chụp sau = evidence SAI).
  - ⚠️ **`before=null` thì `note` PHẢI ghi rõ lý do N/A** (vd "chỉ quan sát, after là bằng chứng" / "số dư lúc chạy đã đổi nên không tái hiện được"). Không để trống không giải thích — dev/Codex phải hiểu vì sao thiếu.

### 3. Tư duy senior QA — CHỦ ĐỘNG SĂN BUG (không chờ bug tự lộ)
Mặc định: **"hệ chắc chắn có chỗ hỏng, việc của tôi là tìm ra."** Bộ test toàn PASS = chưa đào đủ. Áp
kỹ thuật kiểm thử bài bản để moi bug/gap (không phải bấm random):
- **Boundary Value Analysis:** min−1 / min / min+1 / max−1 / max / max+1 cho MỌI ô số/ngày/độ dài
  (0, âm, 1, đúng-số-dư, số-dư+1, cực lớn, chuỗi 255+ ký tự).
- **Equivalence partitioning:** chia lớp hợp lệ/không hợp lệ, test 1 đại diện mỗi lớp.
- **State-transition:** vòng đời đối tượng (active→used→expired→cancelled…). Thao tác ở trạng thái
  "sai" (dùng coupon đã hết hạn/đã dùng hết; hủy 2 lần; sửa khi đang có người giữ).
- **CRUD / cross-screen consistency:** số liệu 1 thực thể phải khớp giữa các màn (list ↔ detail ↔
  history ↔ thống kê). Σ dòng phải = tổng. Đây là mỏ bug (vd cột hiển thị券面 nhưng tổng tính 残).
- **Concurrency / idempotency:** double-submit, 2 request song song, retry, double-refund → không
  nhân đôi / không âm.
- **Chống-bypass tầng API:** bỏ guard client (xoá max/disabled, POST thẳng) → backend phải chặn.
- **Cross-field / business-rule:** SC vs giá, 開始日 vs 終了日, thuế込/抜/免, quyền × trạng thái.
- **Injection / tampering / IDOR:** XSS/SQL vào ô text; URL id lạ/của người khác/khác institute.
- **Định lượng khi báo:** luôn ghi con số THẬT (trước→sau, Σ vs tổng, mã HTTP) để finding không cãi được.
> Khi bí ý tưởng: tự hỏi *"một user ẩu / một kẻ phá hoại / một ca hiếm sẽ làm gì để làm hệ sai số?"*
> và rà lại checklist trên cho từng màn/trường.

## Ranh giới token
- 1 session ấm nghĩ xuyên suốt — không đẻ subprocess `claude -p`.
- Living Business Doc (đã duyệt) cho sẵn cách drive — không mò UI củ chuối, không đọc code.
- Dựa script sếp cho phần cơ khí (xlsx, Playwright) — không viết lại generator.
