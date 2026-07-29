---
name: backfill
description: Use when you need to run + evidence a ticket-pack backfill migration for ONE branch on DEV LOCAL (any direction). Build-time task (ĐƯỢC đọc code + GitNexus — KHÁC qa-brain black-box). Từ 1 folder có config.json (do /backfill-checklist sinh từ threease_sync_ticket_review xlsx) → chạy pipeline: baseline DB → screenshot before → migrate (chọn SoT) → after → confirm bug → Excel evidence 5 sheet (có SUMMARY cho sếp/khách). Phủ ĐỦ report (REPORT_REGISTRY) + ĐỦ flow đụng vé 2 hệ + app khách (FUNC_CASES), mỗi thứ có ảnh. Generic mọi branch/chiều. KHÔNG chạy migrate khi user chưa xác nhận (thao tác phá huỷ, DB dev dùng chung).
---

# backfill — chạy + đóng gói evidence 1 backfill migration (GENERAL, mọi branch/chiều)

> **Build-time**, ĐƯỢC đọc code + GitNexus + DEV-ACCOUNTS. KHÁC `qa-brain` (black-box, mù code).
> Scripts: `.claude/skills-scripts/backfill/`. Mẫu đã chạy: `wtf-is-this/backfill-branch179/`.

## Input & flow (2 command)
1. User tạo `wtf-is-this/backfill-branch-<X>/`, để `threease_sync_ticket_review_*.xlsx` + báo branch/dòng.
2. **`/backfill-checklist <folder>`** → đọc sheet `Branch_要確認` dòng branch → sinh `config.json` + `CHECKLIST.md`.
3. **`/backfill-run <folder>`** → pipeline đầy đủ → Excel 5 sheet. **DỪNG xác nhận trước migrate.**

## config.json (nguồn sự thật — mọi script đọc từ đây)
`{branch_id, institute_code, rails_institute_id, sot ('pro'|'ticket_app'), branch_name_jp, pro_staff_code, ticket_staff_code, password, repo_root, out_dir}`
Account lấy từ **`DEV-ACCOUNTS.xlsx`** sheet `Accounts` (C institute_code · D Pro staff · E Ticket staff · F pass), fallback `DEV-ACCOUNTS.md`.

## 3 file cấu hình (nguồn sự thật cho coverage — sửa ở đây, KHÔNG sửa script)
| File | Dùng cho | Ép cái gì |
|---|---|---|
| `REPORT_REGISTRY.json` | sheet 2_REPORT | **23 báo cáo** = PHASE7 (16 dòng) ∪ route thật. Thiếu ảnh → build_excel in đỏ `未撮影` + banner `N/23 ❌` |
| `FUNC_CASES.json` | sheet 3_CHUCNANG | **28 flow** đụng vé: A(Ticket) · B(Pro) · C(app khách) · D(sync) · **E(vé mới có DÙNG ĐƯỢC không — thêm 2026-07-29 sau BUG-041)**. Thiếu ảnh → đỏ + banner; banner riêng `LUỒNG END-TO-END: N/28` (xem §LUẬT FIELD-DELTA) |
| `notes.json` (trong branch folder, người sửa tay) | cột Status/Note + lời SUMMARY | `{func:{A5:{status,note}}, bugs:{BUG-1:{...}}, summary_override:{headline:...}}` — build lại **KHÔNG xoá** ghi chú người review |

## ⚠️ 4 LUẬT KIỂM CHỨNG (đọc trước khi chấm PASS — rút từ lỗi thật)
1. **Verdict chỉ từ QUAN SÁT, ko từ suy luận code.** `traced-only` ≠ `observed-PASS`. Ko trộn.
2. **Chưa mở xem ảnh thì ko trích làm bằng chứng.** Mỗi screenshot phải `Read` trước khi đưa vào report.
3. **Mỗi output query đối chiếu 1 fact chéo trước khi tin.** Số mâu thuẫn fact đã biết = query sai.
4. **Mỗi mục ghi rõ:** `observed-PASS` / `observed-API` / `observed-FAIL` / `ui-only` / `traced-only` / `未実施`+lý do.
   **KHÔNG dựng ảnh giả** cho thứ chưa quan sát được (vd app khách chưa login được → nhãn `observed-API`).

