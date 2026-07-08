# QA-Server — Kinh thánh của dự án

> Tài liệu tổng: mọi thứ về con QA-Server này — nó là gì, tồn tại để làm gì,
> nghĩ thế nào, mang tri thức gì, làm ra sao, và lộ trình các phase.
> Đọc file này là hiểu trọn dự án. Đây là tài liệu **sống** — cập nhật khi có thay đổi.

Ngày khởi tạo: 2026-07-06 · Cập nhật: 2026-07-07
Trạng thái: **Bản skill-based (Claude Code) — chạy được, đang chuẩn hoá black-box**

---

## Phần I — WHY (tại sao nó tồn tại)

### Nỗi đau

Hệ thống **ThreeSides** (đặt lịch khám bệnh, giường bệnh, vé/coupon) là 5 repo,
4 ngôn ngữ, chạy chung qua Docker. Vấn đề:

- **Không có tài liệu.** Không spec. Business logic phức tạp, đổi liên tục.
- Nghiệp vụ nằm **trong đầu vài người** — mất người là mất tri thức.
- **Không có QA.** Mỗi lần đổi code không ai biết cái gì gãy.
- Một chức năng thường đi **xuyên 4-5 repo** qua HTTP, không ai nắm trọn luồng.

### Nó KHÔNG phải "AI đi click website"

Rất nhiều tool đã làm chuyện mở browser bấm nút. Con này khác:
nó là một **QA senior nhân tạo HIỂU NGHIỆP VỤ** của chính hệ thống này.

### Oracle problem — sự thật phũ, và là trái tim mọi quyết định

Khi một hành vi thay đổi, **nhìn code không phân biệt được** đó là **BUG** (đổi ngoài ý muốn)
hay **FEATURE** (cố ý đổi). Vì "ý định đúng" **không nằm trong code** — nó nằm trong đầu người.
Code chỉ biết nó *đang* làm gì, không biết nó *nên* làm gì. → Nếu test sinh ra **từ code**, nó chỉ
xác nhận "code đang làm gì" (tautology), không bao giờ bắt được lỗi so với ý định.
→ **Ý định đúng = SPEC** (do người viết). Toàn bộ kiến trúc xoay quanh việc lấy oracle từ SPEC,
KHÔNG từ code.

---

## Phần II — WHAT (nó là gì)

**Một câu:** một **skill trong Claude Code** (`qa-brain` + bộ command `testcase-*`) biến session
này thành QA senior **thuần black-box**: từ 1 file **SPEC** (oracle) → sinh test → drive app thật
bằng Playwright → quan sát live → chấm PASS/FAIL kèm evidence (screenshot 2 phía Pro + ticket).
Kiến trúc **skill-based**, chạy per-folder `wtf-is-this/<TestCase>/`. **KHÔNG** phải dịch vụ Python.

### Kiến trúc thực tại (đã chốt)

- **QA-runtime (skill `qa-brain`)**: mù code tuyệt đối. Đọc SPEC + Living Business Doc (navigation)
  → drive UI → quan sát live → report hành vi. Xuất `tcs.json` (schema sếp) + `.xlsx` evidence.
- **Build-time (command `/testcase-systemdoc`)**: tầng "người vẽ bản đồ" — dùng GitNexus + system-docs
  soạn **Living Business Doc** (`knowledge/`), bắt buộc UI-confirm + người duyệt. **Đây KHÔNG phải QA.**
- **Harness cơ khí** (`.claude/skills-scripts/testcase-evidence/`): `pw_lib.js` (login/getPage đa hệ),
  `build_evidence.py` (sinh Excel). Command pipeline: `/testcase-write · run · cleanup · upspecschange · retest`.

### Nó NÓI ĐƯỢC gì vs KHÔNG hứa được gì

| Nói được (mô tả thực tại) | KHÔNG tự hứa (phán ý định) |
| --- | --- |
| "Màn này **đang làm** X, Y, Z" ✅ | "X **là SAI**, đáng lẽ phải là W" — trừ khi có **SPEC** để so ❌ (máy không tự phán) |

→ Quan tòa = **SPEC** (ý định người viết) + **quan sát live**. Máy không tự làm quan tòa cuối cùng.

### Giá trị thật

- ✅ **Test evidence công ty chưa từng có** — screenshot 2 phía + PASS/FAIL theo spec.
- ✅ **Lưới chống regression** khi đổi code.
- ❌ **KHÔNG** phải "AI tự tìm bug logic đúng-sai" mà không có spec — "đúng" đến từ **SPEC**.

---

## Phần III — CÁCH NÓ NGHĨ (triết lý cốt lõi)

