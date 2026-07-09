# Dọn `docs/` — một cửa vào, mỗi khái niệm một nhà

> Ngày: 2026-07-09 · Trạng thái: **đã duyệt + rà lại sau Phase 0–4, chờ thực thi**
> Vấn đề: 6 doc trong `docs/` + `CLAUDE.md` kể lại cùng 7 khái niệm; không có điểm bắt đầu;
> `QA-SERVER.md` tự mâu thuẫn với chính nó.
>
> **Bản rà 15:2x** bổ sung: §2b (`knowledge/` không sạch) · `SPEC-GAP` + harness-stale vào bảng §4 ·
> ngoại lệ thứ 3 (giữ workspace §3, gỡ §8 — hai loại lỗ khác nhau) · `plans/`+`superpowers/` vào §5 ·
> §6 đừng nói "thành cơ chế" · §7 thêm bước kiểm **hành vi** (TestCase-11 → 9 PASS/8 FAIL).

---

## 1. Chẩn đoán

Bệnh **không** phải "nhiều chữ". Bệnh có hai nguyên nhân cơ khí:

**(a) Doc được viết như nhật ký.** Mỗi lần có cái mới, ta nối `## Cập nhật ngày X` ở cuối
thay vì sửa chỗ cũ. Hậu quả trong `QA-SERVER.md`:

| Đọc tới | Nó nói |
|---|---|
| §III.1 (dòng 76) | "Hệ thống có **2 loại tri thức, 2 tầng**" |
| §IX.1 (dòng 272) | "Tri thức **2 tầng**" |
| §X.1 (dòng 302) | "**Ba tầng** tri thức, **không phải hai**" |

Người đọc từ trên xuống học sai ở dòng 76, bị đính chính ở dòng 302.

**(b) Luật "1 tri thức = 1 nhà" chưa bao giờ được áp cho `docs/`.**
Luật này đã tồn tại ở `KNOWLEDGE-STRATEGY.md` §4.6 và được áp cho `knowledge/` — nên `knowledge/`
khá sạch. `docs/` thì không ai áp.

Đo lại sau Phase 0–4 (2026-07-09) — **bệnh nặng hơn lúc chẩn đoán lần đầu**:

| Khái niệm | Số nơi (lần đầu) | Số nơi (nay) |
|---|:--:|:--:|
| 2 bức tường thép | 5 | 4 |
| HOW vs WHAT | 6 | 6 |
| 3 tầng tri thức | 5 | 5 |
| Ca coupon "code-trace sai, black-box đúng" | 6 | **8** |
| Ngân sách GitNexus (473) | 3 | 3 |
| Vòng maintenance | 5 | 5 |
| Access dev / creds | 3 | 3 |

Vì sao tăng: Phase 0–4 chạy song song với việc soạn spec này, và **chính nó cũng nối nhật ký**
(`QA-SERVER.md` §X · `KNOWLEDGE-STRATEGY.md` §4b · 3 khối `## 📥 Nhập từ…` trong `knowledge/`).
⇒ Luật 1 không có ai canh thì bệnh tái phát ngay trong lúc đang viết đơn thuốc.

**(c) Bản đồ chỉ đường dài 7 chặng.** `STATE.md` §0 bảo người mới đọc 7 file để hiểu hệ thống.

---

## 2. Mục tiêu / Không phải mục tiêu

**Mục tiêu**
- Sếp mở **đúng 1 file** (`docs/README.md`) là hiểu hệ thống, đủ để gật đầu.
- Mỗi khái niệm có **đúng 1 nhà**; chỗ khác chỉ link.
- Không doc nào tự mâu thuẫn khi đọc từ trên xuống.
- Doc "có hạn" được đóng dấu rõ, người mới biết bỏ qua.

**KHÔNG phải mục tiêu**
- Không viết lại `MERGE-PLAN.md` (chỉ thêm banner).
- Không đụng **nội dung nghiệp vụ** của `knowledge/` (Phase 3 đã phân loại đúng 3 cửa).
  ⚠️ Nhưng **hình thức** của `knowledge/` thì phải dọn — xem §2b.

> **Cập nhật thực tại (commit `822d5dd` + `e7891be` + `6561b56`, 2026-07-09 14:59):**
> Phase 3–4 **đã xong** trong lúc soạn spec này. `.claude-tester/` đã archive (`0119159`) rồi xoá.
> `knowledge/` mọc thêm 5 file: `playbook.md` · `features.md` (HOW, draft) và
> `system/api-endpoints.md` · `system/domain-rules.md` · `system/ui-theme.md` (WHAT, cấm đọc).

