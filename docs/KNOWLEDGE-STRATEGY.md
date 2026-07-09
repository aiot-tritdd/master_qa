# Chiến lược grow `knowledge/` — Living Business Doc

> Đọc file này để hiểu: `knowledge/` là gì, grow thế nào (ngay bây giờ → dần dần → tương lai),
> maintain ra sao khi 5 repo update liên tục, và đường nâng lên wiki/RAG.
> Ngày: 2026-07-08. Tài liệu **sống** — cập nhật khi cơ chế đổi.

---

## 0. `knowledge/` là gì

`knowledge/` là **trí nhớ dài hạn** của con QA — thứ sống sót qua các phiên. Nó chia theo **quyền lực**:
mẩu tri thức này có được phép trả lời *"kết quả đúng là gì"* không? Đó là ranh giới tách hai thư mục.

### `knowledge/*.md` (thư mục gốc) — **HOW: cách vận hành**
- Trả lời *"bấm gì / vào đâu / xem kết quả ở đâu"*. Ví dụ: *"nút Thanh toán ở tab 会計"*.
- **KHÔNG** phải oracle — nó không nói cái gì đúng/sai. Đúng/sai = **SPEC** đối chiếu **quan sát live**.
- **QA lúc test ĐƯỢC đọc.** An toàn, vì bug sống ở tầng logic (WHAT), không ở tầng nút bấm (HOW):
  dev code sai luật thì *kết quả khi bấm* sai, chứ không dời cái nút đi.
- Gồm: các flow (`pro-open-booking`…), `observation-channels`, `GLOSSARY`, `lessons`, `METHOD`.

### `knowledge/system/*.md` — **WHAT: code đang làm gì**
- Mô tả *cơ chế bên trong*: code làm gì, hành vi ra sao, cái gì đã/chưa build. Ví dụ:
  *"hủy booking thì SC được hoàn"*.
- Tồn tại để **con người hiểu hệ thống** + để soạn tầng HOW nhanh hơn (ở build-time).
- ⛔ **QA lúc test CẤM đọc.** Không phải vì nó sai, mà vì nó **đúng theo code** — đọc nó là gián tiếp
  đọc code → con QA thôi quan sát trung thực, quay ra suy diễn → tautology.

### `knowledge/OPEN-QUESTIONS.md` — **CHƯA BIẾT**
- *"Tra rồi vẫn không đủ căn cứ → hỏi người"*. **QA ĐƯỢC đọc**, vì nó **không phán đúng/sai** —
  nó chỉ nói *"đừng tự tin ở chỗ này"*. Thiếu tầng này, mọi thứ chưa biết bị ép thành "có" (→ **bịa**)
  hoặc "không" (→ điều tra vô hạn). Cùng khái niệm ở tầng test case = **`SPEC-GAP`** (kết quả thứ tư).

> **Tóm:** HOW = *làm sao bấm* (QA đọc) · WHAT = *đúng/sai ra sao* (QA cấm) · CHƯA BIẾT = *chưa chắc, hỏi đi* (QA đọc).

### Cách lưu
Markdown + YAML front-matter, trong git (git log = lịch sử đổi ý). Front-matter:
`id, status(draft→approved→stale), kind, spans_repos, source_symbols, source_hash, ui_confirmed_at,
confidence, verify_by, grown_from`.

> Cùng khái niệm đó ở tầng test case tên là **`SPEC-GAP`** (result thứ tư): *quan sát được, nhưng
> không có căn cứ để chấm*. Xem `docs/MERGE-PLAN.md` §4.

### Fact-confidence (mượn `.claude-tester`)
Mỗi doc khai `confidence:` + `verify_by:`.
⭐ code cứng · 🟢 ổn định · 🟡 đổi theo release · 🔴 có suy luận / chưa xác nhận.

**Vì sao cần, dù đã có `source_hash`** — hai cơ chế bắt hai loại lỗi khác nhau:

| | bắt được | KHÔNG bắt được |
|---|---|---|
| `source_hash` | **code đã đổi** từ lúc duyệt | doc **chưa từng** được xác nhận lần nào |
| `confidence` | doc **chưa chắc ngay từ đầu** | code đổi mà không ai đụng doc |

Một doc `draft` có `source_hash` khớp hoàn hảo vẫn có thể **sai** — hash chỉ nói *"chưa ai đổi code"*,
không nói *"nội dung này đúng"*.

