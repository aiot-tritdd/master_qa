# ROADMAP — threease_qa lớn lên theo hướng nào

> Bản đồ tầm nhìn (KHÁC `STATE.md` = việc-phiên-này). Mở file này để biết *đang đứng đâu trên bức
> tranh lớn, còn mở được gì, và vì sao*. Cập nhật khi hướng đổi, không phải mỗi phiên.
> Cập nhật: 2026-07-16.

---

## 1. Vision — QA tái dùng cho MỌI dự án, không riêng ThreeSides

Đích đến: con QA này là **engine dùng lại được across nhiều dự án**, không phải đồ đóng cứng cho ThreeSides.

Chìa khoá phân loại tri thức theo *độ tái dùng*:

| Phần | Tái dùng across dự án? |
|---|---|
| **Functional** (SPEC + navigation nghiệp vụ) | ❌ riêng từng dự án |
| **a11y / Visual / Performance / Compatibility** (engine phổ quát: axe, so-ảnh, đo-timing) | ✅ gần như 100% — chạy trên web app bất kỳ |

⇒ Mỗi **type-track** build một lần, xài cho mọi dự án sau. Phần dính-dự-án chỉ còn SPEC + nav.
Đây là lý do type-track ĐÁNG đầu tư theo vision này.

---

## 2. Lưới định vị — Level × Type

Hai trục vuông góc (xem `docs/.../Deep-Guide` hoặc README §"Tầng test"):
- **Level** = zoom (Unit → Integration → System/E2E). Con hiện tại kịch trần ở **E2E/System** — vì mù code, KHÔNG thể tụt xuống.
- **Type** = phẩm chất kiểm (Functional / a11y / Visual / Performance / Security / Compatibility).

### Đang đứng đâu (2026-07-16)

```
Level: E2E/System ─── con black-box hiện tại sống ở đây
                      Unit + Integration ─── TRỐNG (chỉ whitebox mới với tới, xem §4)

Type:  Functional      ✅ có
       Accessibility   ✅ vừa build (/testcase-a11y, axe-core, oracle=WCAG)
       Security        ✅ /testcase-security (4 họ: XSS/IDOR/bypass/error-disclosure, oracle=bất biến an ninh)
       Visual          ❌ ứng viên kế
       Performance     ❌ vướng oracle (cần budget do người đặt)
       Compatibility   ❌ rẻ, giá trị tuỳ scope (đáng nhất cho widget public)
```

---

## 3. Type-track — thứ tự & trạng thái

| Track | Trạng thái | Oracle (độc lập code) | Tận dụng |
|---|---|---|---|
| Functional | ✅ core | SPEC + quan sát live | qa-brain |
| **Accessibility** | ✅ **done** (live-verify CÒN TREO — cần Docker dev) | WCAG (axe-core) | `shot()`, khuôn command |
| **Security (gom)** | ✅ **done** (live-verify CÒN TREO — cần dev) | bất biến an ninh phổ quát (XSS escaped, no 500/leak, IDOR 403/404, guard-parity) | `withApi`, khuôn a11y |
| Compatibility | ⏳ hợp vision (0 baseline) | cùng-kết-quả + không-vỡ-layout | Playwright multi-context |
| Performance | ⏳ hợp vision (ngưỡng chuẩn web mặc định) | LCP/timing < ngưỡng phổ quát | `withApi` timing |
| **Visual** | 🔨 **đang build v1** (chỉ hợp dự án MATURE) | baseline PNG đã người-duyệt | `shot()` sẵn + khuôn a11y |

**Vì sao HOÃN Visual (quyết 2026-07-16 theo vision multi-project):** Visual là track **kém "drop-in" nhất**,
ngược vision "engine đa dự án ít setup":
- Cần **baseline curated PER-PROJECT** (chụp + gật + mask data động + maintain) → setup lặp mỗi dự án.
- **Regression-only** — dự án mới chưa có baseline thì chưa nói được gì (mà QA generic hay rơi vào "dự án mới đúng spec không" — chỗ Visual mù).
- **Noise cao nhất** (font/anti-alias/data động) → người không rành tune sẽ ngó lơ → track chết.
- Đối chiếu a11y: WCAG = oracle tuyệt đối + phổ quát + **0 setup** → đó mới là hình mẫu "reusable".
⇒ Visual **đáng cho dự án trưởng thành/ổn định chạy lặp nhiều** (ThreeSides về sau), KHÔNG phải track kế tiếp
cho vision đa-dự-án. Ưu tiên trước: **Performance · Compatibility · Security-gom** (0 setup per-project, oracle phổ quát).

