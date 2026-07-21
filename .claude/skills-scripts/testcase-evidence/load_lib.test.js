// load_lib.test.js — khoá ORACLE load/stress (không cần bắn tải thật). node --test.
// GREY-BOX: chỉ đo phía CLIENT (k6 summary). Không thấy ruột server (không đụng AWS khách).
const test = require('node:test');
const assert = require('node:assert');
const L = require('./load_lib');

// ── parseK6Summary: bóc số từ k6 handleSummary JSON ──
test('parseK6Summary: lấy đúng errorRate / p95 / throughput', () => {
  const summary = { metrics: {
    http_req_failed: { values: { rate: 0.004 } },
    http_req_duration: { values: { 'p(95)': 640, 'p(99)': 1200, med: 210, max: 3000 } },
    http_reqs: { values: { count: 12000, rate: 133.7 } },
    vus_max: { values: { max: 200 } },
  } };
  const m = L.parseK6Summary(summary);
  assert.strictEqual(m.errorRate, 0.004);
  assert.strictEqual(m.p95, 640);
  assert.strictEqual(m.throughput, 133.7);
  assert.strictEqual(m.vusMax, 200);
});

// ── verdictLoad ──
test('verdictLoad: trong ngưỡng → PASS', () => {
  const v = L.verdictLoad({ errorRate: 0.004, p95: 640 }, { kind: 'api' });
  assert.strictEqual(v.result, 'PASS');
  assert.strictEqual(v.reasons.length, 0);
});

test('verdictLoad: error rate vượt → FAIL', () => {
  const v = L.verdictLoad({ errorRate: 0.05, p95: 300 }, { kind: 'api' });
  assert.strictEqual(v.result, 'FAIL');
  assert.ok(v.reasons.some((r) => /error/.test(r)));
});

test('verdictLoad: p95 vượt ngưỡng — api chặt hơn page', () => {
  // 1500ms: FAIL với api (ngưỡng 800), PASS với page (ngưỡng 2500)
  assert.strictEqual(L.verdictLoad({ errorRate: 0, p95: 1500 }, { kind: 'api' }).result, 'FAIL');
  assert.strictEqual(L.verdictLoad({ errorRate: 0, p95: 1500 }, { kind: 'page' }).result, 'PASS');
});

test('verdictLoad: không có số đo → 未実施', () => {
  assert.strictEqual(L.verdictLoad({}, {}).result, '未実施');
  assert.strictEqual(L.verdictLoad(null, {}).result, '未実施');
});

// ── knee: mức VU đầu tiên gãy (stress) ──
test('knee: tìm mức tải đầu tiên vượt ngưỡng', () => {
  const stages = [
    { vu: 50, p95: 300, errorRate: 0 },
    { vu: 100, p95: 620, errorRate: 0 },
    { vu: 150, p95: 1900, errorRate: 0.03 },  // gãy ở đây
    { vu: 200, p95: 4000, errorRate: 0.2 },
  ];
  const k = L.knee(stages, { kind: 'api' });
  assert.strictEqual(k.vu, 150);
  assert.ok(k.reasons.length >= 1);
});

test('knee: không gãy trong dải đã bắn → null', () => {
  const stages = [{ vu: 50, p95: 200, errorRate: 0 }, { vu: 100, p95: 400, errorRate: 0.001 }];
  assert.strictEqual(L.knee(stages, { kind: 'api' }), null);
});

// ── classifyBottleneck: đoán nút thắt từ HÌNH đường cong (hypothesis, không phải kết luận) ──
test('classify: p95 tuyến tính → nghi CPU/worker', () => {
  const stages = [{ vu: 50, p95: 100, errorRate: 0 }, { vu: 100, p95: 200, errorRate: 0 }, { vu: 150, p95: 300, errorRate: 0 }, { vu: 200, p95: 400, errorRate: 0 }];
  const c = L.classifyBottleneck(stages);
  assert.strictEqual(c.hypothesis, 'cpu');
  assert.strictEqual(c.clientSideOnly, true);
});

test('classify: p95 nhảy bậc thang → nghi cạn POOL', () => {
  const stages = [{ vu: 50, p95: 100, errorRate: 0 }, { vu: 100, p95: 110, errorRate: 0 }, { vu: 150, p95: 120, errorRate: 0 }, { vu: 200, p95: 900, errorRate: 0 }];
  assert.strictEqual(L.classifyBottleneck(stages).hypothesis, 'pool');
});

test('classify: 5xx tăng theo tải → nghi WORKER chết', () => {
  const stages = [{ vu: 50, p95: 100, errorRate: 0, server5xx: false }, { vu: 200, p95: 300, errorRate: 0.08, server5xx: true }];
  assert.strictEqual(L.classifyBottleneck(stages).hypothesis, 'worker');
});

test('classify: có timeout → nghi DB-LOCK', () => {
  const stages = [{ vu: 50, p95: 100, errorRate: 0 }, { vu: 200, p95: 500, errorRate: 0.02, timeoutRate: 0.03 }];
  assert.strictEqual(L.classifyBottleneck(stages).hypothesis, 'db-lock');
});

test('classify: <2 mức tải → inconclusive', () => {
  assert.strictEqual(L.classifyBottleneck([{ vu: 50, p95: 100 }]).hypothesis, 'inconclusive');
});

// ── Ngưỡng p95 phải ghi RÕ là PLACEHOLDER (cần SLA business) — chống tưởng là chuẩn cứng ──
test('THRESHOLDS: p95 note nói rõ cần SLA business', () => {
  assert.match(L.P95_NOTE, /business|SLA/i);
});