## Ràng buộc
- **DEV LOCAL ONLY.** Migrate là **phá huỷ, ko revert**; DB dev **dùng chung** → **hỏi user trước khi migrate**.
- **Vé THẬT của khách: chỉ ĐỌC.** Không hủy/hoàn/chuyển. Thao tác ghi bên Django chạy trong
  `transaction.atomic()` rồi **ROLLBACK** (service thật vẫn chạy, `on_commit` sync KHÔNG bắn → không
  đẩy rác sang hệ kia). Bên Rails tạo reservation test marker `AIOT-TEST-BF-<branch>` rồi tự revert —
  **BẮT BUỘC verify `cleanup=done` + rác còn = 0**.
- **Cần** `threease_backend/config/initializers/zz_local_dev_storage.rb` (ép ActiveStorage `:local`) —
  ko có → export kẹt 90% (BUG-3).

## 2 CHIỀU + no-op (cốt lõi)
| sot | Chiều | SoT tạo vé | Bên archive_only | Bug đặc thù |
|---|---|---|---|---|
| `ticket_app` | Ticket→Pro (vd 179, 124) | Django → sync Pro | Rails (mất buổi) | refund crash · remaining dư |
| `pro` | Pro→Ticket (vd 212) | Rails → sync Django | Django | + **BUG-5** sync ticket_option_id fail |
- `FUNC_CASES.json` ghi `app` (ticket/pro/...); nhãn **source/dest lật theo `sot`**, build_excel tự làm.
- **Branch rỗng** (candidates=0 cả 2 bên, vd 211): `db.py` set `noop=true` → bỏ migrate, Excel ghi "trống".
- ⛔ **`sot='pro'` KHÔNG idempotent — bấm migrate lại SINH VÉ TRÙNG.** Bên SoT là bên chạy `migrate_pack`
  (`backfill_tool/views.py:1896-1908`). `ticket_app` → Django làm, **đồng bộ**, bấm lại vô hại. `pro` → **Rails**
  làm, mà Rails `queue_adapter=async` ⇒ API trả về TRƯỚC khi xong ⇒ cú bấm kế đọc lại đúng danh sách ứng viên cũ.
  Đo thật 2026-07-29 branch 66 (gerbill): 11 lô → **1.200 vé mới / 354 vé gốc**, có vé **9 bản**, khách +35 buổi khống.
  `migrate.js` nay **bắt buộc đợi dòng branch đứng yên 3 lần đọc** giữa 2 lô — đừng gỡ chốt đó.
  Dọn nếu lỡ trùng: giữ `min(id)` theo `original_pack_id`, `destroy` phần dư (`destroy` để slip đi theo, đừng `delete_all`).
- Modal backfill: radio `input[name=sotChoice][value=<sot>]`.

## ⛔ TIỀN ĐỀ BẮT BUỘC: sync TICKET MASTER trước, migrate pack sau (đo 2026-07-29)
**Đừng chạy `migrate.js` khi master của công ty đó chưa link xong.** 3 bước, đúng thứ tự này:

| # | Làm gì | Ở đâu | Xong khi |
|---|---|---|---|
| 1 | `Select All (ID + 名前一致)` → `Sync Selected` (chọn chiều theo cột `Ticket、Option、Packどちらを正とするか` của file review) | `/superuser/backfill/tickets/?django_id=<X>&rails_id=<Y>&code=<institute>` | các dòng khớp **cả id lẫn tên** thành xanh |
| 2 | Dòng trắng còn lại: tick 1 dòng Ticket → `→ Copy to Rails`; tick 1 dòng Pro → `Copy to Django ←`. **Cả 2 chiều.** | cùng trang | **0 dòng chưa link ở CẢ 2 BÊN** |
| 3 | `Ticket Pack Migration` → chọn đúng branch → migrate | `/superuser/backfill/ticket-packs/` | — |

