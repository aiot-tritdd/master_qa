# QA-Server — vì sao nó được thiết kế như vậy

> Tài liệu **đào sâu**: triết lý, kiến trúc, và bằng chứng.
> Chưa đọc [`README.md`](README.md) thì đọc cái đó trước — file này giả định bạn đã hiểu hệ thống làm gì.
>
> Tài liệu **sống**: có cái mới → **sửa tại chỗ**, không nối `## Cập nhật ngày…`. Lịch sử ở `git log`.

---

## Phần I — WHY (tại sao nó tồn tại)

### Nỗi đau

Hệ thống **ThreeSides** (đặt lịch khám, giường bệnh, vé/coupon) là 5 repo, 4 ngôn ngữ, chạy chung
qua Docker. Vấn đề:

- **Không có tài liệu.** Không spec. Business logic phức tạp, đổi liên tục.
- Nghiệp vụ nằm **trong đầu vài người** — mất người là mất tri thức.
- **Không có QA.** Mỗi lần đổi code không ai biết cái gì gãy.
- Một chức năng thường đi **xuyên 4-5 repo** qua HTTP, không ai nắm trọn luồng.

### Nó KHÔNG phải "AI đi click website"

Rất nhiều tool đã làm chuyện mở browser bấm nút. Con này khác: nó là một **QA senior nhân tạo hiểu
nghiệp vụ** của chính hệ thống này.

### Oracle problem — sự thật phũ, và là trái tim mọi quyết định

Khi một hành vi thay đổi, **nhìn code không phân biệt được** đó là **BUG** (đổi ngoài ý muốn) hay
**FEATURE** (cố ý đổi). Vì "ý định đúng" **không nằm trong code** — nó nằm trong đầu người. Code chỉ
biết nó *đang* làm gì, không biết nó *nên* làm gì.

⇒ Nếu test sinh ra **từ code**, nó chỉ xác nhận "code đang làm gì" (**tautology**), không bao giờ bắt
được lỗi so với ý định.

⇒ **Ý định đúng = SPEC** (do người viết). Toàn bộ kiến trúc xoay quanh việc lấy oracle từ SPEC,
**không** từ code.

---

## Phần II — WHAT (nó là gì)

**Một câu:** một **skill trong Claude Code** (`qa-brain` + bộ command `testcase-*`) biến session này
thành QA senior **thuần black-box**: từ 1 file **SPEC** (oracle) → sinh test → drive app thật bằng
Playwright → quan sát live → chấm điểm kèm evidence (screenshot 2 phía Pro + ticket).
Kiến trúc **skill-based**, chạy per-folder `wtf-is-this/<TestCase>/`. **Không** phải dịch vụ Python.

### Ba thành phần

- **QA-runtime (skill `qa-brain`)** — mù code tuyệt đối. Đọc SPEC + Living Business Doc (navigation)
  → drive UI → quan sát live → report hành vi. Xuất `tcs.json` + `.xlsx`.
- **Build-time (command `/testcase-systemdoc`)** — tầng "người vẽ bản đồ": dùng GitNexus + system-doc
  soạn Living Business Doc (`knowledge/`), bắt buộc UI-confirm + người duyệt. **Đây không phải QA.**
- **Harness cơ khí** (`.claude/skills-scripts/testcase-evidence/`) — `pw_lib.js` (login/getPage đa hệ),
  `pw_api.js` (sniff devise-token), `build_evidence.py` (sinh Excel), `theme.json`, `cleanup.js`.

### Nó nói được gì vs không hứa được gì

| Nói được (mô tả thực tại) | Không tự hứa (phán ý định) |
|---|---|
| "Màn này **đang làm** X, Y, Z" ✅ | "X **là SAI**, đáng lẽ phải là W" — trừ khi có **SPEC** để so ❌ |

⇒ Quan tòa = **SPEC** (ý định người viết) + **quan sát live**. Máy không tự làm quan tòa cuối cùng.

### Giá trị thật

- ✅ **Test evidence công ty chưa từng có** — screenshot 2 phía + PASS/FAIL theo spec.
- ✅ **Lưới chống regression** khi đổi code.
- ❌ **Không** phải "AI tự tìm bug logic" mà không có spec — "đúng" đến từ **SPEC**.

---

## Phần III — Cách nó nghĩ

### 1. Chìa khoá — tách "vận hành" (HOW) khỏi "đúng/sai" (WHAT)

