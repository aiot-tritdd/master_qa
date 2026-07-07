# Thiết kế — qa-brain thuần black-box + Living Business Doc

> Design doc (spec) để trình sếp. Ngày: 2026-07-07.
> Bản này quyết định *thiết kế*; kế hoạch thực thi chi tiết viết ở plan riêng.

---

## 0. Bối cảnh & vấn đề

`qa-brain` (skill hiện tại) vi phạm nguyên tắc sếp: **QA = black-box, hiểu nghiệp vụ từ
SPEC, KHÔNG đọc code.** Cụ thể SKILL.md bước C (bind `source_symbols`) và bước D (FAIL →
`context/impact` chỉ bug ở `file:line`) **kéo QA vào code**. Tệ hơn: nó thành **cây nạng** —
khi không drive nổi UI để dựng precondition, QA thụt về code-trace thay vì giải bài toán
vận hành (đúng cái đã làm hỏng `TestCase_NEW`: 19 "FAIL code-traced" thay vì evidence thật).

`docs/QA-SERVER.md` (kinh thánh) cũng **stale**: tả kiến trúc dịch vụ Python (đã xoá), và để
living doc đóng vai oracle — trái hướng "SPEC là oracle" mà hệ thống skill thực tế đang chạy.

---

## 1. Chìa khoá thiết kế: tách **"LÀM SAO vận hành"** khỏi **"ĐÚNG/SAI"**

Một hệ thống có 2 loại tri thức, ở 2 tầng khác nhau:

- **HOW — tri thức vận hành:** nút ở đâu, màn nào, bấm thứ tự gì để *làm được một thao tác*.
  → tầng **giao diện / cấu trúc UI**.
- **WHAT — tri thức hành vi:** bấm xong hệ thống *ra kết quả gì*, đúng luật không.
  → tầng **business logic**, và đây là **oracle**.

**Bug sống ở tầng WHAT, không ở tầng HOW.** Dev code sai luật "thu hồi vé" → sai *cái xảy ra
khi bấm*, chứ **không dời nút "Cancel Payment"**, không đổi các bước tạo booking.
→ **Navigation gần như miễn nhiễm với bug logic.**

Vì vậy: business doc (derive từ code) **chỉ chép tầng HOW** — tầng bug không đụng tới.
Còn **đúng/sai (WHAT)** doc **KHÔNG được đụng**; nó do **SPEC** (đúng phải thế nào) đối chiếu
**QUAN SÁT LIVE** (thực tế ra sao) quyết định.

### 3 vai — 3 nguồn sự thật, không vai nào "tin code"

| Vai | Nguồn | Bug ảnh hưởng? |
|---|---|---|
| Precondition **đúng là trạng thái gì** | **SPEC** (người viết) | Miễn nhiễm — spec độc lập code |
| **Bấm gì** để dựng | Navigation map (tầng HOW) | Miễn nhiễm — bug không dời nút |
| **Đã dựng đúng chưa** | **QUAN SÁT LIVE** so spec | Chỗ **bắt** bug: state lệch → dừng |

Hai chốt chặn đúng/sai (định-nghĩa-từ-spec, verify-bằng-mắt) **không hề đọc code**. Mảnh
code-derived duy nhất (navigation) nằm ở tầng bug-không-tới. Bug có lọt vào khâu dựng (vd
thanh toán mà vé không phát hành) → chốt quan sát live thấy state sai ngay → không chạy trên
precondition giả, thành 1 finding.

> **Ẩn dụ cho sếp:** thanh tra toà nhà. Bản vẽ (spec) bảo "cửa chống cháy phải tự đóng".
> Thanh tra đi **cầu thang** (navigation) lên tầng 3 — biết đường lên **không cần biết** cửa
> có chạy đúng không; thợ đấu sai **không dời cầu thang**. Lên tới, **nhìn bảng số tầng**
> (quan sát) để chắc đúng tầng. Rồi **đẩy cửa, nhìn** nó tự đóng không (quan sát vs bản vẽ)
> → pass/fail. Sai của thợ không bao giờ hỏng khả năng *lên tầng* hay *chấm cửa*.

