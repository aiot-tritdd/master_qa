---
name: backfill
description: Use when you need to run + evidence a ticket-pack backfill migration for ONE branch on DEV LOCAL (any direction). Build-time task (ĐƯỢC đọc code + GitNexus — KHÁC qa-brain black-box). Từ 1 folder có config.json (do /backfill-checklist sinh từ threease_sync_ticket_review xlsx) → chạy pipeline: baseline DB → screenshot before → migrate (chọn SoT) → after → confirm bug → Excel evidence 4 sheet. Generic mọi branch/chiều. KHÔNG chạy migrate khi user chưa xác nhận (thao tác phá huỷ, DB dev dùng chung).
---

# backfill — chạy + đóng gói evidence 1 backfill migration (GENERAL, mọi branch/chiều)

> **Build-time**, ĐƯỢC đọc code + GitNexus + DEV-ACCOUNTS. KHÁC `qa-brain` (black-box, mù code).
> Scripts: `.claude/skills-scripts/backfill/`. Ví dụ mẫu đã chạy: `wtf-is-this/backfill-branch179/`.

## Input & flow (2 command)
1. User tạo `wtf-is-this/backfill-branch-<X>/`, để `threease_sync_ticket_review_*.xlsx` + báo branch/dòng.
2. **`/backfill-checklist <folder>`** → đọc sheet `Branch_要確認` dòng branch → sinh `config.json` + `CHECKLIST.md`.
3. **`/backfill-run <folder>`** → pipeline đầy đủ → Excel evidence. **DỪNG xác nhận trước migrate.**

## config.json (nguồn sự thật — mọi script đọc từ đây)
`{branch_id, institute_code, rails_institute_id, sot ('pro'|'ticket_app'), branch_name_jp, pro_staff_code, ticket_staff_code, password, repo_root, out_dir}`

## ⚠️ 4 LUẬT KIỂM CHỨNG (đọc trước khi chấm PASS — rút từ lỗi thật)
1. **Verdict chỉ từ QUAN SÁT, ko từ suy luận code.** `traced (chưa chạy)` ≠ `PASS (đã chạy + thấy)`. Ko trộn.
2. **Chưa mở xem ảnh thì ko trích làm bằng chứng.** Mỗi screenshot phải `Read` trước khi đưa vào report.
3. **Mỗi output query đối chiếu 1 fact chéo trước khi tin.** Số mâu thuẫn fact đã biết = query sai, ko phải sự thật.
4. **Mỗi mục ghi rõ:** `traced-only` / `observed-PASS` / `observed-FAIL`. Khi user hỏi "xong chưa" → liệt kê thẳng.

## Ràng buộc
- **DEV LOCAL ONLY.** Migrate là **phá huỷ, ko revert**; DB dev **dùng chung** → **hỏi user trước khi migrate**.
- Creds LOCAL từ `DEV-ACCOUNTS.md` (đã đưa vào config): Pro `<institute>/<pro_staff>`, Ticket `<institute>/seed-admin`, Backfill `superadmin/Admin1234!`, pass `password123`. Scripts tự set env localhost (lib_backfill.js).
- **Cần** `threease_backend/config/initializers/zz_local_dev_storage.rb` (ép ActiveStorage `:local`) — ko có → export kẹt 90% (BUG-3).

## 2 CHIỀU + no-op (cốt lõi)
| sot | Chiều | SoT tạo vé | Bên archive_only | Bug đặc thù |
|---|---|---|---|---|
| `ticket_app` | Ticket→Pro (vd 179) | Django → sync Pro | Rails (mất buổi) | refund crash · remaining dư |
| `pro` | Pro→Ticket (vd 212) | Rails → sync Django | Django | + **BUG-5** sync ticket_option_id fail |
- **Branch rỗng** (candidates=0 cả 2 bên, vd 211): `db.py` set `noop=true` → bỏ qua migrate, Excel ghi "trống".
- Modal backfill: radio `input[name=sotChoice][value=<sot>]`.

