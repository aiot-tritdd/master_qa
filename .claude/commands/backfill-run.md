# /backfill-run — chạy hết pipeline backfill + đóng gói Excel evidence 5 sheet

Chạy pipeline đầy đủ cho branch trong folder (đã có `config.json` từ `/backfill-checklist`) → Excel 5 sheet.
**⚠️ Có bước migrate PHÁ HUỶ, ko revert, DB dùng chung → BẮT BUỘC dừng xác nhận với user trước khi migrate.**

## Dùng
```
/backfill-run <folder>        # vd: /backfill-run wtf-is-this/backfill-branch-124
```

## Quy trình (nạp skill `backfill` trước; PY=`/Users/TruongDinhDucTri/Work/ThreeSides/.venv-xlsx/bin/python`)
> Node playwright: `cd .claude/skills-scripts/testcase-evidence` rồi `node ../backfill/<script>.js <abs_folder> ...`
> (nơi có node_modules), hoặc `NODE_PATH=.../testcase-evidence/node_modules`.
> Prereq: `docker compose up -d` + `zz_local_dev_storage.rb` tồn tại.

**⛔ PHASE 0 — MASTER SYNC (làm TRƯỚC, không được bỏ; chi tiết + lý do ở SKILL.md §TIỀN ĐỀ):**
0a. **Vá index trước, nếu chưa có** — nếu không, bước 0b/0c làm Rails treo rồi Django timeout:
   `CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pt_packs_pack_id ON therapists_products_tickets_packs (pack_id);`
   (+ bản `(product_id)`). Bảng 2.4M dòng, 0 index. 884ms → 20.8ms.
0b. Mở `/superuser/backfill/tickets/?django_id=<X>&rails_id=<Y>&code=<institute>` (theo **CÔNG TY**, không phải
   branch) → `Select All (ID + 名前一致)` → `Sync Selected`, chiều lấy từ cột
   `Ticket、Option、Packどちらを正とするか` của file review. Login `/admin/login/` (username thuần `superadmin`).
0c. `node .../backfill/copy_masters.js <institute> <dj_id> <ra_id>` → copy 2 chiều phần còn lệch.
   Chạy `--dry` trước để xem danh sách. Script tự **dừng** khi có alert / dòng không chuyển sang đã-link.
0d. **CỔNG CHẶN:** `--dry` phải in `chưa link=0` ở **CẢ 2 BÊN** mới được đi tiếp. Chưa 0 → **KHÔNG migrate**,
   vì pack sẽ sinh ra với `ticket_option_id` NULL (branch 124 đã bị: 176/176 NULL, sync sau KHÔNG vá ngược).
0e. Báo user: id nào trùng-id-khác-tên (cùng master bị đổi tên) → **user quyết** copy hay link tay, đừng tự đoán.
0f. Sau 0b/0c: đo Rails outbox (`threease_ticket_outbox_events`). Nó sẽ phình (sakainishi: 286 event).
   **KHÔNG tự flush** — báo user, soi model + `created_at` trước.

**PHASE BEFORE (read + chụp):**
1. `$PY .../backfill/db.py <folder> before`
2. `$PY .../backfill/gen_exports.py <folder> before` → 3 xlsx vào `before/` (cần để so bất biến)
3. `node .../backfill/capture.js <folder> before` → loop **REPORT_REGISTRY (23 báo cáo)**
4. `node .../backfill/capture_func.js <folder> before` → loop **FUNC_CASES (23 flow)**, 2 hệ + app khách
   → **Read vài ảnh** kiểm render OK (luật kiểm chứng #2). Báo user màn nào 403/404 (đừng tự đổi account).

**⛔ DỪNG — XÁC NHẬN MIGRATE:**
5. Đọc `DATA_before.md` + `config.json`. Báo user: branch, **chiều + SoT**, số vé sẽ tạo/archive, bên nào mất buổi.
   - `noop=true` → báo "branch trống, KHÔNG migrate" → nhảy tới build Excel (đánh dấu no-op).
   - **Chờ user gật ("chạy đi")** rồi mới sang bước 6. Migrate là phá huỷ.

**PHASE MIGRATE + AFTER:**
6. `node .../backfill/migrate.js <folder>` (đọc sot từ config, loop tới hết).
7. `$PY .../backfill/db.py <folder> after` → verify candidates→0, archive đúng,
   **Σprice incl archived bất biến** (đối chiếu before — luật #3).
8. `$PY .../backfill/gen_exports.py <folder> after`
9. `node .../backfill/capture.js <folder> after` · `node .../backfill/capture_func.js <folder> after`
   → **Read ảnh** (tối thiểu: bf_row, 1 report Ticket, mọi ảnh nhóm B bên đích).
10. `$PY .../backfill/confirm_bugs.py <folder>` → chạy **service THẬT** 2 hệ, chấm verdict 23 case.
    Django: atomic + **ROLLBACK**; Rails: reservation test marker `AIOT-TEST-BF-*` + revert.
    **BẮT BUỘC verify `cleanup.rails=done`, `django_rollback=done`, `django_garbage_rows=0`.**
11. `node .../backfill/capture_bugs.js <folder>` → ảnh **UI thật** cho từng bug (chỉ MỞ, không xác nhận).

**PHASE BUILD:**
12. `$PY .../backfill/annotate.py <folder>` · `$PY .../backfill/make_bug_images.py <folder>`
13. `$PY .../backfill/summarize.py <folder>` → `summary.json` (số liệu sheet SUMMARY)
14. `$PY .../backfill/build_excel.py <folder>` → `Backfill_<inst>_branch<X>_Evidence.xlsx`
15. **Verify:** load Excel — **5 sheet**, **coverage `23/23` cả 2 banner** (thiếu thì đi chụp bù, đừng
    báo xong), 3_CHUCNANG có ảnh **từng** case, 4_BUGS mỗi bug có ảnh UI (hoặc ghi rõ "không quan sát
    được trên UI"), 0_SUMMARY hyperlink nhảy đúng ô. Báo user theo 4 luật: observed-PASS / observed-FAIL /
    未実施 + lý do, bug nào confirmed.

## Ràng buộc (từ SKILL.md)
- KHÔNG bước 6 (migrate) khi user chưa xác nhận rõ ràng ở bước 5.
- Verdict chỉ từ quan sát (đọc DATA/ảnh thật), ko suy luận. **Không dựng ảnh giả** cho case chưa quan sát được.
- **Vé thật của khách: chỉ ĐỌC.** Không hủy/hoàn/chuyển vé khách; thao tác ghi chỉ trên data test + revert.
- Selector gãy → dùng GitNexus trace app (KHÔNG mò mù), cập nhật `REPORT_REGISTRY.json`/`FUNC_CASES.json`
  hoặc script, rồi ghi lại vào mục Routes/selector của SKILL.md.
- Muốn ghi chú "cái này không phải bug" → sửa `notes.json` trong branch folder rồi chạy lại
  `build_excel.py` (build lại KHÔNG xoá note).
