# .claude-knowledge — Tri thức dùng chung (Threease)

Nguồn thật duy nhất cho tri thức **không thuộc riêng 1 mảng việc** (test hay design) — dùng chung giữa
`.claude-tester/` và `.claude-task/` qua symlink. Không chứa skill/script, chỉ chứa `.md` tri thức.

| File | Nội dung | Độ ổn định |
|---|---|---|
| [PROJECT_MAP.md](PROJECT_MAP.md) | Bảng app/repo/tech stack/vai trò/nguồn sự thật/dev URL | 🟢 tech stack ít đổi, 🟡 dev URL |
| [DOMAIN.md](DOMAIN.md) | Nghiệp vụ + **bảng thuật ngữ business chuẩn** (dùng khi nói chuyện khách hàng) | 🟢 |
| [SYNC_MAP.md](SYNC_MAP.md) | Đồng bộ dữ liệu Hệ thống Lõi ↔ Hệ thống Vé — endpoint/file:line/known gaps | 🔴 có phần chưa xác nhận hết |
| [FEATURES.md](FEATURES.md) | Sổ tay tính năng — vào đâu, luồng chính, chuẩn bị data | 🟢 |
| [REPORTING.md](REPORTING.md) | Báo cáo/export/tính tiền-thuế-coupon (No.11 và liên quan) | 🔴 phần Coupon toàn bộ là spec, đã verify **chưa có trong code** |
| [UI_UX.md](UI_UX.md) | Bảng màu/font/layout/icon theo từng app — dùng khi mockup | 🟡 đổi theo release |
| [OUTPUT_LOCATIONS.md](OUTPUT_LOCATIONS.md) | Quy tắc "output ghi ở đâu" (`7.Tests/` vs `8.Tasks/`) | ⭐ quy ước cố định |

## Routing table — "Khi nào đọc file nào"
**Nguyên tắc: Knowledge-first. Source-on-demand. Không grep toàn repo nếu knowledge đã chỉ ra
file/endpoint cụ thể** — knowledge (đặc biệt `SYNC_MAP.md`/`UI_UX.md`) đã ghi sẵn `file:line`, dùng
`Read` thẳng vào đó thay vì `grep`/`Explore` lại từ đầu. Chỉ grep repo khi knowledge thật sự KHÔNG có
manh mối (không file nào được chỉ ra) hoặc fact đã cũ/nghi ngờ sai.

| Tình huống | Đọc file nào |
|---|---|
| Task/spec chung, chưa rõ phạm vi | `PROJECT_MAP.md` + `DOMAIN.md` + `FEATURES.md` |
| Vé/coupon/số dư/đồng bộ dữ liệu | `SYNC_MAP.md` |
| Report/export/tax/coupon report/No.11 | `REPORTING.md` |
| Mockup UI (Pro/Admin/Reservation/Therapists) | `UI_UX.md` |
| Mockup Hệ thống Vé/Django/`ticket` | `REPORTING.md` + đọc thẳng template/CSS trong `threease_ticket/` — **KHÔNG dùng `UI_UX.md` làm chuẩn** (chưa khảo sát nền tảng này) |
| Output path (spec/mockup/test ghi đâu) | `OUTPUT_LOCATIONS.md` |
| Thiết kế test case (`/testcase-write`) | `METHOD.md` (tester-only) + common knowledge liên quan (PROJECT_MAP/DOMAIN/FEATURES bắt buộc, SYNC_MAP/REPORTING nếu liên quan) |
| Chạy/retest/dọn test (`/testcase-run`, `/testcase-retest`, `/testcase-cleanup`) | `SYSTEM.md` + `PLAYBOOK.md` + `LESSONS.md` (tester-only) + `SYNC_MAP.md`/`REPORTING.md` nếu case liên quan |