Trang mở theo **công ty**, KHÔNG phải branch (`システム構造`: Ticket Master 直属 institute).
Bước 2 tự động hoá: `node copy_masters.js <institute_code> <django_id> <rails_id> [--dry] [--max N]`
(`--dry` in danh sách chưa link rồi thoát; script **dừng ngay** khi có alert hoặc khi dòng nguồn
không chuyển sang đã-link — copy là ghi 2 bên, timeout giữa đường sinh rác không kiểm soát được).

**Vì sao bước 3 phải cuối — không phải quy ước, đây là đường dữ liệu:**
```
Django gửi  pro_backend_sync.py:163   'pro_ticket_option_id': ticket_option.pro_ticket_option_id
Rails nhận  sync_controller.rb:228    option = Tickets::Option.find_by(id: pro_ticket_option_id) if pro_ticket_option_id
Rails ghi   sync_controller.rb:247    ticket_option_id: option&.id
```
Master chưa link ⇒ `pro_ticket_option_id` NULL ⇒ `option` nil ⇒ pack sinh ra với **`ticket_option_id` NULL**,
rời khỏi master. Branch 124 đã bị đúng lỗi này: **176/176 pack NULL**, và **sync master sau đó KHÔNG vá ngược**.
Hệ quả: mọi query Pro join `packs → options → tickets` (nhóm theo 回数券, đơn giá master, 税率) không thấy
số pack đó — `Tickets::Pack.with_ticket_options` (`pack.rb:42`) lọc qua `joins(:reservation_ticket)`.

**Guard giải thích tại sao phải có bước 1:** `TICKET_MASTER_SYNC_START_ID = 10000` ·
`TICKET_SYNC_START_ID = 200000` (pack). Record id **dưới** ngưỡng bị coi là dữ liệu cũ và **cấm sync**,
trừ khi có trong allowlist (`threease_ticket_sync_job.rb:226`). Master công ty cũ có id 5–1087 → chặn hết.
Pack mới sinh id ≥ 200000 nên không cần allowlist (đó là lý do `th_sync_ticket_pack_allowlist` rỗng mà pack
vẫn sync được — **không phải bug**).

**Bẫy khi copy — id trùng nhưng TÊN khác = CÙNG một master bị đổi tên một bên.** Ở sakainishi có 4 cặp
(774 `★ﾌﾟﾘﾝｾｽﾌﾟﾛｸﾞﾗﾑ` ↔ `旧★…`, 776, 936, **939**). `Select All` bỏ qua chúng vì so cả tên — **tool làm đúng**.
Copy sẽ sinh bản trùng. Riêng **939 tên bị lệch 1 nhịp giữa 2 hệ** (Rails 939=`EMS(学割)半額` ↔ Django 939=`猫背矯正(学割)半額`)
→ link theo id là nối 2 dịch vụ KHÁC nhau. **Nêu ra cho user quyết, đừng tự đoán.**
User branch 124 đã chọn: cứ copy cả 2 chiều, chấp nhận trùng. Sau khi copy phải verify **link 1-1 đối xứng**
(không có 2 record trỏ cùng đích) — đã verify 108/108 đối xứng.

**Sau bước 1+2, Rails outbox phình.** Mỗi master bị sửa → `after_commit` → `threease_ticket_outbox_events`.
Ở sakainishi: 72 event sau sync, **286** sau khi copy xong. `retry_count=0` toàn bộ = **chưa có cron nào chạy**
`rake threease_ticket:flush_outbox`. **Đừng flush mù** — soi model + `created_at` trước; event cũ nhiều ngày
mang state lỗi thời, flush là đẩy nó ghi đè bên kia.