### 1. Chìa khoá — tách "LÀM SAO vận hành" (HOW) khỏi "ĐÚNG/SAI" (WHAT)

Hệ thống có 2 loại tri thức, 2 tầng:
- **HOW — vận hành:** nút ở đâu, màn nào, bấm thứ tự gì. Tầng giao diện.
- **WHAT — hành vi:** bấm xong ra kết quả gì, đúng luật không. Tầng logic — **oracle**.

**Bug sống ở tầng WHAT, không ở HOW.** Dev code sai luật → sai *cái xảy ra khi bấm*, không dời nút.
→ Navigation gần như **miễn nhiễm bug logic**. Nên Living Business Doc (chép tầng HOW) có thể derive
từ code (build-time) mà không làm QA sai — vì **đúng/sai luôn do SPEC + quan sát live**, không do doc.

### 2. Structural vs Semantic

```
STRUCTURAL (facts — rút máy móc)          → GitNexus, chỉ ở BUILD-TIME
SEMANTIC (ý nghĩa — LLM sinh, dễ sai)     → Living Business Doc, BẮT BUỘC UI-confirm + người duyệt
```

Semantic-doc = **navigation-only** (không đóng vai quan tòa). GitNexus chỉ là nguyên liệu build-time.

### 3. Test đẻ từ Ý ĐỊNH (= SPEC), không đẻ từ code

Tại mọi thời điểm có 3 thứ, việc QA là phát hiện chúng **lệch nhau**:

```
① CODE đang làm gì        (hệ thống thật — quan sát qua UI, KHÔNG đọc code)
② SPEC = ý định đã chốt   (oracle — test đo theo cái này)
③ Ý ĐỊNH MỚI              (spec change)
```

| Tình huống | QA nói | Ai quyết |
| --- | --- | --- |
| Hành vi khác spec | "spec bảo X, màn làm Y → FAIL" | → ticket dev |
| Spec đổi, code chưa | "muốn W, màn vẫn X — FAIL: code chưa theo kịp" | → ticket dev |
| Cả 2 khớp | "màn khớp spec → PASS" ✅ | (ca đẹp) |

### 4. Precondition Protocol (dựng tình huống mà không tin code)

1. **Định nghĩa** precondition từ **SPEC (ô `pre`)** — nghiệp vụ, không code.
2. **Dựng** bằng flow CŨ đã chạy ổn (Living Business Doc) — **KHÔNG dùng feature MỚI đang test**.
3. **Verify bằng mắt**: quan sát trạng thái thật (Pro + ticket-admin) đối chiếu spec → khớp mới chạy.

---

## Phần IV — KIẾN TRÚC (tầng)

```
① NGUỒN        5 repo + stack đang chạy trên dev (đánh test qua UI/HTTP)
② KNOWLEDGE    SPEC (oracle, per-folder specs.md) + Living Business Doc (navigation, knowledge/)
     │  build-time: GitNexus facts + UI-confirm → Living Business Doc (người duyệt)
③ BỘ NÃO       skill qa-brain: ĐỌC SPEC → VIẾT CASE (mù code) → SEAM → PRECONDITION → RUN → REPORT
④ TEST         Playwright evidence (pw_lib) — drive UI, chụp 2 phía; build Excel
⑤ EVIDENCE     tcs.json + <Folder>.xlsx (PASS/FAIL/未実施 + ảnh + lý do hành vi)
```

CÓ: skill + command pipeline, harness Playwright, GitNexus (chỉ build-time), stack dev + data thật.
XÂY tiếp: nhiều Living Business Doc, stale-detection tự động, viewer.

---

## Phần V — KNOWLEDGE BASE (nó mang gì trong người)

### 3 nguồn tri thức tách bạch
- **SPEC (oracle)** — `wtf-is-this/<TestCase>/specs.md` (mỗi task). QA đo đúng/sai theo cái này.
- **Living Business Doc (navigation)** — `knowledge/*.md`. *Cách vận hành* (HOW) + kênh quan sát.
  **KHÔNG phải oracle.** Firewall: cấm ghi kết quả kỳ vọng / luật pass-fail. Approved qua **UI-confirm**.
- **System-map (hiểu business toàn hệ)** — `knowledge/system/*.md`. *"Mô tả code làm gì"* per domain
  (draft, từ GitNexus + CLAUDE.md). Để **hiểu hệ thống** khi viết case — **KHÔNG phải oracle**, cần người duyệt.

> 📘 **Chiến lược grow/maintain tri thức** ở `docs/KNOWLEDGE-STRATEGY.md` (bootstrap system-map →
> demand-driven per spec → maintenance `source_hash` → tương lai wiki/RAG). ĐỌC file đó để cày tiếp.

### Cách lưu Living Business Doc

