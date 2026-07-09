# Kế hoạch hợp nhất — nâng cấp `threease_qa` bằng những gì học được từ `.claude-tester`

> **Đọc trước:** [`SYSTEM-COMPARISON.md`](SYSTEM-COMPARISON.md) — phân tích hai hệ, lỗ hổng mỗi bên,
> và bằng chứng đối chứng vì sao không được nhập tri thức của sếp nguyên khối.
>
> Ngày: 2026-07-09 · Trạng thái: **Phase 0 ĐÃ XONG + verified**. Phase 1 sẵn sàng chạy.
>
> **Quyết định đã chốt:**
> - **Q1 — `spec-gap`** → **hướng A: `result` thứ tư `SPEC-GAP`.** Đã implement trong `theme.json` +
>   `build_evidence.py` (Cover có dòng `⚠️ SPEC-GAP`, Checklist đếm riêng, warn khi gặp `result` lạ).
> - **Q2 — `.claude-tester/` để đâu** → **không còn là câu hỏi.** Sau khi merge xong sẽ
>   **`git rm -r .claude-tester/`**. Nó tan hoàn toàn vào hệ này. Xem §6.2.

---

## 0. Mục tiêu và nguyên tắc

**Mục tiêu:** giữ nguyên hai bức tường thép (oracle = SPEC · QA mù code), nhưng lấy về **cơ khí**
và **vệ sinh tri thức** của sếp, cộng thêm một trạng thái mà **cả hai hệ hiện đều thiếu**:
chỗ cất *"tôi quan sát được nhưng không đủ căn cứ để chấm"*.

**Nguyên tắc xuyên suốt — một câu:**

> **Nhập CƠ KHÍ và VỆ SINH TRI THỨC của sếp. Không nhập KẾT LUẬN của sếp.**

**Bộ lọc — một câu hỏi, ba cửa.** Mọi mục tri thức đi qua biên giới `.claude-tester/` → `threease_qa/`
phải trả lời được:

> ### *"Cái này nói HOW, nói WHAT, hay nói 'chưa biết'?"*

| Trả lời | Đi đâu | QA-runtime đọc được? |
|---|---|:--:|
| **HOW** — cách drive, nơi quan sát, cách chụp, cách dọn | `knowledge/*.md` | ✅ |
| **WHAT** — kết quả nào đúng, cái gì đã/chưa build | `knowledge/system/*.md` + `source_hash` | ❌ **cấm** |
| **"chưa biết"** — đã tra rồi vẫn không kết luận được | `knowledge/OPEN-QUESTIONS.md` | ✅ |

Cửa thứ ba là cửa mới. Nó an toàn vì nó **không phán đúng/sai** — nó phán *"chưa đủ căn cứ, đi hỏi người"*.

**Thước đo thành công:** sau khi merge, chạy lại TestCase-11 (coupon report) phải vẫn ra **9 PASS / 8 FAIL**
— nghĩa là tri thức mới **không** làm con QA suy diễn thay vì quan sát. Nếu kết quả đổi thành
"FAIL toàn bộ vì chưa build", tức là chất độc đã lọt qua cửa. Đây là **regression test cho chính hệ QA**.

---

## 1. Toàn cảnh 5 phase

| Phase | Tên | Công | Rủi ro triết lý | Trạng thái |
|:--:|---|:--:|:--:|---|
| **0** | Vá lệnh chết (harness) | 2–3h | Không | ✅ **XONG + verified** |
| **1** | Nhập vệ sinh tri thức | ~4h | Thấp | ✅ **XONG** |
| **2** | `METHOD.md` + `spec-gap` | ~4h | Trung bình | ✅ **XONG** (`knowledge/METHOD.md` + `SPEC-GAP` + adapter) — ⛔ chờ live-verify `pw_api` cho archetype #5 |
| **3** | Khử độc `.claude-knowledge/` | 1 ngày | **Cao** | ✅ **XONG** — 11 file qua 3 cửa |
| **4** | Vòng lặp học + **xoá `.claude-tester/`** | ~4h | Trung bình | ✅ **XONG** — archive `0119159` → `git rm` `822d5dd` |

Thứ tự có lý do: **Phase 0 sửa thứ đang âm thầm chạy sai**, ưu tiên cao hơn *chưa đủ mạnh*.
Phase 3 khó nhất và cần bộ lọc (Phase 1) dựng xong mới làm được.

---

## 2. Phase 0 — Vá lệnh chết