## 2b. `knowledge/` KHÔNG sạch — hai lỗi hình thức phải sửa

Phase 3 phân loại nội dung đúng, nhưng để lại rác:

**(a) Nhật ký trong `knowledge/` (vi phạm Luật 1).** Ba file có khối `## 📥 Nhập từ .claude-tester/…`
treo ở cuối thay vì hoà vào thân bài:
`system/customer-sync.md:57` · `system/coupon-sc.md:46` · `system/OVERVIEW.md:76`.
→ Hoà vào thân bài. Xoá tiêu đề `## 📥 Nhập từ…`.

**(b) 12 file trỏ tới thư mục đã xoá.** `grown_from:` và các link trong `knowledge/` còn trỏ
`.claude-tester/<path>` — thư mục **không còn tồn tại** (xoá ở `822d5dd`).
→ Đổi thành trỏ commit: `grown_from: "0119159:.claude-tester/<path>"`.
Tra lại bằng `git show 0119159:.claude-tester/<path>`.

---

## 3. Hai luật gốc (chống tái phát)

> **Luật 1 — Doc là ảnh chụp hiện tại, không phải nhật ký.**
> Có cái mới → **sửa tại chỗ cũ**.
> Cấm mọi tiêu đề dạng nhật ký: `## Cập nhật ngày…` · `## Phần X — Cập nhật…` · `## 📥 Nhập từ…`
> · `## Bổ sung…`. Lịch sử đã có `git log` giữ hộ.
> Áp cho **cả `docs/` lẫn `knowledge/`** (`knowledge/` đã dính 3 lần — xem §2b).

> **Luật 2 — Mỗi khái niệm có đúng 1 nhà.**
> Chỗ khác chỉ được **link**, cấm chép lại. (Đã có ở `KNOWLEDGE-STRATEGY.md` §4.6 —
> nay áp cho cả `docs/` và `CLAUDE.md`.)

Ghi cả hai luật vào đầu `docs/README.md`.

---

## 4. Chia nhà cho từng khái niệm

| Khái niệm | **Nhà duy nhất** | Chỗ khác |
|---|---|---|
| Vấn đề oracle (vì sao không test từ code) | `QA-SERVER.md` §I | README tóm 3 dòng + link |
| 2 bức tường thép | `docs/README.md` | `CLAUDE.md` giữ 2 dòng (máy thi hành); còn lại link |
| HOW vs WHAT | `QA-SERVER.md` §III | link |
| 3 tầng tri thức | `KNOWLEDGE-STRATEGY.md` §0 | README tóm bảng 3 dòng + link |
| **`SPEC-GAP` — kết quả thứ tư** | `QA-SERVER.md` (cạnh 3 tầng tri thức) | README §7 (1 dòng) · `METHOD.md` giữ adapter "coverage ≠ oracle" |
| **Ca coupon 9 PASS** | `QA-SERVER.md` §IX | mọi nơi khác link |
| Ngân sách GitNexus (473) | `KNOWLEDGE-STRATEGY.md` §1 | STATE + QA-SERVER bỏ, chỉ link |
| Vòng maintenance | `KNOWLEDGE-STRATEGY.md` §3 | `CLAUDE.md` 1 dòng |
| **Harness-stale (`source_hash` mù)** | `KNOWLEDGE-STRATEGY.md` §3 (hoà vào maintenance) | hiện treo rời ở §4b → gỡ |
| Access dev / creds | `STATE.md` §5 | `CLAUDE.md` link |
| **5 repo nối nhau + cách dùng GitNexus** | workspace `CLAUDE.md` §2/§3/§6 | `threease_qa` **không chép**, chỉ trỏ — **ngoại lệ 3, xem dưới** |
| GitNexus → sản phẩm knowledge | `KNOWLEDGE-STRATEGY.md` §1–2 | link |
| Ground truth sync backend↔ticket | `knowledge/system/customer-sync.md` | workspace `CLAUDE.md` §8 → 1 dòng trỏ (xem §6) |

**Hai khái niệm mới (sinh ra ở Phase 0–4, chưa từng có nhà):**

- **`SPEC-GAP`** — hệ giờ có **4 kết quả**, không phải 3: `PASS` · `FAIL` · `未実施` (**không quan sát
  được**) · `SPEC-GAP` (**quan sát được nhưng SPEC không định nghĩa kỳ vọng** → không bịa `expect`).
  Đang nằm rải ở 13 file (`theme.json`, `build_evidence.py`, `SKILL.md`, `METHOD.md`, 3 command…).
  Đây là thay đổi **user-visible** — sếp sẽ hỏi ngay. Phải có nhà + 1 dòng ở README.
