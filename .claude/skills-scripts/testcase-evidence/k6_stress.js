// k6_stress.js — STRESS test: ramp VU tăng dần TỚI KHI GÃY, tự dừng (không cần đánh sập thật). GREY-BOX.
//
// ⛔ KHÔNG tự chạy. Guard 2 lớp như k6_load.js. CHỈ GET (read-only). Target = API, KHÔNG bắn Amplify.
//
// `abortOnFail`: k6 tự DỪNG khi p95 vượt 3× ngưỡng hoặc error > 10% → tìm ĐIỂM GÃY an toàn.
// ⚠️ Để lấy stages[] cho classifyBottleneck (đoán nút thắt), CÁCH TỐT HƠN là chạy k6_load.js ở nhiều mức
// VU rời rạc (50/100/150/200) rồi gom từng summary thành 1 stage — xem testcase-stress.md. Script này là
// bản ramp-1-lần tiện dụng; số per-stage đọc từ time-series (-e SUMMARY + --out json nếu cần chi tiết).
//
// Chạy (khi đã được phép):
//   k6 run -e BASE_URL=... -e ENDPOINTS=/api/a,/api/b -e KIND=api -e SUMMARY=stress.summary.json k6_stress.js
import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE_URL || 'https://reservation-dev.threease.com';
const ENDPOINTS = (__ENV.ENDPOINTS || '/2').split(',').map((s) => s.trim()).filter(Boolean);
const KIND = __ENV.KIND || 'api';
const P95 = parseInt(__ENV.P95 || (KIND === 'page' ? '2500' : '800'), 10);
const STEP = __ENV.STEP_DURATION || '30s';
const PEAK = parseInt(__ENV.PEAK || '200', 10);

export const options = {
  stages: [
    { duration: STEP, target: Math.round(PEAK * 0.05) },
    { duration: STEP, target: Math.round(PEAK * 0.25) },
    { duration: STEP, target: Math.round(PEAK * 0.50) },
    { duration: STEP, target: Math.round(PEAK * 0.75) },
    { duration: STEP, target: PEAK },
  ],
  thresholds: {
    http_req_duration: [{ threshold: `p(95)<${P95 * 3}`, abortOnFail: true, delayAbortEval: '10s' }],
    http_req_failed: [{ threshold: 'rate<0.10', abortOnFail: true, delayAbortEval: '10s' }],
  },
};

export default function () {
  for (const p of ENDPOINTS) {
    const res = http.get(BASE + p); // CHỈ GET
    check(res, { 'status < 500': (r) => r.status < 500 });
  }
}

export function handleSummary(data) {
  const out = __ENV.SUMMARY || 'stress.summary.json';
  return { [out]: JSON.stringify(data, null, 2), stdout: '\n(summary ghi ra ' + out + ')\n' };
}
