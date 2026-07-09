# threease_qa — QA senior tự động, mù code

> **Đọc file này là đủ hiểu hệ thống.** Không cần mở file nào khác.
> Muốn đào sâu chỗ nào → bảng cuối trang chỉ đường.

---

## 1. Nó là gì

Repo này **không chứa code sản phẩm**. Nó chứa một **con QA senior nhân tạo**.

Đưa nó một file **SPEC**. Nó tự viết test case, tự lái app dev bằng Playwright, **quan sát bằng mắt**
như một tester thật, rồi chấm điểm kèm ảnh chụp màn hình.

Nó **không đọc một dòng code sản phẩm nào** — kể cả khi được phép.

```
specs.md  ──►  viết test case  ──►  lái app dev  ──►  quan sát  ──►  PASS/FAIL + 2 ảnh/case + Excel
 (oracle)       (mù code)          (Playwright)     (bằng mắt)
```

---

## 2. Vì sao không được sinh test từ code

Đây là lý do tồn tại của mọi thứ còn lại. Nếu bỏ qua mục này thì phần sau vô nghĩa.

Khi một hành vi thay đổi, **nhìn code không phân biệt được** đó là **bug** (đổi ngoài ý muốn) hay
**feature** (cố ý đổi). Vì "ý định đúng" **không nằm trong code** — nó nằm trong đầu người. Code chỉ
biết nó *đang* làm gì, không biết nó *nên* làm gì.

⇒ Test sinh ra từ code chỉ khẳng định *"code làm đúng cái code làm"*. Đó là **tautology** — một vòng
lặp tự khen, giá trị bằng không.

⇒ Ý định đúng = **SPEC**, do người viết. Đó là **oracle** duy nhất.

*(Chi tiết: [`QA-SERVER.md`](QA-SERVER.md) §I)*

---

## 3. Hai bức tường thép

Hai luật này không được phá. Phá là sai từ gốc, không phải sai chi tiết.

> **Tường 1 — Oracle là SPEC, không phải code.**
> Cột `expect` (kỳ vọng đúng/sai) **chỉ** suy từ spec. Lúc viết `expect`, QA mù code hoàn toàn.
> Test chỉ có nghĩa khi kỳ vọng đến từ **một nguồn độc lập với thứ đang bị test**.

> **Tường 2 — QA mù code tuyệt đối ở runtime.**
> Không đọc code, không dùng code-graph lúc test. Khi FAIL, báo cáo mô tả **hành vi**:
> *"spec bảo X, màn hình làm Y"* + ảnh. **Không bao giờ** ghi symbol / `file:line`.
> Định vị bug trong code là việc của dev.

**Trạng thái thật:** hai bức tường này hiện là **văn bản**, chưa phải **cơ chế**. Chưa có gì về mặt
kỹ thuật ngăn một phiên Claude đọc code lúc chạy test. Việc biến nó thành cơ chế (PreToolUse hook)
là việc lớn nhất còn lại — xem [`STATE.md`](STATE.md).

---

## 4. Ba tầng tri thức

Tri thức **không** chia theo chủ đề (booking / vé / coupon). Nó chia theo **quyền lực**: mẩu tri thức
này có trả lời hộ câu hỏi *"kết quả đúng là gì"* không?

| Tầng | Trả lời câu hỏi | Ở đâu | QA lúc test |
|---|---|---|:--:|
| **HOW** | bấm gì, vào đâu, xem kết quả ở đâu | `knowledge/*.md` | ✅ đọc được |
| **WHAT** | code làm gì, cái gì đã/chưa build | `knowledge/system/*.md` | ⛔ **CẤM** |
| **CHƯA BIẾT** | *"tra rồi vẫn không đủ căn cứ → hỏi người"* | `knowledge/OPEN-QUESTIONS.md` | ✅ đọc được |

**HOW an toàn** vì bug sống ở tầng WHAT: dev code sai luật nghiệp vụ thì *kết quả khi bấm* sai, chứ
dev không vì thế mà dời cái nút đi chỗ khác. Navigation gần như **miễn nhiễm với bug logic**.

**WHAT độc** không phải vì nó sai, mà vì nó **đúng theo code** — đọc nó là gián tiếp đọc code.

**CHƯA BIẾT an toàn** vì nó **từ chối** phán đúng/sai. Không có tầng này thì mọi thứ chưa biết bị ép
thành "biết rồi" → QA bịa `expect`.

*(Chi tiết + vòng đời doc: [`KNOWLEDGE-STRATEGY.md`](KNOWLEDGE-STRATEGY.md))*

---

## 5. Vòng đời — hai pha, cùng một con Claude, quyền hạn khác nhau

```
┌─ BUILD-TIME (soạn tri thức) ────────────────────────────────────────┐
│  ĐƯỢC: GitNexus · đọc code · đọc cả 5 repo                          │
│                                                                     │
│  GitNexus ──► doc [draft] ──► UI-confirm (drive app thật) ──►       │
│                                          doc [approved]             │
└─────────────────────────────────────────────────────────────────────┘
                              │
              chỉ doc [approved] ở knowledge/ (KHÔNG phải system/)
                              ▼
┌─ QA-RUNTIME (chạy test) ────────────────────────────────────────────┐
│  CẤM: code · GitNexus · knowledge/system/ · phán "đã/chưa build"    │
│  ĐƯỢC: specs.md (oracle) · knowledge/ approved · Playwright · mắt   │
│                                                                     │
│  SPEC ──► viết case ──► dựng precondition ──► lái app ──► quan sát  │
│                                                              │      │
│                        PASS · FAIL · 未実施 · SPEC-GAP  + 2 ảnh    │
└─────────────────────────────────────────────────────────────────────┘
```

