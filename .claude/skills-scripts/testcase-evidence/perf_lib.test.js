// Chạy: node --test perf_lib.test.js
// Khoá ORACLE track Performance. Live-verify khoá phần "probe có đo thật" (việc khác).
const { test } = require('node:test');
const assert = require('node:assert');
const { THRESHOLDS, FIELD_ONLY, rate, median, aggregate, verdict, findings } = require('./perf_lib');

test('THRESHOLDS đúng số Google công bố — KHÔNG được tự chế/nới', () => {
  assert.equal(THRESHOLDS.LCP.good, 2500); assert.equal(THRESHOLDS.LCP.poor, 4000);
  assert.equal(THRESHOLDS.CLS.good, 0.1);  assert.equal(THRESHOLDS.CLS.poor, 0.25);
  assert.equal(THRESHOLDS.TBT.good, 200);  assert.equal(THRESHOLDS.FCP.good, 1800);
  assert.equal(THRESHOLDS.TTFB.good, 800);
  // mỗi ngưỡng phải có nguồn tra lại được — nếu không thì là số tự chế
  for (const [m, t] of Object.entries(THRESHOLDS)) {
    assert.match(t.src, /^https:\/\/web\.dev\//, `${m} thiếu nguồn công bố`);
    assert.ok(t.good < t.poor, `${m}: good phải chặt hơn poor`);
  }
});

test('INP KHÔNG được có trong THRESHOLDS — lab không đo được, thêm vào = chuẩn bị bịa số', () => {
  assert.equal(THRESHOLDS.INP, undefined, 'INP là FIELD-only (cần tương tác người thật); lab dùng TBT proxy');
  assert.ok(FIELD_ONLY.includes('INP'));
  assert.ok(THRESHOLDS.TBT, 'phải có TBT làm proxy lab cho INP');
});

test('rate: đúng 3 bậc good / needs-improvement / poor theo mốc Google', () => {
  assert.equal(rate('LCP', 2400), 'good');
  assert.equal(rate('LCP', 2500), 'good', 'đúng mốc = vẫn good (≤)');
  assert.equal(rate('LCP', 2501), 'needs-improvement');
  assert.equal(rate('LCP', 4000), 'needs-improvement');
  assert.equal(rate('LCP', 4001), 'poor');
  assert.equal(rate('CLS', 0.05), 'good');
  assert.equal(rate('CLS', 0.3), 'poor');
  // không đo được -> unknown, KHÔNG được thành 'good'
  assert.equal(rate('LCP', null), 'unknown');
  assert.equal(rate('LCP', NaN), 'unknown');
  assert.equal(rate('KHONGCO', 1), 'unknown');
});

test('median: dùng TRUNG VỊ để 1 lần chạy dính lag không kéo lệch', () => {
  assert.equal(median([100, 200, 3000]), 200, 'trung bình sẽ là 1100 — sai lệch vì 1 outlier');
  assert.equal(median([100, 200]), 150);
  assert.equal(median([]), null);
  assert.equal(median([5, null, NaN, 7]), 6, 'bỏ giá trị không đo được');
});

test('aggregate: gộp nhiều lần chạy + cờ `unstable` khi số nhiễu', () => {
  const a = aggregate([{ LCP: 1000 }, { LCP: 1100 }, { LCP: 1050 }]);
  assert.equal(a.LCP.median, 1050); assert.equal(a.LCP.rating, 'good');
  assert.equal(a.LCP.runs, 3); assert.equal(a.LCP.unstable, false);

  // spread > trung vị -> phải báo nhiễu để người đọc giảm niềm tin
  const b = aggregate([{ LCP: 500 }, { LCP: 5000 }, { LCP: 900 }]);
  assert.equal(b.LCP.median, 900);
  assert.equal(b.LCP.unstable, true, 'dao động 500–5000 quanh trung vị 900 = không tin được');
});

test('verdict: KHÔNG đo được cái nào = 未実施, TUYỆT ĐỐI không phải PASS', () => {
  assert.equal(verdict({}), '未実施');
  assert.equal(verdict(null), '未実施');
  assert.equal(verdict(aggregate([])), '未実施', 'chạy 0 lần -> chưa biết gì -> không được PASS');
});

test('verdict: chuẩn "good" của Google LÀ mốc đạt — needs-improvement cũng FAIL', () => {
  assert.equal(verdict(aggregate([{ LCP: 1000, CLS: 0.01, TBT: 50, FCP: 900, TTFB: 200 }])), 'PASS');
  // needs-improvement = KHÔNG đạt chuẩn công bố -> FAIL (nới cho qua = tự hạ chuẩn)
  assert.equal(verdict(aggregate([{ LCP: 3000, CLS: 0.01, TBT: 50, FCP: 900, TTFB: 200 }])), 'FAIL');
  assert.equal(verdict(aggregate([{ LCP: 9000, CLS: 0.01, TBT: 50, FCP: 900, TTFB: 200 }])), 'FAIL');
  // cwvOnly: chỉ soi 2 chỉ số Core Web Vital đo được ở lab (LCP, CLS)
  const agg = aggregate([{ LCP: 1000, CLS: 0.01, TTFB: 1500 }]);
  assert.equal(verdict(agg), 'FAIL', 'TTFB 1500 > 800 -> FAIL khi soi hết');
  assert.equal(verdict(agg, { cwvOnly: true }), 'PASS', 'chỉ CWV thì LCP+CLS đều good');
});

test('findings: chỉ báo chỉ số KHÔNG đạt; kèm số đo, ngưỡng, nguồn tra lại', () => {
  const agg = aggregate([{ LCP: 5000 }, { LCP: 5200 }, { LCP: 5100 }, { CLS: 0.02 }]);
  const f = findings(agg, { url: '/2', where: 'widget' });
  const lcp = f.find((x) => x.metric === 'LCP');
  assert.ok(lcp, 'LCP poor phải được báo');
  assert.equal(lcp.severity, 'High', 'poor -> High');
  assert.match(lcp.observed, /5100/);           // trung vị
  assert.match(lcp.observed, /good ≤ 2500ms/);  // ngưỡng công bố nằm ngay trong câu
  assert.match(lcp.fix, /web\.dev/);            // nguồn để dev tra
  assert.ok(!f.some((x) => x.metric === 'CLS'), 'CLS good -> KHÔNG báo');

  assert.equal(findings(aggregate([{ LCP: 3000 }]))[0].severity, 'Medium', 'needs-improvement -> Medium');
  assert.deepEqual(findings(aggregate([{ LCP: 1000, CLS: 0.01, TBT: 10, FCP: 500, TTFB: 100 }])), [],
    'mọi chỉ số good -> 0 finding');
});