> Hiện tại `/testcase-cleanup` **không chạy được lần nào**, và evidence có nguy cơ dính spinner.
> Đây không phải "thiếu tính năng", đây là **hỏng**.

| # | Việc | Nguồn | File tôi sửa |
|---|---|---|---|
| 0.1 | Copy `theme.json`; refactor `build_evidence.py` đọc nó thay vì hardcode palette | `scripts/theme.json` | `build_evidence.py:30-36` |
| 0.2 | Copy `example.tcs.json` (khung 5 archetype) | `scripts/example.tcs.json` | *(file mới)* |
| 0.3 | Copy `cleanup.js`, chỉnh `BRANCH_ID` default | `scripts/cleanup.js` | *(file mới)* |
| 0.4 | Thêm `shot(page, path, readySelector)`; sửa `testcase-run.md` bỏ `waitForTimeout(6000)` | `scripts/pw_lib.js:44` | `pw_lib.js`, `testcase-run.md:33` |
| 0.5 | Viết lại `pw_api.js` theo cơ chế **sniff devise-token** | `scripts/pw_api.js:12-20` | `pw_api.js` |
| 0.6 | Thêm `storageState` cache vào `getPage()` | `scripts/pw_lib.js:17,27,37` | `pw_lib.js` |
| 0.7 | Sửa 7 symlink gãy trong `.claude-tester/knowledge/` | — | `ln -sf` |

**Chi tiết 0.4 — vì sao `shot()` quan trọng.** Hiện `testcase-run.md:33` dạy:
```js
await page.goto(BASE + '/...'); await page.waitForTimeout(6000);
await page.screenshot({ path: '...' });
```
Sáu giây là một con số cầu may. Của sếp:
```js
async function shot(page, path, readySelector, opts = {}) {
  if (readySelector) await page.waitForSelector(readySelector, { timeout: 15000 });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(opts.settle || 500);
  await page.screenshot({ path, ...opts.screenshot });
}
```
Chờ **selector đặc trưng của màn hình** → chờ mạng nghỉ → đệm animation → mới chụp.
Tôi giữ nguyên PNG (không nén JPG như ổng) vì đó là chuẩn giao hàng của tôi.

**Chi tiết 0.5 — vì sao `pw_api` của sếp là black-box thuần.** Tôi đang dùng
`Authorization: Bearer ${API_TOKEN}` — env phải set tay, và **sai cơ chế**: app dùng devise-token
(5 header: `access-token, client, uid, expiry, token-type`). Của sếp:

```js
page.on('request', (r) => {
  if (!headers && r.url().includes(API_HOST) && r.headers()['access-token']) { /* bắt lại */ }
});
await page.goto(BASE + '/reservations');   // mở 1 trang có gọi API
```

Mở một trang thật, **nghe lén header của chính app**, tái sử dụng. Không cần biết code, không cần
token thủ công. Đây là kỹ thuật **hoàn toàn tương thích với black-box** — nó quan sát app, không đọc app.

> ✅ **CỔNG CHẶN ĐÃ MỞ (2026-07-09) — `pw_api` + `shot()` chạy thật trên dev.**
> `GET /permissions/presets` → 200 (7 preset) · id không tồn tại → 404 ⇒ `api.status` dùng được cho
> archetype #5. `shot()` bắt `text=権限設定`, ảnh 2880×1800.
>
> **Live-verify tìm ra 4 bug harness mà syntax-check không thể thấy** (xem `knowledge/lessons.md`):
> thiếu `locale:'ja-JP'` (**gây FAIL SAI** — spec JP không match UI EN) · thiếu `deviceScaleFactor:2` ·
> lưu `storageState` quá sớm (cache rỗng session) · 3 cách sai để hỏi *"đã đăng nhập chưa"*.
> → Bài học: **"syntax ok" ≠ "chạy được"**. Harness phải được drive thật trước khi tin.

**Kết quả sau Phase 0:**
- `/testcase-cleanup` chạy được lần đầu tiên
- Case *"kiểm tầng API / chống bypass"* trở nên khả thi lần đầu tiên
- Evidence hết nguy cơ dính spinner
- Build Excel deterministic (khung 5 archetype là **dữ liệu**, không phải trí nhớ của model)

---

## 3. Phase 1 — Nhập vệ sinh tri thức

