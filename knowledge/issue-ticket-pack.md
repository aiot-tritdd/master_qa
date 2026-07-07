---
id: issue-ticket-pack
status: draft
kind: flow
spans_repos: [pro, backend, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: null
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
- Pro: Customer → số dư vé của khách.
- ⚠️ Gói vé/使用履歴 phía ticket: **CHƯA chốt kênh.** Django admin (`ticket-dev/admin/th/`) chỉ lộ
  model sync (customer/institute/branch/staff), **không có model pack** → khả năng phải xem ở
  **ticket-app** (`getPage('ticket')`, TESTSEED001). Cần confirm lại trước khi approve.

**Ghi chú vận hành:** booking KH tương lai không hiện ở calendar mặc định (hôm nay); điều hướng
ngày trước khi thao tác. Dữ liệu test PHẢI prefix `AIOTTEST*` để `/testcase-cleanup` quét được.

## Build-time confirm log (2026-07-07)
- GitNexus `@threease` cho flow này **thưa/lạc** (backend Rails yếu index) → UI-confirm gánh sự thật.
- `ticket_admin` login ✅. Django admin lộ model sync, **KHÔNG** thấy pack → điểm quan sát pack cần
  xác nhận lại ở ticket-app. → **status giữ `draft`** (gate chưa pass đủ, chưa `approved`).
