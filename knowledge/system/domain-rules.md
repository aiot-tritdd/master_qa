---
id: system-domain-rules
status: draft
kind: system-domain
spans_repos: [backend, pro, ticket]
source_symbols: []
source_hash: null
confidence: 🟢
verify_by: "Khái niệm nghiệp vụ ổn định, không đổi theo release UI. Nghi ngờ → đối chiếu spec gốc trong wtf-is-this/<TestCase>/specs.md."
grown_from: ".claude-tester/.claude-knowledge/DOMAIN.md#khái-niệm-cốt-lõi"
---
# Domain rules — vì sao một hành vi LÀ bug (WHAT)

> ⛔ **QA-runtime CẤM đọc file này.** Đây là **WHAT** — nó nói *"kết quả nào là đúng"*, tức là nó có thể
> **thay SPEC làm oracle** → tautology. Nó tồn tại để **con người** hiểu hệ thống và để build-time soạn
> doc HOW nhanh hơn.
>
> Tên nghiệp vụ ↔ tên kỹ thuật: `knowledge/GLOSSARY.md` (file đó QA **được** đọc, vì nó chỉ đặt tên).

## Khái niệm cốt lõi

**締め / Kết sổ** — chốt sổ kế toán theo kỳ. Sau khi kết sổ, **số liệu quá khứ không được biến động**.
→ Xóa/sửa đặt lịch **đã thanh toán** sau kết sổ = mất tin cậy số dư vé + biến động tiền ngoài kiểm soát.
Đây là lý do gốc của No.10.5 (kiểm soát quyền sửa/xóa sau thanh toán).

**回数券 / Gói vé (ticket pack)** — gói N buổi (vd 100 slip). Khách mua qua đặt lịch.
Khi booking chuyển `支払い済` thì khách **mới** được cấp vé (0 → N slip).
Hủy thanh toán → **phải thu hồi vé** (xử lý như `返金`/refund).
*(No.10.1 đã thống nhất; bug TC-09 = chưa làm.)*

**SC / Store credit (Coupon)** — khác vé về bản chất: tiêu theo **FIFO trên toàn tài khoản khách**,
không gắn với một coupon cụ thể. Vé thì tiêu theo từng gói/slip riêng.

## State machine

- **Đặt lịch:** `確認待ち → 本予約 → 受付済 → 進行中 → 完了` · nhánh `キャンセル済`
- **Thanh toán:** `未払い → 一部支払済 → 支払い済`

## Vì sao quan trọng khi test

Đụng tới **tiền + vé + sổ** → mọi thao tác hủy/xóa phải kiểm **cả 3 phía**:
Ứng dụng Pro (đặt lịch) · hóa đơn (giao dịch) · Hệ thống Vé (số dư vé).
Chỉ nhìn UI Ứng dụng Pro là **thiếu** — nhất là với khoảng trống đồng bộ
(`system/customer-sync.md` § known gap), số dư bên Hệ thống Vé có thể không đáng tin.

## ⚠️ Ranh giới với oracle

Các luật trên **KHÔNG** được dùng làm `expect`. Chúng chỉ nói *"vì sao chuyện này quan trọng"*.
Nếu SPEC **im lặng** về việc "hủy thanh toán phải thu hồi vé" thì con QA **không được bịa** kỳ vọng đó
từ file này → kết quả phải là **`SPEC-GAP`**, không phải `FAIL`.
→ Xem `knowledge/METHOD.md` (coverage ≠ oracle).