| # | Việc | Chi tiết |
|---|---|---|
| 1.1 | **Fact-confidence vào front-matter** | Thêm `confidence: ⭐/🟢/🟡/🔴` + `verify_by: <cách tự kiểm>` vào `knowledge/*.md` |
| 1.2 | **`knowledge/OPEN-QUESTIONS.md`** | Registry mới. Mỗi mục: câu hỏi · đã thử gì · ai trả lời được · block case nào |
| 1.3 | **Routing table** | Bảng tường minh trong `SKILL.md`: bước A/B/C/D nạp doc nào |
| 1.4 | **Checklist "Before final"** | Nhập vào 5 command |
| 1.5 | **Luật "1 tri thức = 1 nhà"** | Thêm vào `KNOWLEDGE-STRATEGY.md` |
| 1.6 | **`knowledge/GLOSSARY.md`** | Bảng thuật ngữ business từ `DOMAIN.md:7-14` |

**1.1 — vì sao `confidence` không thừa dù đã có `source_hash`.** Hai cơ chế bắt hai loại lỗi khác nhau:

| | bắt được gì | không bắt được gì |
|---|---|---|
| `source_hash` (của tôi) | **code đã đổi** kể từ lúc duyệt | doc **chưa từng** được xác nhận lần nào |
| `confidence` (của sếp) | doc **chưa chắc** ngay từ đầu | code đổi mà không ai đụng doc |

Một doc `draft` với `source_hash` khớp hoàn hảo vẫn có thể **sai** — vì nó chưa bao giờ được UI-confirm.
Hash chỉ nói *"chưa ai đổi code"*, không nói *"nội dung này đúng"*. Ghép cả hai mới đủ.

**1.2 — `OPEN-QUESTIONS.md`, món quý nhất.** Nhập nguyên tinh thần `SYNC_MAP.md §2` của sếp:

> *"Đây là khoảng trống **thông tin**, không phải khoảng trống **code**. CẦN HỎI DEV thay vì tự kết luận."*

Format đề xuất:
```markdown
## OQ-01 — Sender phía Django cho sync ngược đã triển khai chưa?
- **Đã thử:** grep `requests.post|httpx.post` + 13 tên event trong `threease_ticket/` → rỗng
- **Không kết luận được vì:** có thể nằm chỗ khác / qua Celery / chưa làm. Grep-không-thấy ≠ không tồn tại
- **Ai trả lời được:** dev backend
- **Block case nào:** mọi case đối chiếu số dư vé 2 phía
- **Trạng thái:** 🔴 chưa hỏi
```

QA-runtime **được đọc** file này. Nó không phán đúng/sai — nó chỉ nói *"chỗ này chưa ai biết,
đừng tự tin"*. Đó chính là thứ giải **L3**.

**1.4 — checklist "Before final".** Giữ nguyên câu của sếp:

> *"Có đọc source code không? **Nếu có, vì sao?**"*

Với hệ của sếp, đáp án có thể là "có, vì knowledge thiếu". Với hệ của tôi ở QA-runtime,
**đáp án đúng luôn là KHÔNG**. Nên cùng một câu hỏi biến thành **tripwire tự kiểm** — rất rẻ,
và nó ép model tự khai nếu đã lỡ phá tường.

---

## 4. Phase 2 — `METHOD.md` + `spec-gap`

> Hai việc này **phải làm cùng lúc**. Làm một cái thôi là hỏng — lý do ở dưới.

`METHOD.md` là file quý nhất trong 4 file tester-only của sếp, và nó **code-blind sẵn**:
5 archetype + "luật vàng" rút từ bug thật (toàn vẹn dữ liệu sau hủy/xóa · chống bypass tầng API ·
state-transition · permission matrix · negative).

**Nhưng có bẫy.** Luật này:

> *"Với mọi thao tác cancel/delete/refund, PHẢI kiểm dữ liệu phái sinh được hoàn/thu hồi đúng."*

Nếu spec **im lặng** về chuyện đó, `expect` lấy ở đâu? Lấy từ `METHOD.md` = **phá Tường 1**
(oracle không còn là spec).

### Adapter — luật một dòng

> `METHOD.md` quyết định **case nào phải tồn tại** (coverage).
> Nó **không bao giờ** quyết định `expect` (oracle).
> Spec im lặng ở chỗ METHOD bảo phải có case → **không bịa `expect`** → ghi nhận một **`spec-gap`**.

Vẽ ra:

```
METHOD.md: "cancel/refund PHẢI có case kiểm dữ liệu phái sinh"
                          │
                          ▼
        Spec có nói vé phải thu hồi không?
                    │              │
                  CÓ              KHÔNG
                    │              │
                    ▼              ▼
        expect ← SPEC        ⚠️ SPEC-GAP
        chạy, chấm PASS/FAIL  "METHOD bảo phải kiểm; spec không định nghĩa
                               kỳ vọng. Quan sát được: vé vẫn còn 100 slip.
                               Không chấm được. → hỏi BA/dev."
```

**Vì sao `spec-gap` trở thành bắt buộc, không còn là tuỳ chọn:** nhập `METHOD.md` mà **không** có
chỗ đổ spec-gap thì METHOD sẽ **ép con QA bịa `expect`** để lấp chỗ trống. Tường 1 sập ngay lập tức.
Nên hai việc này đi liền.

**Và `spec-gap` chính là finding có giá trị cao nhất của một con QA mù code** — nó là bằng chứng
rằng **spec chưa nghĩ tới**, thứ mà không có test tự động nào khác tìm ra được. Chôn nó vào một cột
phụ là phí.

→ **Cần chốt Q1 (§7) trước khi code phase này.**

---

## 5. Phase 3 — Khử độc `.claude-knowledge/`

> Phase khó nhất. **Không copy file nào.** Phân loại **từng mục** rồi định tuyến.

```
.claude-knowledge/<FILE>.md
   │
   ├─ mục nói HOW ────────► knowledge/*.md        [QA-runtime đọc được]
   │                        BẮT BUỘC: UI-confirm bằng Playwright trước khi status: approved
   │
   ├─ mục nói WHAT ───────► knowledge/system/*.md [build-time ONLY, QA-runtime CẤM]
   │                        BẮT BUỘC: source_symbols + source_hash
   │
   └─ mục "chưa biết" ────► knowledge/OPEN-QUESTIONS.md   [QA-runtime đọc được]
```

Bảng định tuyến đầy đủ nằm ở [`SYSTEM-COMPARISON.md` Phần VI](SYSTEM-COMPARISON.md). Tóm tắt khối lượng:

| Nguồn | HOW | WHAT | Open-Q |
|---|:--:|:--:|:--:|
| `METHOD.md` | **toàn bộ** | — | — |
| `PLAYBOOK.md` | **gần toàn bộ** | — | — |
| `LESSONS.md` (11 mục) | 9 | 2 | — |
| `FEATURES.md` | phần lớn | — | — |
| `SYSTEM.md` | selector, route | bảng endpoint | — |
| `SYNC_MAP.md` | — | §1, §3 | §2, §4 (3 câu) |
| `REPORTING.md` | cấu trúc màn | ⚠️ **"coupon chưa có code"** | 2 điểm chưa rõ |
| `DOMAIN.md` | → `GLOSSARY.md` | 締め, 回数券, state machine | 1 |
| `PROJECT_MAP.md` | dev URL, basic auth | tech stack | 3 dev URL |
| `UI_UX.md` | — | màu/font | — |

**Ví dụ xé một file — `REPORTING.md` tách làm ba:**

| Đoạn | Loại | Đi đâu |
|---|---|---|
| *"tab 販売: filter + 8 KPI card + bảng 50 dòng/trang + nút CSV"* | HOW | `knowledge/` (sau UI-confirm) |
| *"CouponPack/get_coupon_metrics() **CHƯA TỒN TẠI TRONG CODE**"* | WHAT **sai** | `knowledge/system/` — cách ly. Kèm ghi chú: *đã bị black-box bác bỏ 2026-07-08, 9 PASS* |
| *"KPI 消化SC ở tab 販売 lọc theo kỳ mua hay kỳ dùng?"* | chưa biết | `OPEN-QUESTIONS.md` |

Lưu ý dòng giữa: tôi **không xoá** nó. Tôi **cách ly + ghi chú phản chứng**. Vì nó vẫn có giá trị
build-time (biết mà đi hỏi dev), chỉ là **tuyệt đối không được để QA-runtime nhìn thấy**.

**Quy tắc an toàn khi làm phase này:** với mỗi mục HOW nhập vào `knowledge/`, phải **UI-confirm**
(drive app thật, selector chạy) rồi mới `status: approved`. Không tin selector của sếp chỉ vì
nó nằm trong file của sếp — `SYSTEM.md` của ổng lấy endpoint từ `repository/*.ts`,
là **code-derived, chưa UI-confirm**. Theo luật của tôi, đó chỉ là `draft`.

---

## 6. Phase 4 — Vòng lặp học + cưỡng chế bức tường

### 4.1 Capture Lessons

