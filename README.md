# threease_qa — QA senior tự động, mù code

> **Đọc file này là đủ hiểu trọn hệ thống** — nó là gì, nghĩ thế nào, vận hành ra sao, và lớn lên
> ra sao sau mỗi lần chạy. Không cần mở file nào khác. Muốn đào sâu chỗ nào → bảng cuối trang chỉ đường.
>
> 🛠️ **Chỉ muốn CÀI ĐẶT cho chạy** (cài gì, theo thứ tự nào, lấy credentials ở đâu) → [`SETUP.md`](docs/SETUP.md).
> File này giải thích *hệ nghĩ gì*; SETUP.md lo phần *máy trắng → chạy được test đầu tiên*.

---

## 1. Nó là gì

Repo này **không chứa code sản phẩm**. Nó chứa một **con QA senior nhân tạo, mù code**.

Đưa nó một file **SPEC**. Nó tự viết test case, tự lái app dev bằng Playwright, **quan sát bằng mắt**
như một tester thật, rồi chấm điểm kèm ảnh chụp màn hình. Nó **không đọc một dòng code sản phẩm nào**
lúc chạy test — kể cả khi được phép.

```
specs.md  ──►  viết test case  ──►  lái app dev  ──►  quan sát  ──►  PASS/FAIL + 2 ảnh/case + Excel
 (oracle)       (mù code)          (Playwright)     (bằng mắt)
```

Toàn bộ chạy trong **một session Claude ấm** — không đẻ subprocess, không sinh file phụ. Suy nghĩ là
việc của model; script chỉ làm phần cơ khí (Playwright, xuất Excel).

---

## 2. Vấn đề oracle — trái tim của mọi quyết định

Đây là lý do tồn tại của mọi thứ còn lại. Bỏ qua mục này thì phần sau vô nghĩa.

Khi một hành vi trên màn hình thay đổi, **nhìn code không phân biệt được** đó là **bug** (đổi ngoài ý
muốn) hay **feature** (cố ý đổi). Vì "ý định đúng" **không nằm trong code** — nó nằm trong đầu người.
Code chỉ biết nó *đang* làm gì, không biết nó *nên* làm gì.

⇒ Test sinh ra **từ code** chỉ khẳng định *"code làm đúng cái code làm"*. Đó là **tautology** — một
vòng lặp tự khen, giá trị bằng không. Test chỉ có nghĩa khi kỳ vọng đến từ **một nguồn độc lập với
thứ đang bị test**.

⇒ Nguồn độc lập đó = **SPEC**, do người viết. Đó là **oracle** duy nhất. Mọi kiến trúc bên dưới chỉ
để bảo vệ một điều: *kỳ vọng đúng/sai luôn đến từ SPEC, không bao giờ từ code.*

---

## 3. Hai bức tường thép

Hai luật không được phá. Phá là sai từ gốc, không phải sai chi tiết.

> **Tường 1 — Oracle là SPEC, không phải code.**
> Cột `expect` (kỳ vọng đúng/sai) **chỉ** suy từ spec. Lúc viết `expect`, QA mù code hoàn toàn.

> **Tường 2 — QA mù code tuyệt đối ở runtime.**
> Không đọc code, không dùng code-graph lúc test. Khi FAIL, báo cáo mô tả **hành vi**:
> *"spec bảo X, màn hình làm Y"* + ảnh. **Không bao giờ** ghi symbol / `file:line`. Định vị bug trong
> code là việc của dev.

> ⚠️ **Hiện tại hai tường này là VĂN BẢN, chưa phải CƠ CHẾ.** Chưa có gì kỹ thuật ngăn một phiên
> `/testcase-run` đọc code. Biến nó thành cơ chế (PreToolUse hook) là việc lớn nhất còn lại — xem
> `docs/STATE.md` / `OPEN-QUESTIONS.md#OQ-09`.

---

## 4. Chìa khoá làm cho "mù code" khả thi: tách HOW khỏi WHAT

Nếu mù code mà vẫn phải lái đúng app, làm sao biết đường bấm? Câu trả lời là tách đôi tri thức:

| | **HOW — vận hành** | **WHAT — hành vi** |
|---|---|---|
| Trả lời | nút ở đâu, màn nào, bấm thứ tự nào, xem kết quả ở đâu | bấm xong ra kết quả gì, có đúng luật không |
| Tầng | giao diện | logic nghiệp vụ |
| Là oracle? | ❌ không | ✅ **chính là oracle** |

