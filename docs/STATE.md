# STATE — điểm dừng & việc tiếp (đọc ĐẦU TIÊN mỗi phiên)

> File **sống** — cập nhật cuối mỗi phiên. Mục đích: mở phiên mới là biết ngay *đang ở đâu, làm gì tiếp*.
> Cập nhật: **2026-07-09**. Branch git: `qa-brain` (threease_qa).

---

## 0. Đọc theo thứ tự để nắm hệ thống

`docs/STATE.md` (file này) → `CLAUDE.md` → `docs/QA-SERVER.md` (kinh thánh) →
**`docs/SYSTEM-COMPARISON.md`** (so hệ mình vs hệ sếp — hiểu vì sao có 2 bức tường) →
**`docs/MERGE-PLAN.md`** (kế hoạch hợp nhất, đang chạy) →
`docs/KNOWLEDGE-STRATEGY.md` → `knowledge/system/OVERVIEW.md`.

## 1. Hệ thống LÀ GÌ (1 dòng)

QA senior **black-box** (skill `qa-brain` + commands `testcase-*`): SPEC → sinh+chạy test trên **dev** →
evidence PNG/xlsx. Oracle = SPEC + quan sát live. **Mù code.** GitNexus chỉ ở build-time (soạn knowledge).

## 2. ĐÃ XONG (đừng làm lại)

- ✅ **Redesign black-box:** SKILL.md · commands · `build_evidence.py` (3-sheet) ·
  `pw_lib.js` (5 target: pro/ticket/ticket_admin/reservation/admin) · docs · 2× CLAUDE.md.
- ✅ **Chuẩn evidence:** xlsx 3 sheet (Cover/Test Cases/Checklist+Nguồn), **mỗi case 2 ảnh before+after PNG rõ**.
- ✅ **Skill `/specs-md`** (html→md). ✅ **`/testcase-stale`** + `stale_check.py` + `source_hash` thật (GĐ-0).
- ✅ **Re-UI-confirm `pro-open-booking.md`** (2026-07-09, ja-JP) — phát hiện toạ độ cứng + nhãn EN đều mục rữa.
- ✅ **Test đã chạy:** `TestCase_NEW` (thu hồi vé) 7 case verified ·
  `TestCase-11` (coupon report) **9 PASS / 8 FAIL**, khớp 100% scope dev.
- ✅ **Phân tích + kế hoạch merge hệ của sếp** (`.claude-tester/`): `docs/SYSTEM-COMPARISON.md` + `docs/MERGE-PLAN.md`.

### ✅ MERGE Phase 0 — vá lệnh chết (2026-07-09, đã verify)
Trước đó 4 lệnh trỏ vào file **không tồn tại**. Nay:
- ✅ `theme.json` (mới) — single source of truth cho format. `build_evidence.py` đọc nó, hết hardcode palette.
- ✅ `example.tcs.json` (mới) — khung 5 archetype thành **dữ liệu**, không còn là trí nhớ của model.
- ✅ `cleanup.js` (mới) — `/testcase-cleanup` lần đầu chạy được. `BRANCH_ID` **không** hardcode.
- ✅ `shot(page, path, readySelector)` trong `pw_lib.js` — hết ảnh dính spinner.
- ✅ `pw_api.js` viết lại: **sniff devise-token** từ request thật (bỏ `Bearer API_TOKEN` sai auth).
  Trả `{status, body, ok}` → case chống-bypass phân biệt được 403 vs 204.
- ✅ `storageState` cache theo target (`.state.<target>.json`, đã gitignore).
- ✅ **`SPEC-GAP` = result thứ tư** (Q1 chốt hướng A). Cover đếm riêng, Checklist đếm riêng, `result` lạ → WARN.
- **Verify:** 4 tcs.json cũ (17/34/25/44 case) build lại sạch · ảnh nhúng khớp bản cũ (34↔34, 7↔7) ·
  `SPEC-GAP` chạy end-to-end · `node --check` sạch 3 file JS.

### ✅ MERGE Phase 1 — vệ sinh tri thức (2026-07-09)
- ✅ **`knowledge/OPEN-QUESTIONS.md`** (mới) — **tầng tri thức thứ ba**: *"tra rồi vẫn không đủ căn cứ"*.
  8 câu (OQ-01..08). QA-runtime **đọc được** (nó không phán đúng/sai).
- ✅ **`knowledge/GLOSSARY.md`** (mới) — thuật ngữ nghiệp vụ, để report FAIL không lộ tên repo.
- ✅ **`knowledge/lessons.md`** (mới) — 12 bẫy **cơ khí**, có luật nhập HOW-vs-WHAT ngay đầu file.
- ✅ `confidence:` + `verify_by:` vào front-matter mọi doc `knowledge/`.
- ✅ **Routing table + ⛔ danh sách CẤM đọc** trong `SKILL.md`.
- ✅ **Checklist "Before final"** vào cả 5 command (câu tripwire: *"Có đọc source code không? Nếu có, vì sao?"*
  — ở QA-runtime đáp án đúng luôn là **KHÔNG**).
