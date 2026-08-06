# /backfill-checklist — sinh config.json + CHECKLIST.md cho 1 branch (KHÔNG migrate)

Đọc dòng branch trong review xlsx → sinh `config.json` + `CHECKLIST.md` trong folder. **Chỉ đọc DB, KHÔNG chạy migrate.**

## Dùng
```
/backfill-checklist <folder>          # vd: /backfill-checklist wtf-is-this/backfill-branch-212
```
Trước đó user đã: tạo folder, để `threease_sync_ticket_review_*.xlsx` (trong folder hoặc repo root), và **báo branch/dòng cần làm**. Nếu chưa rõ branch → hỏi user.

## Quy trình (theo skill `backfill` — nạp nó trước)
1. **Tìm review xlsx** (folder → master_qa root → ThreeSides root). Đọc sheet `Branch_要確認`, tìm dòng branch user chỉ định.
   - Cols: `D=branch_id` · `E=会社コード (institute_code)` · `P=Ticket/Option/Pack どちらを正` → `Pro`→`sot=pro`, `Ticket`→`sot=ticket_app`.
   - Tên JP branch: cột `Pro: 店舗名` hoặc `Ticket DB: 店舗名` (lấy tên có thật).
2. **Lấy staff code** từ **`DEV-ACCOUNTS.xlsx`** sheet `Accounts` (cột C `institute_code` · D `Pro staff_code` ·
   E `Ticket staff_code` · F `Password`) → `pro_staff_code` + `ticket_staff_code` (thường `seed-admin`).
   Không thấy dòng institute đó trong xlsx → fallback `DEV-ACCOUNTS.md`; vẫn không có → **hỏi user**.
3. **Lấy `rails_institute_id`**: query `Therapists::Institute.find_by(institute_code:...).id` (hoặc từ db.py sau).
4. **Ghi `config.json`** vào folder (schema ở SKILL.md). `repo_root=/Users/TruongDinhDucTri/Work/ThreeSides`.
5. **Chạy baseline (read-only):**
   ```
   /Users/TruongDinhDucTri/Work/ThreeSides/.venv-xlsx/bin/python .claude/skills-scripts/backfill/db.py <folder> before
   ```
   → đọc `data_before.json`: candidates 2 bên, orphan Σprice/buổi, noop.
6. **Sinh `CHECKLIST.md`** = copy `.claude/skills/backfill/CHECKLIST_TEMPLATE.md`, thay placeholder từ config + data_before:
   - `{{DIRECTION}}` = `Ticket→Pro` (ticket_app) / `Pro→Ticket` (pro).
   - `{{SOT_LABEL}}` = `Ticket App (Django) が SoT` / `Pro (Rails) が SoT`.
   - `{{ORPHAN_SUMMARY}}`, `{{DJANGO_CAND}}`, `{{RAILS_CAND}}`, `{{RAILS_CAND_DETAIL}}` từ data_before.
   - `{{NOOP_BANNER}}` = cảnh báo nếu noop=true, else "".
   - `{{DIRECTION_EXPLAIN}}`: ticket_app→"Django tạo vé đẩy sang Pro; Rails archive vé mồ côi (mất buổi)"; pro→"Rails tạo vé đẩy sang Django; Django archive; **coi chừng BUG-5 sync**".
   - `{{BUG5_LINE}}`/`{{BUG5_CONCL}}`: chỉ điền phần BUG-5 nếu `sot=pro`, else bỏ.
   - Mọi chữ Nhật PHẢI có chú thích tiếng Việt kế bên.
7. **In phạm vi sẽ soi** (để user biết trước độ phủ): số dòng trong
   `.claude/skills/backfill/REPORT_REGISTRY.json` (báo cáo) + `FUNC_CASES.json` (flow chức năng).
8. **Báo user:** tóm tắt config (branch, chiều, candidates, noop) + đường dẫn CHECKLIST.md + phạm vi ở bước 7.
   **KHÔNG chạy /backfill-run** — chờ user xem checklist + ra lệnh.

## Ràng buộc
- Read-only. Nếu `db.py` báo `noop=true` → nói rõ "branch trống, migrate = no-op, chỉ để ghi nhận".
- Nếu review xlsx ko có dòng branch / cột どちらを正 trống → hỏi user chiều (sot) thay vì đoán.