## Pipeline `/backfill-run` (gọi script theo thứ tự)
```
python3 .claude/skills-scripts/backfill/db.py <folder> before
node    .claude/skills-scripts/backfill/capture.js <folder> before
# ==== DỪNG: đọc DATA_before.md, xác nhận chiều + số với user (migrate phá huỷ) ====
node    .claude/skills-scripts/backfill/migrate.js <folder>          # đọc sot từ config
python3 .claude/skills-scripts/backfill/db.py <folder> after
python3 .claude/skills-scripts/backfill/gen_exports.py <folder>       # 3 xlsx thật
node    .claude/skills-scripts/backfill/capture.js <folder> after
python3 .claude/skills-scripts/backfill/confirm_bugs.py <folder>      # tạo+cleanup test data
python3 .claude/skills-scripts/backfill/annotate.py <folder>
python3 .claude/skills-scripts/backfill/make_bug_images.py <folder>
python3 .claude/skills-scripts/backfill/build_excel.py <folder>       # → Backfill_<inst>_branch<X>_Evidence.xlsx
```
> Python dùng venv có openpyxl+pillow: `/Users/TruongDinhDucTri/Work/ThreeSides/.venv-xlsx/bin/python`.
> Node chạy từ `.claude/skills-scripts/testcase-evidence/` (nơi có node_modules playwright) HOẶC set NODE_PATH.

## Artifacts trong branch folder (scripts đọc/ghi)
`config.json`(in) · `CHECKLIST.md`(người đọc) · `data_<phase>.json`+`DATA_<phase>.md` · `captures.json`(manifest ảnh) · `bugs.json` · `exports.json` · `before/ after/ shots_raw/` · `Backfill_*_Evidence.xlsx`(out).

## Bug catalog (đã biết — confirm_bugs.py tự kiểm)
- **BUG-1 refund crash:** vé migrate `reservation_ticket=nil` → `RefundCase` NoMethodError (`refund_case.rb:65`). Fix: safe-nav.
- **BUG-2 remaining dư:** `update_view_job.rb remaining_ticket_count` đếm slip ko `.not_archived` → phồng.
- **BUG-3 export S3:** dev thiếu AWS key → kẹt 90%. Workaround `zz_local_dev_storage.rb`.
- **OBS-1 đếm phồng 30 ngày:** vé migrate created_at=now → lọt dashboard. Tiền đúng, đếm sai. Cần hỏi dev.
- **BUG-5 (Pro→Ticket):** Rails gửi `ticket_option_id=direct_option.django_ticket_option_id`, 2008/2011 option thiếu mapping → Django `TicketPack.ticket_option` null=False → reject → khách mất buổi. confirm_bugs.py check `th_syncoutboxevent`.

## Routes/selector (dò rồi — dùng GitNexus nếu app đổi)
- Branch switch (Pro): header `text=整骨院` → click tên branch JP.
- Backfill: `/superuser/backfill/ticket-packs/` · radio `input[name=branch-select][value=<B>]` · `#migrate-btn` · `input[name=sotChoice][value=<sot>]` · nút `text=OK (実行)`. Rails archive lô 100 → loop.
- Pro packs 合計: `/tickets/packs` → `tr:has(text=合計)`.
- Customer: `顧客管理` → click td 顧客ID = code → modal → tab `text=チケット情報`. (URL trực tiếp 404.)
- 3 export: nút `回数券消化履歴`/`スタッフ別消化履歴`/`月末時点残高` (async → dùng gen_exports.py sinh thẳng).
- 精算: `/accounting` → `PRINT JOURNAL`. Reservations: `/dashboard` → 予約履歴 → `EXCEL` (GitNexus: DashboardReservationTable.vue).

## Verify (đọc-only, an toàn) trước khi chạy thật
`/backfill-checklist <folder>` + `db.py <folder> before` → số khớp DB (candidates), noop đúng. KHÔNG migrate tới khi user OK.