- ✅ **Capture Lessons** (bắt buộc) vào `/testcase-run` + `/testcase-retest`.
- ✅ Luật **"1 tri thức = 1 nhà"** + **"dot-folder không chứa deliverable"** vào `KNOWLEDGE-STRATEGY.md`.

### ✅ REGRESSION TEST cho chính hệ QA (2026-07-09) — merge KHÔNG phá black-box
Thước đo thành công của `MERGE-PLAN`: chạy lại TestCase-11 phải vẫn ra **9 PASS / 8 FAIL**. → ✅ **ĐÚNG**.
- `200`: top-tab `チケットレポート`+`クーポンレポート` · `/reports/` · `/coupon-reports/sales/` (filter, KPI,
  `CSVエクスポート`, cột `発行元`) · `/coupon-reports/usage/`
- `404`: `/coupon-reports/` (dashboard) · `/monthly/` · `/by-store/` · `/csv-snapshots/`; nút `過去のCSV` = 0
- Sub-tab クーポンレポート thật = **2** (`販売`,`消費`), spec đòi 5 → TC-04 FAIL.
- ⚠️ **Chốt OQ-01:** coupon report **CÓ tồn tại**, mới build 2/5 sub-tab. Khẳng định `grep` của sếp
  (*"CHƯA TỒN TẠI TRONG CODE"*) **sai**. Model nằm chỗ khác/tên khác.
- 📌 Bẫy tự bắt: selector `.nav-link,[role=tab]` hốt cả top-nav → ra 9. Số thật là 2.
  Tin thẳng số 9 ⇒ TC-04 PASS **sai**. Luôn nhìn ảnh khi con số lạ.

### ✅ LIVE-VERIFY harness (2026-07-09) — cổng chặn đã MỞ
Chạy thật trên dev, không phải syntax check:
- ✅ `pw_api` sniff devise-token: `GET /permissions/presets` → **200**, 7 preset. Id không tồn tại → **404**
  ⇒ `api.status` dùng được cho archetype #5 (chống bypass).
- ✅ `shot()` bắt được `text=権限設定`, ảnh **2880×1800 / 267KB**, không phải màn trắng.
- ✅ Cache `.state.pro.json` hoạt động cả 2 chiều (sạch → có).
- 🐞 **Tìm + vá 4 bug harness** (chi tiết `knowledge/lessons.md`): thiếu `locale:'ja-JP'` (**gây FAIL SAI**
  vì spec tiếng Nhật không match UI tiếng Anh) · thiếu `deviceScaleFactor:2` · lưu `storageState` quá sớm
  (cache rỗng session) · 3 cách sai để hỏi "đã đăng nhập chưa" (`count()` / `url()` / `visible` sớm).
- 🗑️ Phát hiện rác trên dev: preset **`AIOT-TEST-105`** còn sót → `/testcase-cleanup` khi rảnh.

## 3. VIỆC TIẾP (ưu tiên trên xuống)

1. ✅ **Live-verify `pw_api` + `shot()` — XONG.** Cổng chặn Phase 2 đã mở.
2. ✅ **[MERGE Phase 2] XONG** — `knowledge/METHOD.md` (5 archetype + 6 luật vàng + adapter
   *"coverage ≠ oracle"* + sơ đồ rẽ nhánh `SPEC-GAP`). Còn: live-verify archetype #5 (chống bypass).
3. ✅ **[MERGE Phase 3] XONG** — 11 file của sếp xé qua 3 cửa. Nhà mới: `knowledge/playbook.md` ·
   `features.md` (draft, chờ UI-confirm) · `system/domain-rules.md` · `system/ui-theme.md` ·
   `system/api-endpoints.md`; phần còn lại đổ vào nhà có sẵn (`customer-sync`/`coupon-sc`/`OVERVIEW`/
   `observation-channels`/`lessons`/`KNOWLEDGE-STRATEGY`).
4. ✅ **[MERGE Phase 4] XONG** — archive `0119159` → `git rm` `822d5dd` → `rm -rf` phần untracked.
   `.claude-tester` **không còn trong working tree** ⇒ bức tường thép thành **cơ chế**.
   ⚠️ Nó **chưa từng được commit** — suýt mất vĩnh viễn. Xem `MERGE-PLAN.md` §6.2.
5. **[Grow knowledge/system]** Còn 3 domain: **6 Booking** (GitNexus được việc) ·
   **7 Reservation widget** + **8 Admin** — ✅ **hết bị chặn** (OQ-02 đã đóng: dev URL xác nhận đúng).
6. ✅ **[Nav doc] `pro-open-booking.md` đã re-UI-confirm 2026-07-09** dưới `ja-JP` → `approved`.
   Nhãn thật: `請求書` (không phải `INVOICE`) · `削除する` (không phải `Remove`) · `保存する` ·
   `.mdi-delete-outline`. Toạ độ cứng `mouse.click(877,68)` đã bỏ → selector ngữ nghĩa.
