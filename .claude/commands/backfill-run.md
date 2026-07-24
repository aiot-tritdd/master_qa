# /backfill-run — chạy hết pipeline backfill + đóng gói Excel evidence

Chạy pipeline đầy đủ cho branch trong folder (đã có `config.json` từ `/backfill-checklist`) → Excel 4 sheet.
**⚠️ Có bước migrate PHÁ HUỶ, ko revert, DB dùng chung → BẮT BUỘC dừng xác nhận với user trước khi migrate.**

## Dùng
```
/backfill-run <folder>        # vd: /backfill-run wtf-is-this/backfill-branch-212
```

## Quy trình (nạp skill `backfill` trước; PY=`/Users/TruongDinhDucTri/Work/ThreeSides/.venv-xlsx/bin/python`)
> Node chạy playwright: `cd .claude/skills-scripts/testcase-evidence` rồi `node ../backfill/<script>.js <abs_folder> ...` (nơi có node_modules), hoặc `NODE_PATH=.../testcase-evidence/node_modules`.

**PHASE BEFORE (read + chụp):**
1. `$PY .claude/skills-scripts/backfill/db.py <folder> before`
2. `node .claude/skills-scripts/backfill/capture.js <folder> before` → **Read vài ảnh** kiểm render OK (luật kiểm chứng #2).

**⛔ DỪNG — XÁC NHẬN MIGRATE:**
3. Đọc `DATA_before.md` + `config.json`. Báo user: branch, **chiều + SoT**, số vé sẽ tạo/archive, bên nào mất buổi.
   - Nếu `noop=true` → báo "branch trống, KHÔNG migrate" → nhảy tới build Excel (đánh dấu no-op).
   - **Chờ user gật ("chạy đi")** rồi mới sang bước 4. Migrate là phá huỷ.

**PHASE MIGRATE + AFTER:**
4. `node .claude/skills-scripts/backfill/migrate.js <folder>` (đọc sot từ config, loop tới hết).
5. `$PY .claude/skills-scripts/backfill/db.py <folder> after` → verify candidates→0, archive đúng, **Σprice incl archived bất biến** (đối chiếu before — luật #3).
6. `$PY .claude/skills-scripts/backfill/gen_exports.py <folder>` → 3 xlsx thật vào after/.
7. `node .claude/skills-scripts/backfill/capture.js <folder> after` → **Read vài ảnh** kiểm.
8. `$PY .claude/skills-scripts/backfill/confirm_bugs.py <folder>` → refund/remaining/redeem/reclaim/sync (+BUG-5 nếu sot=pro). Tạo test data marker `AIOT-TEST-BF-*` **tự cleanup** — verify `bugs.json.tier3.cleanup=done`.

**PHASE BUILD:**
9. `$PY .claude/skills-scripts/backfill/annotate.py <folder>` · `$PY .../make_bug_images.py <folder>`
10. `$PY .claude/skills-scripts/backfill/build_excel.py <folder>` → `Backfill_<inst>_branch<X>_Evidence.xlsx`.
11. **Verify:** load Excel (4 sheet, có ảnh), **Read ảnh bf_row after** (candidates→0). Báo user theo 4 luật: cái nào observed-PASS, cái nào observed-FAIL, bug nào confirmed.

## Ràng buộc (từ SKILL.md)
- KHÔNG bước 4 (migrate) khi user chưa xác nhận rõ ràng ở bước 3.
- Verdict chỉ từ quan sát (đọc DATA/ảnh thật), ko suy luận. Ghi rõ traced vs observed.
- Nếu script UI (capture/migrate) gãy selector → dùng GitNexus trace app (KHÔNG mò mù), cập nhật selector trong `.claude/skills-scripts/backfill/`.
- confirm_bugs tạo reservation test → BẮT BUỘC kiểm `cleanup=done`, ko để rác DB chung.
