# SETUP — từ máy trắng đến chạy được test đầu tiên

> `README.md` giải thích **hệ thống nghĩ gì**. File này chỉ trả lời **cài gì, theo thứ tự nào** để nó
> chạy. Người mới hoàn toàn: làm đúng từ trên xuống là xong.

---

## 0. Hai track — chọn đúng kẻo cài thừa

| Bạn muốn                                                                                          | Làm track      | Cần gì                                                                                 |
| --------------------------------------------------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------- |
| **Chỉ chạy test** (viết case, drive app, ra evidence)                                      | **A**     | Node+Playwright · Python+openpyxl ·`account.txt` · Claude Code + skill `qa-brain` |
| **Grow/maintain knowledge** (soạn Living Business Doc, `/testcase-systemdoc`, stale-check) | **A + B** | thêm: clone 5 repo · GitNexus (index + group + MCP)                                    |

> ⚠️ **QA chạy test lái dev server TỪ XA** (`develop.pro.threease.com`, `ticket-dev.threease.com`…),
> **không** phải docker localhost. Nên track A **không cần** `docker compose up`, **không cần** GitNexus,
> **không cần** clone 5 repo sản phẩm. Chỉ cần **mạng vào được dev + `account.txt`**.
> Docker/DB (workspace `CLAUDE.md` §4–5) chỉ cần nếu bạn muốn soi DB tay hoặc chạy sản phẩm cục bộ.

---

## TRACK A — chạy được test

### A1. Vị trí thư mục (bắt buộc đúng)

- Clone `threease_qa` vào workspace `ThreeSides/`. Track A **không cần** 5 repo kia.
- `CLAUDE.md` phải nằm đúng 2 chỗ để Claude Code tự nạp context:
  - workspace root `ThreeSides/CLAUDE.md` (bản đồ 5 repo) — *có thể vắng nếu chỉ làm track A, nhưng nên có*
  - `threease_qa/CLAUDE.md` (2 bức tường thép + cách xài) — **bắt buộc**
- Mở Claude Code **tại thư mục `threease_qa/`** (hoặc workspace) → skill `qa-brain` tự xuất hiện
  (nguồn: `threease_qa/.claude/skills/qa-brain/`).

### A2. Cài dependency của harness

```bash
# Node + Playwright (drive app, chụp evidence)
cd threease_qa/.claude/skills-scripts/testcase-evidence
npm install                 # playwright ^1.44 (đã vendor sẵn node_modules, chạy lại cho chắc)
npx playwright install chromium   # tải browser binary — KHÔNG có bước này là fail câm

# Python + openpyxl (build file Excel evidence)
python3 -m pip install openpyxl   # stale_check.py chỉ dùng stdlib, không cần thêm
```

Yêu cầu nền: **Node ≥ 16**, **Python 3**, **Claude Code** (skill + harness chạy trong 1 session Claude).

### A3. Credentials — `.env` (XIN TEAM LEAD)

`pw_lib.js` đọc creds từ **`.env` ở repo root `threease_qa/`** (đã gitignore → clone mới KHÔNG có sẵn).
Tạo bằng cách copy template rồi điền giá trị thật (xin team lead):

```bash
cd threease_qa
cp .env.example .env
# mở .env điền: BASIC_USER/PASS · INST/THER/PW · TK_INST/TK_STAFF/TK_PW · TK_ADMIN_USER/PASS
```

> ⚠️ **TUYỆT ĐỐI không commit `.env`.** Creds không còn hardcode trong `pw_lib.js` — thiếu biến nào,
> harness **báo rõ tên biến** + trỏ về đây. Biến set sẵn ngoài shell (CI) sẽ thắng `.env`.
> ⚠️ **Report ticket** có màn cần tài khoản quyền cao hơn → đổi `TK_STAFF` trong `.env` (hỏi team lead).

### A4. (tuỳ nhu cầu) Env override hành vi

Creds đã ở `.env` (A3). Bảng dưới là **override hành vi** — set khi cần (biến shell thắng `.env`):

| Env                             | Default    | Khi nào set                                                                    |
| ------------------------------- | ---------- | ------------------------------------------------------------------------------- |
| `HEADED=1`                      | headless   | muốn **xem** browser lái                                                     |
| `LOCALE`                        | `ja-JP`    | test UI tiếng Anh (spec tiếng Nhật → giữ `ja-JP`)                         |
| `NO_STATE=1`                    | cache on   | login sạch (đổi account giữa chừng)                                        |
| `BRANCH_ID`                     | —          | **bắt buộc** cho `/testcase-cleanup` (= branch phiên; sai → API 404) |
| `BASE_URL`/`TICKET_URL`/… | URL dev    | trỏ sang hệ dev khác                                                         |

### A5. Verify track A chạy