- **Harness-stale** — `source_hash` chỉ bắt *code đổi*. Đổi `locale` trong `pw_lib` làm **mọi doc
  `kind: flow`** sai, mà code sản phẩm không đổi dòng nào (đã xảy ra thật với `pro-open-booking.md`).
  ⇒ Ba loại stale, chỉ 1 loại tự động bắt được. Thuộc mục maintenance.

### Hai quyết định đi ngược trực giác

**(a) Ca coupon về `QA-SERVER.md`, không ở lại `SYSTEM-COMPARISON.md`.**
Nó đang được kể hay nhất ở `SYSTEM-COMPARISON.md` Phần III — nhưng file đó **có hạn, sẽ archive**.
Đặt bằng chứng nền tảng vào file sắp chết là sai. `SYSTEM-COMPARISON` link ngược lại.

**(b) `QA-SERVER.md` §VIII bị xoá thẳng**, không phải vì trùng, mà vì nó là **WHAT** (mô tả code
làm gì, có tên file). WHAT không sống trong `docs/`. Nhà của nó: `knowledge/system/customer-sync.md`.

### Ba ngoại lệ có chủ ý (ghi rõ lý do tại chỗ, kèm dòng "đây là ngoại lệ của Luật 2")

**(1) `STATE.md` §6** ("7 nguyên tắc bất di") **giữ nguyên** dù trùng README. Lý do: `STATE.md` là
file Claude đọc đầu mỗi phiên để biết "đang đứng đâu"; bắt nó nhảy file để đọc luật là sai mục đích.

**(2) `SYSTEM-COMPARISON.md` giữ nguyên toàn bộ nội dung**, kể cả những đoạn trùng README/QA-SERVER.
Lý do: đây là doc **mang đi trình sếp** — nó phải **đứng một mình đọc được**, không bắt người đọc
mở file khác. Nó chấp nhận trùng để đổi lấy tính độc lập. (Chỉ thêm banner "có hạn".)

**(3) Workspace `CLAUDE.md` §3 (cách dùng GitNexus) GIỮ NGUYÊN**, dù chính file này bị §6 gọi là
lỗ tường thép. Đây **không** phải mâu thuẫn — `§8` và `§3` là **hai loại lỗ khác nhau**:

| | Nó đưa gì cho con QA | Xoá chữ có bịt được không? |
|---|---|---|
| **`§8`** (sync backend↔ticket) | **CÂU TRẢ LỜI** — cơ chế + tên file code. Đây là **WHAT** = chất độc. | ✅ Có. Gỡ đi là hết. |
| **`§3`** (cách gọi `query`/`impact`) | **ĐỒ NGHỀ** — mô tả cách dùng tool. | ❌ **Không.** GitNexus đã nằm trong tay QA qua **MCP server**, bất kể doc viết gì. |

Xoá `§3` = mất một mục tra cứu tiện tay cho 4 repo còn lại, mà **lỗ vẫn nguyên** (tool vẫn gọi được).
Cách chặn thật là **cấm gọi tool**, không phải **cấm đọc mô tả tool** → PreToolUse hook (xem §6).

⇒ Giữ `§3`. Gỡ `§8`. Ghi 1 dòng ngay tại `§3`: *"⛔ QA-runtime không được dùng — xem
`threease_qa/.claude/skills/qa-brain/SKILL.md` § danh sách cấm."*

---

## 5. `docs/` sau khi dọn

```
docs/
├── README.md              [MỚI]      ⭐ CỬA VÀO — 2-3 trang. Hút DEMO.md vào.
├── QA-SERVER.md           [VIẾT LẠI] đào sâu triết lý. Gỡ §VIII/§IX/§X. ~200 dòng.
├── KNOWLEDGE-STRATEGY.md  [TỈA]      vòng đời tri thức: 3 tầng · grow · maintain · GitNexus
├── STATE.md               [TỈA]      chỉ "đang ở đâu, làm gì tiếp". Gỡ §0 (chuỗi 7 file).
│
├── SYSTEM-COMPARISON.md   [BANNER]   ⏳ HẾT HẠN RỒI (Phase 4 xong 822d5dd). Nội dung giữ nguyên.
├── MERGE-PLAN.md          [BANNER]   ⏳ HẾT HẠN RỒI.
├── DEMO.md                [XOÁ]      → về README.md
│
├── plans/                 [ARCHIVE]  kế hoạch cũ — README ghi 1 dòng "bỏ qua"
└── superpowers/           [ARCHIVE]  spec/plan cũ (kể cả file này) — README ghi "bỏ qua"
```

