# ✅ Checklist backfill — {{INSTITUTE_CODE}} · Branch **{{BRANCH_ID}} ({{BRANCH_NAME_JP}})**

> **Chiều (sếp quyết ở cột `Ticket/Option/Pack どちらを正`):** {{DIRECTION}} (`sot = {{SOT}}`)
> **Nguồn:** sheet `Branch_要確認` — file review xlsx.

| Branch | Tên (JP) | 会社 | Chiều | Vé mồ côi (baseline) |
|---|---|---|---|---|
| **{{BRANCH_ID}}** | {{BRANCH_NAME_JP}} | {{INSTITUTE_CODE}} (rails id {{RAILS_INSTITUTE_ID}}) | **{{DIRECTION}}** | {{ORPHAN_SUMMARY}} |

{{NOOP_BANNER}}

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
- [ ] `capture.js <folder> before` → chụp: 4 report Ticket + Pro 合計 + customer チケット情報 + 精算 + reservations + backfill row.

# 🅱️ A2 · MIGRATE ({{DIRECTION}})
1. [ ] Backfill `/superuser/backfill/ticket-packs/` → radio branch **{{BRANCH_ID}} {{BRANCH_NAME_JP}}**.
2. [ ] `Migrate Selected` → modal chọn **`{{SOT_LABEL}}`** ← ĐÚNG chiều · bấm `OK (実行)`.
3. [ ] Loop tới hết (Rails archive lô 100). `migrate.js` tự loop.
- [ ] Ghi: migrate = ______ vé (mong đợi {{EXPECT_MIGRATE}}).

# A3 · SAU MIGRATE — 3 tầng
### Tầng 1 DATA — `db.py <folder> after`
- [ ] candidates → **0** · Rails archived = {{EXPECT_ARCHIVE}} · **Σprice incl archived GIỮ NGUYÊN** (doanh thu bất biến).
### Tầng 2 REPORT — `capture.js <folder> after` + `gen_exports.py`
- [ ] 4 report Ticket + Pro 合計 + 精算 + reservations: **販売金額 GIỮ NGUYÊN**. 3 file xlsx thật (history/performance/annual).
- [ ] ⚠️ Dashboard 販売冊数/発行枚数 có thể **phồng** (vé migrate lọt 30 ngày) — tiền đúng, đếm sai (OBS-1).
### Tầng 3 CHỨC NĂNG — `confirm_bugs.py`
- [ ] ① customer thấy vé migrate đúng (vé cũ ẩn) · ② redeem 1 buổi OK · ③ hủy trả buổi OK · ⑤ sync 2 chiều khớp.
- [ ] ④ **refund vé migrate → nghi CRASH** (reservation_ticket nil). {{BUG5_LINE}}

# A4 · Kết luận (điền báo sếp)
| Hạng mục | PASS? |
|---|---|
| Data: candidates→0, archive đúng, doanh thu bất biến | ☐ |
| Report: 販売金額 bảo toàn | ☐ |
| Chức năng: redeem/reclaim/sync chạy | ☐ |
| Bug: refund {{BUG5_CONCL}} | ☐ |

## 📎 Ghi nhớ
- Vé migrate: `price=0` + `effective_price=giá gốc` + `reservation_ticket=nil`.
- Doanh thu bất biến vì report ko lọc archived (vé cũ vẫn đếm) + vé mới price=0.
- Idempotent: bấm migrate lại vô hại.