| | **HOW — vận hành** | **WHAT — hành vi** |
|---|---|---|
| Trả lời | nút ở đâu, màn nào, bấm thứ tự nào, xem kết quả ở đâu | bấm xong ra kết quả gì, có đúng luật không |
| Tầng | giao diện | logic nghiệp vụ |
| Là oracle? | ❌ không | ✅ **chính là oracle** |
| Ai cấp? | Living Business Doc (`knowledge/`) | SPEC + quan sát live |

**Bug sống ở tầng WHAT, không ở HOW.** Dev code sai luật → sai *cái xảy ra khi bấm*, chứ không dời nút.
⇒ Navigation gần như **miễn nhiễm bug logic**. Nên Living Business Doc (chỉ chép HOW) có thể derive
từ code ở build-time mà **không** làm QA sai — vì đúng/sai luôn do SPEC + quan sát live, không do doc.

Đây là toàn bộ lý do `knowledge/` được phép tồn tại trong một hệ "mù code".

### 2. Ba tầng tri thức

Tri thức chia theo **quyền lực** (có cấp được `expect` không), không theo chủ đề:

| Tầng | Ở đâu | QA-runtime |
|---|---|:--:|
| **HOW** — bấm gì, xem đâu | `knowledge/*.md` | ✅ |
| **WHAT** — code làm gì, đã/chưa build | `knowledge/system/*.md` | ⛔ **CẤM** |
| **CHƯA BIẾT** — tra rồi vẫn không đủ căn cứ | `knowledge/OPEN-QUESTIONS.md` | ✅ |

Tầng "chưa biết" an toàn vì nó **không phán đúng/sai** — nó chỉ nói *"đừng tự tin ở đây"*. Thiếu nó,
mọi thứ chưa biết bị ép thành "có" (→ **bịa**) hoặc "không" (→ điều tra vô hạn).

*(Vòng đời doc, `source_hash`, 3 loại stale: [`KNOWLEDGE-STRATEGY.md`](KNOWLEDGE-STRATEGY.md))*

### 3. Structural vs Semantic

```
STRUCTURAL (facts — rút máy móc)       → GitNexus, chỉ ở BUILD-TIME
SEMANTIC (ý nghĩa — LLM sinh, dễ sai)  → Living Business Doc, BẮT BUỘC UI-confirm + người duyệt
```

Semantic-doc = **navigation-only**, không đóng vai quan tòa. GitNexus chỉ là nguyên liệu build-time.

### 4. Test đẻ từ Ý ĐỊNH (= SPEC), không đẻ từ code

Tại mọi thời điểm có 3 thứ; việc của QA là phát hiện chúng **lệch nhau**:

```
① CODE đang làm gì      (hệ thống thật — quan sát qua UI, KHÔNG đọc code)
② SPEC = ý định đã chốt (oracle — test đo theo cái này)
③ Ý ĐỊNH MỚI            (spec change)
```

| Tình huống | QA nói | Ai quyết |
|---|---|---|
| Hành vi khác spec | "spec bảo X, màn làm Y → FAIL" | → ticket dev |
| Spec đổi, code chưa | "muốn W, màn vẫn X → FAIL: code chưa theo kịp" | → ticket dev |
| Cả 2 khớp | "màn khớp spec → PASS" ✅ | (ca đẹp) |

### 5. Bốn kết quả, không phải ba — và `SPEC-GAP`

| Kết quả | Nghĩa |
|---|---|
| `PASS` | quan sát khớp spec |
| `FAIL` | quan sát lệch spec (mô tả hành vi + ảnh) |
| `未実施` | **không quan sát được** |
| `SPEC-GAP` | **quan sát được, nhưng SPEC không định nghĩa kỳ vọng** |

`SPEC-GAP` xảy ra khi `knowledge/METHOD.md` bảo *phải có case* mà **SPEC im lặng**.
Ranh giới một dòng, nhầm là phá Tường thép #1:

> `METHOD.md` quyết định **case nào phải tồn tại** (coverage).
> Nó **không bao giờ** quyết định `expect` (oracle).

⇒ Gặp `SPEC-GAP` thì **không bịa `expect`**. Đây là finding **giá trị cao nhất** của QA mù code:
bằng chứng rằng **spec chưa nghĩ tới**.

`SPEC-GAP` ở tầng test case chính là `OPEN-QUESTIONS.md` ở tầng tri thức — cùng một khái niệm:
*"tôi quan sát được, nhưng không có căn cứ để chấm"*.

### 6. Precondition Protocol (dựng tình huống mà không tin code)

1. **Định nghĩa** precondition từ **SPEC** (ô `pre`) — bằng ngôn ngữ nghiệp vụ, không phải code.
2. **Dựng** bằng flow CŨ đã chạy ổn (Living Business Doc) — **không dùng feature MỚI đang test**.
3. **Verify bằng mắt**: quan sát trạng thái thật (Pro + ticket-admin) đối chiếu spec → khớp mới chạy.

