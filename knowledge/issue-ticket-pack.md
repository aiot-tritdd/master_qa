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
- ticket-admin (ticket-dev/admin): Packs của customer → pack + slips.

**Ghi chú vận hành:** booking KH tương lai không hiện ở calendar mặc định (hôm nay); điều hướng
ngày trước khi thao tác. Dữ liệu test PHẢI prefix `AIOTTEST*` để `/testcase-cleanup` quét được.
