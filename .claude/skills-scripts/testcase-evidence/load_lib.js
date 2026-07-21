// load_lib.js — oracle CƠ KHÍ cho track Load + Stress. GREY-BOX (KHÔNG black-box, KHÔNG code-blind).
//
// ⚠️ TRACK NÀY KHÁC 6 track kia: nó KHÔNG thuộc "con đen". Load/stress là chuyện Performance Engineering/
// SRE. Ở đây ta CHỈ đo được phía CLIENT (k6 summary: latency/error/throughput) — KHÔNG thấy ruột server
// (CPU/RAM/DB pool) vì KHÔNG đụng AWS của khách. Vì vậy phần "vì sao gãy" chỉ là **GIẢ THUYẾT** suy từ
// HÌNH đường cong, không phải kết luận.
//
// ⛔ GUARD 2 LỚP (ghi ở command doc): chỉ CHẠY khi (a) user ra lệnh tường minh VÀ (b) khách/sếp gật cho
// tạo tải lên dev. Lib này chỉ CHẤM số đã có — bản thân nó không bắn gì.
//
// KIẾN TRÚC (giống các *_lib khác): hàm THUẦN nhận số đo → verdict. Unit-test được không cần bắn tải.

// ── Ngưỡng. errorRate ~ phổ quát. p95 = PLACEHOLDER lấy tạm từ CWV, PHẢI thay bằng SLA business. ──
const THRESHOLDS = {
  errorRate: 0.01,          // < 1% — mức chấp nhận phổ biến
  p95: { api: 800, page: 2500 }, // ms — api mượn ngưỡng TTFB-good, page mượn LCP-good
};
const P95_NOTE = 'Ngưỡng p95 là PLACEHOLDER mượn từ Core Web Vitals (api≈TTFB 800ms, page≈LCP 2500ms). '
  + 'Load/stress THẬT cần SLA do business đặt (đỉnh concurrency + p95 mục tiêu). Chưa có số đó → coi kết quả là tham khảo.';

// ── Bóc số từ k6 handleSummary JSON ──
function _v(metrics, name, key) {
  const m = metrics && metrics[name];
  return m && m.values ? m.values[key] : undefined;
}
function parseK6Summary(summary) {
  const m = (summary && summary.metrics) || {};
  return {
    errorRate: _v(m, 'http_req_failed', 'rate'),
    p95: _v(m, 'http_req_duration', 'p(95)'),
    p99: _v(m, 'http_req_duration', 'p(99)'),
    med: _v(m, 'http_req_duration', 'med'),
    max: _v(m, 'http_req_duration', 'max'),
    throughput: _v(m, 'http_reqs', 'rate'),
    count: _v(m, 'http_reqs', 'count'),
    vusMax: _v(m, 'vus_max', 'max') != null ? _v(m, 'vus_max', 'max') : _v(m, 'vus_max', 'value'),
  };
}

function _th(opts) {
  const kind = opts && opts.kind === 'page' ? 'page' : 'api';
  return {
    kind,
    p95: opts && opts.p95 != null ? opts.p95 : THRESHOLDS.p95[kind],
    errorRate: opts && opts.errorRate != null ? opts.errorRate : THRESHOLDS.errorRate,
  };
}

// ── verdict LOAD (giữ tải ở mức mục tiêu) ──
function verdictLoad(metrics, opts = {}) {
  if (!metrics || (metrics.errorRate == null && metrics.p95 == null)) {
    return { result: '未実施', reasons: ['không có số đo (chưa bắn hoặc summary rỗng)'] };
  }
  const t = _th(opts);
  const reasons = [];
  if (metrics.errorRate != null && metrics.errorRate > t.errorRate) {
    reasons.push(`error rate ${(metrics.errorRate * 100).toFixed(2)}% > ${t.errorRate * 100}%`);
  }
  if (metrics.p95 != null && metrics.p95 > t.p95) {
    reasons.push(`p95 ${Math.round(metrics.p95)}ms > ${t.p95}ms (${t.kind})`);
  }
  return { result: reasons.length ? 'FAIL' : 'PASS', reasons, thresholds: t };
}

