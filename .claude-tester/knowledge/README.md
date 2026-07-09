# Knowledge Base — Tester (Threease)

Tri thức cố định để skill "hiểu hệ thống" mà không phải grep lại code mỗi lần —
mục tiêu là train Claude thành "tester có kinh nghiệm lâu năm" trên chính hệ thống Threease.
11 file — **7 file common** (symlink từ `.claude-knowledge/`, dùng chung với `.claude-task/`) +
**4 file chuyên dụng tester** (`METHOD/SYSTEM/PLAYBOOK/LESSONS`, chỉ tồn tại ở đây). Định nghĩa đầy đủ
7 file common: xem [`../../.claude-knowledge/README.md`](../../.claude-knowledge/README.md).

### 7 file common (đọc trước — nền tảng dùng chung mọi mảng việc)
| File | Nội dung | Ổn định |
|------|----------|---------|
| [PROJECT_MAP.md](PROJECT_MAP.md) 🔗 | Bảng app/repo/tech/vai trò/nguồn sự thật/dev URL | 🟢 |
| [DOMAIN.md](DOMAIN.md) 🔗 | Nghiệp vụ Threease (締め, 回数券, quyền, kế toán) + thuật ngữ business | 🟢 |
| [SYNC_MAP.md](SYNC_MAP.md) 🔗 | Đồng bộ Hệ thống Lõi ↔ Hệ thống Vé — endpoint/file:line/known gaps | 🔴 có phần chưa xác nhận |
| [FEATURES.md](FEATURES.md) 🔗 | Sổ tay tính năng — vào đâu, luồng chính, chuẩn bị data, bẫy thao tác | 🟢 |
| [REPORTING.md](REPORTING.md) 🔗 | Báo cáo/export/tính tiền-thuế-coupon (No.11 — phần Coupon chưa có code) | 🔴 |
| [UI_UX.md](UI_UX.md) 🔗 | Bảng màu/font/layout theo từng app (dùng khi đối chiếu UI) | 🟡 |
| [OUTPUT_LOCATIONS.md](OUTPUT_LOCATIONS.md) 🔗 | Quy tắc "output ghi ở đâu" (`7.Tests/` vs `8.Tasks/`) | ⭐ |

### 4 file chuyên dụng tester (đọc sau — sâu vào việc chạy test)
| File | Nội dung | Ổn định |
|------|----------|---------|
| [METHOD.md](METHOD.md) | Kỹ thuật test bất biến (boundary, negative, data-integrity…) | ⭐ Không đổi |
| [SYSTEM.md](SYSTEM.md) | URL, auth, branch, endpoint, selector | 🟡 Đổi theo release — **verify trước khi dùng** |
| [PLAYBOOK.md](PLAYBOOK.md) | "Cách làm X" cụ thể (tạo booking đã TT, số dư vé, `shot()`, thứ tự cleanup) | 🟡 Đổi theo UI |
| [LESSONS.md](LESSONS.md) | Bài học / war stories tích luỹ, có ngày | 🔴 Tăng liên tục |

> 🔗 = symlink sang `../../.claude-knowledge/` — dùng chung với `.claude-task/`. Sửa nội dung ở đâu
> cũng được (trỏ chung 1 file thật), nhưng viết **trung lập với test** vì nơi khác cũng đọc.
> `METHOD/SYSTEM/PLAYBOOK/LESSONS` là kiến thức **riêng của test**, không chia sẻ ra ngoài.

## Cách dùng
- **Không tự đọc tay** — 5 skill (`/testcase-write`, `/testcase-run`, `/testcase-upspecschange`,
  `/testcase-retest`, `/testcase-cleanup`) tự nạp đúng file cần thiết theo bảng "Skill nạp gì" dưới đây.
  (Tạo spec giờ ở `/task-spec-create` bên `.claude-task/`, không còn ở `.claude-tester/`.)
- Khi hỏi trực tiếp về hệ thống ("tính năng X ở đâu", "sync vé thế nào"...), tra `FEATURES.md`/
  `SYSTEM.md`/`SYNC_MAP.md` trước — nhưng fact có nhãn 🟡/🔴/⚠️ phải **verify lại code/live** trước khi
  trả lời chắc chắn (xem quy ước fact-confidence ở `../../.claude-knowledge/README.md`).
- Muốn thêm tri thức mới: xác định đúng file theo bảng trên rồi thêm vào cuối/đầu file tương ứng
  (không tạo file mới trừ khi thật sự là 1 loại tri thức khác biệt — xem 3 nguyên tắc bên dưới).

## Skill nạp gì
- `/testcase-write` (thiết kế) → **METHOD + DOMAIN + FEATURES** (+ SYSTEM để biết màn hình/endpoint;
  + SYNC_MAP/REPORTING nếu task liên quan vé/coupon/report).
- `/testcase-run` `/testcase-retest` (chạy) → **SYSTEM + FEATURES + PLAYBOOK + LESSONS** (+ SYNC_MAP
  nếu case liên quan số dư vé/coupon).
- `/testcase-cleanup` → PLAYBOOK (thứ tự xóa) + SYSTEM (endpoint) + LESSONS.

## 3 nguyên tắc chống "tri thức rác"
1. **Có nguồn + ngày**: mỗi fact ghi `[nguồn]` + `(YYYY/MM/DD)` — xem quy ước fact-confidence đầy đủ ở
   `../../.claude-knowledge/README.md`. Fact volatile (endpoint/branch/selector/sync) đánh dấu
   ⚠️/🟡/🔴 **verify trước khi dùng** — kiểm lại code/live rồi mới tin, KHÔNG tin mù.
2. **Dạng luật**: "Khi X → làm Y (vì Z)". Ngắn, actionable.
3. **Vòng lặp học hỏi**: sau mỗi run/retest, bước "Capture Lessons" → thêm bẫy mới vào LESSONS.md;
   endpoint/branch đổi → cập nhật SYSTEM.md (đổi ngày); bug lặp pattern → nâng thành luật METHOD.md;
   phát hiện lệch giữa 2 hệ (vd sync) → cập nhật SYNC_MAP.md, không ghi lặp lại ở DOMAIN/SYSTEM.
