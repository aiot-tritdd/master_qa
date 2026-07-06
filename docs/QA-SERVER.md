# QA-Server — Kinh thánh của dự án

> Tài liệu tổng: mọi thứ về con QA-Server này — nó là gì, tồn tại để làm gì,
> nghĩ thế nào, mang tri thức gì, làm ra sao, và lộ trình các phase.
> Đọc file này là hiểu trọn dự án. Đây là tài liệu **sống** — cập nhật khi có thay đổi.

Ngày khởi tạo: 2026-07-06 · Trạng thái: **Phase 1 (MVP) — đang xây**

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
nó là một **QA senior nhân tạo HIỂU NGHIỆP VỤ** của chính hệ thống này,
sâu tới mức xuyên cả 5 repo.

### Oracle problem — sự thật phũ, và là trái tim mọi quyết định
Khi một hành vi thay đổi, **nhìn code không phân biệt được** đó là:
- **BUG** (đổi ngoài ý muốn), hay
- **FEATURE** (cố ý đổi).

Vì "ý định đúng" **không nằm trong code** — nó nằm trong đầu người. Code chỉ biết
nó *đang* làm gì, không biết nó *nên* làm gì. → Nếu test sinh ra **từ code**, nó chỉ
xác nhận "code đang làm gì" (tautology), không bao giờ bắt được lỗi so với ý định.
Đây là lý do toàn bộ kiến trúc phải xoay quanh việc **ghi lại ý định của con người**.

---

## Phần II — WHAT (nó là gì)

**Một câu:** một repo độc lập (repo thứ 6, đứng ngoài 5 repo ThreeSides), một dịch vụ
kiểu QA-senior tự động, hiểu nghiệp vụ xuyên repo, **tự sinh tài liệu sống từ code**
(người duyệt qua UI = nguồn ý định), rồi **tự sinh + chạy test đẻ từ ý định đã duyệt**.

### Nó NÓI ĐƯỢC gì vs KHÔNG hứa được gì
| Nói được (mô tả thực tại) | KHÔNG tự hứa (phán ý định) |
|---|---|
| "Flow này **đang làm** X, Y, Z" ✅ | "X **là SAI**, đáng lẽ phải là W" ❌ (máy tự phán, không người) |

→ Lằn ranh: máy **không** tự làm quan tòa cuối cùng. **Con người gật qua UI** chính là
"quan tòa" (oracle) mình thiếu. Cái UI không phải để đẹp — nó **trám đúng lỗ hổng oracle**.

### Giá trị thật (gọi đúng tên để không bán nhầm)
- ✅ **Đẻ ra tài liệu công ty chưa từng có** — giá trị tức thì.
- ✅ **Lưới chống regression**: "hôm nay khác hôm qua" + "đổi X thì gãy đâu".
- ❌ **KHÔNG** phải "AI tự tìm bug logic đúng-sai". Không spec/không QA → "đúng" chỉ
  đến từ **con người gật**, không phải từ máy.

---

## Phần III — CÁCH NÓ NGHĨ (triết lý cốt lõi)

### 1. Structural vs Semantic
```
STRUCTURAL (facts — sự thật, rút máy móc)     → GitNexus cho sẵn, KHÔNG bịa
   entity, field, route, ai-gọi-ai, call graph
        │ LLM đọc facts + code, SUY DIỄN lên
        ▼
SEMANTIC (ý nghĩa — LLM sinh, dễ sai)          → mình xây, BẮT BUỘC người duyệt
   "flow này nghĩa là gì", "rule là X", "ý định"
```
**Nguyên tắc vàng:** structural làm móng cứng để semantic đứng lên. LLM không đọc bừa
cả repo rồi phán — nó chỉ suy diễn *trên nền facts GitNexus đã trích*.

### 2. Test đẻ từ Ý ĐỊNH, không đẻ từ code
Test **không** sinh từ code (tautology). Test sinh từ **tầng knowledge đã-được-người-duyệt**.
Tại mọi thời điểm có 3 thứ, việc của con QA là phát hiện chúng **lệch nhau** rồi hỏi người:
```
① CODE đang làm gì        (GitNexus / hệ thống thật)
② Ý ĐỊNH đã thống nhất     (knowledge base — người duyệt)   ← test đo theo cái này
③ Ý ĐỊNH MỚI              (khách/mình vừa đổi)
```
| Tình huống | Con QA nói | Ai quyết |
|---|---|---|
| Code đổi, ② không đổi | "hành vi đổi mà intent không đổi — BUG?" | 👤 người |
| Sửa ② (đổi ý), code chưa đổi | "muốn W, code vẫn X — test FAIL: code chưa theo kịp" | → ticket dev |
| Cả 2 đổi cùng | "code khớp intent mới → test pass" ✅ | (ca đẹp) |

