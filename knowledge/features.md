---
id: features
status: draft
kind: flow
spans_repos: [pro, ticket]
source_symbols: []
source_hash: null
confidence: 🟡
verify_by: "CHƯA UI-confirm dưới ja-JP. Mỗi tính năng phải drive thật (vào đúng route, thấy đúng nhãn) rồi mới approved."
ui_confirmed_at: null
grown_from: ".claude-tester/.claude-knowledge/FEATURES.md (chỉ phần HOW: vào đâu · luồng · bẫy thao tác)"
---
# FEATURES — sổ tay tính năng (HOW: vào đâu · luồng · bẫy thao tác)

> ⚠️ **`status: draft`.** Phần **"vì sao là bug"** của file gốc đã bị tách sang
> `knowledge/system/domain-rules.md` (WHAT, QA cấm đọc). Ở đây **chỉ còn navigation**.
>
> Firewall: không ghi kết quả kỳ vọng. Đúng/sai = SPEC + quan sát live.

## Đặt lịch có mua vé (回数券)
- **Vào đâu:** `/reservations` → mở booking → thêm item vé.
- **Luồng thao tác:** tạo đặt lịch + thêm item vé (`未払い`) → mở `請求書` → thanh toán `現金` (`支払い済`)
  → khách được cấp vé.
- **Chuẩn bị data:** cần khách test + item vé có sẵn.
  ✅ Booking mẫu trên dev: `Jenny` 07/09 14:20, **branch 3**, `id=774`, `一部支払済み`,
  có dòng vé `AIOT-TEST-TK1` + coupon `Yoga coupon`.
- **Bẫy thao tác:** hủy thanh toán dùng nút `キャンセル` trên **dòng giao dịch** (màn Hóa đơn) —
  **khác** nút xóa (thùng rác `.mdi-delete-outline`) ở màn Đặt lịch. Hai nút tác dụng khác nhau.
- **Quan sát:** 2 phía — Pro + Hệ thống Vé, đối chiếu API Hệ thống Lõi.
  → `knowledge/observation-channels.md`.
- **Navigation chi tiết (đã UI-confirm):** `knowledge/pro-open-booking.md`.

## Quyền / Preset (権限設定)
- **Vào đâu:** `/clinic_setting/permissions` — bảng preset + bảng gán staff.
  ✅ verify 2026-07-09: `shot()` bắt được `text=権限設定`.
- **Luồng:** tạo preset quyền → gán preset cho staff → preset quyết định staff thấy/thao tác được gì.
- **Chuẩn bị data:** preset **mặc định** không sửa được ô quyền (`disabled`) → tạo preset mới
  `AIOT-TEST-*` rồi gán cho staff test `AIOTTEST*`.
- **Bẫy thao tác:** quên rằng preset mặc định `disabled` → tưởng là bug khi không sửa được.
- **Quan sát API:** `api.get('/permissions/presets')` ✅ đã verify (`200`, 7 preset).

## Hóa đơn / Kế toán (会計)
- **Vào đâu:** `/accounting` — tab `取引履歴` / `予約履歴`. Hóa đơn mở qua nút `請求書` trong booking detail.
  ✅ nhãn `請求書` đã verify (`button.v-btn--outlined:has-text("請求書")`).
- **Luồng:** xem/thao tác giao dịch thanh toán gắn với booking; hủy giao dịch bằng `キャンセル`
  (chuyển trạng thái, **không** xóa hẳn).
- **Chuẩn bị data:** booking đã có giao dịch (`支払い済` / `一部支払済`).
- **Bẫy thao tác:** dialog hủy có **2 nút gần giống**: `閉じる` (đóng) vs `キャンセル` (hủy thật).
  Bấm nhầm `閉じる` → tưởng đã hủy nhưng chưa.

## Báo cáo Coupon/Ticket (レポート) — Hệ thống Vé
- **Vào đâu:** Hệ thống Vé → `/reports` (Ticket) · `/coupon-reports/` (Coupon).
- ⚠️ **Cần quyền riêng:** account `TESTSEED001 / ticket-admin / password123` (env `TK_STAFF=ticket-admin`).
  `STAFF001` **không** vào được (nav thiếu tab, `/reports` redirect về home) → dễ tưởng "chưa build".
- **Cấu trúc màn (theo spec, verify UI thật trước khi tin):** 2 sub-tab `販売` / `消費`.
  Tab `販売`: filter + 8 KPI card + bảng phân trang 50 dòng + nút CSV. Tab `消費`: filter + 3 KPI card + bảng + CSV.
- **Bẫy khái niệm:** đừng nhầm `発行元` (nơi bán) với `使用元` (nơi tiêu) — **2 trục độc lập**.
- **Điểm spec chưa rõ** → `knowledge/OPEN-QUESTIONS.md#OQ-06`, `#OQ-07`. Chạy vào đó ⇒ **`SPEC-GAP`**, không phải FAIL.
- **Navigation:** `knowledge/ticket-coupon-reports.md` (approved).
