# qa-brain Black-Box Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gỡ code-knowledge (GitNexus) khỏi vai QA-runtime, đưa nó về build-time để sinh Living Business Doc (navigation-only, người-duyệt), và cập nhật toàn bộ tài liệu (SKILL.md, CLAUDE.md, QA-SERVER.md) khớp 100% với kiến trúc black-box mới.

**Architecture:** Tách 2 tầng — *build-time cartographer* (được đụng GitNexus + CLAUDE.md, bắt buộc UI-confirm, người duyệt → `knowledge/*.md`) và *runtime QA* (mù code: đọc SPEC + Living Business Doc → drive UI → quan sát live → FAIL báo hành vi). Oracle = SPEC; doc = HOW (navigation); đúng/sai = SPEC + quan sát.

**Tech Stack:** Claude Code skill (`.claude/skills/qa-brain/SKILL.md`) · commands (`.claude/commands/testcase-*.md`) · Playwright helper (`pw_lib.js`) · Markdown+YAML living docs (`knowledge/`) · Excel generator (KHÔNG đụng).

## Global Constraints

- Tài liệu viết bằng **tiếng Việt** (khớp repo).
- **QA-runtime TUYỆT ĐỐI không** nhắc `GitNexus`, `query`, `context`, `impact`, `source_symbols` — chỉ tầng build-time (cartographer) được nhắc.
- **KHÔNG đụng:** `build_evidence.py`, schema `tcs.json` (12 khoá), các command đã black-box (`testcase-run/cleanup/retest/upspecschange/write`).
- Living Business Doc: **firewall navigation-only** — cấm ghi kết quả kỳ vọng / luật pass-fail.
- Oracle = **SPEC**; Living Business Doc **không phải** oracle.
- Provenance frontmatter giữ schema sếp: `id, status, spans_repos, source_symbols, source_hash` + `ui_confirmed_at`.
- Spec nguồn: `docs/plans/2026-07-07-qa-brain-blackbox-redesign.md`.

---

### Task 1: pw_lib.js — thêm target `ticket_admin` (kênh quan sát ticket)

**Files:**
- Modify: `.claude/skills-scripts/testcase-evidence/pw_lib.js`
- Test: chạy inline smoke (Node) — không tạo file test cố định.

**Interfaces:**
- Consumes: `getPage(target)` hiện có.
- Produces: `getPage('ticket_admin')` → `{ browser, context, page, BASE }` đã đăng nhập Django admin của ticket-dev.

- [ ] **Step 1: Thêm entry `ticket_admin` vào `CFG`**

Trong object `CFG` (sau entry `admin`), thêm:

```js
  ticket_admin: {
    BASE: process.env.TICKET_ADMIN_URL || 'https://ticket-dev.threease.com',
    basic: null,
    django_admin: {
      user: process.env.TK_ADMIN_USER || 'admin',
      pass: process.env.TK_ADMIN_PASS || 'password123',
    },
  },
```

- [ ] **Step 2: Thêm nhánh đăng nhập Django admin trong `getPage`**

Ngay sau khối `if (c.login) { ... }` (login Nuxt), thêm nhánh riêng cho Django admin. Trước khối Nuxt, hoặc thay bằng phân nhánh theo `c.django_admin`:

```js
  // Django admin (ticket-dev) — form login riêng, không phải Nuxt data-cy.
  if (c.django_admin) {
    await page.goto(c.BASE + '/admin/login/', { waitUntil: 'domcontentloaded' });
    if (await page.locator('#id_username').count()) {
      await page.fill('#id_username', c.django_admin.user);
      await page.fill('#id_password', c.django_admin.pass);
      await page.click('input[type=submit]');
      await page.waitForTimeout(3000);
    }
    return { browser, context, page, BASE: c.BASE };
  }
```

- [ ] **Step 3: Smoke test đăng nhập ticket_admin**

Chạy (thư mục scratchpad, KHÔNG lưu vào repo):

```bash
cd .claude/skills-scripts/testcase-evidence
node -e "const {getPage}=require('./pw_lib');(async()=>{const{browser,page,BASE}=await getPage('ticket_admin');await page.waitForTimeout(1500);console.log('URL',page.url());console.log('logged_in',!(await page.locator('#id_username').count()));await browser.close();})().catch(e=>{console.log('ERR',e.message);process.exit(1);})"
```

Expected: in ra `URL https://ticket-dev.threease.com/admin/...` và `logged_in true`.
(Nếu FAIL do selector khác → điều chỉnh `#id_username/#id_password` theo form thật, giữ nguyên cấu trúc nhánh.)

