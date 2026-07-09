# Bộ skill Test Case Evidence (Threease Pro)

5 skill khép kín cho phần **test** trong vòng đời task: **viết → chạy → cập nhật change → retest → dọn**.
Tạo spec là bước làm TRƯỚC, ở `/task-spec-create` bên `.claude-task/` (xem `.claude-task/README.md`).
Sinh file Excel evidence đẹp (ảnh bind in-cell), chạy test thật bằng Playwright + API trên dev.

## 0. Cách gọi skill (gõ trong khung chat Claude Code)
Skill là **slash command** — gõ `/` + tên skill + tham số. Copy-paste:
```
/task-spec-create TestCase_No.10.5 spec.html   ← (ở .claude-task/, làm trước)
/testcase-write 7.Tests/TestCase_No.10.5
/testcase-run 7.Tests/TestCase_No.10.5
/testcase-cleanup 7.Tests/TestCase_No.10.5
/testcase-retest 7.Tests/TestCase_No.10.5 TC-01 TC-06
/testcase-upspecschange 7.Tests/TestCase_No.10.5
- Change: đổi text quyền ... → ...
- Bug: dời quyền mới về cuối
```
- Tham số 1 của 5 skill test = **đường dẫn folder** của task trong `7.Tests/`; skill tự đọc
  `specs.md` từ `8.Tasks/specs/<TênTask>/` (tên khớp `<Folder>` bỏ `7.Tests/`).
- `/testcase-upspecschange`: viết các change/bug xuống **dòng dưới** lệnh, mỗi mục 1 dòng.
- `/testcase-retest`: thêm **id case/change** cần chạy lại (bỏ trống = chạy lại mọi mục còn 🔴/🟡).
- Gõ `/testcase` rồi Tab để xem gợi ý tên skill. Nếu skill không hiện → mở lại Claude Code
  tại thư mục project `Workspaces/threease` (skill nằm ở `.claude/commands/`).

## 1. Setup (1 lần)
```
cd .claude-tester/scripts && npm i
```
Cài `playwright` local → helper require chạy thẳng, **không cần NODE_PATH**.
Chromium đã cache ở `~/Library/Caches/ms-playwright`. (Python cần `openpyxl`, `Pillow`.)

## 2. Cấu trúc mỗi task
```
8.Tasks/specs/<TênTask>/specs.md   ← spec chuẩn (export từ Google Sheet) — nguồn dùng chung

7.Tests/<TênFolder>/
├── tcs.json        ← dữ liệu test case (Skill 1 tạo, Skill 2/4 cập nhật)
├── shots/          ← ảnh evidence (Skill 2/4 chụp, nén ~560px JPG)
└── <TênFolder>.xlsx ← file kết quả (build ra)
```

## 3. Năm skill (+ tạo spec ở `.claude-task/`)
| Skill | Lệnh | Vai trò | Chạy test? |
|------|------|---------|:---:|
| 0 *(ở `.claude-task/`)* | `/task-spec-create <TênTask> [file.html]` | Lọc spec HTML → soạn `specs.md` chuẩn | ❌ |
| 1 | `/testcase-write <folder>` | Đọc `specs.md` → thiết kế test case (kế thừa khung 5 case) → `tcs.json` + `.xlsx` | ❌ |
| 2 | `/testcase-run <folder>` | Chạy live toàn bộ → evidence → kết quả → build | ✅ |
| 3 | `/testcase-upspecschange <folder>` | Ghi change/bug mới (có **ngày**) vào `specs.md` + thêm TC | ❌ |
| 4 | `/testcase-retest <folder> [id…]` | Chạy lại **chỉ** case bị ảnh hưởng sau khi fix | ✅ (subset) |
| 5 | `/testcase-cleanup [<folder>]` | Dọn dữ liệu test trên dev theo prefix — **chạy tay khi cần** (dry-run mặc định) | — |