**Sync master làm Rails treo — phải vá index TRƯỚC.** Callback `tickets/ticket.rb:20 update_packs_view`
gom mọi `reservation_ticket` liên quan → `UpdatePacksJob` (adapter **Async = cùng process Puma**).
Ở sakainishi là **24,900** reservation_ticket. Mà `therapists_products_tickets_packs` có **2.4M dòng và 0 index**
(Postgres KHÔNG tự tạo index cho FK) → mỗi vòng là 1 seq scan 884–3268 ms → Rails no CPU → Django
`timeout=30` nổ `Rails API error: HTTPConnectionPool(...) Read timed out`.
⚠️ **Alert đó KHÔNG có nghĩa là ghi thất bại — dữ liệu đã commit. ĐỪNG bấm lại (ghi đè lần 2).** Verify bằng DB.
Vá: `CREATE INDEX CONCURRENTLY` trên `(pack_id)` + `(product_id)` → 884ms xuống **20.8ms** (42×), ~13s/index.
Index này hiện **chỉ có trên DB local** — dev/prod vẫn thiếu, cần migration trong `threease_backend`.

## Pipeline `/backfill-run`
```
# ==== BƯỚC 0 (BẮT BUỘC, xem mục trên): master sync xong 0 dòng lệch 2 bên ====
node copy_masters.js <institute> <dj_id> <ra_id> --dry   # phải in "chưa link=0" cả 2 bên mới đi tiếp
$PY db.py <folder> before
$PY gen_exports.py <folder> before        # cần bản BEFORE để chứng minh 3 export bất biến
node capture.js <folder> before           # loop REPORT_REGISTRY (23 báo cáo)
node capture_func.js <folder> before      # loop FUNC_CASES (ảnh từng flow, 2 hệ + app khách)
# ==== DỪNG: đọc DATA_before.md, xác nhận chiều + số với user (migrate phá huỷ) ====
node migrate.js <folder>                  # ⛔ sot=pro: KHÔNG idempotent — chốt chờ job nền đã nhúng sẵn
$PY sync_close.py <folder> [--flush]      # ⛔ BẮT BUỘC: "migrate xong" ≠ "đã sang Django"
$PY db.py <folder> after                  # DATA_after.md tự in 🔴 nếu còn vé chưa sync / có vé trùng
node smoke_usable.js <folder>             # ⛔ CỬA CHẶN: vé mới có DÙNG ĐƯỢC không (không phải đúng dữ
                                           #   liệu không). exit≠0 → DỪNG PIPELINE ngay, đừng chụp tiếp.
$PY gen_exports.py <folder> after
node capture.js <folder> after
node capture_func.js <folder> after
$PY confirm_bugs.py <folder>              # chạy service THẬT 2 hệ, chấm verdict 28 case (A-D + E1-E5)
node capture_bugs.js <folder>             # ảnh UI THẬT cho từng bug
$PY annotate.py <folder> · $PY make_bug_images.py <folder>
$PY summarize.py <folder>                 # → summary.json (số liệu cho sheet SUMMARY)
$PY build_excel.py <folder>               # → Backfill_<inst>_branch<X>_Evidence.xlsx (5 sheet)
```
> `$PY` = `/Users/TruongDinhDucTri/Work/ThreeSides/.venv-xlsx/bin/python`.
> Node chạy từ `.claude/skills-scripts/testcase-evidence/` (nơi có node_modules playwright) HOẶC set NODE_PATH.

## Excel 5 sheet
| Sheet | Cho ai | Nội dung |
|---|---|---|
| **0_SUMMARY** | **sếp → call khách** | ①kết luận ②đã làm gì ③ảnh hưởng tới khách ④phần vẫn chạy (hyperlink tới ảnh) ⑤điểm cần biết (bug → 4_BUGS; không phải bug → 2_REPORT/3_CHUCNANG + lý do) ⑥đã xử lý gì + caveat |
| 1_DATA | QA/dev | candidates→0, archive, **Σprice incl archived bất biến** |
| 2_REPORT | QA/dev | 23 báo cáo, before/after + banner coverage |
| 3_CHUCNANG | QA/dev | 28 flow (A-E, nhóm E thêm 2026-07-29 sau BUG-041) — bảng 6 cột (Tính năng·Cơ chế·Quan sát·Kết luận·**Status**·**Note**) + ảnh từng case + banner coverage ẢNH + banner riêng **LUỒNG END-TO-END: N/28** (case `verdict_scope=data` không tính vào end-to-end) + dòng cleanup |
| 4_BUGS | dev | **ảnh UI thật trước** → panel "chi tiết kỹ thuật (cho dev)" sau + Status/Note |

