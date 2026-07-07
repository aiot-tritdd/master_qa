# QA-Server — Bộ não QA senior cắm vào pipeline testcase-evidence

> **Loại:** Design spec (brainstorming output) · **Ngày:** 2026-07-07 · **Trạng thái:** chờ duyệt
> **Liên quan:** `docs/QA-SERVER.md` (tầm nhìn gốc) · pipeline `testcase-evidence` của sếp
> (`.claude/commands/testcase-*.md`, `wtf-is-this/`).
> **Nguyên tắc ưu tiên xuyên suốt:** **#1 Spec = oracle** · **#2 Hiểu hệ thống = đầy tớ đi định vị**
> (không bao giờ leo lên thành `expect`).

---

## 1. Mục tiêu & bối cảnh

Sếp đã có một **pipeline QA "test case + evidence" chạy thật** (6 slash-command:
`/specs-md → /testcase-write → /testcase-run → /testcase-cleanup → /testcase-upspecschange →
/testcase-retest`), sinh ra `tcs.json` + `.xlsx` có screenshot evidence — đúng format khách Nhật nhận.
Đã chạy ~40 case thật (folder `wtf-is-this/TestCase_No.10.4`, `10.1~3`, `10.5`).

Pipeline đó là **đôi tay** (thực thi + evidence + giao hàng). Phần **"senior"** — hiểu hệ thống xuyên
5 repo, thiết kế case cross-repo, khoanh retest, dò lỗi thời — hiện **con người làm tay**.

**Dự án này bổ sung phần "senior" đó bằng một bộ não tự động**, cắm vào pipeline có sẵn, **không xây lại đôi tay**.
Kết quả: một **"QA senior tự động"**.

### Không làm gì (để tránh hiểu lầm)
- **Không** extract spec từ code. Spec (`specs.html`) là input **độc lập**, do người/khách chốt.
- **Không** thay `/testcase-run` / evidence / Excel / cleanup / retest của sếp — dùng nguyên.
- **Không** sửa code sản phẩm; chỉ định vị bug.

---

## 2. Danh tính & 2 lằn ranh thép

Con QA = **QA senior tự động**: hiểu hệ thống để **thiết kế case + phân tích impact + dò stale +
đo coverage + định vị bug + xuất evidence**.

**Lằn ranh thép (bất biến):**
1. **Oracle = spec.** Tiêu chí `expect`/pass-fail **chỉ** đến từ spec, **không bao giờ** từ code.
2. **Định vị, không sửa.** Chỉ ra bug gãy ở đâu; **không** sửa code sản phẩm.

**Cấm tuyệt đối:** sinh `expect`/assertion từ code (tautology → test vô dụng).

---

## 3. Kiến trúc (Form: bộ não-thành-skill cắm vào pipeline sếp)

```
specs.html ──/specs-md (của sếp)──▶ specs.md ─┐
                                               ├─▶ [BỘ NÃO: qa/]
   GitNexus @threease (5 knowledge-graph) ─────┘        │
                                                         ├─▶ tcs.json (schema của sếp)
                                                         ├─▶ trace.json (sidecar — mình sở hữu)
                                                         └─▶ system-doc store (SIDE, lớn dần)
                                                         │
   /testcase-run (của sếp: Playwright + API) ────────────┴─▶ evidence (📸 | ⧗ timeline) ─▶ .xlsx
                                                         │
   VIEWER (web/ Next.js hồi sinh, đọc file) ─────────────┘  tài liệu sống + truy vết + coverage + kết quả
```

- **Đọc** `specs.md`, **ghi** `tcs.json` (đúng schema sếp) → `/testcase-run` chạy được ngay.
- **Không đụng** script của sếp (`pw_lib.js`, `pw_api.js`, `build_evidence.py`, `cleanup.js`).
- Truy vết để ở **sidecar `trace.json`** (không nhét vào `tcs.json` để khỏi phá `build_evidence.py`).

---

## 4. Thành phần & interfaces

### 4.1 `/testcase-suggest <folder>` — LÕI (tách 1a → 1b)

Thay việc `/testcase-write` làm tay. Hai module có **tường thép** ở giữa:

**`qa/design.py` — bước 1a (MÙ CODE):**
- `build_cases(spec_md: str) -> list[Case]`
- Đọc **chỉ** `spec_md` → gọi LLM sinh case: `title, screen, pri, pre, steps, expect, spec_section`.
- **RÀNG BUỘC:** module này **không import `qa.gitnexus`**, **không đọc file repo**. `expect` viết xong là **đóng băng**.
- `Case`: `{ id, screen, pri(High|Medium|Low), title, pre, steps, expect, spec_section }`.

**`qa/bind.py` — bước 1b (THẤY CODE):**
- `bind_seams(cases: list[Case]) -> tuple[list[dict], dict]` → trả `(tcs_list, trace)`.
- Với mỗi case: dùng `qa.gitnexus` định vị **seam** (chỗ tạo/chỗ quan sát + loại UI|headless) và
  `source_symbols` + `source_hash`.