Thêm bước bắt buộc cuối `/testcase-run` và `/testcase-retest`. Nhưng **chỉ được ghi thứ quan sát trực tiếp**:

| ✅ Được ghi vào `knowledge/lessons.md` | ❌ Cấm ghi |
|---|---|
| selector đổi, timing, mã HTTP quan sát được | *"vé không bị thu hồi **vì** backend thiếu callback"* |
| thứ tự xóa (2 vòng, hủy transaction trước) | *"coupon chưa build"* |
| branch của phiên này = 3 | bất kỳ suy luận nào về nguyên nhân |

**Luật phân biệt:** bài học trả lời câu hỏi **HOW** → nhập. Trả lời câu hỏi **WHAT** → độc.

**Bug tìm được KHÔNG vào knowledge.** Nó thuộc về `specs.md` (`BUG-xx`) và file Excel.
`knowledge/` không phải nơi cất kết luận về sản phẩm — cất vào đó là tự tay xây chất độc cho phiên sau.

### 4.2 Xoá `.claude-tester/` — và bức tường tự thành cơ chế (giải **L6**)

Sau Phase 3, mọi giá trị của `.claude-tester/` đã tan vào hệ này. Lúc đó:

```bash
git rm -r .claude-tester/
```

**Vì sao việc này giải luôn L6:** bức tường thép của tôi vốn là **văn bản** — một session tương lai
chạy `/testcase-run` hoàn toàn có thể `grep` trúng `REPORTING.md` và đọc nó. Xoá đi thì **thứ độc
không còn tồn tại trong cây thư mục để mà grep trúng**. Luật thành cơ chế, miễn phí.

**Ba điều kiện bắt buộc:**

1. **Xoá SAU Phase 3, không trước.** Mọi mục HOW đã UI-confirm + `approved`; mọi mục WHAT đã vào
   `knowledge/system/` kèm `source_hash`; mọi câu hỏi mở đã vào `OPEN-QUESTIONS.md`.
2. **Giữ dấu vết nguồn.** Mỗi doc nhập về ghi `grown_from: .claude-tester/knowledge/PLAYBOOK.md#<mục>`
   trong front-matter. Sau này hỏi *"selector này ở đâu ra"* vẫn trả lời được, dù file gốc đã bay.
3. ~~**`git rm`, không phải `rm -rf`.**~~ ⚠️ **GIẢ ĐỊNH NÀY SAI — phát hiện 2026-07-09.**
   `.claude-tester` **chưa bao giờ được commit** (`git ls-files` → 0 file, không có trong `HEAD`,
   cũng không bị gitignore). `git rm` báo `pathspec did not match`. Xoá lúc đó = **mất vĩnh viễn**.
   → Đường đúng, đã làm: **commit lưu trữ trước** (31 file, bỏ `node_modules`) rồi mới `git rm`.
   - archive: `0119159` — tra lại: `git show 0119159:.claude-tester/<path>`
   - xoá: `822d5dd`
   - 7 symlink gãy + `node_modules` (17MB) là untracked → `rm -rf` phần còn lại (nội dung thật của
     7 symlink nằm trong `.claude-knowledge/`, đã có trong archive).

   📌 **Bài học:** *"git giữ hộ rồi"* là một **giả định**, không phải sự thật. Kiểm `git ls-files`
   **trước** khi dựa vào history làm lưới an toàn cho thao tác không hồi lại.

**Bổ sung (nên làm):** thêm vào `SKILL.md` mục **"Danh sách CẤM đọc ở QA-runtime"**:
`knowledge/system/**`, mọi file sản phẩm trong 5 repo. Mạnh nhất là PreToolUse hook chặn `Read`/`Grep`
vào các path đó khi đang chạy `/testcase-run`.

**Kiểm cuối:** `grep -r "claude-tester" threease_qa/` chỉ còn trúng trong `docs/` (nơi kể lại lịch sử),
không trúng trong `.claude/` hay `knowledge/`.

> ⚠️ `.claude-tester` là **của sếp**. Xoá trong repo `threease_qa` của mình thì thoải mái —
> **đừng đụng bản gốc** ở workspace của ổng.

---

## 7. Quyết định đã chốt

### Q1 — `spec-gap` biểu diễn thế nào? → **Hướng A: `result` thứ tư `SPEC-GAP`** ✅ đã implement