## Artifacts trong branch folder
`config.json`(in) · `notes.json`(người) · `CHECKLIST.md` · `data_<phase>.json`+`DATA_<phase>.md` ·
`captures.json`(manifest ảnh) · `bugs.json`(bug + 23 verdict + cleanup) · `exports_<phase>.json` ·
`summary.json` · `before/ after/ shots_raw/` · `Backfill_*_Evidence.xlsx`(out).

## ⛔ LUẬT FIELD-DELTA (đọc trước khi chấm bất kỳ case nào PASS — thêm 2026-07-29 sau BUG-041)

**Nguyên tắc chốt:** *Bất biến dữ liệu xanh (đếm vé, tổng tiền, tổng buổi, đồng bộ 2 hệ) KHÔNG kết
luận được tính năng còn DÙNG ĐƯỢC hay không.* Mọi thao tác sửa hàng loạt lên vé/đơn/booking phải có
ít nhất 1 case đi UI THẬT, TRỌN VẸN, kèm đối chứng bằng bản ghi không bị đụng.

**Cách áp dụng — liệt kê mọi cột hàm tạo/sửa vé thay đổi → hỏi "ai đọc cột đó" → cột không có case
phủ = lỗ:**
- ⚠️ **2 chiều = 2 HÀM KHÁC NHAU, đọc field-delta CHUNG cho cả 2 chiều là sai** (đã tự mắc lỗi này 1
  lần — xem case thật bên dưới). Soi riêng `Tickets::PackMigrationService#migrate!`
  (`pack_migration_service.rb`, chiều `sot=pro`) VÀ `SyncController#handle_pack_issued`
  (`sync_controller.rb`, chiều `sot=ticket_app`) — đừng suy luận chéo từ chiều này sang chiều kia.
- Cột bị bỏ/đổi mà **chưa liệt kê được ai đọc nó** ⇒ ghi `chưa kiểm`, **CẤM ghi "cố ý nên không sao"**.
  Ghi chú thiết kế giải thích *VÌ SAO làm* — nó KHÔNG chứng minh *KHÔNG HẠI*.
- Case có giá trị là "người dùng làm được X" (dùng buổi, chọn product, transfer...) → **CẤM đóng bằng
  `driver: code` một mình**. Gọi thẳng hàm ở tầng Rails/Django console chứng minh *dữ liệu đúng*,
  KHÔNG chứng minh *nhân viên bấm được*. Xem field `verdict_scope` trong `FUNC_CASES.json`: case nào
  ghi `"data"` thì verdict của nó chỉ là PASS(data), KHÔNG được liệt vào "vẫn chạy bình thường" ở
  sheet SUMMARY nếu chưa có case UI thật (nhóm E) xác nhận song song.

**Case thật đã xảy ra (đọc để nhớ bẫy, đừng lặp):** Branch 66 migrate xong, 4 bất biến dữ liệu đều
xanh (13 PASS/2 FAIL, doanh thu bất biến, sync 817/817). Nhân viên thao tác TAY phát hiện: **vé mới
không chọn được product nào để dùng**. Điều tra qua 3 bước, 2 lần sai trước khi đúng:
1. ❌ Đoán `update_packs_job.rb` (fill product qua `reservation_ticket`) — đo branch 66 thấy
   `pack_migration_service.rb#migrate!` copy `products:`/`items:` đúng, giả thuyết sai, tự sửa.
2. ⚠️ Kết luận tạm "chưa xác định cơ chế, cần dev truy tiếp" — ĐÚNG cho branch 66 (chiều `pro`),
   nhưng dừng lại ở đây là CHƯA ĐỦ vì bug là quan sát THẬT (đồng nghiệp tái hiện tay), phải truy tới
   cùng chứ không khoanh tay.
