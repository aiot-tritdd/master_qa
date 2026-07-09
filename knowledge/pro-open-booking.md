---
id: pro-open-booking
status: approved
kind: flow
spans_repos: [pro]
source_symbols: ["pro: components/features/reservations/reservation_form/ReservationForm.vue"]
source_hash: 0d5d5b2cb5f2af2c
ui_confirmed_at: 2026-07-09
confidence: 🟢
verify_by: "Drive lại bằng pw_lib.getPage('pro') (locale ja-JP). Nếu nhãn/selector đổi → sửa + đổi ui_confirmed_at. ⚠️ Đổi locale/viewport trong pw_lib ⇒ doc này stale NGAY, dù source_hash vẫn khớp."
grown_from: "UI-confirm 2026-07-07 (locale EN, đã SAI) → re-confirm 2026-07-09 (locale ja-JP)"
---
# Flow: Mở booking detail trên Pro (HOW — navigation only)

> ✅ **Re-UI-confirmed 2026-07-09** dưới `locale: 'ja-JP'` — drive thật, mọi selector dưới đây đã chạy.
>
> ⚠️ **Lịch sử:** bản 2026-07-07 được confirm khi `pw_lib` **thiếu `locale`** → app chạy tiếng Anh →
> doc ghi `Remove` / `INVOICE` / toạ độ `mouse.click(877,68)`. Tất cả đều **SAI** dưới ja-JP.
> `source_hash` không hề đổi (code sản phẩm y nguyên) ⇒ **`stale_check.py` mù với loại stale này**.
> Xem `docs/KNOWLEDGE-STRATEGY.md` §4b.
>
> Firewall: chỉ ghi cách drive + nơi quan sát. **KHÔNG** ghi kết quả kỳ vọng.

**Mục tiêu:** mở ReservationForm của 1 booking (để quan sát dòng vé / thao tác xoá vé / mở hoá đơn).

## Các bước UI (`getPage('pro')` — locale `ja-JP` mặc định)

1. **Login:** `pw_lib` tự điền `data-cy=institute_code/therapist_code/password` + `[data-cy=loginButton]`.
   Có `.state.pro.json` thì bỏ qua form.
2. `goto(BASE + '/reservations')` rồi `waitForTimeout(7000)` (calendar Nuxt render chậm).
   *(`/en/reservations` cũng chạy — app tự redirect về `/reservations` — nhưng đừng dùng, dễ gây hiểu nhầm.)*
3. **Điều hướng ngày — verification-driven, KHÔNG toạ độ cứng, KHÔNG click mù:**
   ```js
   const nextDay = page.locator('.mdi-chevron-right').first();  // ✅ mũi tên NGÀY (y≈59)
   for (let i = 0; i < 10; i++) {
     if (await page.getByText(/<tên khách>/).first().isVisible().catch(() => false)) break;
     await nextDay.click(); await page.waitForTimeout(2500);
   }
   ```
   ⚠️ Trang có **7 phần tử `.mdi-chevron-right`**: 1 cái ở thanh ngày (y≈59) + **6 cái ở header cột unit**
   (y≈117). `.first()` là cái đúng. **Đừng** dùng `mouse.click(x,y)` — toạ độ phụ thuộc độ dài nhãn ngày,
   đổi theo locale (bản EN từng đo 877, ja-JP thật là **837**).
   Nhãn ngày đọc được bằng `getByText(/2026\/\d{2}\/\d{2}/)` → dạng `2026/07/09 (木)`.
4. `page.getByText(/<tên khách>/).first().click({force:true})` → **ReservationForm** mở ở panel phải.
   URL **không đổi** (vẫn `/reservations`) — đừng dùng URL để xác nhận form đã mở.

## Nhãn & selector trong ReservationForm (đo 2026-07-09, ja-JP)

| Việc | Selector đã xác nhận |
|---|---|
| Mở **hoá đơn** | `button.v-btn--outlined:has-text("請求書")` × 1 — *(bản EN cũ ghi `INVOICE`)* |
| **Lưu** | `getByText('保存する', {exact:true})` × 1 |
| **Xoá booking** | icon thùng rác `.mdi-delete-outline` × 1 (góc trên trái panel) |
| **Xoá dòng vé/coupon** | `getByText('削除する', {exact:true})` — *(bản EN cũ ghi `Remove`)* |
| Dòng vé | text chứa `AIOT-TEST-TK…` + `チケット` |
| Dòng coupon | text chứa `クーポン` (vd `Yoga coupon`, `8000SC`) |

**⚠️ `削除する` LUÔN có trong DOM (đếm được **×2**: 1 cho dòng vé + 1 cho dòng coupon), cả trước lẫn sau
khi hover.** Hover chỉ làm nó **nổi lên**, không phải tạo ra nó. → Muốn đếm/kiểm sự tồn tại thì không cần
hover; muốn **click** thì hover dòng tương ứng trước rồi `.click({force:true})` đúng dòng cần xoá.

**⚠️ `getByText('削除', {exact:true})` trả về `0`** — nhãn thật là `削除する`. Dùng `exact:true` sai chuỗi
là cách âm thầm tạo ra một FAIL giả.

## Nơi quan sát (observe)

- Trạng thái booking / thanh toán: chip ở đầu panel (vd `本予約`, `一部支払済み (現金)`).
- Dòng item: tên · số phút · tiền (vd `taxexe1 / 20分 / 2000円`), `保険分合計`, `割引額`.
- Chi tiết hơn → `knowledge/observation-channels.md`.

## Dữ liệu test trên dev (cập nhật 2026-07-09)

- ✅ **Booking `Jenny`** — `2026/07/09 14:20`, **branch 3**, `id=774`, `一部支払済み`, **có dòng vé
  `AIOT-TEST-TK1` + coupon `Yoga coupon`**. Dùng làm booking mẫu để drive.
- ❌ `AIOTTEST-KH3` booking `07/13`: **không còn tồn tại** (đã bị dọn). Đừng tin ghi chú cũ.
- ⚠️ **Branch của phiên `TESTSEED001` hiện là `3`** — đổi theo phiên, luôn xác nhận lại
  (`GET /branches/{b}/reservations?...` trả 404 nếu sai branch).