| Hướng | Được | Mất |
|---|---|---|
| **A** ✅ **CHỌN** — thêm `result` thứ tư `SPEC-GAP` | Rõ nhất; Cover đếm được; đúng tầm quan trọng | Phá COUNTIF template sếp; tcs.json cũ cần migrate |
| B — chôn vào field `source` | Tương thích 100% | Gap bị chôn; Cover không đếm; dễ bỏ qua |
| C — `未実施 (spec gap)` trong `actual` | Đếm được | Lẫn với "không quan sát được" — hai thứ khác hẳn |

**Lý do chọn A:** ta **vốn đã fork** khỏi template sếp (`build_evidence.py` viết lại, PNG thay JPG,
5 target thay 1). Giữ tương thích COUNTIF với một hệ **sắp bị xoá** là cái giá không đáng trả —
trong khi `spec-gap` là **finding có giá trị cao nhất** của con QA mù code.

Đã đổi: `theme.json` (mới), `build_evidence.py`, `example.tcs.json` (mới), `SKILL.md`,
`testcase-write.md`, `testcase-run.md`.

### Q2 — `.claude-tester/` để đâu? → **Xoá hẳn sau khi merge xong** ✅ (xem §6.2)

---

## 8. Tổng kết — sau khi xong, tôi được gì

| Lỗ hổng | Trước | Sau | Phase |
|---|---|---|:--:|
| **L1** 4 lệnh chết | `/testcase-cleanup` không chạy được | chạy được; build deterministic | 0 |
| **L2** ảnh dính spinner | `waitForTimeout(6000)` cầu may | `shot()` chờ selector | 0 |
| **L3** không chỗ cất "chưa biết" | ép thành "có" (bịa) hoặc "không" | `OPEN-QUESTIONS.md` | 1 |
| **L4** không có `spec-gap` | finding quý nhất bị mất | trạng thái thứ tư | 2 |
| **L5** không tự lớn lên | bay hơi sau mỗi session | Capture Lessons | 4 |
| **L6** tường là văn bản | grep là đọc được | cách ly + danh sách cấm (+ hook) | 4 |
| *(mới)* quan sát tầng API | `Bearer` sai auth → 401 | sniff devise-token | 0 |

Và **giữ nguyên** những gì tôi vốn hơn sếp: oracle = SPEC · mù code ở runtime · tách HOW/WHAT ·
hai pha build-time/runtime · Precondition Protocol · `source_hash` · 5 target · PNG rõ ·
`/testcase-systemdoc`.

**Kiểm chứng cuối cùng:** chạy lại TestCase-11 → phải vẫn ra **9 PASS / 8 FAIL**.
Nếu ra "FAIL toàn bộ vì chưa build" → chất độc đã lọt qua cửa, quay lại Phase 3.

---

## 9. Việc kế tiếp

**Phase 0 xong 2026-07-09.** Verify: 4 tcs.json cũ (17/34/25/44 case) build lại sạch; ảnh nhúng khớp
bản cũ (34↔34, 7↔7); `SPEC-GAP` end-to-end; `result` lạ → WARN; `node --check` sạch 3 file JS.

**Phase 1 xong 2026-07-09.** Đã tạo:
`knowledge/OPEN-QUESTIONS.md` (8 câu, OQ-01..08) · `knowledge/GLOSSARY.md` · `knowledge/lessons.md`
(12 bẫy cơ khí + luật nhập HOW-vs-WHAT) · `confidence`/`verify_by` trên mọi doc `knowledge/` ·
routing table + **⛔ danh sách CẤM đọc** trong `SKILL.md` · checklist "Before final" ×5 command ·
Capture Lessons ×2 command · luật "1 tri thức = 1 nhà" + "dot-folder không chứa deliverable".

> Ghi chú: `lessons.md` đã **kéo trước 9/11 mục** của `.claude-tester/knowledge/LESSONS.md`
> (vốn là việc Phase 3) — vì 4 command vừa trỏ vào file đó, để rỗng sẽ đẻ ra lệnh chết mới.
> 2 mục code-derived (2026/07/08 "đọc code xác nhận…") **chưa nhập** — chờ Phase 3 đưa vào `knowledge/system/`.

**Kế tiếp — theo đúng thứ tự:**
1. ⛔ **Chạy live `pw_api`** (cổng chặn Phase 2).
2. **Phase 2** — nhập `knowledge/METHOD.md` + adapter *"coverage ≠ oracle"*.
3. **Phase 3** — khử độc 8 file `.claude-knowledge/` qua 3 cửa.
4. **Phase 4** — Capture Lessons đã có; còn `git rm -r .claude-tester/` + kiểm cuối.