- **RÀNG BUỘC:** **cấm sửa** `title`/`expect`/`steps` (assert bằng nhau trước/sau; sai → raise).
- Ghi `tcs.json` (schema sếp; seam mô tả gộp vào `steps`/`note`) + `trace.json` (sidecar).

**Skill orchestrate:** đọc `specs.md` → `design.build_cases` → `bind.bind_seams` → ghi 2 file →
in **coverage report** (spec § nào đã phủ / còn thiếu) → build `.xlsx` bằng script sếp.

### 4.2 `/testcase-impact <folder> <symbol|git-range>` — LÕI
- `qa/impact.py :: impact(folder, changed) -> list[str]` (tc ids).
- Dùng `gitnexus.impact` (upstream/downstream, xuyên 5 repo) + `trace.json` → map symbol đổi → TC chạm seam đó.
- Output dùng cho `/testcase-retest <folder> <tc ids>` của sếp.

### 4.3 `/testcase-stale <folder>` — LÕI
- `qa/stale.py :: check_stale(folder) -> list[StaleFlag]`.
- So `source_hash` trong `trace.json` ↔ hash symbol hiện tại (qua `gitnexus.symbol_hash`).
- Khác → cờ ⚠ → ghi vào changelog `specs.md` + `note` case.

### 4.4 Coverage — trong suggest
- So `spec_section` (các mục ①②③④ / 【A】【B】…) ↔ case đã có → chỉ ra lỗ hổng ("spec nói X, chưa có case").

### 4.5 Viewer (`web/` + `api/` hồi sinh) — LÕI (mặt tiền)
- **FastAPI** (`api/`) đọc file: `system-doc store`, per-folder `tcs.json`/`trace.json`/`shots/`/`.xlsx`.
- **Next.js** (`web/`) hiển thị:
  - **Tài liệu hệ thống sống** (SIDE, xem 4.6) — trang chính, lớn dần.
  - **Đồ thị truy vết** spec ↔ code ↔ test ↔ evidence (từ `trace.json`).
  - **Coverage** theo spec section.
  - **Kết quả + evidence**: PASS/FAIL + 📸 screenshot (UI) / ⧗ timeline dữ liệu (headless).
  - **Nút Approve**: duyệt case (chính) + duyệt spec (khi CHANGE).
- Giải luôn 5 complaint UI cũ (render đẹp, có approve, thấy test/kết quả/evidence, thấy luồng, doc nghiệp-vụ-trước).

### 4.6 Tài liệu hệ thống sống — **SIDE** (phụ phẩm, vắt kiệt 5-graph)
- `qa/systemmap.py :: contribute(flow_id, facts, snippets) -> None`.
- Mỗi lần `bind`(1b) hiểu 1 flow → gom **system-map** vào **doc trung tâm** (host trên viewer), **lớn dần**.
- **3 chốt tin cậy (bắt buộc):**
  1. **Freshness** — mỗi mục gắn `source_hash` + trạng thái ✅/⚠ (tái dùng `stale`).
  2. **Provenance** — mỗi khẳng định link về **symbol GitNexus** (facts structural từ GitNexus; LLM chỉ viết văn).
  3. **Cấu trúc** — gom theo domain/flow/entity, **merge** vào mục cũ (không nối đuôi vô tận).
- **Mô tả "code đang làm gì"** — gắn nhãn rõ, **KHÔNG** phải oracle; bước 1a (design) vẫn **mù** nó.

---

## 5. Data model

### 5.1 `tcs.json` — schema của sếp (giữ nguyên, không pollute)
`meta{project,module,issue,tester,date,env}`, `shots_dir`, `tcs[]` với mỗi tc:
`{ id, screen, pri, result(PASS|FAIL|未実施), title, pre, steps, expect, actual, note, before, after }`.
Bộ não chỉ thêm thông tin human-facing vào `note`/cột Nguồn; **không** thêm khoá lạ.

### 5.2 `trace.json` — sidecar (mình sở hữu, đặt cạnh `tcs.json`)
```json
{
  "flow": "10.4-customer-sync",
  "generated_at": "2026-07-07T…",
  "cases": {
    "TC-01": {
      "spec_section": "①Company",
      "seam": { "type": "ui|headless",
                "create": "Threease Admin /companies → New → name → Save",
                "observe": "Ticket Admin · danh sách Institute (hoặc bảng th_institute)" },
      "source_symbols": ["backend:app/models/institute.rb#…", "ticket:…"],
      "source_hash": "abc123def456"
    }
  }
}
```

---

## 6. Mỗi case một seam (crux A)
`bind`(1b) gán seam mỗi case:
- **UI** (hướng user) → steps UI → `/testcase-run` (Playwright của sếp) → evidence **📸 screenshot**.
- **headless** (cơ chế sync/API, không UI) → steps API/DB → `qa/runner.py` (mình) → evidence **⧗ timeline dữ liệu**.
Cả hai chung 1 `tcs.json`; lúc chạy chọn công cụ theo `seam.type`.