3. ✅ Được chỉ đúng hướng ("khi đồng bộ từ ticket sang") → tìm ra `sync_controller.rb#handle_pack_issued`
   (dòng 236-249, chiều `sot=ticket_app`) tạo `Tickets::Pack` **thiếu `products:`/`items:`** — so với
   `migrate!` (dòng 48-49) có copy đủ. Đo branch 124: **169/176 (96%)** vé `product_option='custom'` →
   `item_ids` rỗng → không chọn được product. Branch 179: **90/90 (100%)**.
→ `smoke_usable.js` build ra từ case này, verify: branch 124 FAIL đúng (exit 1), branch 66 PASS đúng
(exit 0, đối chứng — chiều `pro` không dính).

## Bug catalog (đã biết — confirm_bugs.py tự kiểm)
- **BUG-041 (nặng nhất, CONFIRM code+data 2026-07-29):** vé nhận qua sync Ticket App→Pro (chiều
  `sot=ticket_app`) không chọn được product để dùng. Cơ chế: xem mục LUẬT FIELD-DELTA ở trên.
  Chỉ áp dụng chiều `ticket_app` — chiều `pro` (`migrate!`) đã verify KHÔNG dính.
- **BUG-042:** vé mới (cả 2 chiều) mất lịch sử số buổi đã dùng — `migrate!:58` và
  `handle_pack_issued:250` đều tạo mới đúng `redeemable_count` slip, không copy slip đã dùng của vé
  gốc. Đo branch 66: 194/400 (48.5%) vé đổi tổng hiển thị `X/Y`.
- **BUG-1 refund crash (Pro):** vé migrate `reservation_ticket=nil` → `RefundCase` NoMethodError
  (`refund_case.rb:65`). Fix: safe-nav. Đối chứng: bên Ticket `is_refundable()` không crash.
- **BUG-2 remaining dư (Pro):** `update_view_job.rb remaining_ticket_count` đếm slip ko `.not_archived`.
- **BUG-3 export S3:** dev thiếu AWS key → kẹt 90%. Workaround `zz_local_dev_storage.rb`.
- **OBS-1 đếm phồng 30 ngày:** vé migrate `created_at=now` → lọt dashboard. Tiền đúng, đếm sai.
- **BUG-5 (Pro→Ticket):** Rails gửi `ticket_option_id` thiếu mapping (option 2008/2011) → Django reject.
- **BUG-6 (mới, do C1 phát hiện được):** app KHÁCH không thấy vé migrate → với khách là "mất vé".

## Routes/selector (dò từ route thật — dùng GitNexus nếu app đổi)
**Ticket app (Django, `backoffice/urls.py`)**
- vé: `/ticketpack/` list · `/ticketpack/<pk>/` detail · `/cancel/` · `/refund/` → `/refund/done/` · `/transfer/`
- khách: `/ticket-ops/view|use|issue/customer/<customer_id>/` · `/customer/link/`
- master: `/ticket/` · `/ticket/<pk>/` · `/ticket/calc/`
- report: `/reports/{,sales/,sales/snapshots/,usage/,timeline/,branches/,staff/}` ·
  `/coupon-reports/{,sales/,sales/snapshots/,usage/,timeline/,branches/,staff/}` (7 trang, PHASE7 ghi "5")
- backfill: `/superuser/backfill/ticket-packs/` · `input[name=branch-select][value=<B>]` · `#migrate-btn` ·
  `input[name=sotChoice][value=<sot>]` · `text=OK (実行)`. Rails archive lô 100 → loop.
- service gọi được từ shell: `TicketUseService(pack).use(1, branch=, staff=, notes=)` ·
  `TicketTransferService(pack).transfer(1, receiver=, notes=)` · predicate `pack.is_cancellable()/is_refundable()/is_usable()`.
  ⚠️ `TicketIssueSevice.create()` có `on_commit` sync sang Pro → **không submit thật**.

**Pro (Rails/Nuxt)**
- `/tickets/packs` (`tr:has(text=合計)`) · `/accounting` → `PRINT JOURNAL` · `/dashboard` → 予約履歴 `EXCEL` ·
  `/clinic_setting/tickets` · `/crm`
