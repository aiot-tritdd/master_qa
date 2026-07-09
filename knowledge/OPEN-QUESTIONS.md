---
id: open-questions
status: approved
kind: registry
spans_repos: [backend, ticket, pro, admin, reservation]
source_symbols: []
source_hash: null
confidence: ⭐
verify_by: "Không cần verify — file này CHỈ chứa câu hỏi, không chứa khẳng định."
ui_confirmed_at: null
---
# OPEN QUESTIONS — "đã tra rồi mà vẫn không kết luận được"

> **Trạng thái tri thức thứ ba.** Hệ này có 3 loại tri thức, không phải 2:
>
> | Loại | Ở đâu | QA-runtime |
> |---|---|:--:|
> | **HOW** — bấm gì, xem ở đâu | `knowledge/*.md` | ✅ đọc được |
> | **WHAT** — hành vi đúng/sai, cái gì đã/chưa build | `knowledge/system/*.md` | ❌ **CẤM** |
> | **CHƯA BIẾT** — tra rồi vẫn không đủ căn cứ | **file này** | ✅ đọc được |
>
> **Vì sao QA-runtime được đọc file này mà không phá Tường thép #2:** nó **không phán đúng/sai**.
> Nó chỉ nói *"chỗ này chưa ai biết chắc — đừng tự tin, đừng suy diễn"*. Đó là thuốc giải cho
> suy diễn, không phải nguồn của suy diễn.
>
> **Luật vàng (mượn `SYNC_MAP.md` của sếp):**
> > *"Đây là khoảng trống **THÔNG TIN**, không phải khoảng trống **CODE**. CẦN HỎI DEV thay vì tự kết luận."*
>
> **`grep` không thấy ≠ không tồn tại.** Đã sai 2 lần (xem `docs/SYSTEM-COMPARISON.md` Phần III).

## Cách dùng
- **Thêm mục** khi: đã tra (GitNexus / doc / quan sát live) mà vẫn không kết luận được. KHÔNG ép nó
  thành "có" (→ bịa) hay "không" (→ chạy `/testcase-systemdoc` vô hạn).
- **Đóng mục** khi: dev trả lời, HOẶC lần refresh sau GitNexus/quan sát live cho câu trả lời rõ.
  Đóng thì ghi ngày + căn cứ, **không xoá** (giữ lịch sử vì sao từng không biết).
- Trạng thái: `🔴 chưa hỏi` → `🟡 đã hỏi, chờ trả lời` → `✅ đã đóng`

---

## OQ-01 — `ReportService.get_coupon_metrics()` có tồn tại không? 🟡 **thu hẹp 2026-07-09**
**Vì sao hỏi:** hai nguồn cùng ngày 2026-07-08 **mâu thuẫn trực tiếp**.

| Nguồn | Phương pháp | Kết luận |
|---|---|---|
| `0119159:.claude-tester/.claude-knowledge/REPORTING.md:7-14` | đọc code (`grep -i coupon` → rỗng) | *"CHƯA TỒN TẠI TRONG CODE"* |
| `README.md §11` + `TestCase-11` | quan sát live | **9 PASS** / 8 FAIL, khớp 100% list dev khai |
| `knowledge/ticket-coupon-reports.md` (của ta) | GitNexus + UI-confirm | `approved`, `source_symbols` **có** symbol này |

**Đã thu hẹp bằng quan sát live (regression TestCase-11):** coupon report **CÓ tồn tại** —
`/coupon-reports/sales/` và `/usage/` trả **`200`** với filter + KPI + `CSVエクスポート` + cột `発行元`.
Bốn route còn lại (`/`, `/monthly/`, `/by-store/`, `/csv-snapshots/`) trả **`404`**.
⇒ Khẳng định *"CHƯA TỒN TẠI TRONG CODE"* của `REPORTING.md` **SAI**. Thực tế: **đã build 2/5 sub-tab**.

**Câu hỏi còn lại (thu hẹp):** tên/vị trí thật của model + service là gì (vì `grep -i coupon` trên
`th/models/` ra rỗng)? → dev trả lời, hoặc `context({name:"get_coupon_metrics", repo:"threease_ticket"})`
(build-time). **Không chặn test nào nữa** — QA-runtime chấm bằng quan sát live, không bằng câu trả lời này.

## OQ-02 — Dev URL của Ứng dụng Quản trị / Widget Đặt lịch / Hệ thống Vé? ✅ **ĐÃ ĐÓNG 2026-07-09**
**Cách đóng:** tự mở thử (`curl` + đọc `<title>`) — **không cần hỏi ai**. Cả 5 URL đều sống, đúng app:

| URL | HTTP | `<title>` |
|---|---|---|
| `develop.pro.threease.com` | 200 | `threease_pro` |
| `api-dev.threease.com` | 200 | — |
| `ticket-dev.threease.com` | 302 | `ログイン \| threeaseチケット` |
| `admin-dev.threease.com` | 200 | `threease_admin` |
| `reservation-dev.threease.com` | 200 | `Threease` |

**Kết luận:** giá trị đoán sẵn trong `pw_lib.js` **ĐÚNG cả 3**. `PROJECT_MAP.md` (sếp) ghi 🟡 *"chưa xác
nhận"* — nay xác nhận rồi.
**Hệ quả:** ⛔→✅ domain 7 (Reservation widget) + domain 8 (Admin) **hết bị chặn**, UI-confirm được ngay.

