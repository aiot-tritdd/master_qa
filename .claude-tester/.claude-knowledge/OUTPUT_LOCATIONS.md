# OUTPUT_LOCATIONS — Quy ước nơi ghi file (nguồn định nghĩa DUY NHẤT)

> Mọi README khác (`.claude-tester/README.md`, `.claude-task/README.md`) chỉ **trỏ về file này**,
> không lặp lại nội dung — sửa quy ước thì sửa Ở ĐÂY, 1 chỗ.
> (`7.Tests/README.md` đã bị xoá 2026/07/08 — nội dung vận hành test gộp thẳng vào
> `.claude-tester/README.md` để tránh trùng lặp.)

## Quy tắc gốc
| Bộ công cụ (tooling — dot-folder, không chứa deliverable) | Deliverable thật (nơi user mở/xem) |
|---|---|
| `.claude-task/` (commands + knowledge) | **`8.Tasks/`** — `specs/<TênTask>/specs.md` (+ file spec gốc vd `.html`), `mockup/<TênTask>/mockup.html` |
| `.claude-tester/` (commands + scripts + knowledge) | **`7.Tests/`** — `<Folder>/tcs.json`, `<Folder>/shots/*`, `<Folder>/<Folder>.xlsx` |
| `.claude-knowledge/` | Không sinh deliverable — chỉ chứa tri thức tĩnh dùng chung (đọc, không phải nơi ghi output) |

**Nguyên tắc**: dot-folder (`.claude-*`) không bao giờ chứa dữ liệu công việc thật (spec/mockup/test
case/evidence) — chỉ chứa skill (.md) + script + tri thức. Dữ liệu thật luôn nằm ở folder số thường
(`7.Tests/`, `8.Tasks/`) để dễ mở/dễ thấy, không ẩn trong dot-folder.

## Trường hợp đặc biệt: cache kỹ thuật (KHÔNG phải deliverable)
- Session login cache (`state.json` của Playwright) và thư mục `shots` mặc định khi skill quên chỉ
  định path → nằm trong **`.claude-tester/scripts/`** (`.state.json`, `.shots/`), KHÔNG leak ra root
  hay `7.Tests/`. Đây là cache dùng lại giữa các lần chạy, không phải bằng chứng test cần lưu lại.
- Trong vận hành thật, skill LUÔN chỉ định path tường minh (`<folder>/shots/...`) — default trên chỉ
  là lưới an toàn khi quên set.

## Đối chiếu tên `<TênTask>` giữa 2 hệ
`8.Tasks/specs/<TênTask>/` và `7.Tests/<Folder>/` phải **cùng tên** (folder trong `7.Tests/` chính là
`<TênTask>`, không rút gọn/đổi khác) để `/testcase-write` tự tìm đúng spec. Vd:
`8.Tasks/specs/TestCase_No.10.5/specs.md` ↔ `7.Tests/TestCase_No.10.5/`.

## Lịch sử
- 2026/07/08: khởi tạo quy ước 2 folder `7.Tests`/`8.Tasks` (đổi tên từ `7.Test`/`Mockup` cũ), dọn
  4 `specs.md` + 1 `specs.html` còn sót trong `7.Tests/<Folder>/` sang `8.Tasks/specs/<Folder>/`.