---

## 2. Kiến trúc: tách VAI + tách THỜI ĐIỂM

```
BUILD-TIME  (được đụng code)                RUNTIME  (mù code tuyệt đối)
┌────────────────────────────────┐         ┌──────────────────────────────────┐
│  "Người vẽ bản đồ" (cartographer)│        │  QA                              │
│  GitNexus + CLAUDE.md system-docs│  ──►   │  đọc: SPEC (oracle)              │
│  + BẮT BUỘC UI-confirm mỏng      │ living │        + Living Business Doc (HOW)│
│  → Living Business Doc            │  doc   │  KHÔNG đụng GitNexus/code         │
│  → NGƯỜI DUYỆT (status: approved) │ đã duyệt│  drive UI → quan sát → so SPEC   │
│  + source_hash (staleness)       │        │  → FAIL báo hành vi + ảnh        │
└────────────────────────────────┘         └──────────────────────────────────┘
```

**3 lằn ranh thép** (để đúng nguyên tắc "QA không cần biết gì về code"):
1. Cartographer **không phải QA** — là bước soạn tài liệu (như tech-writer/BA), chạy offline,
   **có người duyệt**. Lúc QA chạy test thì graph đã đóng.
2. Nội dung doc mà QA đọc = **CÁCH DRIVE + KÊNH QUAN SÁT (navigation) THÔI**. Cấm ghi kết quả
   kỳ vọng / luật pass-fail (đó là SPEC + quan sát live).
3. `source_symbols`/`source_hash` = **metadata provenance/staleness**, QA **không đọc** — QA
   đọc văn xuôi nghiệp vụ.

Núm độ thuần đã chốt: **Graph là tác giả chính + CLAUDE.md trám luồng xuyên hệ + BẮT BUỘC
UI-confirm mỗi flow mới `approved`.** (GitNexus map tốt Nuxt/Django/jobs nhưng **0 link**
Rails-route & HTTP Pro→backend→ticket — §3 CLAUDE.md — nên phần xuyên hệ trám bằng system-docs
+ mắt.)

---

## 3. Living Business Doc (hồi sinh system-map của sếp)

Vị trí: `knowledge/`. Frontmatter giữ schema cũ + thêm `ui_confirmed_at`:

```yaml
---
id: issue-ticket-pack
status: draft            # draft (máy) → approved (người + UI-confirm) → stale (code đổi)
kind: flow               # flow (navigation) | channels (observation)
spans_repos: [pro, backend, ticket]
source_symbols: [ ... ]  # metadata provenance — QA KHÔNG đọc
source_hash: <hash>
ui_confirmed_at: 2026-07-07
---
# Flow: Phát hành gói vé  (HOW — navigation only)
Mục tiêu nghiệp vụ: ...
Các bước UI: 1. Reservation → tạo booking → 2. thêm SP vé → 3. lưu → 4. mở hóa đơn →
             5. 現金 thanh toán → vé phát hành.
Nơi quan sát: Customer → số dư vé; ticket-admin → Packs.
```

Hai loại doc:
1. **flow** — cách DRIVE UI dựng precondition (navigation).
2. **channels** — quan sát gì → ở UI nào (bảng ở §5).

🔒 **Firewall:** cấm ghi kết quả kỳ vọng/luật nghiệp vụ. Chỉ thao tác + nơi quan sát.

**Staleness:** code đổi → `source_hash` lệch → doc gắn `stale` → phải **re-derive + re-confirm
UI** trước khi QA tin lại. (Hồi sinh ý tưởng `/testcase-stale` của sếp.)

---

## 4. Precondition Protocol (xương sống — thứ đang thiếu)

Mỗi test case, trước khi chạy:

1. **Định nghĩa** trạng thái precondition từ **SPEC (ô `pre`)** — nghiệp vụ, không code.
2. **Dựng** bằng flow trong Living Business Doc. ⚠️ **Dùng flow CŨ đã chạy ổn** (tạo booking,
   thanh toán, phát hành) — **KHÔNG dùng feature MỚI đang test** → code sai của feature mới
   không đụng khâu dựng.