- Customer: `顧客管理` → click td 顧客ID = code → modal → tab `text=チケット情報` (URL trực tiếp 404).
  **Mở tab này tự gọi API refundability → BUG-1 lộ ra ngay, KHÔNG cần bấm 返金.**
- refund API: `GET/POST /therapists/.../ticket_packs/:id/refundability|refund` (`routes.rb:192`)
- app KHÁCH: `GET /api/home/authenticated/ticket_packs` (`routes.rb:327`) →
  `Therapists::Branch::Customers::TicketPacks::IndexCase` + `Tickets::CustomerTicketPackSerializer`.
  UI ở `threease_reservation/pages/_branchId/tickets.vue` (8082) — **`pw_lib` target `reservation` có
  `login: null`** → chưa login được khách bằng Playwright ⇒ nhãn `observed-API`, không bịa ảnh.
- 3 export async → dùng `gen_exports.py` sinh thẳng.

## Bẫy cơ khí đã gặp (đọc trước khi debug)
- 🔴 **NGUY HIỂM NHẤT — `pw_lib` build CFG MỘT LẦN lúc require.** Target nào require trước sẽ quyết
  định BASE của mọi target sau. `capture.js` gọi `getPage('ticket')` trước ⇒ nếu chỉ set env của
  target hiện tại thì `CFG.pro.BASE` rơi về default = **`https://develop.pro.threease.com` (DEV
  REMOTE)** + dùng state cache account remote (`テスト 管理者`) ⇒ **chụp evidence của môi trường khác**
  (và tệ hơn: có thể thao tác ghi lên môi trường người khác). Fix: `lib_backfill.setAllEnv(cfg)` set
  env cho **mọi** target trước bất kỳ require nào, + `assertLocal()` chốt cứng chỉ cho localhost.
  Dấu hiệu nhận biết: header Pro là `テスト 管理者` thay vì tên staff trong config.
- **Pro chỉ hiện 1 branch trong bộ chọn** → **KHÔNG phải account thiếu quyền.** Therapist có
  `branch_option='all'` nhưng bảng join `therapists_therapists_branches` chưa được gán đủ
  (`branch_ids=[3]` trong khi institute có 30 branch). Fix: chạy **`./seed_dev_accounts.sh`** ở
  workspace root (idempotent, dev-only) — script này gán `t.branch_ids = inst.branches`.
  Kiểm nhanh: `Therapist.find_by(staff_code:'<x>').branch_ids.size` vs `institute.branches.count`.
  ⚠️ Đã kết luận SAI 1 lần ("matuda không có quyền") vì chỉ nhìn UI. Kiểm DB trước khi đổi account.
- **Ticket app không switch branch** → report dashboard/販売 lấy số của branch đang chọn trong
  session ⇒ **bằng chứng sai branch**. `capture.js` bắt buộc `switchBranchTicket` + chặn cứng nếu lệch.
- **`/reports/staff/` · `/coupon-reports/staff/` trả HTTP 400** → không phải bug: 2 report này
  **chỉ có CSV**, không có trang HTML. Đường thật: trang 店舗別 → khu スタッフ別消化履歴 → `CSVダウンロード`.
- **Pro `seed-admin` KHÔNG login được** (Pro dùng therapist staff_code riêng theo institute) — đừng
  lấy `seed-admin` làm Pro staff; đó là staff code của **Ticket app**.
- **KHÔNG `goto('/')` ngay sau khi login Pro** — devise-token chưa kịp vào localStorage, hard-reload
  1 nhịp là app đá về `/login`. `switchBranch` bấm dropdown ngay trên trang hiện tại.
- **Pro login flake** — `pw_lib` dùng `waitForURL(...).catch(()=>{})` nên login trượt là IM LẶNG đứng
  ở `/login`. `lib_backfill` đã bọc retry 3 lần + `assertLocal`. Sau switch còn **assert header =
  tên branch đích** (từng lạc sang user `テスト 管理者`).