⚠️ `plans/` và `superpowers/` **có thật** trên đĩa. Bản vẽ cũ bỏ sót → người mới mở `docs/` sẽ lạc.
README phải nói rõ chúng là kho lưu, không phải đường đọc.

Đường đọc cho sếp: **1 file**. Cuối README có bảng *"muốn biết X → mở file Y"*.

### `docs/README.md` — dàn bài (2–3 trang)

1. **Nó là gì** — 3 câu. SPEC → test chạy thật → PASS/FAIL + ảnh.
2. **Vấn đề oracle** — vì sao không được sinh test từ code (tautology). ~5 dòng + link `QA-SERVER.md` §I.
3. **2 bức tường thép** (nhà chính ở đây).
4. **3 tầng tri thức** — bảng 3 dòng: HOW ✅ / WHAT ⛔ / CHƯA BIẾT ✅. Link `KNOWLEDGE-STRATEGY.md`.
5. **Vòng đời** — 1 sơ đồ: build-time ↔ QA-runtime.
6. **Bằng chứng** — ca coupon 9 PASS + ca guard vé (từ `DEMO.md`). Link `QA-SERVER.md` §IX.
7. **Pipeline + chuẩn evidence** — command `testcase-*`, xlsx 3 sheet, 2 ảnh/case.
8. **Bảng "muốn biết X → mở file Y"**.
9. **Hai luật gốc** (§3 của spec này).

### `CLAUDE.md` (threease_qa) — tỉa

Chỉ giữ **luật thi hành cho máy** + trỏ `docs/README.md`. Bỏ phần chép lại triết lý.

---

## 6. Thay đổi ngoài `threease_qa/` (quyết định B)

**Phát hiện:** workspace `/Users/tritdd/Work/ThreeSides/CLAUDE.md` được Claude Code **nạp tự động
vào mọi phiên**, kể cả phiên `/testcase-run` đang chạy test mù code. `§8` của nó
("Ground truth: backend ↔ ticket customer/master sync") là **WHAT thuần tuý** — sơ đồ cơ chế sync
+ tên file code.

⇒ Con QA đã đọc code (gián tiếp) từ token đầu tiên, mọi phiên. Đây là lỗ tường thép **to hơn**
lỗ `L6` mà docs đang mô tả (`.claude-tester/` — thứ phải `grep` mới trúng).

### ⚠️ Một khẳng định sai phải sửa

`docs/STATE.md:88` (commit `e7891be`) đang ghi:

> *"`.claude-tester` không còn trong working tree ⇒ bức tường thép thành **cơ chế**."*

**Sai.** Xoá `.claude-tester/` chỉ bịt lỗ *phải đi tìm mới trúng*. Lỗ *tự chui vào* — workspace
`CLAUDE.md` §8, nạp tự động mọi phiên — vẫn nguyên. Tường thép **vẫn là văn bản**.

Đây là lần thứ **ba** cùng một dạng lỗi trong dự án (lần 1: guard vé-đã-dùng; lần 2: coupon report):
**nhầm "cái quan sát được" với "cái tồn tại"**. Lần này nó tự cắn mình — xoá được thứ nhìn thấy
nên tưởng đã kín.

⇒ Sửa `STATE.md:88` và `SYSTEM-COMPARISON.md` (L6).

### ⚠️ Nhưng ĐỪNG thay bằng một câu sai khác

Gỡ `§8` **không** làm tường thép thành cơ chế. Nó chỉ làm **văn bản sạch hơn**.
Cơ chế thật = **PreToolUse hook** chặn `Read`/`Grep` vào `knowledge/system/**` + 5 repo sản phẩm,
và chặn mọi tool GitNexus, khi đang chạy `/testcase-run`. **Chưa ai làm.**

Câu đúng để ghi vào `STATE.md` + `SYSTEM-COMPARISON.md`:

> *"Lỗ tự-nạp (workspace `CLAUDE.md` §8) đã bịt. Lỗ phải-grep-mới-trúng (`.claude-tester/`) đã bịt.
> Tường thép **vẫn là văn bản**. Cơ chế = PreToolUse hook — **chưa làm**."*