- [ ] **Step 4: Commit**

```bash
git add .claude/skills-scripts/testcase-evidence/pw_lib.js
git commit -m "feat(qa): add ticket_admin observation target to pw_lib"
```

---

### Task 2: `knowledge/observation-channels.md` — ma trận kênh quan sát black-box

**Files:**
- Create: `knowledge/observation-channels.md`

**Interfaces:**
- Produces: doc tham chiếu "quan sát gì → ở UI nào" cho QA-runtime.

- [ ] **Step 1: Tạo file với nội dung đầy đủ**

```markdown
---
id: observation-channels
status: approved
kind: channels
spans_repos: [pro, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: 2026-07-07
---
# Kênh quan sát black-box (WHAT observe → WHERE)

> QA quan sát kết quả bằng **UI đang chạy**, KHÔNG đọc DB/code.

| Quan sát | Kênh (UI) | Login (từ account.txt) |
|---|---|---|
| Booking / hóa đơn / số dư vé (Pro) | https://develop.pro.threease.com | TESTSEED001 / STAFF001 / password123 (basic: threesides/threesides) |
| Gói vé, 使用履歴, trạng thái pack | https://ticket-dev.threease.com/admin | admin / password123 |
| Vé phía khách (ticket app) | https://ticket-dev.threease.com | TESTSEED001 / STAFF001 / password123 |

## Quy tắc sync Pro → ticket
Sau thao tác trên Pro, gói vé sync sang ticket **không tức thì**. Trước khi quan sát
ticket-admin: chờ ~5–8 giây rồi mới đọc. Không thấy → chờ thêm 1 nhịp rồi mới kết luận.
KHÔNG truy cập DB, KHÔNG đọc code để "chắc".

## Cách dùng trong script
`const { getPage } = require('<repo>/.claude/skills-scripts/testcase-evidence/pw_lib');`
`getPage('pro')` · `getPage('ticket_admin')` · `getPage('ticket')`.
```

- [ ] **Step 2: Verify firewall (không có ngôn ngữ kết quả kỳ vọng)**

```bash
grep -nEi "phải|đáng lẽ|kỳ vọng|expect|đúng là|sai nếu" knowledge/observation-channels.md
```

Expected: **không có dòng nào** (doc chỉ mô tả kênh, không phán đúng/sai).

- [ ] **Step 3: Commit**

```bash
git add knowledge/observation-channels.md
git commit -m "docs(qa): add black-box observation channels matrix"
```

---

### Task 3: `knowledge/issue-ticket-pack.md` — Living Business Doc mẫu (flow, navigation-only)

**Files:**
- Create: `knowledge/issue-ticket-pack.md`

**Interfaces:**
- Produces: doc flow mẫu QA đọc để **dựng precondition** "booking đã phát hành gói vé + đã thanh toán". Là khuôn mẫu cho các flow sau.

- [ ] **Step 1: Tạo file với nội dung đầy đủ**

```markdown
---
id: issue-ticket-pack
status: draft
kind: flow
spans_repos: [pro, backend, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: null
---
# Flow: Phát hành gói vé (HOW — navigation only)

> ⚠️ Firewall: doc này chỉ ghi **cách vận hành + nơi quan sát**. KHÔNG ghi kết quả kỳ vọng
> / luật nghiệp vụ (đó là SPEC + quan sát live). `status: draft` cho tới khi UI-confirm + người duyệt.

**Mục tiêu nghiệp vụ:** dựng 1 booking đã phát hành gói vé và đã thanh toán (precondition).

**Các bước UI (Pro — develop.pro.threease.com):**
1. Reservation → tạo booking mới cho 1 customer test (prefix `AIOTTEST*`).
2. Trong booking, thêm **sản phẩm vé** (gói N vé).
3. Lưu booking.
4. Mở **hóa đơn** của booking.
5. Thanh toán (現金) → hoàn tất.

**Nơi quan sát (để verify precondition đã dựng — đối chiếu SPEC, KHÔNG phải để phán đúng/sai):**
- Pro: Customer → số dư vé của khách.
- ticket-admin (ticket-dev/admin): Packs của customer → pack + slips.

**Ghi chú vận hành:** booking KH tương lai không hiện ở calendar mặc định (hôm nay); điều hướng
ngày trước khi thao tác. Dữ liệu test PHẢI prefix `AIOTTEST*` để `/testcase-cleanup` quét được.
```

- [ ] **Step 2: Verify firewall**

```bash
grep -nEi "phải là|đáng lẽ|kỳ vọng|thu hồi|bị chặn|đúng/sai|pass|fail" knowledge/issue-ticket-pack.md
```