**Vì sao phải tách:** cần hiểu hệ thống (không thể mò UI mù), nhưng không được để cái hiểu đó quyết
định đúng/sai. Giải pháp: **hiểu ở pha 1, quên ở pha 2**.

### Bốn kết quả, không phải ba

| Kết quả | Nghĩa |
|---|---|
| `PASS` | quan sát khớp spec |
| `FAIL` | quan sát lệch spec (kèm ảnh + mô tả hành vi) |
| `未実施` | **không quan sát được** (không vào được màn, thiếu quyền…) |
| `SPEC-GAP` | **quan sát được, nhưng SPEC không định nghĩa kỳ vọng** |

`SPEC-GAP` là finding **giá trị cao nhất** của QA mù code: bằng chứng rằng **spec chưa nghĩ tới**.
Gặp nó thì **không bịa `expect`** — ghi nhận và hỏi người.

---

## 6. Bằng chứng: nó hoạt động, và code-trace thì không

Hai ca thật, cùng chứng minh một điều.

**Ca 1 — Coupon report (TestCase-11, 2026-07-08).** Test mù code, mù cả danh sách dev khai.
Kết quả **9 PASS / 8 FAIL** → đối chiếu list dev khai "đã làm / chưa làm": **khớp 100%**, đến chi tiết
*"tab 販売 làm 1 phần: Report ✅ / 過去のCSV ❌"* cũng bắt đúng.
Cùng ngày, một hệ khác **đọc code** (`grep -i coupon` → rỗng) kết luận *"coupon report CHƯA TỒN TẠI
TRONG CODE"*. Một tính năng không tồn tại thì không thể có 9 case PASS.

**Ca 2 — Guard "vé đã dùng".** Code-trace qua GitNexus → kết luận *"chưa build"* → **SAI**.
Black-box lái app thật → guard **đã build, chạy đúng**, chặn với nguyên văn tiếng Nhật.
Và còn bắt được **bug thật** mà code-trace không thấy: luồng Remove lộ raw i18n key
`reservations.used_ticket_cannot_remove` thay vì câu tiếng Nhật.

> **`grep` không thấy ≠ không tồn tại.** Đã sai **2 lần**. Code có thể ở chỗ khác, tên khác, sinh
> động lúc runtime, hoặc index code-graph yếu.

*(Chi tiết: [`QA-SERVER.md`](QA-SERVER.md) §IX)*

---

## 7. Dùng nó thế nào

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

**Precondition Protocol** — trước mỗi case: định nghĩa tiền đề *từ SPEC* → dựng bằng **flow CŨ đã
chạy ổn** (không dùng feature đang test) → **verify bằng mắt** rồi mới chạy.

Truy cập dev + tài khoản: [`STATE.md`](STATE.md) §5.

---

## 8. Muốn biết X → mở file Y

| Muốn biết | Mở |
|---|---|
| Đang làm tới đâu, việc gì tiếp | [`STATE.md`](STATE.md) ← **đọc đầu mỗi phiên** |
| Vì sao oracle phải là SPEC · HOW vs WHAT · 2 ca code-trace sai | [`QA-SERVER.md`](QA-SERVER.md) |
| Tri thức grow/maintain ra sao · 3 loại stale · GitNexus dùng làm gì | [`KNOWLEDGE-STRATEGY.md`](KNOWLEDGE-STRATEGY.md) |
| 5 repo nối nhau ra sao · cách dùng GitNexus | `../../CLAUDE.md` (workspace) |
| Luật cho Claude khi chạy test | `../CLAUDE.md` · `.claude/skills/qa-brain/SKILL.md` |

**Kho lưu — không nằm trên đường đọc, bỏ qua khi tìm hiểu hệ thống:**

| Thư mục / file | Là gì |
|---|---|
| [`SYSTEM-COMPARISON.md`](SYSTEM-COMPARISON.md) · [`MERGE-PLAN.md`](MERGE-PLAN.md) | ⏳ doc dự án merge — **đã hết hạn** (Phase 4 xong) |
| `plans/` · `superpowers/` | spec + kế hoạch cũ |

---

## 9. Hai luật giữ cho tài liệu không loạn lại

> **Luật 1 — Doc là ảnh chụp hiện tại, không phải nhật ký.**
> Có cái mới → **sửa tại chỗ cũ**. Cấm mọi tiêu đề dạng `## Cập nhật ngày…` / `## 📥 Nhập từ…`.
> Lịch sử đã có `git log` giữ hộ.

> **Luật 2 — Mỗi khái niệm có đúng 1 nhà.**
> Chỗ khác chỉ được **link**, cấm chép lại.

Bệnh cũ: 7 khái niệm bị chép 4–8 lần, `QA-SERVER.md` tự mâu thuẫn với chính nó, và bản đồ chỉ đường
dài 7 chặng. Hai luật trên là thuốc. Ai thêm doc mới thì đọc lại chúng trước.

Ngoại lệ có chủ ý (đã cân nhắc, đừng "dọn" đi):
`STATE.md` §6 lặp lại 7 nguyên tắc · `SYSTEM-COMPARISON.md` lặp lại nhiều thứ để **đứng một mình
đọc được** khi mang đi trình bày.
