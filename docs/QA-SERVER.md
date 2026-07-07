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

### 2 nguồn tri thức tách bạch

- **SPEC (oracle)** — `wtf-is-this/<TestCase>/specs.md` (mỗi task). QA đo đúng/sai theo cái này.
- **Living Business Doc (navigation)** — `knowledge/*.md`. *Cách vận hành* (HOW) + kênh quan sát.
  **KHÔNG phải oracle.** Firewall: cấm ghi kết quả kỳ vọng / luật pass-fail.

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
/testcase-systemdoc <flow>   soạn Living Business Doc (build-time, GitNexus + UI-confirm + duyệt)
        │
(dùng skill qa-brain cho 1 folder spec)
   ĐỌC SPEC → VIẾT CASE (mù code) → SEAM (spec + Living Business Doc) → tcs.json + xlsx
        │
/testcase-run    drive UI live → evidence 2 phía → result/actual → build Excel
        │
/testcase-cleanup   dọn dữ liệu test trên dev (prefix AIOTTEST*)
        │  (review ra change/bug)
/testcase-upspecschange → (dev fix) → /testcase-retest (subset)
```

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
