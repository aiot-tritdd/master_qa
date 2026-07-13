# Vận hành kho tri thức `knowledge/` — cơ khí

> File này là phần **cơ khí**: cách một doc tự khai độ tin, cách grow, cách phát hiện doc cũ, và lệnh
> để làm. **Khái niệm** (3 tầng HOW/WHAT/chưa-biết, 2 pha, vì sao mù code) đã ở
> [`README.md`](../README.md) — file này giả định bạn đã hiểu chúng, không giải thích lại.
> Tài liệu **sống**: có cái mới → sửa tại chỗ, không nối `## Cập nhật ngày…`.

---

## 1. Mỗi doc tự khai lý lịch (front-matter)

Không doc nào được nói *"cứ tin tôi"*. Mỗi file mở đầu bằng YAML khai rõ **từ đâu ra, tin tới đâu,
kiểm lại bằng cách nào**:

```yaml
id: pro-open-booking
status: approved         # draft → approved → stale   (vòng đời, KHÔNG phải nhãn trang trí)
kind: flow               # flow | channels | method | lessons | glossary | registry | system-map
spans_repos: [pro]
source_symbols: ["pro: components/.../ReservationForm.vue"]
source_hash: 0d5d5b2cb5f2af2c   # hash file nguồn LÚC DUYỆT → phát hiện code đã đổi
ui_confirmed_at: 2026-07-07     # đã drive app thật, selector chạy ổn định
confidence: 🟢                   # ⭐ code cứng · 🟢 ổn định · 🟡 đổi theo release · 🔴 chưa xác nhận
verify_by: "Drive lại bằng pw_lib.getPage('pro'); selector đổi → cập nhật + đổi ui_confirmed_at."
grown_from: "0119159:.claude-tester/knowledge/LESSONS.md"   # nếu kế thừa (pin commit vì thư mục đã xoá)
```

### `source_hash` vs `confidence` — hai trường trông giống, bắt hai lỗi khác nhau

| | Bắt được | KHÔNG bắt được |
|---|---|---|
| `source_hash` (cơ khí, tự động) | **code đã đổi** kể từ lúc duyệt | doc **chưa từng** được xác nhận lần nào |
| `confidence` (người tự khai) | doc **chưa chắc ngay từ đầu** | code đổi mà không ai đụng doc |

> Một doc `draft` có `source_hash` khớp hoàn hảo **vẫn có thể sai**. Hash chỉ nói *"chưa ai đổi code"*,
> không nói *"nội dung này đúng"*. Vì thế phải có cả hai — bỏ cái nào cũng thủng một loại lỗi.

`confidence` **không có lệnh** — người sửa tay. `source_hash` có lệnh (§3).

### `status` là vòng đời, không phải nhãn
Một doc chỉ lên `approved` sau khi **drive app thật** (UI-confirm) — tri thức sinh từ code-graph luôn
dừng ở `draft`. Khi code nguồn đổi, `/testcase-stale` đẩy nó về `stale`, và nó **mất quyền được QA đọc**
cho tới khi có người re-confirm.

---

## 2. Hai nguồn tri thức — KHÔNG trộn

| | GitNexus (5 repo index) | UI-confirm (app chạy) |
|---|---|---|
| Cho | **Skeleton + mechanism** (route/flow/symbol) | **Navigation tin cậy** (nút/bước thật) |
| Ra doc | `draft` | `approved` |
| Yếu | backend 0 HTTP contract · cross-repo 0 link · Nuxt(reservation/admin) 0 process | đắt: phải drive app |

→ **Graph tăng tốc, UI-confirm chốt.** Graph-derived = `draft`, chưa đủ tin.

**Ngân sách GitNexus thật** (đo `list_repos`) — `processes = 0` **≠ graph rỗng**:

| Repo | processes | Graph vẫn cho gì |
|---|---:|---|
| backend · ticket · pro | 227 · 130 · 116 | call-chain đầy đủ |
| **admin** · **reservation** | **0** · **0** | `route_map` → 20 route; `query`→`definitions` → màn + method (skeleton mỏng hơn, UI-confirm nặng hơn) |

**473 = 227+130+116** là *tổng call-chain*, **không phải** "473 flow phải viết doc" — `system/OVERVIEW.md`
gom thành **8 domain**. Cross-repo wiring (backend 0 contract) được trám bằng workspace `CLAUDE.md` §2,
không bằng contract registry.