Expected: chỉ khớp dòng "⚠️ Firewall" (giải thích), **không** khớp trong phần Các bước/Nơi quan sát. Nếu khớp chỗ khác → sửa lại cho thuần navigation.

- [ ] **Step 3: Commit**

```bash
git add knowledge/issue-ticket-pack.md
git commit -m "docs(qa): add sample living business doc (issue-ticket-pack flow)"
```

---

### Task 4: `.claude/commands/testcase-systemdoc.md` — thủ tục cartographer (build-time)

**Files:**
- Create: `.claude/commands/testcase-systemdoc.md`

**Interfaces:**
- Produces: command build-time soạn/refresh Living Business Doc. Đây là **tầng duy nhất** được đụng GitNexus.

- [ ] **Step 1: Tạo file với nội dung đầy đủ**

```markdown
# /testcase-systemdoc — Soạn Living Business Doc (BUILD-TIME, được đụng code)

> Tầng "người vẽ bản đồ". **Đây KHÔNG phải con QA.** Nó soạn tài liệu navigation cho QA đọc.
> Con QA-runtime (skill qa-brain) TUYỆT ĐỐI không chạy command này lúc test.

## Dùng
`/testcase-systemdoc <flow-id>`  — vd `/testcase-systemdoc issue-ticket-pack`

## Quy trình
1. **Structural (GitNexus):** `query({repo:"@threease", search_query})` + `context` để lấy
   facts: màn Nuxt / endpoint Django / job liên quan flow. GitNexus map tốt Nuxt/Django/jobs;
   luồng xuyên hệ (Pro→backend→ticket) graph **0 link** → trám bằng `CLAUDE.md` system-docs.
2. **Distill → nháp** `knowledge/<flow-id>.md`, `kind: flow` hoặc `channels`, `status: draft`,
   điền `source_symbols` + `source_hash` (metadata provenance).
3. **BẮT BUỘC UI-confirm mỏng:** dùng `pw_lib.getPage(...)` click thật qua flow 1 lần để xác
   nhận các bước/nút đúng app thật. Điền `ui_confirmed_at`.
4. **Người duyệt** → đổi `status: draft → approved`. Chỉ doc `approved` mới cho QA tin.

## FIREWALL (bắt buộc)
Doc CHỈ ghi **cách vận hành (HOW) + nơi quan sát**. **CẤM** ghi kết quả kỳ vọng / luật pass-fail
(đó là SPEC + quan sát live của QA). `source_symbols/source_hash` = metadata, QA không đọc.

## Staleness
Code đổi → `source_hash` lệch → gắn `status: stale` → phải re-derive (bước 1–2) + re-confirm UI
(bước 3) + duyệt lại trước khi QA tin.
```

- [ ] **Step 2: Verify có đủ 4 mục xương sống**

```bash
grep -nE "BUILD-TIME|UI-confirm|FIREWALL|Staleness" .claude/commands/testcase-systemdoc.md
```