Bước 2 là chỗ tinh tế: dựng precondition bằng chính feature đang test thì code sai của nó sẽ làm hỏng
khâu dựng, và ta không phân biệt được *"bug ở feature"* với *"tôi dựng sai từ đầu"*.

---

## Phần IV — Kiến trúc (tầng)

```
① NGUỒN      5 repo + stack đang chạy trên dev (đánh test qua UI/HTTP)
② KNOWLEDGE  SPEC (oracle, per-folder specs.md) + Living Business Doc (navigation, knowledge/)
    │  build-time: GitNexus facts + UI-confirm → Living Business Doc (người duyệt)
③ BỘ NÃO     skill qa-brain: ĐỌC SPEC → VIẾT CASE (mù code) → SEAM → PRECONDITION → RUN → REPORT
④ TEST       Playwright evidence (pw_lib) — drive UI, chụp 2 phía; build Excel
⑤ EVIDENCE   tcs.json + <Folder>.xlsx (PASS/FAIL/未実施/SPEC-GAP + ảnh + lý do hành vi)
```

---

## Phần V — Knowledge base (nó mang gì trong người)

### Ba nguồn tri thức tách bạch

- **SPEC (oracle)** — `wtf-is-this/<TestCase>/specs.md`, mỗi task một file. QA đo đúng/sai theo đây.
- **Living Business Doc (navigation)** — `knowledge/*.md`. *Cách vận hành* (HOW) + kênh quan sát.
  **Không phải oracle.** Firewall: cấm ghi kết quả kỳ vọng / luật pass-fail. `approved` qua UI-confirm.
- **System-map (hiểu business toàn hệ)** — `knowledge/system/*.md`. *"Mô tả code làm gì"* per domain.
  Để **hiểu hệ thống** khi soạn doc — **không phải oracle**, và **QA-runtime cấm đọc**.

### Chỗ đau nhất

**Cross-repo (Pro→backend→ticket)**: GitNexus không parse Rails routes → **0 auto-link** giữa các repo.
Build-time trám bằng workspace `CLAUDE.md` §2 + **UI-confirm**, không bằng contract registry.

*(Chiến lược grow/maintain + 3 loại stale: [`KNOWLEDGE-STRATEGY.md`](KNOWLEDGE-STRATEGY.md))*

---

## Phần VI — Vòng đời hiện tại

```
/specs-md <folder>           spec.html → specs.md format chuẩn
        │
/testcase-systemdoc <flow>   soạn Living Business Doc (build-time: GitNexus + UI-confirm + duyệt)
        │
(dùng skill qa-brain cho 1 folder spec)
   ĐỌC SPEC → VIẾT CASE (mù code) → SEAM (spec + Living Business Doc) → tcs.json + xlsx
        │
/testcase-run       drive UI live → evidence → result/actual → build Excel
        │
/testcase-cleanup   dọn dữ liệu test trên dev (prefix AIOTTEST*)
        │  (review ra change/bug)
/testcase-upspecschange → (dev fix) → /testcase-retest (subset)
```

### Chuẩn evidence (bắt buộc)

- `build_evidence.py` xuất **3 sheet**: **Cover** (SUMMARY COUNTIF) · **Test Cases** (block dọc/case +
  Evidence Before/After ảnh to) · **Checklist** (+ cột **Nguồn / 発生元**).
- **Mỗi case = 1 before + 1 after (2 ảnh)**, **PNG rõ** (không nén JPG). Dùng chung ảnh khi cùng màn.
- Định dạng Excel nằm ở `theme.json` — đổi màu/font **không đụng code**.
- FAIL báo **hành vi + ảnh**, **không** symbol/`file:line`.

### Chống flaky

Thao tác trên Pro sync sang ticket **không tức thì** → chờ vài giây rồi mới quan sát ticket-admin;
chưa thấy thì chờ thêm một nhịp. **Không** đọc DB/code để "chắc".
Chụp ảnh bằng `shot(page, path, readySelector)` — không `waitForTimeout` + screenshot trần.

---

## Phần VII — Ranh giới thép & cây thư mục

QA-runtime **cấm đọc code, cấm GitNexus, cấm `knowledge/system/**`**. Lén đọc code = tautology.
Chỉ đọc SPEC + Living Business Doc approved + `OPEN-QUESTIONS.md`.

