// k6_load.js — LOAD test: giữ tải ở mức VU mục tiêu 1 khoảng. GREY-BOX, chỉ đo client-side.
//
// ⛔ KHÔNG tự chạy. Chỉ bắn khi (a) user ra lệnh VÀ (b) khách/sếp gật cho tạo tải lên dev.
// ⛔ CHỈ GET (read-only). TUYỆT ĐỐI không thêm POST/PUT/DELETE (đẻ booking/data rác trên dev khách).
// Target = API endpoint (path EC2→RDS), KHÔNG bắn trang Amplify (CDN scale vô tư, vô nghĩa).
//
// Chạy (khi đã được phép):
//   k6 run -e BASE_URL=https://reservation-dev.threease.com -e ENDPOINTS=/api/a,/api/b \
//          -e VUS=200 -e DURATION=3m -e KIND=api -e SUMMARY=load.summary.json k6_load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'https://reservation-dev.threease.com';
// Điền path THẬT của các API mà widget /2 gọi (sniff network lúc chạy). Mặc định /2 chỉ để inspect.
const ENDPOINTS = (__ENV.ENDPOINTS || '/2').split(',').map((s) => s.trim()).filter(Boolean);
const VUS = parseInt(__ENV.VUS || '200', 10);
const DURATION = __ENV.DURATION || '3m';
const KIND = __ENV.KIND || 'api';
const P95 = parseInt(__ENV.P95 || (KIND === 'page' ? '2500' : '800'), 10);

export const options = {
  vus: VUS,
  duration: DURATION,
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: [`p(95)<${P95}`],
  },
};

export default function () {
  for (const p of ENDPOINTS) {
    const res = http.get(BASE + p); // CHỈ GET
    check(res, { 'status < 500': (r) => r.status < 500 });
  }
  sleep(1);
}

export function handleSummary(data) {
  const out = __ENV.SUMMARY || 'load.summary.json';
  return { [out]: JSON.stringify(data, null, 2), stdout: '\n(summary ghi ra ' + out + ')\n' };
}