## 1. Hai nguồn tri thức — KHÔNG trộn
| | GitNexus (5 repo index) | UI-confirm (app chạy) |
|---|---|---|
| Cho | **Skeleton + mechanism** (route/flow/symbol) | **Navigation tin cậy** (nút/bước thật) |
| Kết quả | doc `draft` | doc `approved` |
| Lỗ | backend 0 HTTP contract · cross-repo 0 link · Nuxt(reservation/admin) 0 **process** | (đắt: phải drive app) |
→ Graph **tăng tốc**, UI-confirm **chốt**.

### Hai lỗ khác nhau — chỉ MỘT được `CLAUDE.md` trám (đo thật 2026-07-09)

| Lỗ | Ai trám |
|---|---|
| **Cross-repo wiring** — backend 0 HTTP contract, 0 auto-link giữa 5 repo | ✅ **workspace `CLAUDE.md`** §2 (links là HTTP, không phải call-graph) + §8 (sync direct-first / outbox-fallback) |
| **Flow nội bộ admin & reservation** — `processes = 0` | ❌ `CLAUDE.md` **không** trám (chỉ có 1 dòng bảng/repo). → `route_map` + `definitions` (skeleton) → **UI-confirm** |

⚠️ **`processes = 0` ≠ graph rỗng.** Đo thật (`list_repos`, 2026-07-09):

| Repo | processes | nodes | Graph vẫn cho gì |
|---|---:|---:|---|
| backend | 227 | 15 813 | call-chain đầy đủ |
| ticket | 130 | 2 449 | call-chain đầy đủ |
| pro | 116 | 11 729 | call-chain đầy đủ |
| **admin** | **0** | 502 | `route_map` → **20 route + handler** |
| **reservation** | **0** | 634 | `query` → `definitions`: `pages/_branchId/index.vue:bookReservation`, `guest_confirm.vue:submitGuestReservation`, … |

**473 = 227+130+116** (tổng call-chain của 3 repo có process), **không phải** "473 business flow phải viết doc".
`system/OVERVIEW.md` gom chúng thành **8 domain**. Với admin/reservation, graph cho skeleton **mỏng hơn**
(route + file + method, không có call-chain) → phần UI-confirm nặng hơn, chứ **không phải vô dụng**.

## 2. Tool GitNexus → sản phẩm knowledge
| Tool | Cho |
|---|---|
| `route_map({repo,route})` | route/screen nào TỒN TẠI (đã build/chưa) — chính xác nhất cho "đã build?" |
| `gitnexus://repo/{name}/processes` | danh sách business flow (call-chain) + symbol |
| `query({repo:"@threease"})` | 1 domain chạm repo nào (xuyên hệ) |
| `context({name,repo})` | 360° 1 symbol → pinpoint đọc code mechanism |
| `impact` + `source_hash` | blast radius + phát hiện doc lỗi thời |

## 3. Chiến lược grow — 3 giai đoạn

> **Nguyên tắc xuyên suốt: grow theo NHU CẦU, không grow trước.** Không ngồi viết doc cho cả 8 domain
> ngay từ đầu — chỉ viết một flow khi có test thật cần tới nó. Ba giai đoạn = ba thời điểm khác nhau của
> vòng đời: **dựng khung** (GĐ-0) → **lớn dần theo mỗi spec** (GĐ-1) → **giữ tươi khi code đổi** (GĐ-2),
> và một hướng tương lai (GĐ-3).

### GĐ-0 — bootstrap skeleton + cơ chế staleness ✅ **XONG 2026-07-08**
1. ✅ **INDEX tổng** → `knowledge/system/OVERVIEW.md` (8 domain × repo × trạng thái).
2. ✅ **source_hash thật** — `stale_check.py` compute hash các file trong `source_symbols`.
3. ✅ **Lệnh stale-check** `/testcase-stale` — so `source_hash` cũ ↔ mới sau refresh → in doc `stale`.

### GĐ-1 (DẦN DẦN, theo mỗi spec mới) — demand-driven, UI-confirm
- Mỗi spec/TestCase mới → qa-brain cần 1 flow để dựng precondition.
  - Có trong `knowledge/` (approved) → dùng luôn.
  - Chưa có → build-time cartographer (`route_map`/`context` + **UI-confirm**) → doc mới `approved`.
- **Sau release feature** → confirm flow khớp app → `approved`. → knowledge grow **đúng cái thực sự test tới**.
- Doc `draft` (từ skeleton) được **nâng lên `approved`** khi có lần đầu UI-confirm.