→ **Anh không đuổi theo test; test đuổi theo anh.** Đổi ý = sửa bản ghi ý định trước,
test tự chạy theo. Việc người không bỏ được: **giữ bản ghi ý định luôn tươi** — và đó
chính là thứ đáng giá nhất.

### 3. Kỷ luật chống tự-lừa (bài học 2026-07-06)
Đã từng sai vì *đoán cơ chế thay vì trace code* + *confirmation bias*. Nguyên tắc:
- **Trace luồng bằng GitNexus TRƯỚC khi phán cơ chế.**
- Rule LLM sinh ra mặc định `status: draft` + **bắt buộc trỏ `source_symbols`**.
- Một quan sát mâu thuẫn > cả đống quan sát ủng hộ → đuổi theo mâu thuẫn.

---

## Phần IV — KIẾN TRÚC (5 tầng)

```
① NGUỒN        5 repo (đọc code) + stack docker đang chạy (đánh test HTTP)
     │ đọc code                              │ test qua HTTP
     ▼                                       │
② KNOWLEDGE    GitNexus (facts ✅) + living docs md+yaml (intent 🔨) + stitch HTTP 🔨
     │ tra cứu "flow này là gì"              │
     ▼                                       │
③ BỘ NÃO       vòng lặp: WATCH→DETECT→UNDERSTAND→DECIDE→RUN→REPORT (WATCH: phase sau)
     │ "chạy test cho flow X"                ▼
④ TEST         smoke/build · API+DB (xương sống) · E2E Playwright (mỏng)
     │
     ▼
⑤ DASHBOARD    người giám sát: thay đổi nào · business đổi gì · pass/fail · lý do
```
Cái nào CÓ: GitNexus (query/impact/context/detect_changes), stack docker, flow đã trace.
Cái nào XÂY: living docs + intent, stitch cross-repo HTTP, test-gen/run, UI, orchestrator.

---

## Phần V — KNOWLEDGE BASE (nó mang gì trong người)

### 2 lớp (xem Phần III.1) + 6 loại tri thức
| Loại | Ví dụ ThreeSides | Rút từ |
|---|---|---|
| 1. Entity/Domain | Hospital·Branch·Doctor·Bed·Customer·Coupon·Ticket + quan hệ | Rails/Django models + structure.sql |
| 2. Business Flow | "Phát hành vé", "Đặt lịch", "Sync customer" — xuyên repo | call-graph + mối HTTP |
| 3. Business Rule | "Giường VIP cần deposit", "trẻ <6t miễn phí" | code service/handler |
| 4. State Machine | Bed: Available→Reserved→Occupied→Cleaning · Ticket: pending→sent→failed | enum/status + code |
| 5. Permission | Admin/Receptionist/Customer làm được gì | before_action / DRF permissions |
| 6. API Contract | route mỗi service phục vụ + gọi ai | routes.rb / urls.py / axios |

### Cách lưu
- **Markdown + YAML front-matter, trong git** = nguồn sự thật (git log = lịch sử đổi ý).
  **KHÔNG** vector RAG (chưa cần). **KHÔNG** Neo4j/vector DB.
- Mỗi flow/rule = 1 file. Front-matter: `status` (draft→approved→stale), `source_symbols`
  (trỏ GitNexus), `source_hash` (phát hiện lỗi thời).

Ví dụ:
```yaml
---
id: customer-sync
status: draft            # draft (AI) → approved (người gật) → stale (code đổi)
spans_repos: [backend, ticket]
source_symbols:
  - backend:app/models/concerns/threease_ticket_syncable.rb
  - backend:app/jobs/threease_ticket_sync_job.rb#perform
  - ticket:admin_api/data_sync/handlers.py#sync_data
source_hash: <hash các symbol lúc duyệt>
---
# Flow: Sync customer (backend → ticket) ...
```

### Chỗ đau nhất + giữ tươi
- **Cross-repo stitching**: GitNexus 0 auto-link (không parse Rails routes). Phải nối tay
  ở mối HTTP: parse `rails routes` + match URL với axios(pro)/urls.py(ticket).
- **Stale-detection**: code đổi → so `source_hash` cũ↔mới → khác thì gắn `stale` → UI báo review lại.

---

## Phần VI — MVP (Phase 1, mai/mốt build)

