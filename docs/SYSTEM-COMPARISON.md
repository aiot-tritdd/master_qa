# So sánh 2 hệ thống — `threease_qa` (của tôi) vs `.claude-tester` (của sếp)

> ⏳ **DOC ĐÃ HẾT HẠN — kho lưu.** Việc merge đã xong (`.claude-tester/` đã tan vào hệ + xoá,
> 2026-07-09). File này **cố ý viết để đứng một mình** (giải thích trọn vẹn vì sao có 2 bức tường
> thép, kể cả ca coupon 9 PASS) nên hơi trùng với `README.md`/`QA-SERVER.md` — đó là chủ ý, để mang
> đi trình bày. Muốn nắm hệ thống nhanh: [`README.md`](README.md).
>
> **Mục đích (khi còn là dự án đang chạy):** đọc file này xong là hiểu (1) hệ của tôi là gì, (2) hệ
> của sếp là gì, (3) hai hệ khác nhau ở đâu và **vì sao**, (4) mỗi bên mạnh/yếu chỗ nào, (5) bù trừ
> ra sao. Kế hoạch thực thi: [`MERGE-PLAN.md`](MERGE-PLAN.md).
>
> Ngày: 2026-07-09 · Nguồn: đọc trực tiếp `.claude-tester/` (23 file) + `.claude-tester/.claude-knowledge/`
> (8 file, 512 dòng) + toàn bộ `threease_qa/`.

---

## Phần I — Hệ thống của TÔI

### 1. Nó là con gì

`threease_qa` **không chứa code sản phẩm**. Nó chứa một **con QA senior tự động, mù code**.

Đầu vào là một file **SPEC**. Đầu ra là **test case đã chạy thật + bằng chứng ảnh**, chấm
PASS/FAIL. Ở giữa, nó tự lái app dev bằng Playwright và **quan sát bằng mắt** như một người
tester thật — không đọc một dòng code sản phẩm nào.

Toàn bộ chạy trong **một session Claude ấm**, không đẻ subprocess `claude -p`, không sinh file
`.py` phụ trợ. Suy nghĩ là việc của model; script chỉ làm phần cơ khí (Playwright, xuất Excel).

### 2. Hai bức tường thép

Đây là hai luật không được phá. Phá là sai từ gốc, không phải sai chi tiết.

**Tường 1 — Oracle là SPEC, không phải code.**
Cột `expect` (kỳ vọng đúng/sai) **chỉ** được suy ra từ spec. Lúc viết `expect`, tôi mù code hoàn toàn.

> Lý do: nếu lấy kỳ vọng từ code, test chỉ đang khẳng định *"code làm đúng cái code làm"*.
> Đó là **tautology** — một vòng lặp tự khen, giá trị bằng không. Test chỉ có nghĩa khi
> kỳ vọng đến từ **một nguồn độc lập với thứ đang bị test**.

**Tường 2 — QA mù code tuyệt đối ở runtime.**
Không đọc code, không dùng code-graph lúc test. Khi FAIL, báo cáo mô tả **hành vi**:
*"spec bảo X, màn hình làm Y"* + ảnh. **Không bao giờ** ghi symbol / `file:line`.
Định vị bug trong code là việc của dev, không phải của QA.

### 3. Chìa khoá: tách HOW khỏi WHAT

Đây là ý tưởng làm cho "mù code" trở nên **khả thi** thay vì bất tiện.

| | **HOW — vận hành** | **WHAT — hành vi** |
|---|---|---|
| Trả lời | nút ở đâu, màn nào, bấm theo thứ tự nào, xem kết quả ở đâu | bấm xong ra kết quả gì, có đúng luật không |
| Tầng | giao diện | logic nghiệp vụ |
| Là oracle? | ❌ không | ✅ **chính là oracle** |
| Ai cấp? | Living Business Doc (`knowledge/`) | SPEC + quan sát live |

**Vì sao tách được:** bug sống ở tầng WHAT. Dev code sai luật nghiệp vụ → sai *cái xảy ra khi bấm*.
Dev **không** vì thế mà dời nút, không đổi các bước tạo booking. Nên tri thức navigation
**gần như miễn nhiễm với bug logic** → tôi có thể ghi sẵn nó vào doc, đọc thoải mái, mà không
làm ô nhiễm oracle.

Đây là toàn bộ lý do `knowledge/` được phép tồn tại trong một hệ "mù code".

### 4. `knowledge/` của tôi là gì

`knowledge/` là **trí nhớ dài hạn** của con QA. Session Claude chết sau mỗi lần chạy; `knowledge/`
là thứ duy nhất sống sót và được mang sang lần sau.

Nhưng trí nhớ của một con QA mù code là thứ **nguy hiểm**. Nhớ sai một chút thì test vẫn chạy, vẫn
ra PASS/FAIL đẹp đẽ — chỉ là **không còn giá trị gì**. Nên toàn bộ thiết kế của `knowledge/` xoay
quanh đúng một câu hỏi: *con QA được phép nhớ những gì?*

#### 4.1 Tiêu chí phân loại: **quyền lực**, không phải chủ đề

Đây là chỗ dễ hiểu nhầm nhất. `knowledge/` **không** chia theo chủ đề (booking / vé / coupon).
Nó chia theo **mức quyền** mà mỗi mẩu tri thức có đối với phán quyết đúng/sai.

Mỗi lần thêm một dòng vào `knowledge/`, tôi hỏi đúng **một câu**:

> ### *"Mẩu tri thức này có trả lời hộ câu hỏi 'kết quả đúng là gì' không?"*

| | Trả lời | Nghĩa là | Xử lý |
|---|---|---|---|
| **KHÔNG** | *"nút Thanh toán nằm ở tab 会計"* | nó chỉ giúp tôi **thao tác**, không nói kết quả nào đúng | ✅ **an toàn** — QA đọc lúc test |
| **CÓ** | *"hủy booking thì SC phải được hoàn"* | nó **thay SPEC** làm oracle → tautology | ⛔ **độc** — cách ly, chỉ build-time |
| **"chưa rõ"** | *"KPI 消化SC lọc theo kỳ mua hay kỳ dùng? — chưa ai biết"* | nó **từ chối** phán đúng/sai | ✅ **an toàn** — QA đọc lúc test |

