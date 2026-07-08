# Demo — QA-Server (black-box, skill-based)

> Kiến trúc hiện tại = **skill Claude Code** (`qa-brain` + `testcase-*`), KHÔNG phải dịch vụ Python.
> Chuẩn bị: chỉ cần **truy cập dev** (`wtf-is-this/account.txt`) + Playwright (`pw_lib`). Không docker/uvicorn.

## Cách chạy 1 test thật
Bỏ spec vào `wtf-is-this/TestCase-XX/` (nếu là HTML → `/specs-md` sinh `specs.md`) → nạp skill
`qa-brain` trỏ folder → skill: đọc SPEC (oracle, mù code) → viết case → drive app dev → quan sát
live → chấm PASS/FAIL + **evidence 2 ảnh/case (before+after, PNG rõ)** → xuất `.xlsx` 3 sheet.

## Punchline A — "Black-box khớp đúng scope dev" (TestCase-11, 2026-07-08)
- Test Coupon Report (`mockup_coupon_report.md`) trên ticket-dev, **mù code + mù cả list dev khai**.
- Kết quả **9 PASS / 8 FAIL** → đối chiếu list dev khai "đã làm / chưa làm": **khớp 100%, không sai 1 dòng**
  (đến chi tiết "販売 đã làm 1 phần: Report ✅ / 過去のCSV ❌" cũng bắt đúng).
- → QA black-box **tự tới đúng thực tế triển khai** chỉ bằng quan sát app (route 404 / thiếu tab / thiếu nút).

## Punchline B — "Code-trace SAI, black-box ĐÚNG" (guard vé đã dùng)
- Ban đầu tôi **code-trace** qua GitNexus → kết luận "guard vé-đã-dùng CHƯA build → FAIL". **SAI**
  (Rails index yếu, graph không thấy).
- **Black-box** (drive app thật): cancel payment / cancel booking / delete → **CHẶN đúng** với nguyên văn
  `使用済みチケットが含まれているため、支払キャンセル・削除はできません。` → guard **ĐÃ build + chạy đúng**.
- Còn bắt **bug thật**: luồng **Remove** lộ **raw i18n key** `reservations.used_ticket_cannot_remove`
  thay vì câu JP → chỉ black-box mới thấy.
- → Bằng chứng sống cho nguyên tắc sếp: **QA phải black-box, oracle = SPEC + quan sát live, KHÔNG tin code.**

## Deliverable mỗi task
`wtf-is-this/<TestCase>/<Tên>.xlsx` — 3 sheet (Cover + SUMMARY · Test Cases block-dọc + Evidence
Before/After · Checklist + cột Nguồn/発生元) + `shots/*.png` (**2 ảnh/case: 1 before + 1 after**, PNG rõ).
Gửi PM đọc là khớp scope dev.