Ba lần cùng một dạng lỗi (guard vé · coupon report · "xoá là kín rồi") đều là: **nhầm cái quan sát
được với cái tồn tại**. Đừng phạm lần thứ tư ngay trong câu sửa lỗi lần thứ ba.

**Hành động:**
- Chuyển nội dung §8 → `knowledge/system/customer-sync.md` (đã kiểm: file này là **superset**
  của §8 — có thêm 9 model serializer, `MAX_RETRIES=5`, cron 5 phút, known gap `handlers.py`.
  ⇒ **không mất mát**, chỉ cần xoá §8 và để lại con trỏ).
- workspace `CLAUDE.md` §8 → còn **1 dòng**: *"Sync backend↔ticket: xem
  `threease_qa/knowledge/system/customer-sync.md` (build-time only)."*
- Sửa định nghĩa `L6` trong `SYSTEM-COMPARISON.md` + `STATE.md`: lỗ chính là **file tự nạp**,
  không phải `.claude-tester/`.
- Thêm 1 câu vào `knowledge/OPEN-QUESTIONS.md`: workspace `CLAUDE.md` §3 vẫn dạy Claude cách gọi
  `query`/`impact`/`context` — đồ nghề code-trace trong tay con QA phải mù code. Chưa xử.

⚠️ Ảnh hưởng: workspace `CLAUDE.md` dùng chung cho cả 5 repo. Thay đổi này làm mất một mục tra cứu
tiện tay khi làm việc ở `threease_backend`/`threease_ticket` — đổi lại bằng 1 dòng trỏ sang.

---

## 7. Cách kiểm chứng đã xong

### Kiểm hình thức
1. `grep -rn "Cập nhật ngày\|## Cập nhật\|## 📥 Nhập từ" docs/ knowledge/` → **0 kết quả** (Luật 1).
2. Với mỗi khái niệm ở bảng §4: `grep -rn` ra **đúng 1 file có nội dung**, các file kia chỉ có link.
   Trừ **3** ngoại lệ đã khai ở §4.
3. Đọc `docs/README.md` từ trên xuống, không gặp câu nào đính chính câu ở trên.
4. `docs/README.md` không quá 3 trang (~150 dòng).
5. `grep -n "ThreeaseTicketSyncJob" /Users/tritdd/Work/ThreeSides/CLAUDE.md` → **0 kết quả**.
6. Mọi link tương đối trong `docs/*.md` trỏ tới file **có thật**.
7. `grep -rn "\.claude-tester/" knowledge/` → mọi hit đều ở dạng `0119159:.claude-tester/…`
   (trỏ commit, không trỏ path đã xoá).

### ⭐ Kiểm HÀNH VI (bước quan trọng nhất — 6 bước trên chỉ kiểm hình thức)
8. **Chạy lại TestCase-11 → phải vẫn ra `9 PASS / 8 FAIL`.**

   Vì sao bắt buộc: §6 **gỡ `§8` khỏi file mà QA tự nạp mọi phiên**. Đó là đổi **hành vi**, không phải
   đổi văn bản. Nếu sau khi dọn mà con QA chấm khác đi (vd FAIL toàn bộ vì mất context, hoặc PASS
   nhiều hơn vì đọc trúng WHAT ở đâu đó) ⇒ **dọn hỏng**, hoàn tác.

   Đây là **regression test cho chính hệ QA**, không phải cho sản phẩm.
   Cách chạy + con số nền: `docs/QA-SERVER.md` §IX.

---

## 8. Còn lại sau khi spec này xong

- ~~`git rm -r .claude-tester/`~~ → **đã xong** (`822d5dd`, archive ở `0119159`).
- ~~Quyết định workspace `CLAUDE.md` §3~~ → **đã quyết: GIỮ** (ngoại lệ 3, §4). Xoá chữ không gỡ được
  tool; chặn thật phải bằng hook.
- **PreToolUse hook** — biến tường thép từ văn bản thành cơ chế: chặn `Read`/`Grep` vào
  `knowledge/system/**` + 5 repo, chặn mọi tool GitNexus, khi chạy `/testcase-run`. **Chưa làm.**
  Đây là việc lớn nhất còn lại của toàn dự án, lớn hơn dọn docs.
- Nâng `knowledge/playbook.md` + `features.md` từ `draft` → `approved` (cần UI-confirm dưới `ja-JP`).
- Dọn rác dev: preset `AIOT-TEST-105` · staff `AIOT Test105` · ticket master `AIOT-TEST-TK1`
  (`/testcase-cleanup` với `BRANCH_ID=3`).