Expected: khớp cả 4.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/testcase-systemdoc.md
git commit -m "feat(qa): add /testcase-systemdoc build-time cartographer command"
```

---

### Task 5: Rewrite `.claude/skills/qa-brain/SKILL.md` — vai QA thuần black-box

**Files:**
- Modify (rewrite): `.claude/skills/qa-brain/SKILL.md`

**Interfaces:**
- Consumes: `knowledge/*.md` (Task 2–4), `pw_lib.getPage('ticket_admin')` (Task 1).
- Produces: skill QA-runtime mù code.

- [ ] **Step 1: Rewrite — giữ frontmatter `name: qa-brain`, thay `description` bỏ cụm "5 GitNexus knowledge-graphs" và "locates the bug via the graph"**

Description mới (1 dòng): nêu QA đọc SPEC (oracle) + Living Business Doc (navigation), drive UI, quan sát live, FAIL báo hành vi, không đọc code.

- [ ] **Step 2: Thay "2 BỨC TƯỜNG THÉP"**

Tường #1 giữ nguyên (Oracle = SPEC, mù code khi viết `expect`).
Tường #2 viết lại:

```markdown
2. **QA mù code tuyệt đối — không GitNexus.** Hiểu *cách vận hành* từ Living Business Doc
   (`knowledge/`, đã duyệt). Đúng/sai do **SPEC** đối chiếu **quan sát live** quyết định.
   FAIL báo **hành vi** ("spec bảo X, màn làm Y" + ảnh), **không** symbol/file:line.
```

- [ ] **Step 3: Thêm mục "Chìa khoá: HOW vs WHAT" + bảng 3 vai**

Chép nguyên §1 của spec (`docs/plans/2026-07-07-qa-brain-blackbox-redesign.md`): 2 tầng tri thức, "bug ở WHAT không ở HOW", bảng 3 vai (SPEC / navigation / quan sát live).

- [ ] **Step 4: Thay bước C (BIND SEAM)**

Bỏ toàn bộ `source_symbols`/`query`/`context`. Thay bằng:

```markdown
### C. SEAM — từ SPEC + Living Business Doc (KHÔNG đụng code)
create/observe suy từ **tên màn trong spec** + tra `knowledge/*.md` để biết bước UI cụ thể.
Chưa có flow trong `knowledge/` → dừng, yêu cầu chạy `/testcase-systemdoc <flow>` (build-time)
để soạn + duyệt trước; QA KHÔNG tự đọc code để bù.
Ghi seam vào `note`: `[seam:ui] tạo: … · xem: …`. Không đổi `expect`.
```

- [ ] **Step 5: Thêm "Precondition Protocol" + thay bước D**

Chép §4 spec (3 bước: định-nghĩa-từ-SPEC → dựng-bằng-flow-cũ → verify-bằng-mắt).
Bước D mới:

```markdown
### D. CHẠY + EVIDENCE → REPORT HÀNH VI
Drive UI theo seam, chụp before/after 2 phía (Pro + ticket-admin) vào `<F>/shots/`.
Điền `result` (PASS|FAIL|未実施), `actual` (mô tả **quan sát được**, bắt đầu PASS/FAIL/未実施).
- FAIL: `actual` = "spec kỳ vọng …; thao tác trên màn … kết quả …". KHÔNG symbol/file:line.
- **Feature chưa build → FAIL** (quan sát "không có nút / behavior không xảy ra" + ảnh absence).
- **未実施** chỉ khi *không quan sát được* (vd không truy cập được kênh).
Build lại Excel bằng `build_evidence.py` (không đụng script).
```

- [ ] **Step 6: Xoá mục "Ngữ cảnh 5 knowledge-graph" và mọi tool `query/context/impact`**

- [ ] **Step 7: Verify GitNexus đã sạch khỏi vai QA**

```bash
grep -nEi "gitnexus|query\(|context\(|impact\(|source_symbols|file:line" .claude/skills/qa-brain/SKILL.md
```

Expected: **không có dòng nào** (chỉ được phép nhắc "không dùng GitNexus" dạng phủ định — nếu có, kiểm bằng mắt rằng đó là câu cấm, không phải hướng dẫn dùng).

- [ ] **Step 8: Verify có mặt khái niệm mới**

```bash
grep -nE "HOW|WHAT|Precondition Protocol|Living Business Doc|quan sát live" .claude/skills/qa-brain/SKILL.md
```

Expected: khớp đủ.

- [ ] **Step 9: Commit**

```bash
git add .claude/skills/qa-brain/SKILL.md
git commit -m "refactor(qa): rewrite qa-brain skill to pure black-box (drop GitNexus from QA role)"
```

---

### Task 6: Reconcile `CLAUDE.md` (repo master_qa) — phần qa-brain

**Files:**
- Modify: `/Users/tritdd/Work/ThreeSides/master_qa/CLAUDE.md`

**Interfaces:**
- Consumes: khái niệm từ Task 5.

- [ ] **Step 1: Thay mục "5 knowledge-graph (GitNexus)"**

Thay toàn bộ block GitNexus (query/context/impact/@threease) bằng:

```markdown
## Tri thức QA (black-box) — KHÔNG đọc code
- **Oracle = SPEC** (mỗi TestCase folder có `specs.md`). QA mù code.
- **Living Business Doc** (`knowledge/*.md`, đã duyệt) = *cách vận hành* (HOW/navigation) +
  kênh quan sát. **Không phải oracle.** Đúng/sai = SPEC + quan sát live.
- **Precondition Protocol:** định-nghĩa-từ-SPEC → dựng-bằng-flow-cũ (không dùng feature đang test)
  → verify-bằng-mắt (Pro + ticket-admin).
- GitNexus **chỉ dùng ở build-time** (`/testcase-systemdoc`) để soạn Living Business Doc, có
  người duyệt. QA-runtime KHÔNG đụng GitNexus.
```

- [ ] **Step 2: Verify**

```bash
grep -nE "Oracle = SPEC|Living Business Doc|Precondition Protocol|build-time" CLAUDE.md
grep -nEi "query\(\{repo|context\(\{name|impact\(\{target" CLAUDE.md
```

Expected: nhóm 1 khớp đủ; nhóm 2 (cú pháp tool GitNexus hướng dẫn QA dùng) **không còn**.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(qa): reconcile CLAUDE.md qa-brain section to black-box model"
```

---

### Task 7: Reconcile `docs/QA-SERVER.md` — khớp 100% kiến trúc skill black-box

**Files:**
- Modify: `docs/QA-SERVER.md`

**Interfaces:**
- Consumes: toàn bộ thiết kế (spec §1–§8).

- [ ] **Step 1: Phần II (WHAT) — thay mô tả dịch vụ Python bằng skill**

Sửa "một repo độc lập… tự sinh tài liệu sống từ code…" để nêu đúng bản thực tại:
kiến trúc **skill Claude Code** (`qa-brain` + `.claude/commands/testcase-*` + `pw_lib` Playwright
evidence + `build_evidence.py` Excel), chạy per-folder `wtf-is-this/<TestCase>/`. Tầng
build-time (`/testcase-systemdoc`) soạn Living Business Doc; tầng QA-runtime mù code.

- [ ] **Step 2: Thêm nguyên tắc nền — HOW vs WHAT + Precondition Protocol**

Chèn (Phần III hoặc mục mới): §1 (HOW vs WHAT, bảng 3 vai, ẩn dụ thanh tra) + §4 (Precondition
Protocol) từ spec. Nêu rõ **oracle = SPEC**; Living Business Doc **không phải oracle** (chỉ HOW).

- [ ] **Step 3: Phần IV/V (kiến trúc & knowledge) — sửa vai GitNexus**

Giữ Structural/Semantic, nhưng nói rõ: Semantic-doc = **navigation-only**, người duyệt qua
**UI-confirm**, **không** đóng vai quan tòa. GitNexus **chỉ ở build-time**. Bỏ mô tả
`extractor/testgen/runner.py`, FastAPI, Next.js như "hiện có" (đã xoá) — chuyển sang mô tả skill.

- [ ] **Step 4: Phần VI/VII — cập nhật MVP & Phase tracker**

Ghi Phase 1 (Python MVP) = **đã thay bằng skill-based**; roadmap phản ánh hướng skill hiện tại.
Giữ Phần VIII (Ground truth sync) — vẫn đúng.

- [ ] **Step 5: Verify khớp — không còn mô tả stale như "hiện có"**

```bash
grep -nE "qa-brain|testcase-|pw_lib|Living Business Doc|Precondition Protocol|oracle = SPEC|Oracle = SPEC" docs/QA-SERVER.md
grep -nEi "extractor\.py|testgen\.py|runner\.py|FastAPI|Next\.js|Ghibli" docs/QA-SERVER.md
```

Expected: nhóm 1 khớp đủ. Nhóm 2 nếu còn thì chỉ trong bối cảnh **lịch sử/đã thay** (kiểm mắt: không được mô tả là kiến trúc *hiện hành*).

- [ ] **Step 6: Commit**

```bash
git add docs/QA-SERVER.md
git commit -m "docs(qa): reconcile QA-SERVER.md bible to black-box skill architecture"
```

---

## Self-Review

**Spec coverage (spec §→ task):**
- §1 HOW vs WHAT → Task 5 (SKILL §Chìa khoá), Task 7 (QA-SERVER).
- §2 Kiến trúc 2 tầng → Task 4 (cartographer command), Task 5 (QA runtime), Task 6/7 (docs).
- §3 Living Business Doc (schema/firewall/staleness) → Task 2, 3 (docs mẫu), Task 4 (staleness).
- §4 Precondition Protocol → Task 5 (SKILL), Task 6/7 (docs).
- §5 Observation channels → Task 1 (pw_lib target), Task 2 (matrix).
- §6 Vòng đời skill (bỏ C/D, FAIL hành vi, unbuilt→FAIL) → Task 5.
- §7 Files → tất cả task.
- §8 Reconcile QA-SERVER.md → Task 7.
- §9 YAGNI → Global Constraints (không đụng generator/schema/Python).

**Placeholder scan:** nội dung file mới (Task 2,3,4) đầy đủ; rewrite lớn (Task 5,7) có chỉ dẫn section + prose chốt + grep acceptance. Không TBD/TODO.

**Type consistency:** `getPage('ticket_admin')` (Task 1) dùng ở Task 2 (matrix) + Task 5 (evidence 2 phía) — khớp. Frontmatter fields nhất quán giữa Task 2/3/4.

---

## Execution Handoff

Chọn cách chạy khi bắt đầu thực thi (sau khi sếp gật spec).