**Bug sống ở tầng WHAT, không ở HOW.** Dev code sai luật nghiệp vụ thì *kết quả khi bấm* sai — chứ dev
**không** vì thế mà dời cái nút đi chỗ khác. Nên tri thức navigation (HOW) gần như **miễn nhiễm với bug
logic**: ghi sẵn vào doc, con QA đọc thoải mái, mà oracle vẫn sạch. Đó là toàn bộ lý do một hệ "mù code"
vẫn được phép có sẵn một cuốn sổ tay navigation.

---

## 5. Ba tầng tri thức — và ai được đọc tầng nào

Tri thức trong `knowledge/` **không** chia theo chủ đề (booking / vé / coupon). Nó chia theo **quyền
lực**: mẩu tri thức này có được phép trả lời *"kết quả đúng là gì"* không?

| Tầng | Ở đâu | Trả lời | QA lúc test |
|---|---|---|:--:|
| **HOW** | `knowledge/*.md` | bấm gì, vào đâu, xem kết quả ở đâu | ✅ đọc được |
| **WHAT** | `knowledge/system/*.md` | code làm gì, cái gì đã/chưa build | ⛔ **CẤM** |
| **CHƯA BIẾT** | `knowledge/OPEN-QUESTIONS.md` | *"tra rồi vẫn không đủ căn cứ → hỏi người"* | ✅ đọc được |

**Vì sao ranh giới nằm đúng chỗ đó:**
- **HOW an toàn** — vì bug ở tầng WHAT (§4), nút bấm gần như không đổi theo bug logic.
- **WHAT độc** — không phải vì nó sai, mà vì nó **đúng theo code**. Nếu con QA đọc *"coupon report chưa
  build"* trước khi test, nó thôi quan sát trung thực và bắt đầu **suy diễn** — rồi chấm sai (xem §11).
  Đọc WHAT lúc test = mất đúng cái giá trị duy nhất của black-box.
- **CHƯA BIẾT an toàn** — vì nó **từ chối** phán đúng/sai; nó chỉ nói *"đừng tự tin ở đây, đi hỏi người"*.
  Không có tầng này, mọi thứ chưa biết bị ép thành "có" (→ **bịa**) hoặc "không" (→ điều tra vô hạn).

---

## 6. Hai pha — cùng một Claude, hai chế độ, quyền hạn khác nhau

Đây là kiến trúc cốt lõi. Con QA cần **hiểu** hệ thống (không thể mò UI mù), nhưng không được để cái
hiểu đó **quyết định đúng/sai**. Giải pháp: **hiểu ở pha 1, quên ở pha 2** — và cái "quên" được cưỡng
chế bằng việc chỉ cho doc HOW đã lọc sạch WHAT đi qua biên giới.