**⚠️ Giới hạn auto-mask (live-verify 2026-07-17):** `explorer.js dynamic`/`detectDynamic` chỉ bắt **động
TRONG-phiên** (đồng hồ/spinner/animation tự nhảy giữa 2 snapshot cùng-trạng-thái). Nó **KHÔNG thấy
"động XUYÊN-phiên"**: dữ liệu bảng đổi khi tester thêm/xoá data, số dư đổi theo ngày. Trên màn data-heavy
(vd coupon list, 顧客詳細) auto-mask trả `[]` (tưởng tĩnh) nhưng baseline vẫn **FAIL-giả** khi data đổi →
phải re-bless. Muốn hết noise phải **mask vùng-data tay** (điều user không thích) hoặc chỉ bless màn UI ổn định.
Đây là lý do thực nghiệm củng cố "Visual = dự án mature/ổn định".

**Bỏ qua (quyết 2026-07-16):**
- **Analyzer** (gom cụm bug) — sổ mới 11 bug/1 nguồn, ad-hoc "kêu Claude nhóm giùm" là đủ tới khi sổ lớn. Đóng gói = YAGNI.
- **PreToolUse hook** (biến tường thép thành cơ chế) — OQ-09, để sau.

---

## 4. Kiến trúc 2-con — black-box (nay) + whitebox (tương lai)

**Ý tưởng cần build, ghi lại kẻo rơi.**

Con hiện tại mù code ⇒ **cấu trúc không thể** phủ đáy pyramid (Unit/Integration). Muốn phủ ⇒ **con thứ hai**:

```
threease_qa (black_box)      Level E2E/System · MÙ code · oracle = SPEC + quan sát live
threease_qa_whitebox (MỚI)   Level Unit + Integration · ĐỌC code · GitNexus lúc RUNTIME
```

Tách đôi = giữ **linh hồn mỗi con sạch**: tường chống-tautology của black-box không bị nhiễm; con whitebox
tự do đọc code. GitNexus đã index 5 repo → whitebox có code-graph sẵn.

**Mô hình 2-con hồi sinh mấy nguồn đã "khai tử" cho black-box:**

| Nguồn (khảo sát 2026-07-16) | Vai trong whitebox |
|---|---|
| test-automator (VoltAgent) | lõi: dựng framework unit/IT, coverage, CI |
| security-auditor (VoltAgent) | nhánh security white-box (SAST, audit code) |
| qa-skills: `unit-testing`, `api-testing`, `database-testing`, `contract-testing`, `coverage-analysis` | bị CẤM ở black-box, HỢP LỆ ở whitebox |
| qa-expert | strategy chung 2 con |

**3 cạm bẫy phải giải trước khi build whitebox:**
1. **Tautology áp thẳng vào whitebox.** Test sinh từ code = "code làm đúng cái code làm" = vô nghĩa (đúng cái
   README black-box chửi). ⇒ whitebox vẫn phải neo oracle vào **SPEC** (test tầng unit/IT nhưng kỳ vọng từ spec);
   code chỉ để *biết đường test tới đâu*, KHÔNG để *quyết đúng/sai*.
2. **Scope ×5 repo.** Unit/IT sống TRONG từng repo, bằng ngôn ngữ repo (RSpec/pytest/Jest) — 3 test-runner,
   không phải "Claude lái Playwright". Gần như 1 QA-engineer-in-a-box cho 5 codebase.
3. **Ownership.** Unit/IT thường DEV tự viết trong repo. Agent riêng viết test vào 5 repo sản phẩm = mô hình
   sở hữu khác → cần sếp/dev đồng ý, không chỉ là quyết định kỹ thuật.

**Khuyến nghị khi khởi động:** làm **1 lát mỏng trước** (vd chỉ Integration/API-contract cho 1 flow, oracle vẫn SPEC)
để thử mô hình — đừng nuốt cả đáy pyramid × 5 repo ngay.

---

## 5. Khảo sát nguồn tham khảo (2026-07-16) — dùng gì cho đâu

| Nguồn | Cho black-box | Cho whitebox |
|---|---|---|
| **petrkindlmann/qa-skills** | a11y ✅ · visual/security/perf (seed) | unit/api/db/contract/coverage |
| VoltAgent **ui-ux-tester** | seed persona Visual/UX | — |
| VoltAgent **test-automator** | — (white-box, sai tool) | 🟢 lõi |
| VoltAgent **security-auditor** | — (white-box) | 🟢 nhánh security |
| VoltAgent **qa-expert** | metrics (đã có breakdown xlsx) | strategy |
| **Testsigma** | ý 5-agent (đã rút) | — |