Markdown + YAML front-matter, trong git. Mỗi flow/channels = 1 file. Front-matter:
`status` (draft→approved→stale), `source_symbols` + `source_hash` (metadata provenance, QA KHÔNG đọc),
`ui_confirmed_at`. Ví dụ:

```yaml
---
id: issue-ticket-pack
status: draft            # draft (máy) → approved (người + UI-confirm) → stale (code đổi)
kind: flow               # flow (navigation) | channels (observation)
spans_repos: [pro, backend, ticket]
source_symbols: [ ... ]  # metadata — QA KHÔNG đọc
source_hash: <hash>
ui_confirmed_at: 2026-07-07
---
# Flow: Phát hành gói vé (HOW — navigation only)
```

### Chỗ đau nhất + giữ tươi

- **Cross-repo (Pro→backend→ticket)**: GitNexus 0 auto-link (không parse Rails routes) → build-time
  trám bằng `CLAUDE.md` system-docs + **UI-confirm**.
- **Stale-detection**: code đổi → `source_hash` lệch → `status: stale` → re-derive + re-confirm UI + duyệt lại.

---

## Phần VI — Vòng đời hiện tại (skill-based)

### Pipeline (command của sếp)

```
/specs-md <folder>           spec.html → specs.md format chuẩn (đẹp, oracle tốt hơn)
        │
/testcase-systemdoc <flow>   soạn Living Business Doc (build-time, GitNexus + UI-confirm + duyệt)
        │
(dùng skill qa-brain cho 1 folder spec)
   ĐỌC SPEC → VIẾT CASE (mù code) → SEAM (spec + Living Business Doc) → tcs.json + xlsx
        │
/testcase-run    drive UI live → evidence → result/actual → build Excel
        │
/testcase-cleanup   dọn dữ liệu test trên dev (prefix AIOTTEST*)
        │  (review ra change/bug)
/testcase-upspecschange → (dev fix) → /testcase-retest (subset)
```

### Chuẩn evidence (bắt buộc — khớp template sếp)
- `build_evidence.py` xuất **3 sheet**: **Cover** (SUMMARY COUNTIF) · **Test Cases** (block-dọc/case +
  Evidence Before/After ảnh to) · **Checklist** (+ cột **Nguồn / 発生元**).
- **Mỗi case = 1 before + 1 after (2 ảnh)**, **PNG rõ** (KHÔNG nén JPG nhỏ). Dùng chung ảnh khi cùng màn.
- `result` = PASS / FAIL / 未実施. FAIL báo hành vi + ảnh, KHÔNG symbol/file:line.

### Chống flaky (tri thức nghiệp vụ nhét vào runner)

Thao tác trên Pro sync sang ticket **không tức thì** → chờ vài giây rồi mới quan sát ticket-admin;
chưa thấy thì chờ thêm 1 nhịp. **KHÔNG** đọc DB/code để "chắc".

### Ranh giới thép

QA-runtime **cấm đọc code / cấm GitNexus**. Lén đọc code = tautology. Chỉ đọc SPEC + Living Business Doc.

### Cây thư mục repo

```
threease_qa/
├── wtf-is-this/<TestCase>/{specs.md, tcs.json, shots/, <Folder>.xlsx}   # per task (SPEC = oracle)
├── knowledge/{observation-channels.md, <flow>.md}                        # Living Business Doc (navigation)
├── .claude/skills/qa-brain/SKILL.md                                      # QA-runtime (black-box)
├── .claude/commands/testcase-*.md                                        # pipeline + /testcase-systemdoc
├── .claude/skills-scripts/testcase-evidence/{pw_lib.js, build_evidence.py}
├── docs/QA-SERVER.md                                                     # file này
└── account.txt (wtf-is-this/)                                            # creds test các service
```

---

## Phần VII — ROADMAP & PHASE TRACKER

> Section **sống**: mỗi mảnh xong → tick + ghi "đã làm gì / còn thiếu gì".

| Phase | Tên | Trạng thái |
| --- | --- | --- |
| **0** | Nền móng (GitNexus index 5 repo · stack + data thật · trace flow) | ✅ XONG |
| **1 (cũ)** | MVP dịch vụ Python (extractor/testgen/runner + FastAPI + Next.js) | ⛔ **THAY** bằng skill-based |
| **1 (nay)** | Skill-based black-box (qa-brain + testcase-* + Playwright evidence + Excel) | ✅ chạy được; đang chuẩn hoá |
| **2** | Nhân rộng Living Business Doc · stale-detection tự động · cross-repo stitching | ⏸ |
| **3** | Tầng WATCH (branch/PR webhook · detect_changes vs base_ref) | ⏸ |
| **4** | Always-on + deploy | ⏸ |
| **5** | Self-doubt engine (adversarial verify) | ⏸ |
| **6** | Phủ toàn hệ · viewer đầy đủ | ⏸ |

