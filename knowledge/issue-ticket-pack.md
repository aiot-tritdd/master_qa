---
id: issue-ticket-pack
status: approved
kind: flow
spans_repos: [pro, backend, ticket]
source_symbols: []
source_hash: null
ui_confirmed_at: 2026-07-14
confidence: 🟢
verify_by: "UI-confirmed 2026-07-14 (ja-JP): drive thật tạo booking + thêm gói vé + lưu chạy được (booking AIOTTEST-KH3 lưu thành công với item AIOT-TEST-TK10/opt10). ⚠️ Khâu customer-autocomplete FLAKY ~20%/lần → BẮT BUỘC bọc retry-loop (xem §Ghi chú vận hành). Approve theo uỷ quyền của chủ dự án 2026-07-14."
grown_from: "GitNexus draft 2026-07-07 (create steps chưa drive) → UI-confirm + approve 2026-07-14"
---
# Flow: Phát hành gói vé (HOW — navigation only)

> ⚠️ Firewall: doc này chỉ ghi **cách vận hành + nơi quan sát**. KHÔNG ghi kết quả kỳ vọng
> / luật nghiệp vụ (đó là SPEC + quan sát live). `status: draft` cho tới khi UI-confirm + người duyệt.

**Mục tiêu nghiệp vụ:** dựng 1 booking đã phát hành gói vé và đã thanh toán (precondition).

**Các bước UI (Pro — develop.pro.threease.com) — CONFIRMED 2026-07-14 (ja-JP):**
0. Chọn store: click `page.locator('text=/院\\d/').first()` → `getByText('<AIoT院N>',{exact:true}).last()`.
   ⚠️ **Branch map:** API `/branches/N` ⇔ store UI **`AIoT院(N-1)`** (branch 2=院1, 4=院3…). Đổi ngày: `.mdi-chevron-left` (2 cái, dùng `.first()`), đọc ngày `getByText(/2026\/\d{2}\/\d{2}/)`.
1. **Mở form tạo booking:** click ô trống calendar. KHÔNG có DOM-class ổn định → **quét toạ độ** (x∈{820,1050,1300,1550}, y∈{520,600,680,760}) tới khi `getByText('お客様')` visible.
2. **Chọn khách:** arrow `.mdi-menu-down` NGAY DƯỚI label `お客様` (không phải arrow trạng thái ở trên) → `input:focus`.fill('AIOTTEST-KH3') → click option `.v-list-item:has-text('AIOTTEST-KH3')`.
   ⚠️ **FLAKY ~20% thành công/lần** → BẮT BUỘC retry (mở lại dropdown / reload trang). Gõ **tên đầy đủ** (search theo prefix; 'KH3' không match).
3. **Thêm gói vé:** `アイテムを追加` → tab **`チケット`** → click tên gói (vd `AIOT-TEST-TK10`) để bung option → tick **icon checkbox** (`.mdi-checkbox-blank-outline`, panel phải x>950) của option (vd `AIOT-opt10`) → **`適用する`** (có **2 nút** cùng tên → dùng `.last()` = nút primary).
4. **Bật nút Lưu:** nếu hiện panel `前回の商品` (gợi ý sản phẩm lần trước) → **đóng bằng X** của panel đó, nếu không **`追加` bị disabled**.
5. **Lưu:** `getByRole('button',{name:'追加',exact:true})` (góc trên phải). Form đóng = đã lưu. (Booking lưu ở trạng thái `完了`.)
6. **Thanh toán (現金) để PHÁT HÀNH vé — CONFIRMED 2026-07-14:** mở `請求書` → click `現金` (chờ ~2.5s, nút お支払い bật do お預かり tự điền = tổng) → poll `お支払い` enabled → click. **Đã verify: thanh toán XONG thì customer +1 gói vé** (保有 1→2). ⇒ **vé phát hành khi THANH TOÁN, không phải lúc lưu 完了.**

## ĐÃ VERIFY (API, 2026-07-14) — precondition mẫu + endpoint
- **Precondition #1 dựng xong:** reservation **804** (branch **2** = store AIoT院1), customer **700006** (`AIOTT03`/AIOTTEST-KH3), invoice **259**. `payment_status=paid` 3000/3000, gói `AIOT-TEST-TK10/AIOT-opt10` 10 vé `used=false`.
- **Endpoint API (bắt thật, kênh ổn định thay UI flaky):**
  - `GET /branches/2/reservations/{id}` → payment_status, reservation_tickets[].used_for_service
  - `GET /branches/2/customers/700006/ticket_packs` → đếm gói
  - `POST /branches/2/invoices/{invoice_id}/transactions` → **thanh toán** (payload có お預かり/method)
  - `PUT /branches/2/reservations/{id}` → cập nhật booking
- **Cancel-payment (Part A) nav:** trên invoice `支払い済`, nút **キャンセル nằm TRONG bảng 取引** (dòng giao dịch), KHÔNG phải header (header là `返金`). ⚠️ Khi mở lại invoice mà còn item chưa trả sẽ hiện "未払いの商品を統合する(1)" che view 取引 → cần đóng/skip merge trước.
- ⚠️ **CLEANUP:** hiện có **2 booking AIOTTEST-KH3 hôm 2026-07-14** (1 paid=804, 1 chưa trả) bị lẫn nhau khi mở invoice → `/testcase-cleanup` nên xoá bớt cái chưa trả để test không nhập nhằng.
- ⚠️ **Customer-autocomplete + calendar-block** trên Pro FLAKY ~20–50%/lần → mọi driver PHẢI bọc retry-loop (đã chứng minh: create booking attempt 5 mới trúng).

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