> ⚠️ **Hiện tại đây là VĂN BẢN, chưa phải CƠ CHẾ.** Không có gì kỹ thuật chặn một phiên đọc code lúc
> test. Cơ chế thật = PreToolUse hook — **chưa làm**. Xem [`STATE.md`](STATE.md).

```
threease_qa/
├── wtf-is-this/<TestCase>/{specs.md, tcs.json, shots/, <Folder>.xlsx}   # per task (SPEC = oracle)
├── knowledge/            # HOW + OPEN-QUESTIONS (QA đọc được) · system/ = WHAT (cấm)
├── .claude/skills/qa-brain/SKILL.md                # QA-runtime (black-box)
├── .claude/commands/testcase-*.md                  # pipeline + /testcase-systemdoc
├── .claude/skills-scripts/testcase-evidence/       # pw_lib, pw_api, build_evidence, theme, cleanup
└── docs/                 # README (cửa vào) · file này · KNOWLEDGE-STRATEGY · STATE
```

---

## Phần VIII — Roadmap

| Phase | Tên | Trạng thái |
|---|---|---|
| **0** | Nền móng (GitNexus index 5 repo · stack + data thật · trace flow) | ✅ XONG |
| **1 (cũ)** | MVP dịch vụ Python (extractor/testgen/runner + FastAPI + Next.js) | ⛔ **THAY** bằng skill-based |
| **1 (nay)** | Skill-based black-box (qa-brain + testcase-* + Playwright evidence + Excel) | ✅ chạy được |
| **2** | Nhân rộng Living Business Doc · stale-detection tự động · cross-repo stitching | ⏸ |
| **3** | Tầng WATCH (branch/PR webhook · detect_changes vs base_ref) | ⏸ |
| **4** | Always-on + deploy | ⏸ |
| **5** | Self-doubt engine (adversarial verify) | ⏸ |
| **6** | Phủ toàn hệ · viewer đầy đủ | ⏸ |

---

## Phần IX — Bằng chứng đối chứng: code-trace SAI, black-box ĐÚNG

Đây là phần quan trọng nhất của tài liệu. Không phải lý thuyết — hai ca thật, và chúng là **lý do hai
bức tường thép tồn tại**.

### Ca 1 — Coupon report (TestCase-11, 2026-07-08)

Test màn báo cáo Coupon trên Hệ thống Vé, **mù code + mù cả danh sách dev khai**.
Kết quả: **9 PASS / 8 FAIL**. Đối chiếu list dev khai "đã làm / chưa làm" → **khớp 100%, không sai một
dòng** (đến chi tiết *"tab 販売 làm 1 phần: Report ✅ / 過去のCSV ❌"* cũng bắt đúng).

Cùng ngày, một hệ khác dùng phương pháp **đọc code** (`grep -i coupon` trên `th/models/` → **rỗng**)
kết luận nguyên văn: *"`ReportService.get_coupon_metrics()` **CHƯA TỒN TẠI TRONG CODE**"*.

Một tính năng không tồn tại thì **không thể có 9 case PASS**.

### Ca 2 — Guard "vé đã dùng"

- **Code-trace** qua GitNexus → kết luận *"guard chưa build → FAIL"*. **SAI** (Rails index yếu,
  graph không thấy).
- **Black-box** (drive app thật): cancel payment / cancel booking / delete → **chặn đúng**, nguyên văn
  `使用済みチケットが含まれているため、支払キャンセル・削除はできません。` ⇒ guard **đã build, chạy đúng**.
- Còn bắt được **bug thật** mà code-trace không thấy: luồng **Remove** lộ raw i18n key
  `reservations.used_ticket_cannot_remove` thay vì câu tiếng Nhật.

### Kết luận rút ra

> **`grep` không thấy ≠ không tồn tại.** Hai lần, cùng một kiểu sai.
> Code có thể nằm chỗ khác, tên khác, sinh động lúc runtime, hoặc index code-graph yếu.

⇒ **Không code-trace để phán "đã build / chưa build".** Route/skeleton dùng `route_map` (build-time);
đúng/sai dùng **quan sát live vs SPEC**.

Cả hai ca đều là một dạng lỗi nhận thức: **nhầm "cái quan sát được" với "cái tồn tại"**.
Dạng lỗi này đã tái phát lần thứ ba (2026-07-09: *"xoá `.claude-tester/` rồi ⇒ tường thép thành cơ chế"*
— sai, vì lỗ tự-nạp vẫn còn). Nó rất dai. Cảnh giác.

Câu hỏi chưa trả lời được thì đổ vào [`knowledge/OPEN-QUESTIONS.md`](../knowledge/OPEN-QUESTIONS.md),
**không** ép thành "có" hay "không".
