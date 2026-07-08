# Chiến lược grow `knowledge/` — Living Business Doc

> Đọc file này để hiểu: `knowledge/` là gì, grow thế nào (ngay bây giờ → dần dần → tương lai),
> maintain ra sao khi 5 repo update liên tục, và đường nâng lên wiki/RAG.
> Ngày: 2026-07-08. Tài liệu **sống** — cập nhật khi cơ chế đổi.

---

## 0. `knowledge/` là gì (nhắc lại — kẻo lệch)
- Nơi chứa **Living Business Doc** = tri thức **HOW (cách vận hành app)** + **kênh quan sát**.
- **KHÔNG** phải oracle. Đúng/sai = **SPEC** (mỗi TestCase có `specs.md`) đối chiếu **quan sát live**.
  → Doc chỉ trả lời *"bấm gì / vào đâu / xem ở đâu"*, không trả lời *"đúng hay sai"*.
- Lưu **markdown + YAML front-matter, trong git** = source of truth (git log = lịch sử đổi ý).
- Front-matter: `id, status(draft→approved→stale), kind(flow|channels), spans_repos, source_symbols,
  source_hash, ui_confirmed_at, grown_from`.

## 1. Hai nguồn tri thức — KHÔNG trộn
| | GitNexus (5 repo index) | UI-confirm (app chạy) |
|---|---|---|
| Cho | **Skeleton + mechanism** (route/flow/symbol) | **Navigation tin cậy** (nút/bước thật) |
| Kết quả | doc `draft` | doc `approved` |
| Lỗ | §3: backend 0 HTTP contract, cross-repo 0 link, Nuxt(reservation/admin) 0 process | (đắt: phải drive app) |
→ Graph **tăng tốc**, UI-confirm **chốt**. Lỗ cross-repo §3 trám bằng `/Users/tritdd/Work/ThreeSides/CLAUDE.md`.

## 2. Tool GitNexus → sản phẩm knowledge
| Tool | Cho |
|---|---|
| `route_map({repo,route})` | route/screen nào TỒN TẠI (đã build/chưa) — chính xác nhất cho "đã build?" |
| `gitnexus://repo/{name}/processes` | danh sách business flow (call-chain) + symbol |
| `query({repo:"@threease"})` | 1 domain chạm repo nào (xuyên hệ) |
| `context({name,repo})` | 360° 1 symbol → pinpoint đọc code mechanism |
| `impact` + `source_hash` | blast radius + phát hiện doc lỗi thời |

## 3. Chiến lược grow — 3 giai đoạn

### GĐ-0 (NGAY BÂY GIỜ) — bootstrap skeleton + cơ chế staleness
1. **INDEX tổng:** quét `route_map`+`processes` 5 repo → `knowledge/_system-map/INDEX.md`
   = bản đồ domain × flow × route (đã build/chưa). Rẻ, để định hướng. Toàn `draft`.
2. **source_hash thật:** lúc grow doc, compute hash các `source_symbols` (từ GitNexus) → lưu vào doc.
3. **Lệnh stale-check** (`/testcase-stale`, hồi sinh bản gọn): so `source_hash` cũ ↔ mới sau refresh
   → in list doc `stale`.

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

### GĐ-3 (TƯƠNG LAI) — nâng lên wiki / RAG
- `knowledge/` = markdown (human-readable, git-versioned) = **source of truth bất biến**.
- **Wiki:** render `knowledge/` thành trang duyệt được (sếp từng có "viewer UI / living system doc";
  GitNexus cũng có `gitnexus wiki`). = VIEW trên markdown, không phải viết lại.
- **RAG:** khi doc nhiều → embed vector (AgentDB/vector-search) → agent hỏi "làm sao để X" → retrieve
  đúng flow doc. = INDEX ngữ nghĩa trên markdown, không phải viết lại.
→ Nâng cấp = thêm **view/index** trên cùng nguồn markdown → **không re-author**, không mất công cũ.

## 4. Ranh giới thép (đừng phá khi grow)
1. Doc = navigation-only (HOW). Oracle = SPEC. Không ghi luật đúng/sai vào doc.
2. Graph-derived = `draft`; chỉ UI-confirm mới `approved`.
3. `source_hash` để biết doc lỗi thời — không tin doc `stale` cho tới khi re-confirm.
4. QA-runtime **mù code**; GitNexus chỉ ở **build-time** (soạn/refresh doc), không phải lúc test.

## 5. Trạng thái hiện tại (cập nhật khi grow)
```
knowledge/
├── observation-channels.md   [approved] kênh quan sát Pro/ticket-app/ticket-admin
├── pro-open-booking.md        [approved] mở booking + cancel payment/cancel/delete/remove (Pro)
├── ticket-coupon-reports.md   [approved] route coupon-report (GitNexus route_map + UI-confirm)
└── issue-ticket-pack.md       [draft]    phát hành gói vé (chưa UI-confirm đủ)
```
Chưa làm: `_system-map/INDEX.md`, cơ chế `source_hash` thật + lệnh stale-check (GĐ-0).
