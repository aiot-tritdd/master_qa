# /testcase-stress — Stress test (ramp tới GÃY, tìm sức chịu). GREY-BOX, RUN-GATED.

Ramp VU tăng dần tới khi hệ gãy → tìm **ĐIỂM GÃY** + **giả thuyết nút thắt**. Không pass/fail cứng — là
số **năng lực** ("chịu được ~X người"). **KHÔNG phải black-box** — track SRE riêng.

## ⛔⛔ GUARD 2 LỚP — như /testcase-load, còn NGHIÊM hơn
Stress đẩy hệ tới gãy → rủi ro cao hơn load. CHỈ `k6 run` khi **CẢ HAI**:
1. **User ra lệnh chạy stress tường minh.**
2. **Khách/sếp gật cho tạo tải tới-gãy trên dev** (hẹn giờ vắng, đồng ý riêng — bị AWS tưởng tấn công là có thật).

Chưa đủ → **CHỈ chuẩn bị, KHÔNG bắn.** Mặc định = build/dry.

## ⛔ Ranh giới: CHỈ GET · target = API (không Amplify) · chỉ đo client-side (không thấy ruột server).

## 2 cách lấy số per-stage (để đoán nút thắt)
**Cách A (khuyến nghị — sạch cho `classifyBottleneck`):** chạy `k6_load.js` ở **các mức VU rời rạc**
(50 → 100 → 150 → 200), mỗi mức 1 lần, gom từng summary thành 1 phần tử `stages[]`:
```
for VU in 50 100 150 200; do
  k6 run -e BASE_URL=... -e ENDPOINTS=... -e VUS=$VU -e DURATION=1m -e KIND=api \
         -e SUMMARY=<folder>/stage_$VU.json .claude/skills-scripts/testcase-evidence/k6_load.js
done
```
Rồi mỗi `stage_$VU.json` → `parseK6Summary` → `{vu:$VU, p95, errorRate, throughput}`.

**Cách B (nhanh, ramp 1 lần, tự dừng ở gãy):**
```
k6 run -e BASE_URL=... -e ENDPOINTS=... -e PEAK=200 -e KIND=api \
       -e SUMMARY=<folder>/stress.summary.json .claude/skills-scripts/testcase-evidence/k6_stress.js
```
`abortOnFail` tự dừng khi p95 > 3× ngưỡng / error > 10% (không đánh sập thật).

## Chấm + report (`load_lib`)
1. `stages[]` (cách A) hoặc summary (cách B) → `knee(stages,{kind:'api'})` = mức VU đầu tiên vượt ngưỡng.
2. `classifyBottleneck(stages)` → **GIẢ THUYẾT** (cpu/pool/worker/db-lock) từ HÌNH đường cong.
   ⚠️ Đây KHÔNG phải kết luận — muốn chắc phải nhìn RDS DatabaseConnections / EC2 CPU (cần AWS khách).
3. Viết `<folder>/load.results.json` `mode:"stress"` + `stages` + `knee` + `bottleneck` → factcheck → `build_load_report.py`.
4. Báo cáo: "chịu được tới ~X VU, gãy ở Y, NGHI do Z (client-side, chưa xác nhận metrics server)".

## Before final (checklist)
- [ ] Guard 2 lớp đủ chưa? Chưa → **KHÔNG bắn**.
- [ ] Endpoint toàn **GET** · bắn **API** không phải Amplify?
- [ ] "Nút thắt" báo là **GIẢ THUYẾT** hay lỡ phán thành kết luận? **Phải là giả thuyết.**
- [ ] Report ghi rõ client-side only + DEV≠PROD + p95 placeholder?
- [ ] Bắt đầu nhỏ, ramp dần, dừng khi thấy gãy — KHÔNG cố đánh sập?
