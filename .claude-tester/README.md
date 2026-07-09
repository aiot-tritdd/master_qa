# .claude-tester — Bộ công cụ Test Case Evidence (Threease)

Gom **toàn bộ** thứ liên quan tới test vào 1 folder: skill/command, engine scripts, và **knowledge base**.
Đây là tài liệu **vận hành đầy đủ** cho phần test — mở file này khi bắt đầu 1 task test mới.

```
.claude-tester/
├── commands/     ← 5 skill (.md) — SOURCE. Symlink sang .claude/commands/ để gọi được.
│                    (tạo spec giờ ở /task-spec-create bên .claude-task/, không còn ở đây)
├── scripts/      ← engine: build_evidence.py, pw_lib/pw_api/cleanup.js, html_to_text.py,
│                    theme.json, example.tcs.json, package.json (+ node_modules)
└── knowledge/    ← 11 file: METHOD/SYSTEM/PLAYBOOK/LESSONS (riêng test) + 7 file symlink →
                     ../../.claude-knowledge/ (PROJECT_MAP/DOMAIN/SYNC_MAP/FEATURES/REPORTING/UI_UX/
                     OUTPUT_LOCATIONS — dùng chung với .claude-task/). Chi tiết đầy đủ + quy ước:
                     xem knowledge/README.md
```

> **Vì sao command vẫn ở `.claude/commands/`?** Claude Code chỉ nạp slash command từ `.claude/commands/`.
> Nên file gốc để trong `.claude-tester/commands/` và **symlink** sang `.claude/commands/` — vừa gom 1 chỗ,
> vừa gọi được `/testcase-*`.

## Cách gọi (slash command, có Tab gợi ý)
```
/task-spec-create <TênTask> [spec.html]  # (ở .claude-task/) spec HTML → specs.md — LÀM TRƯỚC
/testcase-write 7.Tests/<Folder>          # thiết kế test case, tự đọc specs.md từ 8.Tasks/specs/
/testcase-run 7.Tests/<Folder>            # chạy + evidence
/testcase-upspecschange 7.Tests/<Folder>  # ghi change/bug (viết dưới lệnh)
/testcase-retest 7.Tests/<Folder> TC-01   # chạy lại case chỉ định
/testcase-cleanup 7.Tests/<Folder>        # dọn dữ liệu test (chạy tay)
```
Tham số đầu của 5 skill test luôn là **folder** của task trong `7.Tests/`; **`<TênTask>` dùng cho
`/task-spec-create` phải khớp tên** với `<Folder>` (bỏ `7.Tests/`) để `/testcase-write` tự tìm đúng spec.

| Skill | Vai trò | Chạy test? |
|---|---|:---:|
| `/task-spec-create` *(ở `.claude-task/`)* | Lọc spec **HTML** → soạn `specs.md` chuẩn (dùng chung cho mockup + test) | ❌ |
| `/testcase-write` | Đọc `specs.md` (từ `8.Tasks/specs/`) → thiết kế test case → `tcs.json` + `.xlsx` | ❌ |
| `/testcase-run` | Chạy live toàn bộ → evidence → result/actual → build | ✅ |
| `/testcase-cleanup` | Dọn preset/account/đặt lịch test trên dev (dry-run mặc định) | — |
| `/testcase-upspecschange` | Ghi change/bug (có **ngày**) vào `specs.md` + thêm TC | ❌ |
| `/testcase-retest` | Chạy lại **chỉ** case bị ảnh hưởng sau khi fix | ✅ (subset) |

## Quy trình
```
task-spec-create (ở .claude-task/, nếu spec là HTML)
   │
   ├─→ mockup-create (ở .claude-task/, xem README ở đó)
   │
write → run → cleanup            (ở đây, đọc lại spec từ 8.Tasks/specs/)
                │  (review ra change/bug)
          upspecschange
                │  (dev fix)
          retest → cleanup
```

## Setup 1 lần
```
cd .claude-tester/scripts && npm i     # playwright local → không cần NODE_PATH
```
Python cần `openpyxl`, `Pillow`. Chromium cache ở `~/Library/Caches/ms-playwright`.