// ── knee: mức VU ĐẦU TIÊN vượt ngưỡng (stress = ramp tới gãy) ──
// stages = [{vu, p95, errorRate, throughput, ...}] theo thứ tự tải tăng dần.
function knee(stages, opts = {}) {
  const t = _th(opts);
  for (const st of stages || []) {
    const why = [];
    if (st.p95 != null && st.p95 > t.p95) why.push(`p95 ${Math.round(st.p95)}ms > ${t.p95}ms`);
    if (st.errorRate != null && st.errorRate > t.errorRate) why.push(`error ${(st.errorRate * 100).toFixed(2)}% > ${t.errorRate * 100}%`);
    if (why.length) return { vu: st.vu, reasons: why };
  }
  return null; // không gãy trong dải đã bắn
}

// ── classifyBottleneck: GIẢ THUYẾT nút thắt từ HÌNH đường cong (client-side, không nhìn ruột server) ──
function _deltas(vals) { const d = []; for (let i = 1; i < vals.length; i++) d.push(vals[i] - vals[i - 1]); return d; }
function _median(vals) { const v = vals.slice().sort((a, b) => a - b); return v.length ? v[Math.floor(v.length / 2)] : 0; }
function isStepwise(vals) {
  const d = _deltas(vals).map((x) => Math.max(0, x));
  if (d.length < 2) return false;
  const sorted = d.slice().sort((a, b) => a - b);
  const mx = sorted[sorted.length - 1];
  const rest = sorted.slice(0, -1); // bỏ ĐÚNG 1 phần tử lớn nhất (không lọc hết bản trùng → tránh rest rỗng khi mọi delta bằng nhau = tuyến tính)
  return mx > 0 && mx > 3 * Math.max(_median(rest), 1);
}
function isLinear(vals) {
  const d = _deltas(vals);
  if (d.length < 2 || !d.every((x) => x > 0)) return false; // phải TĂNG ĐỀU
  return Math.max(...d) <= 2.2 * Math.min(...d);            // các bước xấp xỉ nhau
}
function classifyBottleneck(stages) {
  const s = (stages || []).filter((x) => x && x.vu != null);
  if (s.length < 2) return { hypothesis: 'inconclusive', reason: 'cần ≥2 mức tải mới đọc được hình', clientSideOnly: true };
  if (s.some((x) => x.timeoutRate > 0)) {
    return { hypothesis: 'db-lock', confidence: 'thấp', clientSideOnly: true,
      reason: 'có request timeout → NGHI đang chờ khoá DB (cần nhìn RDS mới chắc)' };
  }
  const err0 = s[0].errorRate || 0, errN = s[s.length - 1].errorRate || 0;
  if (s.some((x) => x.server5xx) && errN > err0 + 0.02) {
    return { hypothesis: 'worker', confidence: 'thấp', clientSideOnly: true,
      reason: 'lỗi 5xx tăng theo tải → NGHI worker chết/quá tải (cần nhìn EC2 mới chắc)' };
  }
  const p95s = s.map((x) => x.p95).filter((v) => v != null);
  if (isStepwise(p95s)) {
    return { hypothesis: 'pool', confidence: 'thấp', clientSideOnly: true,
      reason: 'p95 nhảy BẬC THANG ở 1 mức tải → NGHI cạn connection pool, request xếp hàng (cần nhìn RDS DatabaseConnections mới chắc)' };
  }
  if (isLinear(p95s)) {
    return { hypothesis: 'cpu', confidence: 'thấp', clientSideOnly: true,
      reason: 'p95 tăng ~TUYẾN TÍNH theo tải → NGHI bão hoà CPU/worker (cần nhìn EC2 CPU mới chắc)' };
  }
  return { hypothesis: 'inconclusive', clientSideOnly: true, reason: 'hình đường cong không rõ ràng' };
}

function finding({ where, url, severity, observed, fix, hypothesis }) {
  return {
    family: 'load-capacity', where: where || '', url: url || '',
    severity: severity || 'Medium', observed: observed || '', fix: fix || '', hypothesis: hypothesis || '',
  };
}

module.exports = {
  THRESHOLDS, P95_NOTE,
  parseK6Summary, verdictLoad, knee, classifyBottleneck, isStepwise, isLinear, finding,
};