3. **Verify bằng mắt**: quan sát trạng thái thật (Pro UI + ticket-admin) đối chiếu spec.
   **Khớp → sẵn sàng chạy. Lệch → KHÔNG chạy** (và nếu chính khâu dựng lệch spec → 1 finding).

---

## 5. Kênh quan sát black-box (`knowledge/observation-channels.md`)

| Quan sát | Kênh (UI) | Login |
|---|---|---|
| Booking / hóa đơn / số dư vé (Pro) | develop.pro.threease.com | TESTSEED001/STAFF001 |
| Gói vé, 使用履歴, trạng thái | **ticket-dev.threease.com/admin** | admin/password123 |
| Vé phía khách | ticket-dev.threease.com | TESTSEED001/STAFF001 |

Sync Pro→ticket: chờ N giây → quan sát ticket-admin (**không** đọc DB/code).
`pw_lib.js` thêm target `ticket_admin`.

---

## 6. Vòng đời skill (giữ khung sếp: write → run → cleanup → retest)

- **Bỏ bước C** (`source_symbols`) → **seam từ SPEC + Living Business Doc**.
- **Bỏ bước D** (`context/impact` chỉ `file:line`) → **FAIL báo hành vi + ảnh 2 phía**.
- **Feature chưa build → FAIL behavioral**: quan sát "màn không có nút / behavior không xảy ra"
  + ảnh cái *absence*. Không suy đoán "chưa code" (đó là code-knowledge) — chỉ báo cái quan sát.
- **Schema `tcs.json` GIỮ NGUYÊN**; `build_evidence.py` không đụng.

---

## 7. Files thay đổi

- **Rewrite:** `.claude/skills/qa-brain/SKILL.md` (bỏ GitNexus khỏi vai QA; ghim §1–§6).
- **New:** `knowledge/<flow>.md` (mẫu), `knowledge/observation-channels.md`; thủ tục/command
  "soạn Living Business Doc" build-time (GitNexus + UI-confirm + approval).
- **Edit:** `.claude/skills-scripts/testcase-evidence/pw_lib.js` (+`ticket_admin`);
  `CLAUDE.md` (phần qa-brain: thay GitNexus bằng Living Business Doc + Precondition Protocol).
- **Reconcile (bắt buộc):** `docs/QA-SERVER.md` — xem §8.
- **KHÔNG đụng:** `build_evidence.py`, schema `tcs.json`, các command đã black-box.

---

## 8. Reconcile `docs/QA-SERVER.md` (kinh thánh) — deliverable bắt buộc

QA-SERVER.md phải **khớp 100%** cái đang build. Giữ triết lý (đã đúng), sửa các chỗ stale:

- **WHAT/kiến trúc:** thay mô tả dịch vụ Python (`qa/extractor·testgen·runner`, FastAPI,
  Next.js Ghibli — đã xoá) bằng **skill Claude Code**: `qa-brain` + `testcase-*` +
  Playwright evidence + Excel, chạy per-folder `wtf-is-this/`.
- **Oracle:** ghi rõ **oracle = SPEC** (mỗi TestCase folder có `specs.md`); Living Business Doc
  **KHÔNG phải oracle** — chỉ là navigation (HOW). Ghim §1 (HOW vs WHAT) + §4 (Precondition
  Protocol) làm nguyên tắc nền.
- **Structural/Semantic:** giữ, nhưng nói rõ Semantic-doc = navigation-only + người duyệt qua
  **UI-confirm**, không đóng vai quan tòa.
- **Roadmap/Phase tracker:** cập nhật trạng thái thật (Python MVP → skill-based).
- **Ground truth (Phần VIII):** giữ (vẫn đúng).

---

## 9. KHÔNG làm (YAGNI)

- Không auto-dựng-precondition bằng máy học UI (drive tay theo playbook là đủ).
- Không thêm trạng thái schema mới (unbuilt = FAIL, không tạo NOT-BUILT).
- Không đụng generator Excel / schema tcs.json.
- Không hồi sinh dịch vụ Python/FastAPI/Next.js.