```
┌─ BUILD-TIME (soạn tri thức) ─────────────────────────────────────────────┐
│  ĐƯỢC: GitNexus (route_map/query/context) · đọc code · xem cả 5 repo      │
│                                                                          │
│  GitNexus ──► doc [draft] ──► UI-confirm (drive app thật) ──► [approved]  │
│  Lệnh: /testcase-systemdoc <flow>   ·   graph TĂNG TỐC, UI-confirm CHỐT   │
└──────────────────────────────────────────────────────────────────────────┘
                        │  chỉ doc [approved] ở knowledge/ (KHÔNG phải system/)
                        ▼
┌─ QA-RUNTIME (chạy test, mù code) ────────────────────────────────────────┐
│  CẤM: code · GitNexus · knowledge/system/ · phán "đã/chưa build"          │
│  ĐƯỢC: specs.md (oracle) · knowledge/ approved (HOW) · METHOD · Playwright │
│                                                                          │
│  SPEC ─► viết case (mù code) ─► dựng precondition ─► lái app ─► quan sát  │
│                        PASS · FAIL · 未実施 · SPEC-GAP  + 2 ảnh PNG        │
│  Lệnh: /testcase-write → /testcase-run → /testcase-retest                 │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Bốn kết quả, không phải ba

| Kết quả | Nghĩa |
|---|---|
| `PASS` | quan sát khớp spec |
| `FAIL` | quan sát lệch spec (kèm ảnh + mô tả hành vi) |
| `未実施` | **không quan sát được** (không vào được màn, thiếu quyền…) |
| `SPEC-GAP` | **quan sát được, nhưng SPEC không định nghĩa kỳ vọng** |

`SPEC-GAP` là finding **giá trị cao nhất** của QA mù code: bằng chứng rằng **spec chưa nghĩ tới**. Nó
xảy ra khi `knowledge/METHOD.md` bảo *phải có case* mà SPEC im lặng. Ranh giới một dòng, nhầm là phá
Tường 1:

> `METHOD.md` quyết định **case nào phải tồn tại** (coverage). Nó **không bao giờ** quyết định `expect`.
> Spec im lặng ở chỗ METHOD bảo phải có case → **không bịa `expect`** → ghi một `SPEC-GAP`.

---

## 8. Precondition Protocol — dựng tình huống mà không tin code

Trước mỗi case:

1. **Định nghĩa** trạng thái tiền đề từ **SPEC** (ô `pre`) — bằng ngôn ngữ nghiệp vụ.
2. **Dựng** bằng flow trong Living Business Doc. ⚠️ Bắt buộc dùng **flow CŨ đã chạy ổn** (tạo booking,
   thanh toán, phát hành) — **không dùng feature MỚI đang bị test**.
3. **Verify bằng mắt**: quan sát trạng thái thật, đối chiếu spec. Khớp → chạy. Lệch → **không chạy**,
   và bản thân việc lệch đó là 1 finding.

Bước 2 là điểm tinh tế: nếu dựng precondition bằng chính feature đang test, code sai của feature đó sẽ
làm hỏng khâu dựng, và ta không phân biệt được *"bug ở feature"* với *"tôi dựng sai từ đầu"*.

---

## 9. Cách vận hành

```
/specs-md <folder>          spec.html → specs.md (nếu spec là HTML)
   │
"dùng skill qa-brain cho wtf-is-this/TestCase-XX"
   │                        đọc SPEC → viết case (mù code) → tcs.json + xlsx
/testcase-run               lái app live → evidence → chấm điểm → build Excel
   │
/testcase-cleanup           dọn dữ liệu test trên dev (prefix AIOT-TEST-*)
   │