1. Bỏ 1 `specs.md` (hoặc `specs.html` → chạy `/specs-md <folder>`) vào `wtf-is-this/TestCase-XX/`.
2. Trong Claude Code: *"dùng skill qa-brain cho folder wtf-is-this/TestCase-XX"* → ra `tcs.json` + `.xlsx`.
3. `/testcase-run …` → nếu lái được app dev + có `shots/*.png` → **track A OK**.
   - Login fail → xem lại `account.txt` (A3).
   - Ảnh trắng / thiếu browser → chưa chạy `npx playwright install` (A2).

---

## TRACK B — grow/maintain knowledge (build-time, cần GitNexus)

Chỉ làm khi cần **soạn/cập nhật Living Business Doc** (`/testcase-systemdoc`) hoặc **stale-check** sau khi
5 repo đổi code. QA-runtime (track A) **không đụng** phần này.

### B1. Clone đủ 5 repo sản phẩm vào workspace

Đúng tên: `threease_backend · threease_ticket · threease_pro · threease_admin · threease_reservation`
(cạnh `threease_qa`, trong `ThreeSides/`).

> ⚠️ `refresh-gitnexus.sh` **hardcode** `ROOT="/Users/tritdd/Work/ThreeSides"`. Máy khác → sửa biến `ROOT`
> trong script (hoặc đặt workspace đúng path đó).

### B2. Cài GitNexus + tạo group (một lần)

```bash
npm i -g gitnexus                       # CLI lên PATH
```

Group `threease` là **file config THẬT** ở `~/.gitnexus/groups/threease/group.yaml`, tạo bằng lệnh —
**KHÔNG** phải viết vào `CLAUDE.md`:

```bash
gitnexus group create threease                          # tạo group.yaml khung
gitnexus group add threease backend     threease_backend   # thêm từng repo…
gitnexus group add threease pro         threease_pro
gitnexus group add threease ticket      threease_ticket
gitnexus group add threease admin       threease_admin
gitnexus group add threease reservation threease_reservation
gitnexus group list threease            # xác nhận đủ 5 repo
```

> ⚠️ **`CLAUDE.md` chỉ MÔ TẢ group, không TẠO group.** Nó là bản đồ cho Claude đọc, không đăng ký gì với
> gitnexus. Muốn có group thật phải `group create` + `group add` (hoặc đã có sẵn `group.yaml`).
> Đây là bước **một lần** — code đổi bao nhiêu cũng không cần sửa `group.yaml`.

- Cấu hình **GitNexus MCP** cho Claude Code để dùng `mcp__gitnexus__*` (route_map/query/context).

### B3. Index 5 repo (group sync đã nằm sẵn trong script)

```bash
cd /Users/tritdd/Work/ThreeSides
./refresh-gitnexus.sh          # analyze 5 repo (incremental) + TỰ chạy group sync ở cuối
./refresh-gitnexus.sh --pull   # git pull --ff-only trước rồi mới index
gitnexus group status threease # kiểm độ tươi
```

> **`group sync` KHÔNG phải làm riêng** — dòng cuối `refresh-gitnexus.sh` đã gọi `gitnexus group sync threease`.
>
> ⚠️ **Index ≠ liên kết.** `analyze` dựng **code graph riêng từng repo** (chạy tốt). `group sync` *thử*
> nối API giữa các repo, nhưng với stack này ra **~0 cross-link** (`group.yaml` → `links: []`): GitNexus
> không parse được Rails routes / Ruby HTTP client, mà `threease_backend` (hub) đóng góp **0 HTTP contract**.
> Cái bạn **thật sự** được từ group = **query gộp** `query({repo:"@threease", …})` (tìm cả 5 repo, merge/rank)
>
> + `impact` per-repo — **không** phải 1 call graph liền mạch xuyên 5 repo. Chi tiết: workspace `CLAUDE.md` §3.

### B4. (tuỳ chọn) Docker + DB — chỉ để soi dữ liệu tay

`docker compose up -d` ở workspace + nạp DB (Rails `db:schema:load`, ticket `pg_restore 17`).
Chi tiết: workspace `CLAUDE.md` §4–5. **Không** cần cho việc chạy test (track A lái dev từ xa).

---

## Thứ tự phụ thuộc (đừng đảo)

```
Track A:  A1 vị trí ─► A2 deps ─► A3 .env (creds) ─► A5 verify       # đủ để chạy test
Track B:  B1 clone 5 repo ─► B2 gitnexus+MCP ─► B3 index+sync        # trước khi /testcase-systemdoc
          (B phải xong TRƯỚC khi soạn knowledge; A độc lập với B)
```

---

**Muốn biết thêm** (triết lý · access nhanh dev · cơ khí knowledge · GitNexus) → bảng "muốn biết X → mở Y"
ở [`README.md`](README.md) §13 và `STATE.md` §5.