---

## 7. Workflow end-to-end (ví dụ 10.4)

```
0  spec in   specs.html ─/specs-md─▶ specs.md                    [#1]
1a design    specs.md ─▶ cases (expect đóng băng, MÙ CODE)       [#1]
   ── 🧱 tường thép ──
1b bind      cases + @threease ─▶ tcs.json + trace.json          [#2]   └╌ SIDE: góp system-doc
2  approve   viewer: soi truy vết + coverage → gật               [#1]
3  run       /testcase-run (Playwright | runner) ─▶ evidence + .xlsx  [#2]
4  review    FAIL ─▶ /testcase-upspecschange (BUG có ngày) ─▶ dev fix
5  impact    /testcase-impact <symbol> ─▶ [TC bị ảnh hưởng]      [#2]
6  retest    /testcase-retest <tc…> ─▶ .xlsx cập nhật            [#2]
7  stale     /testcase-stale ─▶ cờ ⚠ ─▶ ⟲ quay lại spec [0]      [#2]
```

---

## 8. Tái sử dụng module hiện có

| Có sẵn | Vai mới |
|---|---|
| `qa/gitnexus.py` | engine 5-graph cho `bind`/`impact`/`stale`/`systemmap` (bổ sung `impact()`, `context()`) |
| `qa/llm.py` | LLM wrapper + cache — dùng cho `design`(1a) và văn của `systemmap` |
| `qa/knowledge.py` | model doc/front-matter — tái dùng cho system-doc store |
| `qa/runner.py` | chạy case **headless** (đã có: create + poll ticket + flush) |
| `qa/extractor.py` | **đổi vai** → phần lõi của `bind.py` (1b) |
| `qa/testgen.py` | **đổi vai** → sinh `tcs.json` (thay vì pytest) |
| `api/`, `web/` | hồi sinh làm **viewer** |

---

## 9. Thực thi lằn ranh thép (bằng cấu trúc, không bằng lời hứa)

- **1a mù code:** `qa/design.py` **không** import `qa.gitnexus`; test khẳng định điều này +
  `build_cases` chạy được khi repo không đọc được (chỉ cần `spec_md`).
- **1b không sửa expect:** `bind_seams` assert `case.title/expect/steps` bằng nhau trước/sau; lệch → raise.
- **Cổng người duyệt (bước 2):** kể cả não lỡ over-reach, người vẫn chặn trước khi chạy.

---

## 10. Thứ tự xây (phasing)

1. **`suggest` (1a + 1b)** — lõi, đẻ `tcs.json` + `trace.json`. + coverage.
2. **`impact` + `stale`** — rẻ, ăn `trace.json` đã có.
3. **Viewer + tài liệu sống (SIDE)** — hồi sinh `api/`+`web/`, gom system-doc.

---

## 11. Tích hợp pipeline sếp (hợp đồng không phá vỡ)
- Chỉ **đọc** `specs.md`, **ghi** `tcs.json` (đúng schema) + `trace.json` (file lạ, sếp bỏ qua).
- `specs.html → specs.md`: **tái dùng `/specs-md`** của sếp; không viết parser HTML mới.
- Quy ước dữ liệu test (`AIOT-TEST-*`/`AIOTTEST*`), cleanup, retest: theo đúng quy ước sếp.

---

## 12. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| Não suy `expect` từ code (tautology) | Tách 1a mù-code + assert-không-đổi ở 1b + cổng người duyệt |
| Tài liệu sống mục ruỗng (đẹp mà sai) | 3 chốt: freshness/provenance/cấu trúc |
| GitNexus không map được Rails routes (đã biết) | Dựa `@threease` query + `impact` per-repo; seam có thể do người xác nhận ở bước 2 |
| Phá schema/Excel của sếp | Truy vết ở sidecar; chỉ ghi `note`/cột Nguồn |
| Playwright 4 app chậm/flaky | Case headless dùng `runner` mình; UI-case mới chạy Playwright |

---

## 13. Ngoài phạm vi (Phase sau)
Always-on regression · CI tự động · self-doubt engine · phủ đủ 5 repo tự động ·
tài liệu sống cross-link toàn hệ + sơ đồ vẽ tay.

---

## 14. Tiêu chí hoàn thành (Phase 1)
- `/testcase-suggest <folder>` chạy trên 1 folder thật (vd 10.4) → ra `tcs.json` hợp lệ (mở được bằng
  `/testcase-run`) + `trace.json` + coverage report; `qa/design.py` chứng minh mù-code bằng test.
- `/testcase-impact` trả đúng tập TC cho 1 thay đổi mẫu; `/testcase-stale` cờ đúng khi sửa symbol tham chiếu.
- Viewer hiện: tài liệu sống (≥1 flow), đồ thị truy vết, coverage, kết quả + evidence, nút approve.
- Không file/script nào của sếp bị sửa.