## Open Questions / Gaps — KHÔNG tự suy đoán khi viết spec/mockup/testcase
Gom các điểm chưa xác nhận từ toàn bộ knowledge — nếu task đang làm chạm đúng điểm nào dưới đây,
**hỏi user/dev thay vì tự kết luận**:
1. **Sender phía Django cho sync ngược** (Hệ thống Vé → Hệ thống Lõi) đã triển khai chưa, nằm ở đâu
   nếu có? Rails đã có receiver đầy đủ (`SYNC_MAP.md` mục 2) nhưng chưa tìm thấy code Django gọi tới.
2. **Dev URL** của Ứng dụng Quản trị, Widget Đặt lịch, Hệ thống Vé chưa xác nhận (`PROJECT_MAP.md`
   mục "Ghi chú xác nhận còn thiếu") — chỉ có Dev URL của Ứng dụng Pro trong `7.Tests/account.txt`.
3. **No.11 Coupon report**: toàn bộ model (`CouponPack`/`CouponUsage`/`CouponTransaction`) và
   `ReportService.get_coupon_metrics()` là **spec, chưa có code** (`REPORTING.md`, đã verify
   `grep -i coupon` trên `threease_ticket/th/models/` và `reports.py` đều rỗng). Chỉ 2 field
   `sales_price_excluding_tax`/`sales_tax_amount` có thật nhưng thuộc model Ticket, không phải Coupon.
4. Kế hoạch bổ sung handler Django còn thiếu cho Pack/Ticket/Option/Coupon (`SYNC_MAP.md` mục 3) —
   chưa rõ timeline.
5. `SYNC_START_ID=200000` (`SYNC_MAP.md` mục 2) đã đúng cấu hình ở môi trường dev/staging hiện tại
   chưa — ảnh hưởng dữ liệu test mới tạo có bị bỏ qua sync ngược hay không.

## Quy ước "fact confidence" (áp dụng cho DOMAIN.md, FEATURES.md, SYNC_MAP.md, PROJECT_MAP.md, REPORTING.md)
Mỗi mục/section nên có 1 dòng khai báo:
```
Nguồn: <file/path hoặc spec đã đọc, kèm :line nếu là code> · Ngày đọc: YYYY/MM/DD ·
Độ ổn định: ⭐ (code cứng, gần như không đổi) / 🟢 (ổn định) / 🟡 (đổi theo release/spec đang review) /
🔴 (có phần suy luận/chưa xác nhận hết) · Verify bằng: <cách tự kiểm lại khi nghi ngờ>
```
Mục đích: người đọc (kể cả Claude ở phiên sau) biết ngay **tin được tới đâu** mà không phải đoán hay
grep lại toàn bộ. `UI_UX.md`/`OUTPUT_LOCATIONS.md` áp dụng tinh thần này ở mức header chung (ít fact
volatile hơn); `DOMAIN.md`/`FEATURES.md`/`SYNC_MAP.md`/`REPORTING.md` áp dụng chi tiết hơn vì nhiều
fact dễ lỗi thời (sync, spec đang review, số liệu tính toán).

## Nguyên tắc chống trùng lặp
- Mỗi loại tri thức chỉ có **1 nhà** — phát hiện nội dung trùng ở 2 file → gộp về 1 file, file kia chỉ
  để lại 1 dòng trỏ sang (đã áp dụng khi tách `SYNC_MAP.md` ra khỏi `DOMAIN.md`/`SYSTEM.md`).
- Sửa quy ước ở đâu thì sửa **đúng 1 chỗ** — các README khác (`.claude-tester/knowledge/README.md`,
  `.claude-task/README.md`) chỉ liệt kê + trỏ link, không copy nội dung.

## Ai dùng các file này
- `.claude-tester/knowledge/` — symlink toàn bộ 7 file trên (test cần đọc tất cả: nghiệp vụ, sync,
  tính năng, report, UI để đối chiếu, project map để biết hệ thống nào test ở đâu).
- `.claude-task/knowledge/` — symlink toàn bộ 7 file trên (spec/mockup cũng cần biết nghiệp vụ, tính
  năng, UI, report, sync, project map để viết spec/vẽ mockup đúng thực tế).