**Tool GitNexus → dùng làm gì** (build-time only): `route_map` = route nào TỒN TẠI ("đã build?" chính
xác nhất) · `context` = 360° 1 symbol → pinpoint đọc code · `query({repo:"@threease"})` = 1 domain chạm
repo nào.

---

## 3. Grow & maintain — cơ khí + lệnh

Vòng lặp grow (demand-driven) và maintain (stale-check) đã mô tả ở [`README.md`](../README.md) §10.
Đây là phần **lệnh + chi tiết**.

**Lệnh stale-check** (qua skill `/testcase-stale`, hoặc chạy thẳng):
```bash
# 1. Sau khi 5 repo update → SO hash cũ↔hiện tại, in ra doc nào STALE (đọc-only):
python3 .claude/skills-scripts/testcase-evidence/stale_check.py

# 2. Sau khi soạn doc mới HOẶC re-confirm xong doc stale → GHI lại source_hash gốc:
python3 .claude/skills-scripts/testcase-evidence/stale_check.py --update
```
⚠️ Chỉ `--update` **sau khi đã re-confirm nội dung đúng** — `--update` khi doc còn sai = "đóng dấu" cái
sai thành mới nhất, stale-check hết tác dụng.

✅ **Surgical:** `source_hash` gắn per-symbol → chỉ doc chạm đúng file vừa đổi mới stale, không quét lại
toàn bộ. INDEX/skeleton drift → rẻ (chạy lại `route_map`). Detail approved drift → cần re-UI-confirm
(đắt hơn, ít hơn).

### ⚠️ `source_hash` mù với STALE DO HARNESS — 3 loại stale, chỉ 1 tự bắt được

`stale_check.py` bắt **code đổi**. Nó **KHÔNG** bắt **harness đổi**. Ca thật: `pro-open-booking.md`
UI-confirm khi `pw_lib` thiếu `locale` → app chạy tiếng Anh → doc ghi selector `Remove`/`INVOICE`. Sau
đó `pw_lib` set `locale:'ja-JP'` (đúng) → nhãn UI đổi → doc **sai**, mà `source_hash` **vẫn khớp** vì
code sản phẩm không đổi dòng nào. (Tệ hơn: phiên đó gặp bug harness rồi *chép bug vào knowledge*.)

| Loại stale | Nguyên nhân | `stale_check.py` bắt? | Cách bắt |
|---|---|:--:|---|
| **Code stale** | 5 repo đổi | ✅ | `source_hash` |
| **Harness stale** | `pw_lib`/locale/viewport đổi | ❌ | **drive lại** |
| **UI stale** | dev đổi UI mà không đổi file trong `source_symbols` | ❌ | **drive lại** |

→ **Luật:** đổi gì trong `.claude/skills-scripts/` mà ảnh hưởng cách app render (locale, viewport, auth)
→ đánh `status: stale` cho **mọi** doc `kind: flow` + re-UI-confirm. Không tin `source_hash` ở đây.

### Tương lai (wiki/RAG)
`knowledge/` = markdown git-versioned = **source of truth bất biến**. Nâng cấp = thêm **view/index** trên
cùng nguồn đó (render `gitnexus wiki`; embed vector cho RAG), **không re-author** — không mất công cũ.

---

## 4. Ba cửa nhập tri thức — ví dụ định tuyến `.claude-tester`

Mọi tri thức đi vào hệ phải trả lời *"nói HOW hay nói WHAT?"* rồi qua đúng một cửa (nguyên tắc ở
[`README.md`](../README.md) §12). Đây là bảng đã soi từng file của hệ sếp — làm mẫu cách phân loại:

| Nguồn | → `knowledge/` (HOW) | → `knowledge/system/` (WHAT) | → `OPEN-QUESTIONS.md` |
|---|---|---|---|
| `METHOD.md` · `PLAYBOOK.md` | **gần như nguyên vẹn** | — | — |
| `LESSONS.md` | 9 mục (Vuetify `data-cy`, dialog 2 nút, `shot()`) | 2 mục "đọc code xác nhận…" | — |
| `SYSTEM.md` | selector, route | bảng endpoint (từ `repository/*.ts`) | — |
| `FEATURES.md` | "vào đâu", "luồng chính", "bẫy thao tác" | — | — |
| `SYNC_MAP.md` | — | §1, §3 (endpoint, handler gaps) | §2 sender Django, §4 |
| `REPORTING.md` | cấu trúc màn, 2 sub-tab, vị trí filter | ⚠️ **toàn bộ "coupon chưa có code"** | 2 điểm chưa rõ |
| `DOMAIN.md` | bảng thuật ngữ → `GLOSSARY.md` | 締め, 回数券, state machine | app mobile bệnh nhân? |
| `PROJECT_MAP.md` | dev URL, basic auth | tech stack | dev URL chưa xác nhận |

`REPORTING.md` bị **xé làm ba**: *"tab 販売 có KPI card, filter ở đâu"* = HOW → nhập · *"coupon chưa
tồn tại trong code"* = WHAT sai → cách ly · *"KPI 消化SC lọc theo kỳ nào?"* = câu hỏi mở → registry.

---

## 5. Ranh giới thép khi grow (đừng phá)

1. `knowledge/*.md` = navigation-only (HOW). Oracle = SPEC. Không ghi luật đúng/sai vào doc.
2. Graph-derived = `draft`; chỉ UI-confirm mới `approved`. Không tin doc `stale` tới khi re-confirm.
3. QA-runtime **mù code**; GitNexus chỉ ở **build-time** (soạn/refresh doc), không phải lúc test.
4. **`grep` không thấy ≠ không tồn tại.** Đã sai 2 lần → không kết luận được thì vào `OPEN-QUESTIONS.md`,
   **không** ép thành "có"/"không".
5. **Mỗi loại tri thức có đúng 1 nhà.** Trùng ở 2 file → gộp về 1, file kia để 1 dòng trỏ sang.
6. **Dot-folder chứa tool, không chứa deliverable** *(nguồn định nghĩa duy nhất về "output ở đâu")*:
   `.claude/` = skill · commands · scripts. Deliverable thật (`specs.md`, `tcs.json`, `shots/`, `.xlsx`)
   ở **`wtf-is-this/<TestCase>/`**. Cache kỹ thuật (`.state.<target>.json`) nằm cạnh script, đã gitignore,
   **không** leak ra folder test.

---

## 6. Trạng thái hiện tại
```
knowledge/                          ← HOW + COVERAGE + registry. QA-runtime ĐỌC ĐƯỢC.
├── OPEN-QUESTIONS.md   [approved] ⭐ 9 câu hỏi mở (OQ-01..09)
├── METHOD.md           [approved] ⭐ COVERAGE: 5 archetype + luật vàng (KHÔNG cấp expect)
├── GLOSSARY.md         [approved] 🟢 thuật ngữ nghiệp vụ (report không lộ tên repo)
├── lessons.md          [approved] 🟢 bẫy cơ khí khi drive app
├── observation-channels.md [approved] 🟢 kênh quan sát Pro/ticket-app/ticket-admin
├── pro-open-booking.md     [approved] 🟢 mở booking + cancel/delete/remove (re-confirm ja-JP)
├── ticket-coupon-reports.md[approved] 🟡 route coupon-report — source_symbols tranh chấp (OQ-01)
├── features.md · playbook.md [draft] 🟡 HOW — CHƯA UI-confirm ja-JP
└── issue-ticket-pack.md    [draft] 🔴 phát hành gói vé — CHƯA UI-confirm
│
system/                             ← WHAT. BUILD-TIME ONLY. QA-runtime CẤM.
├── OVERVIEW.md  [draft] 8 domain × repo × trạng thái
├── customer-sync.md [draft] (NHÀ của ground-truth-sync; workspace CLAUDE.md §8 trỏ về đây)
├── payment-cancel · ticket-issue-sync · coupon-sc  [draft]
├── api-endpoints.md [draft] 🔴 endpoint code-derived, CHƯA gọi thật
├── domain-rules.md  [draft] vì sao một hành vi LÀ bug (WHAT)
└── ui-theme.md      [draft] màu/font (chỉ khi test UI)
```
**Còn thiếu** (theo `system/OVERVIEW.md`): domain 6 Booking (🟡 GitNexus được việc) · 7 Reservation
widget · 8 Admin (🔴). OQ-02 đã đóng (dev URL xác nhận) → 7-8 hết bị chặn.