### Chuẩn hoá black-box (đợt 2026-07-07)

Spec + plan: `docs/plans/2026-07-07-qa-brain-blackbox-redesign*.md`. Gỡ GitNexus khỏi vai QA;
thêm HOW-vs-WHAT + Precondition Protocol + Living Business Doc navigation-only + observation channels.

---

## Phần VIII — GROUND TRUTH đã trace (tri thức mẫu, đừng suy ra sai)

**Sync backend ↔ ticket = hai tầng: direct-first, outbox-as-fallback.**

```
create/update model include ThreeaseTicketSyncable
  → after_commit → ThreeaseTicketSyncJob.perform_later  (Sidekiq; worker chạy ngay)
      ├─ ticket reachable → direct HMAC webhook POST /admin-api/sync → "sent directly"  ← INSTANT
      └─ ticket down      → ThreeaseTicketOutboxEvent.create!(pending)                   ← fallback
                            → chỉ được gỡ bởi  rake threease_ticket:flush_outbox
```

- **Đường chuẩn = TỨC THÌ** qua Sidekiq worker. Không cần thao tác tay.
- **Outbox/flush = lưới an toàn** cho ca direct webhook fail (vd ticket đang restart).
  Local docker không có scheduler → event *failed* nằm `pending` tới khi flush tay;
  nhưng create *khỏe mạnh* không hề đụng outbox.
- Reverse (ticket→backend): `th/services/pro_backend_sync.py` + `SyncOutboxEvent`, gỡ bởi
  `python manage.py flush_sync_outbox`. Config: ticket `config/admin_api_settings.py`
  (gitignore; key/secret/`SYNC_START_ID=200000` phải khớp backend `development.rb`).

File chính: `threease_ticket_syncable.rb` (callback) · `threease_ticket_sync_job.rb`
(direct-vs-outbox) · ticket `admin_api/data_sync/handlers.py` (upsert th_customer).

> ⚠️ Phần VIII là **ground truth build-time** (dùng khi soạn Living Business Doc). QA-runtime KHÔNG đọc.

---

## Phần IX — Cập nhật 2026-07-08 (chốt + bài học)

### 1. Tri thức 2 tầng + chiến lược grow
- `knowledge/*.md` = **Living Business Doc (navigation, approved)** cho QA.
- `knowledge/system/*.md` = **hiểu business toàn hệ (draft)** — `OVERVIEW.md` (8 domain) + deep-dive per domain.
- Chiến lược đầy đủ ở **`docs/KNOWLEDGE-STRATEGY.md`**: bootstrap system-map (bây giờ) → grow per spec →
  maintenance → wiki/RAG. **Specs sau này = để TINH CHỈNH/UPDATE business đã map** (không phải build lại từ 0).

### 2. Maintenance khi 5 repo update (đừng quên nhịp 2)
```
repo update → refresh-gitnexus.sh (graph tươi)  ← CHỈ update graph, KHÔNG update knowledge/
            → stale-check (source_hash cũ↔mới)   ← tìm doc drift
            → re-derive + re-confirm CHỈ doc stale
```
Surgical (per `source_hash`). **CẦN LÀM (GĐ-0):** gắn `source_hash` thật + hồi sinh lệnh `/testcase-stale`.

### 3. Access — account report ticket (quan trọng)
- Report ticket (`/reports/`, `/coupon-reports/*`) cần quyền → account **`TESTSEED001/ticket-admin/password123`**
  (env `TK_STAFF=ticket-admin`). Account thường `STAFF001` **KHÔNG** vào report được (nav thiếu tab, /reports redirect home).
- `pw_lib` targets: `getPage('pro' | 'ticket' | 'ticket_admin' | 'reservation' | 'admin')`.

### 4. Bài học VÀNG — code-trace SAI, black-box ĐÚNG (chứng minh triết lý)
- Guard "vé đã dùng": tôi **code-trace** → kết luận "chưa build" → **SAI** (Rails index yếu). **Black-box** thấy
  guard **đã build + chạy đúng** (message JP nguyên văn), và bắt bug thật (Remove lộ raw i18n key).
- Coupon report (TestCase-11): black-box **9 PASS/8 FAIL khớp 100%** list dev khai — mù code vẫn đúng.
- → **KHÔNG code-trace để phán build/chưa-build.** Route/skeleton dùng `route_map` (build-time); đúng/sai
  dùng **quan sát live vs SPEC**. Đây là lý do 2 bức tường thép tồn tại.