- **Ô `検索` bên Pro chỉ lọc khi bấm ENTER** — chỉ `fill` thì list vẫn 100 dòng trang 1 ⇒ tưởng
  "không có khách này". Danh sách 顧客管理 **phân trang**, phải lọc trước rồi mới tìm 顧客ID.
- **Nút CSV trên report Ticket chỉ render SAU khi bấm 検索** (chưa có bảng thì chưa có nút).
- 🔴 **`migrate.js`: KHÔNG dùng nhãn `移行済み` làm điều kiện dừng** — nhãn hiện sau MỖI lô. Branch 124
  mới chạy 100/307 vé đã báo "xong" ⇒ suýt báo cáo sếp "đã đồng bộ xong" khi còn 207 vé. Lặp tới khi
  **nội dung dòng branch không đổi**, rồi **verify `db.py after` candidates = 0**.
- 🔴 **`candidates=0` ở phase AFTER nghĩa là ĐÃ XONG, không phải "branch trống"** — gán `noop=True`
  làm sheet SUMMARY báo sếp "không có gì để đồng bộ". `db.py` tách `noop` (before) vs `all_done` (after).
- **Phase after phải GHIM đúng khách mẫu của phase before** (sau migrate không còn candidate nên sẽ
  chọn khách khác) — không ghim thì ảnh/số trước-sau là của 2 người khác nhau, không so được.
- **Một key một dòng khi `puts`/`print`** cho parser `kv()`. Nhét 2 key 1 dòng thì key sau MẤT → case
  bị chấm oan `未実施` dù đã chạy OK.
- 🔴 **Đo outbox TRƯỚC khi chạy test sync** — job `sync_remaining` trong test tự tạo outbox event, đo
  sau thì chính test của mình bị đếm là "vé còn nằm chờ" ⇒ **FAIL oan**. Và phân biệt `pending`
  (cron chưa chạy — vấn đề hạ tầng có trước) với `error` (lỗi thật).
- **Test tự tạo dữ liệu thiếu quan hệ ⇒ FAIL oan:** vé test tạo tay không có `TicketIssue` →
  `TicketTransferService` báo "TicketPack has no issue". Chạy service trên **vé thật** trong
  `atomic()+rollback` thay vì dựng vé giả.
- **`confirm_bugs.py` ghi đè `bugs.json`** → chạy lại sau `capture_bugs.js` sẽ xoá ảnh UI của bug.
  Đã cho nó giữ lại `ui_capture` theo bug id.
- **Đừng gộp 3 tầng khi tả bug:** (1) code crash · (2) UI có lộ ra không · (3) điều kiện user chạm tới.
  Branch 124: `RefundCase.valid?` CRASH ở code, nhưng UI **vô hiệu hoá nút 返金** và **không có 5xx**
  (vé migrate chưa dùng buổi nào → `is_refundable=false`). Viết "UI lỗi 500" là phóng đại.
- **Case `driver=code/api` không có màn UI** → đừng đòi ảnh (dễ dẫn tới dựng ảnh giả). Coverage ảnh
  chỉ tính case có UI; case code chấm bằng kết quả chạy thật.
- **Case `ui-only` HTTP 200 = CHẠY BÌNH THƯỜNG**, đừng nhét vào mục "điểm cần biết" của SUMMARY
  (từng làm 10 chức năng tốt bị hiện như đang có vấn đề). Màn lỗi thì phải nói rõ **lỗi có trước
  migrate hay không** (so HTTP before vs after).
- **Đừng cộng buổi của 2 hệ lại** (Ticket 1.514 + Pro 4.312) — đếm trùng cùng tập khách ở 2 sổ.

## Verify (đọc-only, an toàn) trước khi chạy thật
`/backfill-checklist <folder>` + `db.py <folder> before` → số khớp DB (candidates), noop đúng.
`build_excel.py <folder>` trên folder chưa có ảnh → phải ra 5 sheet + banner coverage **đỏ 0/23**
(im lặng bỏ qua = script sai). KHÔNG migrate tới khi user OK.
