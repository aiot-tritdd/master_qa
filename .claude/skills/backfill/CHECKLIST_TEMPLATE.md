# ✅ Checklist backfill — {{INSTITUTE_CODE}} · Branch **{{BRANCH_ID}} ({{BRANCH_NAME_JP}})**

> **Chiều (sếp quyết ở cột `Ticket/Option/Pack どちらを正`):** {{DIRECTION}} (`sot = {{SOT}}`)
> **Nguồn:** sheet `Branch_要確認` — file review xlsx.

| Branch | Tên (JP) | 会社 | Chiều | Vé mồ côi (baseline) |
|---|---|---|---|---|
| **{{BRANCH_ID}}** | {{BRANCH_NAME_JP}} | {{INSTITUTE_CODE}} (rails id {{RAILS_INSTITUTE_ID}}) | **{{DIRECTION}}** | {{ORPHAN_SUMMARY}} |

{{NOOP_BANNER}}

## 0.0 · ⛔ CỔNG CHẶN — MASTER SYNC PHẢI XONG TRƯỚC KHI MIGRATE PACK
Thứ tự này không đổi được. Làm ngược = pack sinh ra rời khỏi master, **và sync master sau đó KHÔNG vá ngược**
(branch 124 đã bị: 176/176 pack `ticket_option_id` NULL).

- [ ] **Index đã vá** — `idx_pt_packs_pack_id` + `idx_pt_packs_product_id` trên `therapists_products_tickets_packs`
      (2.4M dòng, mặc định 0 index). Chưa vá → Rails treo, Django báo `Read timed out`.
- [ ] **Bước 1** — `/superuser/backfill/tickets/?django_id=…&rails_id=…&code={{INSTITUTE_CODE}}` (theo **CÔNG TY**)
      → `Select All (ID + 名前一致)` → `Sync Selected`, chiều = **{{DIRECTION}}**.
- [ ] **Bước 2** — copy 2 chiều phần còn lệch: `node copy_masters.js {{INSTITUTE_CODE}} <dj_id> <ra_id>`
- [ ] **Bước 2 xong**: `copy_masters.js … --dry` in **`chưa link=0` ở CẢ 2 BÊN**. Ghi số: Rails ___ / Django ___
- [ ] **Link 1-1 đối xứng** đã verify (không có 2 record trỏ cùng đích). Số cặp: ___
- [ ] Đã **báo user** các id trùng-id-khác-tên (cùng master bị đổi tên 1 bên) — user quyết, QA không tự đoán
- [ ] Đã **đo Rails outbox** sau bước 1+2 (sẽ phình). Số: ___ · **chưa flush** (không flush mù)
- [ ] **Bước 3** — chỉ khi mọi ô trên đã tick: vào `Ticket Pack Migration` → chọn đúng branch **{{BRANCH_ID}}** → migrate

## 0 · Hiểu cái sắp làm
Mỗi phòng khám có 2 sổ vé (Pro + Ticket), 3 năm lệch nhau. Backfill = dọn cho khớp: chọn 1 sổ làm **chuẩn (SoT)**, đồng bộ cả chi nhánh 1 lượt.
- Chiều này = **{{DIRECTION}}** (`sot={{SOT}}`): {{DIRECTION_EXPLAIN}}
- ⚠️ **CHỈ dev local. Migrate phá huỷ, ko revert. DB dùng chung.**

### 0.1 · Tài khoản (LOCAL, từ DEV-ACCOUNTS)
| # | Vào | URL | Điền |
|---|---|---|---|
| ① Backfill | http://localhost:8000/admin/login/ | `superadmin` / `Admin1234!` |
| ② Ticket | http://localhost:8000/accounts/login/ | `{{INSTITUTE_CODE}}` / `{{TICKET_STAFF}}` / `password123` |
| ③ Pro | http://localhost:8080 | `{{INSTITUTE_CODE}}` / `{{PRO_STAFF}}` / `password123` |

---
# 🅰️ A1 · BASELINE (trước migrate)
- [ ] `db.py <folder> before` → Django candidates = **{{DJANGO_CAND}}** · Rails candidates = **{{RAILS_CAND}}** ({{RAILS_CAND_DETAIL}})
- [ ] `gen_exports.py <folder> before` → 3 xlsx bản BEFORE (cần để chứng minh report bất biến)
- [ ] `capture.js <folder> before` → **đủ 23 báo cáo** trong `REPORT_REGISTRY.json` (banner coverage phải 23/23)
- [ ] `capture_func.js <folder> before` → **đủ 28 flow** trong `FUNC_CASES.json` (A Ticket · B Pro · C app khách · D sync · E vé mới có dùng được không)

# 🅱️ A2 · MIGRATE ({{DIRECTION}})
1. [ ] Backfill `/superuser/backfill/ticket-packs/` → radio branch **{{BRANCH_ID}} {{BRANCH_NAME_JP}}**.
2. [ ] `Migrate Selected` → modal chọn **`{{SOT_LABEL}}`** ← ĐÚNG chiều · bấm `OK (実行)`.
3. [ ] Loop tới hết (Rails archive lô 100). `migrate.js` tự loop.
- [ ] Ghi: migrate = ______ vé (mong đợi {{EXPECT_MIGRATE}}).

