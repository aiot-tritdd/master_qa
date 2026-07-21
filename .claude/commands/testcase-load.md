# /testcase-load — Load test (giữ tải mức mục tiêu). GREY-BOX, RUN-GATED.

Đo hệ chịu được **N người đồng thời** ở mức mục tiêu không. **KHÔNG phải black-box** — đây là track
**Performance Engineering / SRE** riêng.

## ⛔⛔ GUARD 2 LỚP — ĐỌC TRƯỚC KHI CHẠY
Bắn tải = **đổ tải THẬT lên hạ tầng của KHÁCH** (tốn tiền AWS họ, có thể làm chậm môi trường người khác,
thậm chí bị AWS tưởng là tấn công). CHỈ được `k6 run` khi **CẢ HAI** đúng:
1. **User ra lệnh chạy tường minh** (không phải "chuẩn bị"/"build" — phải là "chạy load test đi").
2. **Khách/sếp đã gật cho tạo tải lên dev** (hẹn giờ vắng, đồng ý riêng cho load test — KHÁC "chạy test thường").

Chưa đủ 2 điều → **CHỈ chuẩn bị script + endpoint, KHÔNG bắn.** Mặc định của lệnh này = build/dry, không run.

## ⛔ Ranh giới kỹ thuật
- **CHỈ GET (read-only).** Không POST/PUT/DELETE (đẻ booking/data rác trên dev khách).
- **Target = API endpoint** (path EC2→RDS). **KHÔNG bắn trang Amplify** (CDN, scale vô tư → số vô nghĩa).
- **Chỉ đo được CLIENT-SIDE.** Không thấy ruột server (không đụng AWS khách) → phần "vì sao" chỉ là GIẢ THUYẾT.

## Chuẩn bị (làm được NGAY, không cần phép)
1. **Sniff endpoint thật:** mở widget `/2` (hoặc màn cần đo), ghi lại các **API GET** nó gọi (5 API ra
   `AIoT院1`). Đó là `ENDPOINTS`. Xác nhận vào ĐÚNG màn bằng **API 200 + data thật**.
2. **Chốt số mục tiêu:** `VUS` (đỉnh concurrency — cần SLA business; chưa có thì mặc định 200),
   `KIND=api`, `P95` (mặc định 800ms api / 2500ms page — **placeholder từ CWV**).

## Chạy (CHỈ khi guard 2 lớp đã đủ)
```
k6 run -e BASE_URL=https://reservation-dev.threease.com \
       -e ENDPOINTS=/api/x,/api/y -e VUS=200 -e DURATION=3m -e KIND=api \
       -e SUMMARY=<folder>/load.summary.json \
       .claude/skills-scripts/testcase-evidence/k6_load.js
```
Bắt đầu **NHỎ** (VUS=10) thử thông đường rồi mới lên mục tiêu. Thấy p95 vọt/lỗi tăng bất thường → **DỪNG**.

## Chấm + report (`load_lib` + `build_load_report.py`)
1. `parseK6Summary(summary)` → `{errorRate, p95, p99, throughput, vusMax}`.
2. `verdictLoad(metrics, {kind:'api'})` → PASS/FAIL/`未実施`.
3. Viết `<folder>/load.results.json`:
   `{meta:{case,date,tester,mode:"load",target,endpoints:[...]}, result, metrics, thresholds, caveats:[...]}`.
4. `python3 .../factcheck_report.py <folder>/load.results.json` → `python3 .../build_load_report.py <folder>/load.results.json <folder>/<Tên>.load.xlsx`.
5. Sổ bug (chỉ khi FAIL **và** user duyệt): `bug_type:"Performance"`, kèm cảnh báo client-side/DEV≠PROD.

## Before final (checklist)
- [ ] Guard 2 lớp đã đủ chưa? Nếu chưa → **KHÔNG bắn**, chỉ chuẩn bị.
- [ ] Endpoint toàn **GET** chưa? Có lỡ để endpoint ghi không? **Phải KHÔNG.**
- [ ] Có bắn vào **API** (không phải trang Amplify) không?
- [ ] Report có ghi rõ **client-side only + DEV≠PROD + p95 là placeholder** chưa?
- [ ] "Vì sao gãy" có bị phán như **kết luận** không? **Phải là GIẢ THUYẾT** (chưa nhìn ruột server).