Loại thứ ba mới nhìn tưởng thừa, nhưng nó là thứ giữ hệ thống trung thực. Nếu không có chỗ cất
"tôi chưa biết", mọi thứ chưa biết sẽ bị **ép** thành "biết rồi" (→ con QA bịa `expect`).
Một câu hỏi mở **an toàn** cho con QA đọc, vì nó không phán *"kết quả đúng là X"* — nó chỉ nói
*"đừng tự tin ở chỗ này, đi hỏi người"*.

#### 4.2 Ba tầng, và ai được đọc tầng nào

```
knowledge/            ◄── ✅ QA-RUNTIME ĐỌC ĐƯỢC (không mẩu nào cấp được `expect`)
│
├── ── HOW: bấm gì, vào đâu, xem kết quả ở đâu ─────────────────────────────
│   ├── observation-channels.md   [approved] 🟢  kênh quan sát: Pro / ticket-app / ticket-admin
│   ├── pro-open-booking.md       [stale]    🔴  mở booking · cancel payment · remove vé
│   │      ▲ stale vì HARNESS đổi (locale ja-JP), KHÔNG phải code đổi → source_hash MÙ (§4b KNOWLEDGE-STRATEGY)
│   ├── ticket-coupon-reports.md  [approved] 🟡  route coupon-report
│   └── issue-ticket-pack.md      [draft]    🔴  phát hành gói vé — CHƯA UI-confirm
│
├── ── COVERAGE: case nào BẮT BUỘC phải tồn tại (không nói case đó đúng/sai) ─
│   └── METHOD.md                 [approved] ⭐  5 archetype + luật vàng rút từ bug thật
│
├── ── HỖ TRỢ: không đụng gì tới oracle ──────────────────────────────────────
│   ├── GLOSSARY.md               [approved] 🟢  tên nghiệp vụ để viết report (không lộ tên repo)
│   └── lessons.md                [approved] 🟢  bẫy CƠ KHÍ: selector, timing, mã HTTP
│
└── ── CHƯA BIẾT ─────────────────────────────────────────────────────────────
    └── OPEN-QUESTIONS.md         [approved] ⭐  OQ-01..08 — "tra rồi vẫn không đủ căn cứ"

knowledge/system/     ◄── ⛔ BUILD-TIME ONLY. QA-runtime CẤM ĐỌC.
├── OVERVIEW.md            [draft]  8 domain × repo × trạng thái
├── customer-sync.md       [draft]
├── payment-cancel.md      [draft]
├── ticket-issue-sync.md   [draft]
└── coupon-sc.md           [draft]
       ▲ WHAT — "code đang làm gì". Bản đồ nghiệp vụ toàn hệ.
```

Ba nhóm trên (HOW · COVERAGE · HỖ TRỢ · CHƯA BIẾT) đều nằm ở **một phía của bức tường**: không
nhóm nào cấp được `expect`. `knowledge/system/` nằm phía bên kia.

#### 4.3 Vì sao ranh giới nằm đúng chỗ đó

**HOW an toàn** — vì bug sống ở tầng WHAT (xem §3). Dev code sai luật nghiệp vụ thì *kết quả khi bấm*
sai, chứ dev **không** vì thế mà dời cái nút đi chỗ khác. Tri thức navigation gần như **miễn nhiễm
với bug logic** → ghi sẵn vào doc, đọc thoải mái, oracle vẫn sạch.

**COVERAGE an toàn** — `METHOD.md` nói *"mọi thao tác cancel/delete phải có case kiểm dữ liệu phái sinh"*.
Đó là **danh sách case phải viết**, không phải kết quả case đó. Ranh giới một dòng:

> `METHOD.md` quyết định **case nào phải tồn tại**. Nó **không bao giờ** quyết định `expect`.
> Spec im lặng ở chỗ METHOD bảo phải có case → **không bịa** → ghi một **`SPEC-GAP`**.

**WHAT độc** — không phải vì nó sai, mà vì nó **đúng theo code**. Nếu con QA đọc *"coupon report chưa
build"* trước khi test, nó thôi quan sát trung thực và bắt đầu **suy diễn**. Phần III của tài liệu này
là một ca thật: đúng tình huống đó, black-box ra **9 PASS** cho tính năng mà code-trace khẳng định
"chưa tồn tại". Đọc WHAT ở runtime = mất đúng cái giá trị duy nhất mà black-box mang lại.

Nói ngắn: `knowledge/system/` tồn tại để **con người hiểu hệ thống** và để tôi *soạn* tầng HOW nhanh
hơn ở build-time. Nó **không** phải oracle, và nó ở ngoài tầm với của con QA lúc test.

#### 4.4 Mỗi doc tự khai lý lịch

Không doc nào được phép nói *"cứ tin tôi"*. Mỗi file mở đầu bằng YAML front-matter khai rõ **nó từ đâu
ra, tin được tới đâu, và kiểm lại bằng cách nào**:

```yaml
id: pro-open-booking
status: approved         # draft → approved → stale
kind: flow               # flow | channels | method | lessons | glossary | registry | system-map
spans_repos: [pro]
source_symbols: ["pro: components/.../ReservationForm.vue"]
source_hash: 0d5d5b2cb5f2af2c   # hash file nguồn LÚC DUYỆT → phát hiện code đã đổi
ui_confirmed_at: 2026-07-07     # đã drive app thật, selector chạy ổn định
confidence: 🟢                   # ⭐ code cứng · 🟢 ổn định · 🟡 đổi theo release · 🔴 chưa xác nhận
verify_by: "Drive lại flow bằng pw_lib.getPage('pro'); selector đổi → cập nhật + đổi ui_confirmed_at."
grown_from: ".claude-tester/knowledge/LESSONS.md"   # nếu kế thừa từ hệ của sếp
```