## Chuẩn bị mỗi task
1. Chạy `/task-spec-create <TênTask> [spec.html]` **trước** (spec dạng HTML export từ Google Sheet)
   → sinh `8.Tasks/specs/<TênTask>/specs.md`. Task cũ (trước khi có `.claude-task/`) vẫn có thể giữ
   `specs.md` ngay trong `7.Tests/<Folder>/` — skill test tự fallback sang đó nếu không thấy ở
   `8.Tasks/specs/`.
2. Tạo folder `7.Tests/<TênTask>/` (tên khớp `<TênTask>` ở bước 1) rồi chạy `/testcase-write`.
3. Account test lấy tự động từ [`../7.Tests/account.txt`](../7.Tests/account.txt) (Pro dev:
   `develop.pro.threease.com`, basic `threesides/threesides`, login `TESTSEED001/STAFF001/password123`).

## Cấu trúc folder sau khi chạy
```
8.Tasks/specs/<TênTask>/specs.md   # spec chuẩn — nguồn dùng chung cho mockup + test

7.Tests/<TênTask>/
├── tcs.json            # dữ liệu test case (skill tạo/cập nhật)
├── shots/              # ảnh evidence (nén ~560px JPG, bind in-cell)
└── <TênTask>.xlsx      # file kết quả
```

## Knowledge base (train "tester 50 năm kinh nghiệm")
11 file theo độ ổn định — xem [`knowledge/README.md`](knowledge/README.md) cho danh sách đầy đủ +
quy ước fact-confidence: `METHOD/SYSTEM/PLAYBOOK/LESSONS` (riêng test) + `PROJECT_MAP/DOMAIN/SYNC_MAP/
FEATURES/REPORTING/UI_UX/OUTPUT_LOCATIONS` (dùng chung, symlink từ `.claude-knowledge/`).
- Skill đọc knowledge **thay vì grep lại code** → nhanh + nhất quán.
- Sau mỗi run/retest có bước **Capture Lessons** → knowledge tự lớn lên.

## Quy ước (bắt buộc)
- **Dữ liệu test trên dev**: prefix `AIOT-TEST-*` (preset) / `AIOTTEST*` (staff) → để `cleanup` quét được.
- **Kết quả**: `PASS` / `FAIL` / `未実施` (tô xanh/đỏ/vàng tự động).
- **Change/bug**: `CHANGE-xx` 🔧 / `BUG-xx` 🐞; trạng thái `🔴 chưa xử lý → 🟡 đang fix → ✅ đã verify`.
- **TC phát sinh từ specs change**: title gắn `【Specs Change: …】` + trường `source` trong tcs.json
  → hiện ở cột「Nguồn / 発生元」sheet Checklist.
- **`specs.md`** mục "Cập nhật Specs" = **bảng changelog có ngày** — mỗi đợt change thêm 1 dòng
  (vì sẽ có nhiều đợt), sống ở `8.Tasks/specs/<TênTask>/` (xem [`../.claude-task/README.md`](../.claude-task/README.md)).

## Tuỳ chỉnh (single source of truth)
- Đổi màu/layout/nhãn Excel → sửa `scripts/theme.json`.
- Đổi khung 5 case → sửa `scripts/example.tcs.json`. Không đụng code generator.
- Đổi hệ khác Pro dev → set env `BASE_URL, BASIC_USER/PASS, INST/THER/PW, API_BASE` (chi tiết:
  [`scripts/README.md`](scripts/README.md)).

## Lưu ý
- `.xlsx`, `tcs.json`, `shots/` **luôn cùng folder** `7.Tests/<TênTask>/`; `specs.md` nằm ở
  `8.Tasks/specs/<TênTask>/` (không copy specs.md sang đây nữa).
- Thao tác phá huỷ (xoá đặt lịch, huỷ thanh toán) chỉ dùng dữ liệu test tự tạo; chạy `/testcase-cleanup`
  sau mỗi phiên.
- KHÔNG upload Excel có ảnh lên Drive qua tool (base64 quá lớn) — kéo tay file lên Drive.
- File tham khảo: [`../7.Tests/TestCase_Evidence_Template.xlsx`](../7.Tests/TestCase_Evidence_Template.xlsx)
  · ví dụ đã chạy: [`../7.Tests/TestCase_No.10.5/`](../7.Tests/TestCase_No.10.5/).
- **Output ghi ở đâu** (nguồn định nghĩa duy nhất, đừng đoán):
  [`../.claude-knowledge/OUTPUT_LOCATIONS.md`](../.claude-knowledge/OUTPUT_LOCATIONS.md).