### GĐ-2 (MAINTENANCE — 5 repo update liên tục)
```
repo update → refresh-gitnexus.sh (graph tươi)  ← ĐIỀU KIỆN CẦN, chưa đủ
            → stale-check (source_hash cũ↔mới)   ← tìm doc drift
            → re-derive (graph) + re-confirm (UI) CHỈ doc stale → approved lại
```
⚠️ `refresh-gitnexus.sh` **chỉ update graph, KHÔNG update knowledge/**. Phải thêm nhịp stale-check.
✅ **Surgical:** chỉ doc chạm code vừa đổi mới stale (nhờ `source_hash` per-symbol) — không re-scan toàn bộ.
- INDEX/skeleton drift → rẻ (chạy lại route_map). Detail approved drift → cần re-UI-confirm (đắt hơn, ít hơn).

**Lệnh cụ thể** (qua skill `/testcase-stale`, hoặc chạy thẳng `stale_check.py`):
```bash
# 1. Sau khi 5 repo update → SO hash cũ↔hiện tại, in ra doc nào STALE:
python3 .claude/skills-scripts/testcase-evidence/stale_check.py

# 2. Sau khi soạn doc mới HOẶC re-confirm xong doc stale → GHI lại source_hash gốc:
python3 .claude/skills-scripts/testcase-evidence/stale_check.py --update
```
- Lệnh 1 = *đọc-only*, chỉ báo doc nào drift. Lệnh 2 (`--update`) = *ghi* hash vào front-matter từng doc.
- ⚠️ Chỉ `--update` **sau khi đã re-confirm nội dung đúng** — nếu `--update` khi doc còn sai thì bạn vừa
  "đóng dấu" cái sai thành "mới nhất", stale-check hết tác dụng.
- ❗ `confidence` **không có lệnh** — nó là nhãn người tự khai (⭐🟢🟡🔴) trong front-matter, sửa tay.
  (Máy đo được "code đổi chưa" = `source_hash`; "nội dung tin được không" thì người phải khai.)

### GĐ-3 (TƯƠNG LAI) — nâng lên wiki / RAG
- `knowledge/` = markdown (human-readable, git-versioned) = **source of truth bất biến**.
- **Wiki:** render `knowledge/` thành trang duyệt được (sếp từng có "viewer UI / living system doc";
  GitNexus cũng có `gitnexus wiki`). = VIEW trên markdown, không phải viết lại.
- **RAG:** khi doc nhiều → embed vector (AgentDB/vector-search) → agent hỏi "làm sao để X" → retrieve
  đúng flow doc. = INDEX ngữ nghĩa trên markdown, không phải viết lại.
→ Nâng cấp = thêm **view/index** trên cùng nguồn markdown → **không re-author**, không mất công cũ.

## 4. Ranh giới thép (đừng phá khi grow)
1. Doc `knowledge/*.md` = navigation-only (HOW). Oracle = SPEC. Không ghi luật đúng/sai vào doc.
2. Graph-derived = `draft`; chỉ UI-confirm mới `approved`.
3. `source_hash` để biết doc lỗi thời — không tin doc `stale` cho tới khi re-confirm.
4. QA-runtime **mù code**; GitNexus chỉ ở **build-time** (soạn/refresh doc), không phải lúc test.
5. **`grep` không thấy ≠ không tồn tại.** Đã sai 2 lần. Không kết luận được → `OPEN-QUESTIONS.md`,
   **không** ép thành "có" hay "không".
6. **Mỗi loại tri thức có đúng 1 nhà.** Thấy nội dung trùng ở 2 file → gộp về 1, file kia để 1 dòng trỏ sang.
   Sửa quy ước thì sửa **đúng 1 chỗ**; các doc khác chỉ link, không copy nội dung.
7. **Dot-folder chứa tool, không chứa deliverable** *(nhập từ `.claude-knowledge/OUTPUT_LOCATIONS.md` —
   nguồn định nghĩa DUY NHẤT về "output ghi ở đâu"; các README khác chỉ trỏ về đây, không copy)*:

   | Tooling (dot-folder) | Deliverable thật (nơi user mở/xem) |
   |---|---|
   | `.claude/` — skill · commands · scripts | **`wtf-is-this/<TestCase>/`** — `specs.md`, `tcs.json`, `shots/*.png`, `<Tên>.xlsx` |
   | `knowledge/` | không sinh deliverable — chỉ chứa tri thức (đọc, không phải nơi ghi output) |

   **Nguyên tắc:** dot-folder **không bao giờ** chứa dữ liệu công việc thật. Cache kỹ thuật
   (`.state.<target>.json`, `.shots/` dự phòng) nằm **cạnh script**, đã gitignore, **không** leak ra
   folder test hay repo root. Trong vận hành thật, skill LUÔN chỉ định path tường minh
   (`<folder>/shots/...`); default chỉ là lưới an toàn.

## 4b. ⚠️ Lỗ của `source_hash`: STALE DO HARNESS

`stale_check.py` bắt được **code đổi**. Nó **KHÔNG** bắt được **harness đổi**.

Ca thật: `pro-open-booking.md` được UI-confirm 2026-07-07 khi `pw_lib` **thiếu `locale`** → app chạy
tiếng Anh → doc ghi selector `Remove` / `INVOICE`. Ngày 2026-07-09, `pw_lib` set `locale:'ja-JP'`
(đúng, vì spec viết tiếng Nhật) → nhãn UI đổi. Doc **sai**, nhưng `source_hash` **vẫn khớp hoàn hảo**
vì code sản phẩm không đổi một dòng nào.

Tệ hơn: doc đó ghi nguyên văn *"app ở `/en/` = ENGLISH nên tôi đổi keyword sang EN"* — tức phiên đó
**gặp bug harness rồi chép bug vào knowledge** thay vì sửa harness. **Doc navigation có thể đóng băng
một bug của harness thành "sự thật"**, rồi mọi phiên sau kế thừa cái sai đó.

**Ba loại stale — chỉ 1 loại được tự động bắt:**

| Loại | Nguyên nhân | `stale_check.py` bắt được? | Cách bắt |
|---|---|:--:|---|
| **Code stale** | 5 repo đổi | ✅ | `source_hash` |
| **Harness stale** | `pw_lib`/locale/viewport đổi | ❌ | **drive lại** |
| **UI stale** | dev đổi UI mà không đổi file trong `source_symbols` | ❌ | **drive lại** |

→ **Luật:** đổi bất cứ gì trong `.claude/skills-scripts/` mà **ảnh hưởng cách app render**
(locale, viewport, deviceScaleFactor, auth) → **đánh dấu `status: stale` cho MỌI doc `kind: flow`**
và re-UI-confirm. Không tin `source_hash` ở đây — nó mù với loại stale này.

## 5. Trạng thái hiện tại
```
knowledge/                          ← HOW + COVERAGE + registry. QA-runtime ĐỌC ĐƯỢC.
├── OPEN-QUESTIONS.md   [approved] ⭐ 9 câu hỏi mở (OQ-01..09) — "chưa biết, phải hỏi"
├── METHOD.md           [approved] ⭐ COVERAGE: 5 archetype + luật vàng (KHÔNG cấp expect)
├── GLOSSARY.md         [approved] 🟢 thuật ngữ nghiệp vụ (viết report không lộ tên repo)
├── lessons.md          [approved] 🟢 bẫy cơ khí khi drive app (có ngày)
├── observation-channels.md [approved] 🟢 kênh quan sát Pro/ticket-app/ticket-admin
├── pro-open-booking.md     [approved] 🟢 mở booking + cancel/delete/remove (re-confirm ja-JP)
├── ticket-coupon-reports.md[approved] 🟡 route coupon-report — ⚠️ source_symbols tranh chấp (OQ-01)
├── features.md         [draft]    🟡 sổ tay tính năng (HOW) — CHƯA UI-confirm ja-JP
├── playbook.md         [draft]    🟡 công thức thao tác (HOW) — CHƯA UI-confirm ja-JP
└── issue-ticket-pack.md    [draft] 🔴 phát hành gói vé — CHƯA UI-confirm
│
system/                             ← WHAT. BUILD-TIME ONLY. QA-runtime CẤM.
├── OVERVIEW.md      [draft] 8 domain × repo × trạng thái
├── customer-sync.md      [draft]  (NHÀ của ground-truth-sync; workspace CLAUDE.md §8 trỏ về đây)
├── payment-cancel.md     [draft]
├── ticket-issue-sync.md  [draft]
├── coupon-sc.md          [draft]
├── api-endpoints.md      [draft] 🔴 endpoint code-derived, CHƯA gọi thật
├── domain-rules.md       [draft]     vì sao một hành vi LÀ bug (WHAT)
└── ui-theme.md           [draft]     màu/font (chỉ khi test UI)
```
**Còn thiếu (theo `system/OVERVIEW.md`):** domain 6 Booking (🟡 GitNexus được việc) ·
domain 7 Reservation widget (🔴) · domain 8 Admin (🔴). OQ-02 đã đóng (dev URL xác nhận) → 7-8 **hết bị chặn**.