Hai trường `source_hash` và `confidence` **trông giống nhau nhưng bắt hai loại lỗi khác nhau** — đây là
lý do phải có cả hai, không bỏ được cái nào:

| | Bắt được | KHÔNG bắt được |
|---|---|---|
| `source_hash` (cơ khí) | **code đã đổi** kể từ lúc duyệt | doc **chưa từng** được xác nhận lần nào |
| `confidence` (con người) | doc **chưa chắc ngay từ đầu** | code đổi mà không ai đụng doc |

> Một doc `draft` có `source_hash` khớp hoàn hảo **vẫn có thể sai**. Hash chỉ nói *"chưa ai đổi code"*;
> nó không nói *"nội dung này đúng"*.

Và `status` là một **vòng đời**, không phải nhãn trang trí: một doc chỉ lên `approved` sau khi
**drive app thật** (UI-confirm) — tri thức sinh từ code-graph luôn dừng ở `draft`. Khi code nguồn đổi,
`/testcase-stale` tự đẩy nó về `stale`, và nó **mất quyền được QA đọc** cho tới khi có người
re-confirm.

### 5. Hai pha — build-time và QA-runtime

Đây là kiến trúc cốt lõi. **Cùng một con Claude, hai chế độ, quyền hạn khác nhau.**

```
┌────────────────────── PHA 1: BUILD-TIME (soạn tri thức) ───────────────────────┐
│                                                                                │
│  ĐƯỢC PHÉP: GitNexus (route_map, query, context, impact), đọc code, xem 5 repo │
│                                                                                │
│  GitNexus  ──────────►  doc [draft]      (skeleton + cơ chế, rẻ, nhanh)        │
│      │                      │                                                  │
│      │                      ▼                                                  │
│      │              UI-confirm: drive app thật, selector chạy ổn               │
│      │                      │                                                  │
│      │                      ▼                                                  │
│      └──────────────►  doc [approved]  + source_hash + ui_confirmed_at         │
│                                                                                │
│  Lệnh: /testcase-systemdoc <flow>                                              │
│  Nguyên tắc: graph TĂNG TỐC, UI-confirm CHỐT. Graph-derived = draft, không đủ. │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
        chỉ doc [approved] ở knowledge/ (KHÔNG phải system/) đi qua cửa này
                                        ▼
┌────────────────────── PHA 2: QA-RUNTIME (chạy test) ───────────────────────────┐
│                                                                                │
│  CẤM: đọc code · GitNexus · knowledge/system/ · mọi kết luận "đã/chưa build"   │
│  ĐƯỢC: specs.md (oracle) · knowledge/*.md approved (HOW) · Playwright · mắt    │
│                                                                                │
│  SPEC ──► viết case (expect, mù code) ──► seam (tra HOW) ──► drive app         │
│                                                    │                           │
│                                            quan sát live                       │
│                                                    │                           │
│                                     PASS / FAIL / 未実施  + 2 ảnh PNG          │
│                                                                                │
│  Lệnh: /testcase-write → /testcase-run → /testcase-retest                      │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Vì sao phải tách hai pha:** tôi cần hiểu hệ thống (không thể mò UI mù), nhưng tôi không được
để cái hiểu đó quyết định đúng/sai. Giải pháp là **hiểu ở pha 1, quên ở pha 2** — và cái "quên"
được cưỡng chế bằng việc chỉ cho phép doc `knowledge/*.md` (đã lọc sạch WHAT — xem §4) qua biên giới.

### 6. Precondition Protocol

Một chi tiết nhỏ nhưng là chỗ hệ của sếp không có. Trước khi chạy mỗi case:

1. **Định nghĩa** trạng thái tiền đề từ **SPEC** (ô `pre`) — bằng ngôn ngữ nghiệp vụ.
2. **Dựng** bằng flow trong Living Business Doc. ⚠️ Bắt buộc dùng **flow CŨ đã chạy ổn**
   (tạo booking, thanh toán, phát hành), **không dùng feature MỚI đang bị test**.
3. **Verify bằng mắt**: quan sát trạng thái thật, đối chiếu spec. Khớp → chạy. Lệch → **không chạy**,
   và bản thân việc lệch đó là 1 finding.

Bước 2 là điểm tinh tế: nếu dựng precondition bằng chính feature đang test, thì code sai của
feature đó sẽ làm hỏng khâu dựng, và tôi sẽ không phân biệt được "bug ở feature" với
"tôi dựng sai từ đầu".

### 7. Vòng đời tri thức — grow & maintain

**Grow theo nhu cầu (demand-driven), không grow trước.**

```
Spec mới về  ──►  qa-brain cần 1 flow để dựng precondition
                        │
                        ├── có trong knowledge/ (approved)  ──►  dùng luôn
                        │
                        └── chưa có  ──►  DỪNG. Không tự đọc code để bù.
                                          Chạy /testcase-systemdoc <flow> (build-time)
                                          → GitNexus ra draft → UI-confirm → approved
                                          → quay lại chạy test
```

**Sau mỗi release / mỗi spec mới được confirm:**

```
5 repo update
     │
     ▼
./refresh-gitnexus.sh          ← graph tươi. ĐIỀU KIỆN CẦN, CHƯA ĐỦ.
     │                            ⚠️ KHÔNG tự update knowledge/
     ▼
/testcase-stale                ← so source_hash cũ ↔ mới
     │                            (stale_check.py hash lại file nguồn)
     ▼
danh sách doc bị drift
     │
     ▼
re-derive (GitNexus) + re-confirm (UI)  ── CHỈ những doc stale ──► approved lại
```

Điểm mạnh của cơ chế này là **surgical**: `source_hash` gắn theo từng `source_symbols`, nên chỉ
doc nào chạm đúng file vừa đổi mới bị đánh dấu stale. Không phải quét lại toàn bộ.

Còn khi **spec mới được confirm** thì spec **tinh chỉnh** business đã map, chứ không dựng lại từ 0 —
`knowledge/system/` là bản đồ nền, spec là bản vá lên trên.

### 8. Sản phẩm giao ra

- `<F>/tcs.json` — 12 khoá: `id, screen, pri, result, title, pre, steps, expect, actual, note, before, after`
- `<F>/<Tên>.xlsx` — 3 sheet: Cover / Test Cases / Checklist
- `<F>/shots/*.png` — **mỗi case 2 ảnh** (before + after), **PNG rõ**, không nén JPG
- FAIL → mô tả hành vi lệch spec + ảnh. Feature chưa build → **FAIL** (quan sát 404 / thiếu nút),
  **không** suy đoán "chưa code" (đó là code-knowledge)

---

## Phần II — Hệ thống của SẾP

### 1. Nó là con gì

`.claude-tester/` là một **bộ công cụ test + bộ nhớ tổ chức**. Nó không phải QA mù code. Nó là
một **trợ lý test thành thạo hệ thống**, được trang bị sẵn tri thức để **khỏi phải điều tra lại code
mỗi lần**.

Triết lý được phát biểu nguyên văn ở `.claude-knowledge/README.md`:

> *"**Knowledge-first. Source-on-demand.** Không grep toàn repo nếu knowledge đã chỉ ra file/endpoint
> cụ thể — knowledge đã ghi sẵn `file:line`, dùng `Read` thẳng vào đó."*

Tri thức ở đây tồn tại để **tiết kiệm công điều tra**. Đó là mục đích hoàn toàn khác với `knowledge/`
của tôi (tồn tại để biết bấm nút nào).

### 2. Ba tầng

**Tầng lệnh** — 5 file `.md` trong `commands/`. Mỗi file mở đầu bằng cùng một câu *"Knowledge-first /
source-on-demand"*, và kết bằng checklist **"Before final"** 4 câu bắt buộc, trong đó có câu rất hay:

> *"Có đọc source code không? **Nếu có, vì sao?**"*

Không cấm đọc code. Bắt **khai báo lý do**. Đó là một cơ chế kỷ luật rẻ và thông minh.

**Tầng engine** — `scripts/`:

| File | Vai trò |
|---|---|
| `build_evidence.py` | generator xlsx |
| `theme.json` | **toàn bộ** màu/font/layout/nhãn — single source of truth cho format |
| `example.tcs.json` | khung 5 archetype (Happy / Điều kiện-quyền / Boundary / Regression / API·toàn vẹn) |
| `pw_lib.js` | login + **`shot(page, path, readySelector)`** + cache session `storageState` |
| `pw_api.js` | **sniff devise-token** từ request thật của app rồi tái sử dụng |
| `cleanup.js` | dọn dữ liệu test theo prefix, dry-run mặc định |
| `html_to_text.py` | lọc spec HTML → text gọn |

Đổi giao diện Excel = sửa `theme.json`, không đụng code. Build **deterministic** mọi lần.

**Tầng tri thức** — 11 file, chia theo **độ ổn định** (không theo chủ đề):

| Tier | File | Bản chất |
|---|---|---|
| ⭐ bất biến | `METHOD.md` | kỹ thuật test, độc lập hệ thống |
| 🟡 đổi theo release | `SYSTEM.md`, `PLAYBOOK.md` | URL/endpoint/selector, công thức thao tác |
| 🔴 tăng liên tục | `LESSONS.md` | war stories, mỗi dòng có ngày |
| 🟢 nền chung | 7 file `.claude-knowledge/` | dùng chung với `.claude-task/` (spec + mockup) |

7 file chung: `PROJECT_MAP` · `DOMAIN` · `SYNC_MAP` · `FEATURES` · `REPORTING` · `UI_UX` · `OUTPUT_LOCATIONS`.

### 3. Ba cơ chế vệ sinh tri thức rất đáng học

**(a) Fact-confidence** — mỗi mục tri thức khai báo:
```
Nguồn: <file:line hoặc spec> · Ngày đọc: YYYY/MM/DD ·
Độ ổn định: ⭐ (code cứng) / 🟢 (ổn định) / 🟡 (đổi theo release) / 🔴 (có suy luận, chưa xác nhận) ·
Verify bằng: <cách tự kiểm lại khi nghi ngờ>
```
Người đọc (kể cả Claude phiên sau) biết ngay **tin được tới đâu**, không phải đoán.

**(b) Registry "điều chưa biết"** — `.claude-knowledge/README.md` có mục **Open Questions / Gaps**,
gom 5 câu hỏi chưa xác nhận từ toàn bộ knowledge, kèm luật:

> *"Nếu task đang làm chạm đúng điểm nào dưới đây, **hỏi user/dev thay vì tự kết luận**."*

Xem cách `SYNC_MAP.md §2` phát biểu — đây là văn bản kỷ luật nhận thức tốt nhất trong cả hai hệ:

> *"Chỉ có 2 fact đã verify: (a) Rails **có sẵn code nhận**; (b) grep Django **không tìm thấy** nơi gọi tới.
> → Kết luận tạm: receiver đã build sẵn nhưng sender chưa xác nhận được. **CẦN HỎI DEV** thay vì tự
> kết luận. Đây là khoảng trống **thông tin**, không phải khoảng trống **code**."*

**(c) Vòng lặp học** — sau mỗi `run`/`retest`, bước **"Capture Lessons"** bắt buộc:
- bẫy mới → thêm dòng vào `LESSONS.md` (có ngày)
- endpoint/branch/selector đổi → sửa `SYSTEM.md` (đổi ngày)
- bug lặp một pattern → **nâng cấp** thành luật trong `METHOD.md`

Ba cơ chế này làm tri thức của sếp **tự lớn lên và tự khai báo độ tin cậy**.

### 4. Thêm hai thứ nhỏ mà hay

- **Bảng thuật ngữ business** (`DOMAIN.md`): "Hệ thống Lõi" / "Ứng dụng Pro" / "Hệ thống Vé" —
  kèm luật *"tên kỹ thuật chỉ dùng nội bộ để tra code; nói với khách hàng luôn dùng tên nghiệp vụ"*.
- **`OUTPUT_LOCATIONS.md`**: nguồn định nghĩa **duy nhất** cho "file nào ghi ở đâu". Nguyên tắc:
  dot-folder (`.claude-*`) chứa tool; deliverable thật luôn ở folder số thường (`7.Tests/`, `8.Tasks/`).

---

## Phần III — Bằng chứng đối chứng: hai hệ nói ngược nhau, ai đúng?

Đây là phần quan trọng nhất của tài liệu này. Không phải lý thuyết — là một ca thật, **cùng ngày**.

### Sự việc

Tính năng: **báo cáo Coupon** (No.11) trên Hệ thống Vé.

**Hệ của sếp**, `REPORTING.md` dòng 7-14, ngày **2026/07/08**, phương pháp = đọc code:

> *"⚠️ **Đã verify code (2026/07/08)**: `grep -i coupon` trên `threease_ticket/th/models/` ra **RỖNG** —
> `CouponPack`/`CouponUsage`/`CouponTransaction` và `ReportService.get_coupon_metrics()`
> **CHƯA TỒN TẠI TRONG CODE**, toàn bộ là tên đề xuất trong spec (No.11 chưa code)."*

**Hệ của tôi**, `docs/QA-SERVER.md §IX.4`, ngày **2026-07-08**, phương pháp = quan sát live:

> *"Coupon report (TestCase-11): black-box **9 PASS / 8 FAIL**, khớp **100%** list dev khai — mù code vẫn đúng."*

### Đọc kết quả

Nếu coupon report *"chưa tồn tại trong code"* thì không thể có **9 case PASS**. Một tính năng không
tồn tại thì không PASS được cái gì cả.

Và đây không phải lần đầu. Cũng trong `QA-SERVER.md §IX.4`:

> *"Guard 'vé đã dùng': tôi **code-trace** → kết luận 'chưa build' → **SAI** (Rails index yếu).
> **Black-box** thấy guard **đã build + chạy đúng** (message JP nguyên văn), và bắt bug thật
> (Remove lộ raw i18n key)."*

Hai lần, cùng một kiểu sai: **`grep` không thấy ≠ tính năng không tồn tại.**
Code có thể nằm chỗ khác, tên khác, sinh động lúc runtime, hoặc index code-graph bị yếu.

### Vì sao điều này quyết định toàn bộ kế hoạch merge

`CLAUDE.md` của repo này đã ghi luật, viết bằng máu:

> *"⚠️ **Đừng code-trace để phán 'đã build/chưa'** — từng SAI; dùng `route_map` + quan sát app thật."*

Vậy nên: **`.claude-knowledge/` không phải thứ để nhập thẳng vào `knowledge/`.**

Nếu con QA của tôi đọc `REPORTING.md` trước khi test No.11, nó sẽ **biết trước** rằng "coupon chưa
build" → nó thôi không quan sát trung thực nữa, mà **suy diễn** ra kết luận, rồi chấm FAIL toàn bộ.
9 case PASS thật sẽ bị báo sai. Tôi mất đúng cái giá trị duy nhất mà black-box mang lại.

Chất độc **không** nằm ở `LESSONS.md`. Nó nằm rải trong **4/8 file** của bộ shared, dưới dạng những
khẳng định đúng-sai được "verify từ code".

Nhưng — và đây là chỗ trớ trêu — **món quý nhất của sếp nằm ngay cạnh chất độc**. Chính `SYNC_MAP.md`
biết dừng lại ở *"cần hỏi dev, đây là khoảng trống thông tin"*, trong khi `REPORTING.md` lại
không dừng, mà kết luận thẳng *"CHƯA TỒN TẠI"*. Kỷ luật đó đã có sẵn trong hệ của sếp — chỉ là
**áp dụng không đều**.

---

## Phần IV — Bảng đối chiếu chuẩn hoá

Ký hiệu: **✅** có và tốt · **⚠️** có nhưng yếu/hỏng · **❌** không có

### A. Nhận thức luận & kiến trúc

| # | Chiều | Sếp | Tôi | Hơn | Ghi chú |
|---|---|:--:|:--:|---|---|
| 1 | Oracle (nguồn đúng/sai) | ⚠️ spec + knowledge + code | ✅ chỉ SPEC + quan sát live | **Tôi** | Của sếp có nguy cơ tautology |
| 2 | Chính sách đọc code | ⚠️ được, phải khai lý do | ✅ cấm ở runtime, chỉ build-time | **Tôi** | Checklist của sếp vẫn rất hay |
| 3 | Tách HOW / WHAT | ❌ trộn trong cùng file | ✅ `knowledge/` vs `knowledge/system/` | **Tôi** | Bức tường quan trọng nhất |
| 4 | Tách build-time / runtime | ❌ | ✅ hai pha, quyền hạn khác nhau | **Tôi** | |
| 5 | Precondition Protocol | ❌ | ✅ định nghĩa từ spec → dựng bằng flow CŨ → verify bằng mắt | **Tôi** | |
| 6 | Orchestration | ⚠️ 5 command rời | ✅ skill `qa-brain` agentic A→D | **Tôi** | |
| 7 | Sinh tri thức mới | ❌ viết tay | ✅ `/testcase-systemdoc` (GitNexus + UI-confirm) | **Tôi** | |

### B. Vệ sinh tri thức

| # | Chiều | Sếp | Tôi | Hơn | Ghi chú |
|---|---|:--:|:--:|---|---|
| 8 | Chống stale | ⚠️ nhãn 🟢🟡🔴 + ngày (thủ công) | ✅ `source_hash` + `stale_check.py` (cơ khí) | **Tôi** | Hai cái **bù nhau**, không thay nhau |
| 9 | Fact-confidence convention | ✅ `Nguồn · Ngày đọc · Độ ổn định · Verify bằng` | ❌ | **Sếp** | Rẻ, nên nhập ngay |
| 10 | Registry "điều chưa biết" | ✅ Open Questions, 5 mục | ❌ | **Sếp** | Món quý nhất |
| 11 | Vòng lặp học sau mỗi run | ✅ Capture Lessons bắt buộc | ❌ | **Sếp** | Hệ tôi **không tự lớn lên** |
| 12 | Routing table (skill nạp doc nào) | ✅ bảng tường minh | ⚠️ ngầm trong SKILL.md | **Sếp** | |
| 13 | Luật "1 tri thức = 1 nhà" | ✅ phát biểu rõ | ⚠️ chưa phát biểu | **Sếp** | |
| 14 | Độ sâu nghiệp vụ | ✅ 8 file, 512 dòng, có `file:line` | ⚠️ 5 doc `system/` + 4 doc HOW | **Sếp** | Phải khử độc trước khi dùng |
| 15 | Bảng thuật ngữ business | ✅ | ❌ | **Sếp** | Dùng khi report cho khách |
| 16 | Tri thức dùng chung liên-mảng | ✅ symlink sang `.claude-task/` | ❌ | **Sếp** | Tôi chỉ có QA nên chưa cần |

### C. Cơ khí (harness)

| # | Chiều | Sếp | Tôi | Hơn | Ghi chú |
|---|---|:--:|:--:|---|---|
| 17 | Phủ nhiều app | ❌ `pw_lib` chỉ Pro | ✅ `pro`/`ticket`/`ticket_admin`/`reservation`/`admin` | **Tôi** | |
| 18 | Chất lượng evidence | ⚠️ nén JPG q90 ~1080px | ✅ PNG rõ, 2 ảnh/case bắt buộc | **Tôi** | |
| 19 | Chụp ảnh tin cậy | ✅ `shot(page, path, readySelector)` | ❌ `waitForTimeout(6000)` + screenshot trần | **Sếp** | Tôi đang dùng đúng anti-pattern ổng cấm |
| 20 | Quan sát tầng API | ✅ sniff devise-token từ request thật | ❌ `Bearer ${API_TOKEN}` — sai cơ chế auth | **Sếp** | Kỹ thuật ổng **black-box thuần** |
| 21 | Cache session | ✅ `storageState` | ❌ login lại mỗi script | **Sếp** | |
| 22 | Template deterministic | ✅ `theme.json` + `example.tcs.json` | ❌ **cả 2 file không tồn tại** | **Sếp** | Command của tôi trỏ vào hư không |
| 23 | Cleanup | ✅ `cleanup.js` chạy được | ❌ **`cleanup.js` không tồn tại** | **Sếp** | Lệnh ma |

**Tổng:** tôi hơn 9 chiều (đều thuộc *nhận thức luận + kiến trúc*). Sếp hơn 12 chiều
(đều thuộc *cơ khí + vệ sinh tri thức*).

> **Một câu:** tôi có **bộ não** tốt hơn; sếp có **đôi tay** và **cuốn sổ tay** tốt hơn.

---

## Phần V — Lỗ hổng của mỗi bên

### Lỗ hổng của TÔI

> **Trạng thái 2026-07-09:** L1, L2 → ✅ **đã vá** (Phase 0). L3, L4, L5 → ✅ **đã vá** (Phase 1–2).
> **L6 → chưa vá** (xem định nghĩa lại bên dưới — hoá ra to hơn lúc đầu tưởng).
> Phần dưới giữ nguyên để hiểu **vì sao** phải vá.

**L1 — 4 lệnh chết (đã verify bằng filesystem).** Command ra lệnh dùng file không tồn tại:

| Lệnh | Bảo dùng | Thực tế |
|---|---|---|
| `testcase-write.md:31` | `cp example.tcs.json` | **file không tồn tại** |
| `testcase-write.md:60`, `testcase-run.md:63` | *"đổi màu = sửa `theme.json`"* | **file không tồn tại**, `build_evidence.py` hardcode palette ở dòng 30-36 |
| `testcase-cleanup.md:20` | `node cleanup.js` | **file không tồn tại** → cả command là lệnh ma |
| `pw_api.js` | `Authorization: Bearer ${API_TOKEN}` | app dùng **devise-token** (5 header) → 401 |

Hệ quả của cái thứ 2: khung 5 archetype tồn tại **trong văn bản mô tả** nhưng không tồn tại
**dưới dạng dữ liệu** → mỗi lần chạy Claude bịa lại từ trí nhớ → **không deterministic**.

**L2 — Evidence có nguy cơ dính spinner.** `testcase-run.md:33` dạy `waitForTimeout(6000)` +
`page.screenshot()` trần. Đó chính xác là anti-pattern `LESSONS.md 2026/07/06` của sếp cảnh báo.
Mà PNG rõ lại đúng là thứ tôi coi là chuẩn giao hàng.

**L3 — Không có chỗ cất "tôi không biết".** Tôi chỉ có hai trạng thái: *có trong `knowledge/`*
hoặc *không có → dừng, chạy `/testcase-systemdoc`*. Trạng thái thứ ba — **"đã tra rồi mà vẫn không
kết luận được, phải hỏi người"** — không có chỗ chứa, nên sẽ bị ép thành một trong hai:
ép thành "có" → **bịa**; ép thành "không" → chạy `/testcase-systemdoc` vô hạn.

**L4 — Không có `spec-gap`.** Tôi chỉ có `PASS` / `FAIL` / `未実施`. Không có ô nào cho
*"spec không nói gì về chuyện này, mà nó quan trọng"*. Đây là **finding có giá trị cao nhất** của
một con QA mù code — bằng chứng rằng spec chưa nghĩ tới — và tôi đang không có chỗ để ghi nó.

> L3 và L4 **là cùng một khái niệm** ở hai tầng: *"tôi quan sát được, nhưng không có căn cứ để chấm"*.
> Tầng tri thức gọi là **Open Question**; tầng test case gọi là **spec-gap**.

**L5 — Không tự lớn lên.** Chạy xong một suite, tôi không học được gì. Selector đổi, timing lạ,
bẫy thao tác — tất cả bay hơi hết sau session.

**L6 — Bức tường thép là văn bản, không phải cơ chế.** *(định nghĩa lại 2026-07-09 — hoá ra to hơn.)*
Lúc đầu tưởng lỗ là `.claude-tester/` nằm trong repo (session `/testcase-run` có thể `grep` trúng
`REPORTING.md`). Đã xoá `.claude-tester/` — nhưng đó chỉ là lỗ **phải đi tìm mới trúng**.
Lỗ thật **to hơn** và **tự chui vào**: workspace `CLAUDE.md` được Claude Code **nạp tự động vào mọi
phiên**, và §8 của nó là **WHAT** (cơ chế sync + tên file code). Con QA đọc code gián tiếp từ token
đầu tiên, không cần grep gì cả. Đã dời §8 sang `knowledge/system/customer-sync.md`, nhưng GitNexus
vẫn nằm trong tay QA qua MCP. **Chưa vá xong** — cơ chế thật = PreToolUse hook (`OPEN-QUESTIONS.md#OQ-09`).
Không có gì chặn về mặt kỹ thuật.

### Lỗ hổng của SẾP

**S1 — Nguy cơ tautology.** Oracle không được cô lập. `SYSTEM.md` lấy endpoint từ
`threease_pro/repository/*.ts` (code-derived, chưa UI-confirm) rồi cho QA-runtime đọc thẳng.
Khi `expect` và code cùng một nguồn, test mất khả năng phát hiện sai.

**S2 — `grep` không thấy → kết luận "chưa tồn tại".** Đã chứng minh sai ở Phần III, **hai lần**.
Đáng nói là kỷ luật đúng **đã có sẵn** trong chính hệ ổng (`SYNC_MAP.md §2`: *"khoảng trống thông tin,
không phải khoảng trống code"*), chỉ là không áp dụng đều — `REPORTING.md` không dừng lại.

**S3 — Chống stale thủ công.** Nhãn 🟡 chỉ **nhắc** "hãy verify". Nó không **biết** cái gì đã đổi.
Code đổi mà không ai sửa nhãn → doc sai âm thầm. `source_hash` của tôi giải đúng bài này.

**S4 — Trộn HOW và WHAT trong cùng file.** `LESSONS.md` có 11 mục: ~9 mục HOW (vô hại) nằm chung
với 2 mục WHAT (*"Đọc trực tiếp code, xác nhận…"*). Không thể cho QA đọc file này, cũng không thể
không cho — vì 9 mục kia rất giá trị. Đó là lý do phải **tách đôi**, không thể copy nguyên khối.

**S5 — Chỉ phủ app Pro.** `pw_lib.js` hardcode Pro. Không drive được ticket-app, ticket-admin,
reservation, admin. Mà `SYNC_MAP.md` của chính ổng lại bảo *"số dư bên Hệ thống Vé không đáng tin,
phải đối chiếu API Hệ thống Lõi"* — tức là ổng **biết** cần quan sát 2 phía nhưng **harness không
làm được**.

**S6 — Evidence nén JPG.** `q90`, resize ~1080px. Chữ nhỏ trên UI Vuetify dễ nhoè.

**S7 — Không có Precondition Protocol.** Không có luật "dựng tiền đề bằng flow CŨ". Rủi ro:
dùng feature đang test để dựng tiền đề cho chính nó.

---

## Phần VI — Hai hệ bù trừ cho nhau thế nào

Đây không phải hai hệ cạnh tranh. Chúng **khớp vào nhau gần như hoàn hảo**, vì mỗi bên mạnh đúng
chỗ bên kia yếu.

```
        LỖ CỦA TÔI                              SẾP CÓ SẴN
  ─────────────────────────           ──────────────────────────────
  L1  4 lệnh chết               ◄──   theme.json, example.tcs.json, cleanup.js, pw_api sniff
  L2  ảnh dính spinner          ◄──   shot(page, path, readySelector)
  L3  không chỗ cất "chưa biết" ◄──   Open Questions registry
  L4  không có spec-gap         ◄──   (METHOD.md ép ra nhu cầu này)
  L5  không tự lớn lên          ◄──   Capture Lessons loop
  L6  tường là văn bản          ◄──   (không có — tôi phải tự làm)


        LỖ CỦA SẾP                              TÔI CÓ SẴN
  ─────────────────────────           ──────────────────────────────
  S1  nguy cơ tautology         ◄──   Tường 1: oracle = SPEC
  S2  grep → "chưa tồn tại"     ◄──   Tường 2 + route_map + quan sát live
  S3  chống stale thủ công      ◄──   source_hash + stale_check.py
  S4  trộn HOW/WHAT             ◄──   firewall knowledge/ ↔ knowledge/system/
  S5  chỉ phủ Pro               ◄──   pw_lib 5 target
  S6  evidence nén JPG          ◄──   chuẩn PNG rõ, 2 ảnh/case
  S7  không có precondition     ◄──   Precondition Protocol
```

Chỉ **một lỗ duy nhất không bên nào lấp được cho bên kia**: **L6** — biến bức tường thép từ văn bản
thành cơ chế cưỡng chế. Tôi phải tự làm.

### Nguyên tắc hợp nhất (một câu)

> **Nhập CƠ KHÍ và VỆ SINH TRI THỨC của sếp. Không nhập KẾT LUẬN của sếp.**

Mọi thứ đi qua biên giới `.claude-tester/` → `threease_qa/` phải trả lời được đúng một câu hỏi:

> ### *"Cái này nói HOW hay nói WHAT?"*

- Nói **HOW** (cách drive, nơi quan sát, cách chụp, cách dọn) → **an toàn, nhập**.
- Nói **WHAT** (kết quả nào là đúng, cái gì đã/chưa build) → **độc**, vì nó thay thế SPEC làm oracle.
  → chỉ được vào `knowledge/system/` (build-time), kèm `source_hash`.
- Nói **"chưa biết"** → **an toàn, nhập** vào `OPEN-QUESTIONS.md`. Nó không phán đúng/sai,
  nó phán *"chưa đủ căn cứ, đi hỏi người"*.

Ba cửa. Mỗi mục tri thức của sếp đi qua đúng một cửa.

### Định tuyến cụ thể (đã soi từng file)

| Nguồn | → `knowledge/` (HOW) | → `knowledge/system/` (WHAT) | → `OPEN-QUESTIONS.md` |
|---|---|---|---|
| `METHOD.md` | **gần như nguyên vẹn** | — | — |
| `PLAYBOOK.md` | **gần như nguyên vẹn** | — | — |
| `LESSONS.md` | 9 mục (Vuetify `data-cy`, dialog 2 nút, `shot()`, branch đổi theo phiên, xóa 2 vòng) | 2 mục (2026/07/08 "đọc code xác nhận…") | — |
| `SYSTEM.md` | selector, route | bảng endpoint (từ `repository/*.ts`) | — |
| `FEATURES.md` | "Vào đâu", "luồng chính", "bẫy thao tác" | — | — |
| `SYNC_MAP.md` | — | §1, §3 (endpoint, handler gaps) | §2 sender Django, §4 (3 câu) |
| `REPORTING.md` | cấu trúc màn, 2 sub-tab, vị trí filter | ⚠️ **toàn bộ "coupon chưa có code"** | 2 "điểm chưa rõ" |
| `DOMAIN.md` | bảng thuật ngữ → `GLOSSARY.md` | 締め, 回数券, state machine | app mobile bệnh nhân? |
| `PROJECT_MAP.md` | dev URL, basic auth | tech stack | 3 dev URL chưa xác nhận |
| `UI_UX.md` | — | màu/font (chỉ khi test UI) | — |

Lưu ý cách `REPORTING.md` bị xé làm ba: phần *"tab 販売 có 8 KPI card, filter ở đâu"* là HOW → nhập
được. Phần *"coupon chưa tồn tại trong code"* là WHAT sai → cách ly. Phần *"KPI 消化SC lọc theo kỳ
mua hay kỳ dùng?"* là câu hỏi mở → vào registry.

### Một điều chỉnh bắt buộc khi nhập `METHOD.md`

`METHOD.md` là file quý nhất, và nó **code-blind sẵn**. Nhưng có bẫy:

> *"Toàn vẹn dữ liệu sau HỦY/XÓA: với mọi thao tác cancel/delete/refund, PHẢI kiểm dữ liệu phái sinh
> được hoàn/thu hồi đúng."*

Nếu spec **im lặng** về chuyện này thì `expect` lấy ở đâu? Lấy từ METHOD = **phá Tường 1**.

**Adapter — luật một dòng:**

> `METHOD.md` quyết định **case nào phải tồn tại** (coverage).
> Nó **không bao giờ** quyết định `expect` (oracle).
> Spec im lặng ở chỗ METHOD bảo phải có case → **không bịa `expect`** → ghi nhận một **`spec-gap`**.

Chính vì vậy `spec-gap` (L4) **không còn là tuỳ chọn**. Nhập METHOD mà không có chỗ đổ spec-gap thì
METHOD sẽ ép con QA bịa `expect` — và tôi mất Tường 1.

---

## Phần VII — Sau khi hợp nhất, hệ trông như thế nào

```
┌─ BUILD-TIME ────────────────────────────────────────────────────────────┐
│  GitNexus + code + .claude-tester (nguyên liệu, đọc thoải mái)          │
│         │                                                               │
│         ├──► knowledge/system/*.md    [WHAT]  + source_hash             │
│         ├──► knowledge/*.md           [HOW]   + ui_confirmed_at         │
│         └──► knowledge/OPEN-QUESTIONS.md      [chưa biết → hỏi dev]     │
└─────────────────────────────────────────────────────────────────────────┘
                  │                              │
      chỉ HOW ────┘                              └──── chỉ OPEN-QUESTIONS
                  ▼                              ▼
┌─ QA-RUNTIME (mù code) ──────────────────────────────────────────────────┐
│                                                                         │
│  SPEC ─────────────────────────────────► oracle (expect)                │
│  knowledge/*.md approved ──────────────► HOW (bấm gì, xem đâu)          │
│  knowledge/METHOD.md ──────────────────► coverage (case nào phải có)    │
│  knowledge/lessons.md ─────────────────► bẫy cơ khí (selector, timing)  │
│  OPEN-QUESTIONS.md ────────────────────► "chỗ này chưa ai biết"         │
│                          │                                              │
│                          ▼                                              │
│      shot() + pw_api sniff + 5 target ──► quan sát live 2 phía          │
│                          │                                              │
│                          ▼                                              │
│         PASS · FAIL · 未実施 · ⚠️ SPEC-GAP   + 2 ảnh PNG                │
│                          │                                              │
│                          ▼                                              │
│         Capture Lessons ──► lessons.md (chỉ ghi thứ QUAN SÁT ĐƯỢC)      │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                      5 repo update  │  spec mới confirm
                                     ▼
              refresh-gitnexus.sh → /testcase-stale (source_hash)
                       → re-confirm CHỈ doc stale → approved lại
```

Kết quả mong đợi: **giữ nguyên hai bức tường thép**, nhưng có đôi tay của sếp (harness chạy được),
cuốn sổ tay của sếp (tri thức tự khai báo độ tin cậy, tự lớn lên), và thêm một trạng thái mà
**cả hai hệ hiện đều thiếu**: chỗ cất "tôi quan sát được nhưng không đủ căn cứ để chấm".

---

*Kế hoạch thực thi chi tiết: [`MERGE-PLAN.md`](MERGE-PLAN.md).*
