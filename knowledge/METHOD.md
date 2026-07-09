---
id: method
status: approved
kind: method
spans_repos: []
source_symbols: []
source_hash: null
confidence: ⭐
verify_by: "Kỹ thuật test bất biến, không phụ thuộc hệ thống. Không lỗi thời theo release."
grown_from: "0119159:.claude-tester/knowledge/METHOD.md"
---
# METHOD — kỹ thuật test bất biến (COVERAGE, không phải ORACLE)

## ⚠️ ĐỌC DÒNG NÀY TRƯỚC — ranh giới sống còn

> **`METHOD.md` quyết định CASE NÀO PHẢI TỒN TẠI.**
> **`METHOD.md` KHÔNG BAO GIỜ quyết định `expect`.**

`expect` **chỉ** đến từ **SPEC**. Lấy `expect` từ file này = phá **Tường thép #1** (oracle không còn
độc lập với thứ đang bị test).

Khi METHOD bảo *"phải có case kiểm X"* mà **SPEC im lặng về X**:

```
        METHOD: "cancel/refund PHẢI có case kiểm dữ liệu phái sinh"
                              │
                              ▼
              Spec có định nghĩa kỳ vọng cho X không?
                    │                        │
                   CÓ                      KHÔNG
                    │                        │
                    ▼                        ▼
          expect ← SPEC              ⚠️  result = SPEC-GAP
          chạy → PASS / FAIL         KHÔNG bịa expect. Ghi cái QUAN SÁT ĐƯỢC
                                     + "không chấm được → hỏi BA/dev".
```

`SPEC-GAP` là **finding giá trị cao nhất** của QA mù code: bằng chứng rằng **spec chưa nghĩ tới**.
Bịa `expect` để lấp chỗ trống = vừa mất finding đó, vừa sập Tường thép #1.

---

## Archetype phủ (khớp `example.tcs.json`)

1. **Happy path** — luồng chính của **mỗi màn hình** bị ảnh hưởng (mỗi màn ≥ 1 case).
2. **Biến thể điều kiện / quyền** — cùng thao tác, đổi quyền/trạng thái → hành vi khác
   (`before` = trạng thái A, `after` = trạng thái B).
3. **Boundary** — giá trị ngưỡng/giới hạn **ghi trong spec**.
   ⚠️ Spec không ghi ngưỡng → **không tự bịa ngưỡng**.
4. **Regression** — chức năng liên quan **không** bị ảnh hưởng bởi thay đổi.
5. **Backend/API · toàn vẹn dữ liệu** — kiểm tầng API/DB, chống bypass. **Nhóm dễ ra bug nhất.**

## Luật vàng (rút từ bug thật — đây là COVERAGE)

- **Toàn vẹn dữ liệu sau HỦY / XÓA / REFUND.** Với mọi thao tác cancel/delete/refund, **phải có case**
  kiểm dữ liệu phái sinh được hoàn/thu hồi đúng (số dư vé, tồn kho, sổ kế toán).
  *(Gốc: bug hủy thanh toán không thu hồi vé.)*
  → Spec không nói vé phải thu hồi? **`SPEC-GAP`**, không phải FAIL.

- **Chống bypass tầng API.** Quyền ẩn nút ở UI → **phải có case** gọi thẳng API để chắc backend cũng chặn
  (không chỉ ẩn nút). Dùng `withApi()` + đọc `api.status`.
  → Kỳ vọng cụ thể (403? 401? 204?) lấy từ **SPEC**. Spec chỉ nói "phải bị chặn" mà quan sát thấy `204`
  (dữ liệu không đổi)? → dữ liệu **được bảo vệ** ⇒ chưa đủ căn cứ chấm FAIL ⇒ cân nhắc `SPEC-GAP`.

- **State-transition.** Liệt kê trạng thái (`未払い` / `支払い済` / `キャンセル済`…) và **phải có case** ở
  từng trạng thái, đặc biệt các chuyển tiếp mà spec đổi logic.

- **Permission matrix.** Quyền × trạng thái → **1 ô = 1 case** (có quyền/không × đã TT/chưa TT).

- **Negative.** Nhập sai / thiếu quyền / gọi API không hợp lệ → **phải có case**. Hệ không được
  âm thầm nuốt lỗi.

- **Quan sát 2 phía.** Case đụng vé/coupon/số dư → **phải quan sát cả Ứng dụng Pro lẫn Hệ thống Vé**,
  và đối chiếu **Hệ thống Lõi** (nguồn sự thật). Một phía không đủ làm bằng chứng.

## Kết quả & đối chiếu

| result | Khi nào | `actual` viết gì |
|---|---|---|
| `PASS` | quan sát khớp `expect` | mô tả cái **quan sát được** |
| `FAIL` | quan sát lệch `expect` | *"spec kỳ vọng X; màn hình làm Y"* + số liệu trước/sau + ảnh |
| `未実施` | **không quan sát được** (không vào được kênh) | lý do không quan sát được |
| `SPEC-GAP` | **quan sát được** nhưng spec không định nghĩa kỳ vọng | cái quan sát được + *"không chấm được → hỏi BA/dev"* |

- `actual` **bắt đầu bằng đúng từ đó** (để COUNTIF khớp), và mô tả **quan sát được** — không suy diễn.
- **FAIL không bao giờ ghi symbol / `file:line`.** Định vị bug ở code là việc của dev.
- **Feature chưa build → `FAIL`** (quan sát 404 / thiếu nút + ảnh *absence*).
  KHÔNG suy đoán *"chưa code"* — đó là code-knowledge. ⚠️ `grep` không thấy ≠ không tồn tại
  (đã sai 2 lần — xem `OPEN-QUESTIONS.md#OQ-01`).

## KPI số case

- **Min** = số luồng chính (đối tượng × chiều + luồng đặc thù) — mỗi luồng ≥ 1 happy path.
- **Max** = Min + validation/boundary + negative (retry/conflict) + biến thể theo app/màn hình.
  Dừng **trước khi** case bắt đầu trùng cơ chế (không vét cạn ma trận).
- **KPI mục tiêu ≈ 80% Max** (nhỉnh hơn trung bình). Vd Max 10 → KPI 8; Min 14 / Max 25 → KPI ~20.
- Thiếu KPI → bổ sung nhóm **validation/negative** trước (nhóm hay thiếu nhất).
  **Không** đẻ thêm case trùng happy path để đủ số.
