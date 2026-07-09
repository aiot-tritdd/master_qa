---
id: issue-ticket-pack
status: draft
kind: flow
spans_repos: [pro, backend, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: null
confidence: 🔴
verify_by: "CHƯA UI-confirm — KHÔNG tin. Phải drive thật khâu tạo booking→thanh toán→phát hành vé rồi mới approved."
---
# Flow: Phát hành gói vé (HOW — navigation only)

> ⚠️ Firewall: doc này chỉ ghi **cách vận hành + nơi quan sát**. KHÔNG ghi kết quả kỳ vọng
> / luật nghiệp vụ (đó là SPEC + quan sát live). `status: draft` cho tới khi UI-confirm + người duyệt.

**Mục tiêu nghiệp vụ:** dựng 1 booking đã phát hành gói vé và đã thanh toán (precondition).

**Các bước UI (Pro — develop.pro.threease.com):**
1. Reservation → tạo booking mới cho 1 customer test (prefix `AIOTTEST*`).
2. Trong booking, thêm **sản phẩm vé** (gói N vé).
3. Lưu booking.
4. Mở **hóa đơn** của booking.
5. Thanh toán (現金) → hoàn tất.

**Nơi quan sát (để verify precondition đã dựng — đối chiếu SPEC, KHÔNG phải để phán đúng/sai):**
- Pro: Customer → số dư vé của khách (`getPage('pro')`).
- ✅ Gói vé + 使用履歴 phía ticket: **ticket-app** `getPage('ticket')` → 顧客 → `/customer/<id>/`
  (cột 保有チケット, ステータス 有効/使用済み, 枚数 X/Y, bảng 最近の使用履歴). **Không** phải Django admin.

**Ghi chú vận hành:** booking KH tương lai không hiện ở calendar mặc định (hôm nay); điều hướng
ngày trước khi thao tác. Dữ liệu test PHẢI prefix `AIOTTEST*` để `/testcase-cleanup` quét được.

## Build-time confirm log (2026-07-07)
- GitNexus `@threease` cho flow này **thưa/lạc** (backend Rails yếu index) → UI-confirm gánh sự thật.
- ✅ **Kênh quan sát confirmed:** gói vé/使用履歴 ở **ticket-app** `/customer/<id>/` (vd KH3 `/customer/700006/`
  hiện `有効 8/10 回` + 最近の使用履歴). `getPage('ticket')` + `getPage('ticket_admin')` chạy được.
- ⚠️ **Các bước TẠO (booking→thêm vé→thanh toán→phát hành) CHƯA drive thật** → **status giữ `draft`**.
  Để lên `approved` cần 1 lần drive tạo booking + thanh toán rồi quan sát pack xuất hiện đúng.