7. **[Nav doc]** Nâng `issue-ticket-pack.md` `draft → approved`: UI-confirm khâu tạo booking → thanh toán → phát hành vé.
8. **[Optional]** `TestCase_NEW`: 6 case còn `未実施` cần precondition **gói vé còn nguyên** (KH3 đã dùng 2 vé).

## 4. Cách maintain khi 5 repo update

`refresh-gitnexus.sh` (graph tươi — **CHỈ graph**) → **`/testcase-stale`** (so `source_hash`) →
re-derive + re-confirm **CHỈ doc drift**.
⚠️ refresh KHÔNG tự update `knowledge/`. Graph hiện **đang tươi** (index 2026-07-06/08, không repo nào
báo `commitsBehind`) → chỉ chạy refresh khi 5 repo thực sự có commit mới.

**Ngân sách GitNexus thật** (đo `list_repos` 2026-07-09): backend 227 · ticket 130 · pro 116 ·
**admin 0** · **reservation 0** processes. **473 = 227+130+116**, là *tổng call-chain*, KHÔNG phải
"473 flow phải viết doc" (chúng gom thành 8 domain). `processes=0` ≠ graph rỗng — admin vẫn cho
20 route qua `route_map`, reservation cho `definitions` (màn + method). Chi tiết: `system/OVERVIEW.md`.

## 5. Access nhanh (dev) — để chạy ngay

- Creds: `wtf-is-this/account.txt`. `pw_lib`: `getPage('pro'|'ticket'|'ticket_admin'|'reservation'|'admin')`.
- **Report ticket cần** `TESTSEED001/ticket-admin/password123` → env `TK_STAFF=ticket-admin`.
- Chụp ảnh: **`shot(page, path, readySelector)`**. Gọi API: `withApi()` (tự sniff token).
- Data test: prefix `AIOT-TEST-*`/`AIOTTEST*` → `/testcase-cleanup` (cần `BRANCH_ID=<phiên hiện tại>`).
- **Branch phiên `TESTSEED001` hiện = `3`** (đo 2026-07-09; branch sai → API trả 404).
- Booking mẫu để drive: **`Jenny` 07/09 14:20, branch 3, id=774, `一部支払済み`, có vé `AIOT-TEST-TK1` + coupon**.
  ❌ `AIOTTEST-KH3` booking 07/13 **không còn tồn tại** (đã bị dọn) — ghi chú cũ đã sai.
- 🗑️ Rác còn trên dev: preset `AIOT-TEST-105`, staff `AIOT Test105`, ticket master `AIOT-TEST-TK1`.
- Build xlsx: `python3 .claude/skills-scripts/testcase-evidence/build_evidence.py <F>/tcs.json <F>/<Tên>.xlsx`.
- Session cache: `.state.<target>.json` — `NO_STATE=1` để login sạch.

## 6. NGUYÊN TẮC BẤT DI (đừng phá — đã từng trả giá)

1. Oracle = **SPEC**; viết `expect` MÙ code. `METHOD.md` cấp **coverage**, KHÔNG cấp `expect`.
2. QA-runtime **mù code, không GitNexus, không `knowledge/system/**`**; FAIL báo **hành vi + ảnh**,
   không symbol/file:line.
3. **KHÔNG code-trace để phán "đã build/chưa"** — đã SAI **2 lần** (guard vé-đã-dùng; coupon report).
   Dùng `route_map` (build-time) + quan sát live.
4. `knowledge/` = navigation (HOW), KHÔNG phải oracle. Graph→`draft`; UI-confirm→`approved`.
5. **`grep` không thấy ≠ không tồn tại** → `OPEN-QUESTIONS.md`, không ép thành "có"/"không".
6. Spec im lặng ở chỗ METHOD bảo phải kiểm → **`SPEC-GAP`**, KHÔNG bịa `expect`.
7. Specs sau này = **tinh chỉnh/update** business đã map, không build lại từ 0.

## 7. Trạng thái git / task nền

- Branch `qa-brain`. `wtf-is-this/` đã gitignore (evidence local). `.state.*.json` đã gitignore.
- ✅ `.claude-tester/` **đã xoá** (archive `0119159`, xoá `822d5dd`). Tra nguồn: `git show 0119159:.claude-tester/<path>`.
- Đống transition Python→skill (`D qa/ api/ web/ tests/`) còn trong index — **để user tự xử**.
- Không có background task đang chạy.

---

## 📌 TODO cũ (INFRA, ngoài QA) — "phân tách" claude-mem observer

> Ghi 2026-07-08. Chưa làm. Không chặn việc QA.

- Đo thật: **claude-mem observer (Haiku) = ~2.3% tổng token** → **KHÔNG phải thủ phạm**.
  Thủ phạm = 1 session QA marathon (peak 863k ctx → cache_read 200M). Fix: `/compact`/`/clear` **sớm**.
- Bash đã được skip đúng trong `~/.claude-mem/settings.json`.
- Việc còn: xem 32 observer session/ngày có dư không · gọn nền mỗi phiên (MCP registry ~52k deferred).
- Ruflo: **đã gỡ sạch** 2026-07-08.
