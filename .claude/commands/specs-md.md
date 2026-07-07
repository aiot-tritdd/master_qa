# /specs-md — Convert specs.html → specs.md (format chuẩn, đẹp, rõ)

Đọc `specs.html` (tài liệu xác nhận nghiệp vụ) trong 1 folder → soạn `specs.md` **có cấu trúc, sạch,
business-level** để các skill sau (`/testcase-write`, `qa-brain`) hiểu spec tốt hơn + test đẹp hơn.
KHÔNG chạy test. Đọc HTML thẳng (model đọc được — KHÔNG cần helper .py, KHÔNG OCR).

## Cách dùng
```
/specs-md <folder>            # vd: /specs-md wtf-is-this/TestCase_No.10.1~3
```
Nếu chỉ có `specs.png`/`.pdf` → đọc ảnh (tốn hơn); ưu tiên có `specs.html`.

## Nguyên tắc (bức tường: đây là SPEC = oracle)
- **Chỉ mô tả nghiệp vụ** (ý định/yêu cầu), KHÔNG suy diễn cơ chế code.
- **Giữ nguyên văn** tên màn hình/hàm JP/EN (`請求書`, `キャンセル`, Cancel payment…) và **mọi thông báo
  hệ thống** (vd「使用済みチケットが含まれているため、支払キャンセル・削除はできません。」) — không dịch, không rút gọn.
- Đánh dấu **ĐÃ CHỐT** những phương án khách đã quyết; ghi rõ *(cần làm rõ)* chỗ còn mơ hồ.
- Bảng cho **state machine / so sánh hiện trạng↔mới / ma trận hành vi**.

## Format bắt buộc (khớp mẫu `TestCase_No.10.1~3/specs.md`)
```markdown
# No.XX — <Tên tính năng> (<hệ liên quan>)

> <1 dòng tóm tắt>
> **Nguồn spec**: `specs.html` trong folder này (<ghi chú chốt/nháp>)
> Cập nhật lần cuối: **YYYY/MM/DD**

---

## 1. Bối cảnh & Vấn đề
<hiện trạng + vấn đề, gạch đầu dòng theo từng thao tác/luồng>

## 2. Yêu cầu
### ① PHẦN A — <tên>
- **ĐÃ CHỐT**: <phương án>. Thông báo:「<nguyên văn JP>」
### ② PHẦN B — ...   (bảng hành vi hiện tại nếu spec có)
### ③ PHẦN C — ...   (bảng state machine nếu có trạng thái mới)
### ④ PHẦN D — ...

## 3. Ảnh hưởng hệ thống
**Frontend (threease_pro)** / **Frontend (threease_ticket)** / **Backend**
- <mỗi hệ: màn/luồng nào đổi — mức nghiệp vụ, không tên symbol>

## 4. Cập nhật Specs (Change requests & Bugs)
> Mỗi mục có **ngày**. Trạng thái: `🔴 chưa xử lý → 🟡 đang fix → ✅ đã verify`.
| ID | Ngày | Loại | Nội dung | Ảnh hưởng | Trạng thái |
|----|------|------|----------|-----------|-----------|
<!-- Mẫu: | CHANGE-0x / BUG-0x | YYYY/MM/DD | 🔧/🐞 | ... | ... | 🔴 | -->
```

## Quy trình
1. Đọc `<folder>/specs.html`. Rút: bối cảnh, từng PHẦN (A/B/C/D…), phương án chốt, thông báo JP,
   bảng hiện trạng/state, ảnh hưởng theo hệ.
2. Soạn `<folder>/specs.md` đúng format trên. Điền `Cập nhật lần cuối = hôm nay`.
3. Để sẵn `## 4` (bảng changelog rỗng) cho `/testcase-upspecschange`.
4. **Báo cáo**: liệt kê các PHẦN + số thông báo JP giữ nguyên + đường dẫn `specs.md`.

## Vì sao skill này quan trọng
`specs.md` sạch = **oracle tốt hơn** → `/testcase-write` sinh case sát nghiệp vụ hơn, `qa-brain` test
đúng hơn. Đây là bước đầu của pipeline: **specs-md → write → run → cleanup → upspecschange → retest**.
