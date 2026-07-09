---
id: system-api-endpoints
status: draft
kind: system-domain
spans_repos: [backend, pro]
source_symbols:
  - "pro: repository/*.ts"
source_hash: null
confidence: 🔴
verify_by: "CODE-DERIVED, CHƯA GỌI THẬT. Gọi bằng withApi() rồi mới tin. Endpoint đã verify live → chuyển sang knowledge/observation-channels.md (HOW, QA đọc được)."
grown_from: ".claude-tester/knowledge/SYSTEM.md#endpoint-hay-dùng"
---
# API endpoints — CHƯA VERIFY LIVE (WHAT)

> ⛔ **QA-runtime CẤM đọc.** Danh sách này **lấy từ code** (`threease_pro/repository/*.ts`), **chưa từng
> gọi thật**. Theo luật của hệ này, code-derived = `draft`, không đủ để QA tin.
>
> ✅ Endpoint **đã gọi thật và chạy** đã được chuyển sang `knowledge/observation-channels.md`
> (tầng HOW, QA-runtime đọc được). Đừng chép lại ở đây — **1 tri thức = 1 nhà**.

## Chưa verify (gọi thật rồi mới chuyển nhà)

| Việc | Method + path |
|---|---|
| Xóa preset | `DELETE /permissions/presets/{id}` |
| Cập nhật staff (gán preset) | `PUT /staff/{id}` body `{staff:{preset_id}}` |
| Chi tiết / xóa đặt lịch | `GET \| DELETE /branches/{b}/reservations/{id}` |
| Hủy giao dịch | `PUT /branches/{b}/transactions/{id}` body `{transaction:{status:'cancelled'}}` |
| Số dư vé của khách | `GET /branches/{b}/customers/{c}/ticket_packs` |
| List quyền (slug) | `GET /permissions` |

- Permission slug quyền mới (No.10.5): `branch_accounting_edit_after` [nguồn: `GET /permissions`].

## Auth
`devise_token_auth` — 5 header `access-token, client, uid, expiry, token-type`.
**Không** phải `Authorization: Bearer`.
→ Cách lấy: `pw_api.withApi()` **nghe lén** header từ request thật của app. Không tự dựng token.

## ⚠️ Branch
Mọi path `/branches/{b}/...` phụ thuộc branch của **phiên đăng nhập hiện tại**, và giá trị này **đổi theo
phiên/data** (đã thấy 4 → 2 → 3). Sai branch → API trả **404** (không phải 403).
→ Xác nhận branch trước khi gọi. Đo 2026-07-09: phiên `TESTSEED001` = branch **3**.