## 4. Quy trình chuẩn
```
/task-spec-create →  (spec là HTML, ở .claude-task/) sinh specs.md chuẩn
/testcase-write   →  tạo test case từ specs.md
/testcase-run     →  chạy lần đầu (PASS/FAIL) + evidence
      │  (review phát sinh change/bug)
/testcase-upspecschange  →  ghi CHANGE-xx/BUG-xx + ngày vào specs.md, thêm TC
      │  (dev fix xong)
/testcase-retest CHANGE-01 BUG-02  →  chạy lại đúng phần đó, cập nhật ✅/🔴
```
**Cleanup KHÔNG nằm trong quy trình tự động.** Run/retest giữ nguyên dữ liệu test trên dev
(để đối chiếu evidence / dev debug) và chỉ **liệt kê dữ liệu còn tồn** trong báo cáo.
Khi cần dọn, user chủ động gõ:
```
/testcase-cleanup <folder>     ← dry-run trước, --apply sau khi rà soát
```

## 5. Quy ước (bắt buộc)
- **Dữ liệu test trên dev**: preset prefix `AIOT-TEST-*`, staff/account `AIOTTEST*` → để cleanup quét được.
- **specs.md**: nguồn chính thức là Google Sheet; `.md` là bản làm việc, re-export khi sheet đổi.
  Mục "Cập nhật Specs" là **bảng changelog có ngày** — mỗi đợt change thêm 1 dòng.
- **ID change/bug**: `CHANGE-xx` (🔧) / `BUG-xx` (🐞); trạng thái `🔴 chưa xử lý → 🟡 đang fix → ✅ đã verify`.
- **Kết quả test**: `PASS` / `FAIL` / `未実施`; `actual` bắt đầu bằng đúng từ đó (để công thức đếm khớp).
- **TC phát sinh từ specs change**: title gắn tag `【Specs Change: CHANGE-xx/BUG-xx】` + trường
  `source` trong tcs.json (vd `🔧 Specs Change 2026/07/06 — CHANGE-01`) → hiện ở cột
  「Nguồn / 発生元」sheet Checklist (nền vàng). Case gốc bỏ trống `source`.

## 6. File nguồn (single source of truth)
| File | Vai trò | Sửa khi |
|------|---------|---------|
| `theme.json` | FORMAT (màu/font/layout/nhãn) | đổi giao diện file xuất |
| `example.tcs.json` | KHUNG 5 archetype (nội dung mẫu) | đổi bộ case chuẩn |
| `build_evidence.py` | generator (đọc 2 file trên) | đổi logic dựng ô |
| `pw_lib.js` / `pw_api.js` | đăng nhập / chụp an toàn `shot()` / gọi API | đổi hệ thống/endpoint |
| `cleanup.js` | dọn dữ liệu test | đổi endpoint xóa |
| `html_to_text.py` | lọc spec HTML → text gọn (Skill 0) | đổi cách trích xuất HTML |

Đổi template = sửa `theme.json` (không đụng code/tcs). Mọi lần build đồng nhất (deterministic).

## 7. Token — vì sao rẻ
- File Excel do script ghi ra đĩa → **nội dung không đi qua token**. Model chỉ tốn token cho `tcs.json`.
- Đọc `specs.md` (text) rẻ hơn OCR ảnh spec. Spec HTML lọc qua `html_to_text.py` trước, không đọc raw HTML.
- Skill 3 không chạy test; Skill 4 chỉ chạy subset → tiết kiệm token + không phá dữ liệu dev thừa.
- KHÔNG upload Excel có ảnh lên Drive qua tool (base64 inline ~95k token). Kéo tay file lên Drive.

## 8. Env ghi đè (khi đổi hệ)
`BASE_URL, BASIC_USER/PASS, INST/THER/PW, API_BASE, STATE_FILE, SHOTS_DIR` (pw_lib/pw_api),
`PRESET_PREFIX, STAFF_PREFIX, BRANCH_ID, RESV_IDS` (cleanup).