# A3 · SAU MIGRATE — 5 tầng (thêm tầng "DÙNG ĐƯỢC" sau BUG-041, 2026-07-29)
### Tầng 1 DATA — `db.py <folder> after`
- [ ] candidates → **0** · Rails archived = {{EXPECT_ARCHIVE}} · **Σprice incl archived GIỮ NGUYÊN** (doanh thu bất biến).
- [ ] `DATA_after.md` KHÔNG có dòng 🔴 (còn vé chưa sync / vé trùng) — đọc kỹ, đừng chỉ liếc banner.
### Tầng "DÙNG ĐƯỢC" — ⛔ `node smoke_usable.js <folder>` — CHẠY NGAY SAU db.py after, TRƯỚC report/case
- [ ] `exit=0` (PASS) mới đi tiếp. `exit≠0` → **DỪNG PIPELINE**, báo user ngay — đây là cửa chặn BUG-041
      (4 bất biến dữ liệu xanh mà vé không chọn được product để dùng, chỉ lộ khi thao tác TAY).
### Tầng 2 REPORT — `gen_exports.py after` + `capture.js after`
- [ ] **Đủ 23 báo cáo**, mỗi cái có ảnh before/after. Banner coverage `23/23` — thiếu là đi chụp bù, không báo xong.
- [ ] Mọi TỔNG **販売金額 GIỮ NGUYÊN**; 3 file xlsx so được tổng before vs after.
- [ ] ⚠️ Dashboard 販売冊数/発行枚数 có thể **phồng** (vé migrate lọt 30 ngày) — tiền đúng, đếm sai (OBS-1).
- [ ] ⚠️ `販売記録` từng dòng hiện giá gốc dù thẻ tổng = 0 → **không sai tổng**, cách hiển thị có từ trước.
### Tầng 3 CHỨC NĂNG — `capture_func.js after` + `confirm_bugs.py`
- [ ] **Đủ 28 case có ảnh/verdict** (banner ẢNH riêng + banner **LUỒNG END-TO-END** riêng — 2 con số
      KHÁC NHAU, đừng lẫn: có ảnh ≠ đã xác nhận dùng được). Nhóm A bên nguồn · **nhóm B bên ĐÍCH (nơi vé
      được sync qua)** · C app khách · D sync 2 chiều · **E vé mới có dùng được không (E1-E5)**.
- [ ] Chạy service THẬT: dùng buổi · hủy · hoàn · **chuyển vé (譲渡)** — trên data test, Django rollback.
- [ ] ⚠️ Case `driver:code` (B3/B4) đóng bằng `verdict_scope=data` — nếu E1 FAIL thì tự động hạ cấp
      thành `PASS(data-only)`, KHÔNG được tính là "vẫn chạy bình thường" dù chữ PASS còn đó.
- [ ] **Dọn sạch:** `cleanup.rails=done` · `django_rollback=done` · `django_garbage_rows=0`.
- [ ] ④ **refund vé migrate bên Pro → nghi CRASH** (reservation_ticket nil); đối chứng bên Ticket. {{BUG5_LINE}}
### Tầng 0 SUMMARY — `summarize.py` + `build_excel.py`
- [ ] Sheet `0_SUMMARY` đọc được bởi người KHÔNG kỹ thuật; hyperlink nhảy đúng ô.
- [ ] Mục ⑤ mỗi dòng chỉ rõ **là bug (→4_BUGS)** hay **không phải bug (→2_REPORT/3_CHUCNANG + lý do)**.
- [ ] Ghi chú người review (Status/Note) đặt trong `notes.json`, KHÔNG sửa Excel tay.

# A4 · Kết luận (điền báo sếp)
| Hạng mục | PASS? |
|---|---|
| Data: candidates→0, archive đúng, doanh thu bất biến | ☐ |
| **Dùng được:** `smoke_usable.js` PASS — vé mới CHỌN ĐƯỢC product để dùng | ☐ |
| Report: đủ 23/23 + 販売金額 bảo toàn | ☐ |
| Chức năng: đủ ảnh + banner LUỒNG END-TO-END không đỏ, bên ĐÍCH chạy tốt, app khách thấy vé | ☐ |
| Dọn data test: rác = 0 | ☐ |
| Bug: refund {{BUG5_CONCL}} | ☐ |
| SUMMARY: đủ 6 mục, sếp đọc là call khách được | ☐ |

## 📎 Ghi nhớ
- Vé migrate: `price=0` + `effective_price=giá gốc` + `reservation_ticket=nil`.
- Doanh thu bất biến vì report ko lọc archived (vé cũ vẫn đếm) + vé mới price=0.
- ⛔ **Idempotent CHỈ đúng với `sot='ticket_app'`.** Với `sot='pro'` bấm lại **SINH VÉ TRÙNG**
  (Rails `queue_adapter=async`, API trả về trước khi xong). Branch 66 đã dính: 1.200 vé / 354 gốc.
  → giữa 2 lô phải đợi job nền cạn; `migrate.js` đã có chốt tự đợi.
- ⛔ **BUG-041 (nặng nhất, chiều `sot=ticket_app`):** vé nhận qua sync Ticket→Pro không set
  `products:`/`items:` (`sync_controller.rb#handle_pack_issued`) → phần lớn vé không chọn được
  product để dùng. Chiều `sot=pro` (`migrate!`) KHÔNG dính — đã verify branch 66. `smoke_usable.js`
  đo trực tiếp bug này, chạy NGAY sau migrate — xem SKILL.md §LUẬT FIELD-DELTA.
- **Bất biến dữ liệu xanh KHÔNG kết luận được tính năng dùng được** — mọi thao tác sửa hàng loạt vé
  phải có case UI thật (nhóm E) đi trọn vẹn, kèm đối chứng. Case `driver:code` chỉ chứng minh dữ liệu.
