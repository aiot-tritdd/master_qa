# SYSTEM — Bản đồ hệ thống (🟡 verify trước khi dùng)

> Fact volatile (branch, endpoint, selector) đổi theo release/data → ⚠️ kiểm lại code/live rồi mới tin.
> Cập nhật: 2026/07/08 (branch, sync Rails↔Django).

## Truy cập
- Pro FE: `https://develop.pro.threease.com` · basic auth `threesides/threesides`
- Login (form): institute `TESTSEED001` / therapist `STAFF001` / pass `password123` [nguồn: 7.Tests/account.txt]
- API: `https://api-dev.threease.com/api/v1/therapists`
- Auth API = **devise token** trong header request thật: `access-token, client, uid, expiry, token-type`
  (pw_api.js tự bắt từ 1 request của app — không tự dựng token).

## ⚠️ Branch (hay nhầm)
- `pw_api`/cleanup dùng `BRANCH_ID`. **Phiên staff TESTSEED001 hiện map branch = 3** (đổi từ 2 hôm 07/07, trước đó default cũ = 4)
  [nguồn: LESSONS 2026/07/08]. → Giá trị này đổi theo phiên/data, luôn xác nhận branch của phiên trước khi gọi API theo branch.

## Endpoint hay dùng [nguồn: threease_pro/repository/*.ts]
| Việc | Method + path |
|------|---------------|
| List preset | `GET /permissions/presets` |
| Xóa preset | `DELETE /permissions/presets/{id}` |
| Cập nhật staff (gán preset) | `PUT /staff/{id}` body `{staff:{preset_id}}` |
| List đặt lịch ngày | `GET /branches/{b}/reservations?start_date=YYYYMMDD&end_date=…&session=all` |
| Chi tiết / xóa đặt lịch | `GET|DELETE /branches/{b}/reservations/{id}` |
| Hủy giao dịch | `PUT /branches/{b}/transactions/{id}` body `{transaction:{status:'cancelled'}}` |
| Số dư vé khách | `GET /branches/{b}/customers/{c}/ticket_packs` |
| List quyền (slug) | `GET /permissions` |

- Permission slug quyền mới (No.10.5): `branch_accounting_edit_after` [nguồn: GET /permissions].

## Đồng bộ Hệ thống Lõi ↔ Hệ thống Vé
Đã tách sang [`../../.claude-knowledge/SYNC_MAP.md`](../../.claude-knowledge/SYNC_MAP.md) (nguồn duy
nhất, có endpoint/file:line/2 chiều/known gaps) — đừng lặp lại nội dung ở đây, sửa quy ước thì sửa ở đó.
Quick-login bridge (`ThreeaseTicketController#quick_login` ↔ `TherapistsQuickLoginView`) cũng ghi ở đó.

## Selector UI (Vuetify)
- Login: `input[data-cy=institute_code|therapist_code|password]`, nút `[data-cy=loginButton]`.
- Input Vuetify: field bọc `div[data-cy=...]` → phải target `input[data-cy=...]` (không phải div).
- Dialog đang mở: `.v-dialog--active` (lấy cái cuối cùng nếu chồng nhau).
- Nút thùng rác chi tiết đặt lịch: icon `.mdi-delete-outline`.
- Màn quyền: `/clinic_setting/permissions`; bảng 2 (preset) + bảng staff; ô quyền là `.v-select` (disabled với default preset).

## Màn hình / route
- Đặt lịch `/reservations` · Kế toán `/accounting` (tab 取引履歴 / 予約履歴) · Quyền `/clinic_setting/permissions`
  · Staff `/clinic_setting/staff` · Hóa đơn = nút「請求書」trong chi tiết đặt lịch.