/testcase-upspecschange → (dev fix) → /testcase-retest
```

**Chuẩn giao hàng mỗi task:**
- `<Folder>.xlsx` — 3 sheet: Cover (summary) · Test Cases (block dọc + ảnh) · Checklist (+ cột Nguồn)
- `shots/*.png` — **mỗi case 2 ảnh** (before + after), **PNG rõ**, không nén JPG
- FAIL → mô tả hành vi lệch spec + ảnh. Feature chưa build → **FAIL** (quan sát 404 / thiếu nút),
  **không** suy đoán "chưa code" (đó là code-knowledge).

Truy cập dev + tài khoản: `docs/STATE.md` §5.

---

## 10. Nó lớn lên thế nào — grow & maintain

Đây là chỗ hệ này khác một "bộ test viết cứng": tri thức của nó **tự lớn theo nhu cầu**, và **tự biết
khi nào mình cũ**.

**Grow theo nhu cầu (demand-driven), KHÔNG grow trước** — không ngồi viết doc cho cả 8 domain ngay từ
đầu, chỉ viết một flow khi có test thật cần tới:

```
Spec mới về  ──►  qa-brain cần 1 flow để dựng precondition
                       │
                       ├── có trong knowledge/ (approved)  ──►  dùng luôn
                       │
                       └── chưa có  ──►  DỪNG. KHÔNG tự đọc code để bù.
                                         /testcase-systemdoc <flow> (build-time)
                                         → GitNexus ra draft → UI-confirm → approved
                                         → quay lại chạy test
```

**Maintain khi 5 repo update** — knowledge KHÔNG tự cập nhật theo code; phải có nhịp kiểm:

```
5 repo update → ./refresh-gitnexus.sh (graph tươi — ĐIỀU KIỆN CẦN, chưa đủ)
             → /testcase-stale (so source_hash cũ↔mới → in doc bị drift)
             → re-derive + re-confirm CHỈ doc stale → approved lại
```

Điểm mạnh là **surgical**: `source_hash` gắn theo từng file nguồn, nên chỉ doc nào chạm đúng file vừa
đổi mới bị đánh dấu stale — không phải quét lại toàn bộ.

> Cơ khí đầy đủ (lệnh `stale_check.py`, front-matter, `confidence` vs `source_hash`, 3 loại stale):
> **[`KNOWLEDGE-STRATEGY.md`](docs/KNOWLEDGE-STRATEGY.md)**.

---

## 11. Bằng chứng: nó hoạt động, và code-trace thì không

Hai ca thật, cùng chứng minh một điều — và chúng là **lý do hai bức tường thép tồn tại**.

**Ca 1 — Coupon report (TestCase-11).** Test mù code, mù cả danh sách dev khai. Kết quả **9 PASS /
8 FAIL** → đối chiếu list dev khai "đã làm / chưa làm": **khớp 100%**, đến chi tiết *"tab 販売 làm 1
phần: Report ✅ / 過去のCSV ❌"* cũng bắt đúng. Cùng ngày, một hệ khác **đọc code** (`grep -i coupon` →
rỗng) kết luận *"coupon report CHƯA TỒN TẠI TRONG CODE"*. Một tính năng không tồn tại thì không thể có
9 case PASS.

**Ca 2 — Guard "vé đã dùng".** Code-trace qua GitNexus → kết luận *"chưa build"* → **SAI** (Rails index
yếu). Black-box lái app thật → guard **đã build, chạy đúng**, chặn với nguyên văn tiếng Nhật. Và còn bắt
được **bug thật** code-trace không thấy: luồng Remove lộ raw i18n key `reservations.used_ticket_cannot_remove`
thay vì câu tiếng Nhật.

> **`grep` không thấy ≠ không tồn tại.** Đã sai **2 lần**. Code có thể ở chỗ khác, tên khác, sinh động
> lúc runtime, hoặc index code-graph yếu. Đây chính là lý do `knowledge/system/` bị cấm ở QA-runtime.

---

## 12. Một câu luật vàng cho mọi tri thức đi vào hệ

Mỗi mẩu tri thức, dù từ đâu tới, phải trả lời đúng một câu: **"Cái này nói HOW hay nói WHAT?"** — rồi đi
qua đúng một trong ba cửa:

- Nói **HOW** (cách drive, nơi quan sát, cách chụp, cách dọn) → **an toàn** → `knowledge/*.md`.
- Nói **WHAT** (kết quả nào đúng, cái gì đã/chưa build) → **độc** (nó thay SPEC làm oracle) →
  chỉ `knowledge/system/*.md`, build-time, kèm `source_hash`.
- Nói **"chưa biết"** → **an toàn** → `OPEN-QUESTIONS.md`. Nó không phán đúng/sai, chỉ nói *"đi hỏi người"*.

---

## 13. Muốn biết X → mở file Y

| Muốn biết | Mở |
|---|---|
| **Cài đặt từ máy trắng → chạy được** (deps, credentials, GitNexus) | [`SETUP.md`](docs/SETUP.md) |
| Đang làm tới đâu, việc gì tiếp (dành cho Claude) | `docs/STATE.md` |
| Cơ khí kho tri thức: lệnh stale, front-matter, `confidence`, grow/maintain sâu | [`KNOWLEDGE-STRATEGY.md`](docs/KNOWLEDGE-STRATEGY.md) |
| 5 repo nối nhau ra sao · cách dùng GitNexus | `../CLAUDE.md` (workspace) |
| Luật cho Claude khi chạy test | `CLAUDE.md` · `.claude/skills/qa-brain/SKILL.md` |

**Kho lưu — không nằm trên đường đọc:** `plans/` · `superpowers/`.

---

## 14. Hai luật giữ cho tài liệu không loạn lại

> **Luật 1 — Doc là ảnh chụp hiện tại, không phải nhật ký.** Có cái mới → **sửa tại chỗ cũ**. Cấm
> `## Cập nhật ngày…` / `## 📥 Nhập từ…`. Lịch sử đã có `git log`.

> **Luật 2 — Mỗi khái niệm có đúng 1 nhà.** Chỗ khác chỉ được **link**, cấm chép lại.

Ai thêm/sửa doc thì đọc lại 2 luật này trước.