### Scope đã chốt
- **1 flow**: customer-sync (backend↔ticket) — đã trace sẵn.
- **Test seam (MVP = hybrid)**: TẠO customer bằng `rails runner` (chắc kèo, vẫn kích hoạt
  callback→sync thật) + ASSERT qua ticket HTTP admin-api + ticket DB thật. Backend không có
  REST create customer đơn giản + auth devise_token_auth rối → full HTTP-as-user để **Phase 2**.
- **LLM**: local `claude` CLI (`claude -p`), bọc trong `qa/llm.py`, cache né rate-limit.
- **Stack**: Python + FastAPI + Jinja + Tailwind. **No DB** (đọc thẳng markdown).
- **Runtime**: local hết. Ghibli-lite (CSS, không tranh vẽ tay).

### Lát dọc — 5 mảnh nối đuôi
```
① EXTRACTOR (qa/extractor.py)  GitNexus facts + code → claude → knowledge/customer-sync.md (draft)
② REVIEW UI (web/)             người đọc/sửa/Approve → status draft→approved → git commit  ← ORACLE
③ TESTGEN   (qa/testgen.py)    đọc doc APPROVED (CẤM đọc code) → tests_generated/test_customer_sync.py
④ RUNNER    (qa/runner.py)     pytest trên stack: login HTTP → tạo customer → chờ/flush outbox → assert ticket
⑤ DASHBOARD (web/)             doc + trạng thái + lần chạy + pass/fail + lý do
```

### Chống flaky (tri thức nghiệp vụ nhét vào runner)
Tạo customer có thể **sync tức thì** (ticket khỏe) HOẶC **rơi outbox** (ticket bận).
→ Runner phải: tạo → **poll/chờ vài giây** (bắt ca direct) → nếu chưa thấy thì **flush outbox**
→ rồi mới assert. Chính tri thức này làm test hết flaky (xem Phần VIII).

### Ranh giới thép
`testgen` **cấm đọc code** — chỉ đọc doc đã approved. Lén đọc code = tautology.

### Demo punchline
- **Phá code → bắt**: đổi `threease_ticket_api_secret` bên backend cho lệch → Run lại → FAIL + lý do.
- **Đổi ý → test đuổi** (nếu kịp): sửa 1 rule trong UI → testgen sinh lại → phơi "code chưa theo kịp".

### MVP KHÔNG làm (để phase sau)
Tầng WATCH · always-on daemon · self-doubt engine · đủ 5 repo · E2E Playwright · Railway · Postgres.

### Cây thư mục repo
```
threease_qa/
├── knowledge/customer-sync.md      nguồn sự thật ý định (git)
├── qa/{llm,extractor,testgen,runner,gitnexus}.py
├── tests_generated/test_customer_sync.py
├── web/{app.py, templates/, static/}   FastAPI + Jinja + Tailwind (Ghibli-lite)
├── docs/QA-SERVER.md               file này
└── .env                            creds test-admin + host các service (KHÔNG commit)
```

---

## Phần VII — ROADMAP & PHASE TRACKER

> Section **sống**: mỗi mảnh xong → tick + ghi "đã làm gì / còn thiếu gì".

| Phase | Tên | Gồm gì | Trạng thái |
|---|---|---|---|
| **0** | Nền móng | GitNexus index 5 repo · stack + data thật · trace flow customer-sync · chốt thiết kế | ✅ XONG |
| **1** | MVP — lát dọc | extractor→review UI→testgen→runner→dashboard · claude CLI · local · Ghibli-lite · no DB | 🎯 đang xây |
| **2** | Nhân rộng knowledge | nhiều flow · đủ 6 loại · cross-repo stitching (parse Rails routes) · stale-detection · (Postgres khi cần) | ⏸ |
| **3** | Tầng WATCH | branch push/merge PR (webhook/poll) · detect_changes vs base_ref · multi-branch | ⏸ |
| **4** | Always-on + Deploy | daemon 24/7 · Railway · xem online | ⏸ |
| **5** | Self-doubt engine | rule adversarial verify · confidence · biết nghi ngờ chính nó | ⏸ |
| **6** | Phủ toàn hệ | đủ 5 repo · E2E Playwright · regression impact đầy đủ · UI Ghibli vẽ tay full | ⏸ |

### Chi tiết Phase 1 (cập nhật khi build)
```
Phase 1 — MVP  [0/5]
  ⬜ extractor.py    — sinh doc nháp
  ⬜ review UI       — approve + git commit
  ⬜ testgen.py      — sinh pytest từ doc approved
  ⬜ runner.py       — login HTTP → tạo → flush → assert
  ⬜ dashboard       — hiện kết quả
```

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