> 📌 Bài học: câu hỏi này **không cần dev trả lời** — chỉ cần đi mở thử. Trước khi ghi một OQ,
> hỏi: *"tôi có tự kiểm được không?"* Nếu có → đi kiểm, đừng cất vào registry.

## OQ-03 — Sender phía Django cho sync ngược (Hệ thống Vé → Hệ thống Lõi) đã triển khai chưa? 🔴
**Đã thử:** Rails **có** receiver đầy đủ 13 event (`sync_controller.rb`, route `routes.rb:394`).
Grep `threease_ticket/` theo `requests.post|httpx.post|session.post` + 13 tên event → **không thấy** nơi gọi.
**Không kết luận được vì:** grep-không-thấy ≠ không tồn tại. Có thể (a) chưa làm, (b) nằm ngoài
`admin_api/`, (c) gọi qua Celery/queue. *(`th/services/pro_backend_sync.py` có tồn tại — cần đối chiếu.)*
**Ai trả lời:** dev backend/ticket.
**Block:** mọi case đối chiếu số dư vé/coupon **2 phía**.

## OQ-04 — Kế hoạch bổ sung handler Django còn thiếu (Pack / Ticket / Option / Coupon)? 🔴
**Bối cảnh:** Rails gửi được 9 model; Django (`admin_api/data_sync/handlers.py`) hiện chỉ có handler
cho `Customer` + `Therapist`. Model khác → Django từ chối → outbox `failed` sau `MAX_RETRIES=5`,
**không cảnh báo chủ động**.
**Không kết luận được vì:** không biết timeline, không biết có phải by-design tạm thời không.
**Ai trả lời:** dev · PM.
**Block:** kỳ vọng "sau khi phát hành vé thì Hệ thống Vé phải thấy" — **đừng giả định**.

## OQ-05 — `SYNC_START_ID = 200000` đã cấu hình đúng ở dev/staging chưa? 🔴
**Vì sao quan trọng:** pack ID **nhỏ hơn** giá trị này bị coi là dữ liệu cũ → **tự động bỏ qua** sync ngược.
Nếu dev chưa reset sequence, **dữ liệu test mới tạo có thể bị bỏ qua âm thầm** → QA thấy "không sync"
và tưởng là bug.
**Ai trả lời:** dev/devops (kiểm `config/admin_api_settings.py` ↔ backend `development.rb`).
**Block:** mọi case sync ngược trên dev.

## OQ-06 — KPI「消化SC」ở tab 販売 lọc theo kỳ **mua** hay kỳ **dùng**? 🔴
**Đã thử:** spec No.11 không nói rõ. Mockup cho ra **cùng một số `414,400`** ở cả 2 tab → nghi dùng
chung 1 query, hoặc tính sai.
**Ai trả lời:** BA / dev.
**Block:** không viết được `expect` cho case KPI này → nếu chạy sẽ ra **`SPEC-GAP`**, không phải FAIL.

## OQ-07 — Radio 表示形式 税込/税抜 ở tab 消費 có tác dụng thật không? 🔴
**Bối cảnh:** cột thuế đã bị bỏ khỏi bảng 使用記録 (thuế chỉ tính khi **mua** coupon, không tính khi **dùng** SC).
Vậy radio đó điều khiển cái gì?
**Ai trả lời:** BA / dev.
**Block:** như OQ-06 → `SPEC-GAP`.

## OQ-08 — Có ứng dụng mobile riêng cho **bệnh nhân** không? 🔴
**Đã thử:** không thấy trong 6 repo đang quản lý. Tài liệu cũ có nhắc.
**Ai trả lời:** PM.
**Block:** phạm vi hệ thống trong `system/OVERVIEW.md` (hiện liệt kê 6 hệ).

## OQ-09 — Bức tường thép vẫn là VĂN BẢN, chưa phải CƠ CHẾ 🔴 **chưa xử**
**Vấn đề:** QA-runtime "cấm đọc code / cấm GitNexus / cấm `knowledge/system/**`" hiện chỉ là luật viết
trong doc. Không có gì kỹ thuật chặn một phiên `/testcase-run` thật sự đọc chúng. Hai lỗ đã biết:
- Workspace `CLAUDE.md` §3 vẫn dạy cách gọi `query`/`impact`/`context`, và các tool GitNexus **luôn có
  sẵn** qua MCP bất kể doc viết gì. Xoá chữ không gỡ được tool.
- (Đã bịt phần văn bản: §8 ground-truth-sync đã dời sang `system/customer-sync.md`; thư mục
  `.claude-tester` đã xoá. Nhưng đó chỉ làm văn bản sạch hơn, **không** biến tường thành cơ chế.)

**Cách xử thật:** PreToolUse hook chặn `Read`/`Grep` vào `knowledge/system/**` + 5 repo sản phẩm, và
chặn mọi tool GitNexus, khi đang chạy `/testcase-run` (KHÔNG chặn lúc build-time soạn knowledge).
**Quyết định 2026-07-09:** tạm **GIỮ TEXT** (luật viết trong doc), **chưa dựng hook**. Ghi lại ở đây +
`docs/STATE.md` §3.0 để không rơi. Dựng khi có nhịp.
**Ai trả lời / làm:** user (quyết cách chặn) + build hook.
**Block:** đây là việc lớn nhất còn lại của dự án.

---

## Đã đóng
*(chưa có)*
