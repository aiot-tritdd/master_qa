// Chạy: node --test compat_lib.test.js
// Khoá ORACLE của track Compatibility. Live-verify khoá phần "probe có chạm app thật" (việc khác).
const { test } = require('node:test');
const assert = require('node:assert');
const {
  VIEWPORTS, BROWSERS, probeReflow, probeParity, probeConsole, detectTransient, verdict, finding, sigKey,
} = require('./compat_lib');

test('VIEWPORTS có mốc 320 của WCAG 1.4.10 + cỡ điện thoại; BROWSERS có webkit (Safari/iPhone)', () => {
  assert.ok(VIEWPORTS.some((v) => v.width === 320), '320px = mốc W3C chốt cho Reflow, không được bỏ');
  assert.ok(VIEWPORTS.some((v) => v.width === 390), 'cỡ iPhone phổ biến');
  assert.ok(BROWSERS.includes('webkit'), 'webkit = Safari = iPhone — engine quan trọng nhất với app công khai');
  assert.deepEqual(BROWSERS, ['chromium', 'firefox', 'webkit']);
});

test('probeReflow: rộng hơn viewport = FAIL (phải cuộn ngang); vừa/nhỏ hơn = PASS', () => {
  assert.equal(probeReflow({ scrollWidth: 420, innerWidth: 320 }).overflows, true, '420>320 ⇒ cuộn ngang ⇒ vỡ');
  assert.equal(probeReflow({ scrollWidth: 420, innerWidth: 320 }).overflowPx, 100);
  assert.equal(probeReflow({ scrollWidth: 320, innerWidth: 320 }).overflows, false, 'vừa khít = OK');
  assert.equal(probeReflow({ scrollWidth: 300, innerWidth: 320 }).overflows, false, 'hẹp hơn = OK');
});

test('probeReflow: dung sai 2px chỉ để chống làm tròn subpixel, KHÔNG để nới luật', () => {
  assert.equal(probeReflow({ scrollWidth: 322, innerWidth: 320 }).overflows, false, '2px = nhiễu làm tròn');
  assert.equal(probeReflow({ scrollWidth: 323, innerWidth: 320 }).overflows, true, '3px đã là tràn thật');
  // thiếu số đo -> KHÔNG được phán bừa
  assert.equal(probeReflow({ scrollWidth: null, innerWidth: 320 }).inconclusive, true);
});

const mk = (names) => ({ interactive: names.map((n) => ({ role: 'button', name: n })), title: 'T' });

test('probeParity: engine thiếu nút so với tham chiếu = diff (bug thật)', () => {
  const r = probeParity({
    chromium: mk(['予約確認', '選択する', '次へ']),
    webkit: mk(['予約確認', '選択する']),          // MẤT nút 次へ trên Safari
  });
  assert.equal(r.diffs.length, 1);
  assert.equal(r.diffs[0].browser, 'webkit');
  assert.deepEqual(r.diffs[0].missing, ['button::次へ']);
  assert.deepEqual(r.diffs[0].extra, []);
});

test('probeParity: mọi engine giống nhau = 0 diff (thứ tự KHÔNG được tính là khác)', () => {
  const r = probeParity({
    chromium: mk(['a', 'b', 'c']),
    firefox: mk(['c', 'a', 'b']),      // cùng bộ, khác thứ tự
    webkit: mk(['b', 'c', 'a']),
  });
  assert.deepEqual(r.diffs, [], 'so theo TẬP, không theo thứ tự — thứ tự khác không phải bug compat');
});

test('probeParity: <2 engine hoặc thiếu tham chiếu -> inconclusive, KHÔNG phán', () => {
  assert.equal(probeParity({ chromium: mk(['a']) }).inconclusive, true, '1 engine thì so với ai?');
  assert.equal(probeParity({ firefox: mk(['a']), webkit: mk(['a']) }).inconclusive, true, 'thiếu chromium (ref)');
  // đổi ref thì so được
  assert.equal(probeParity({ firefox: mk(['a']), webkit: mk(['a']) }, { reference: 'firefox' }).inconclusive, false);
});

test('probeConsole: lỗi bên THỨ BA (GTM/analytics) không phải bug sản phẩm -> lọc bỏ', () => {
  const errs = [
    { kind: 'pageerror', text: 'TypeError: x is not a function', url: 'https://develop.pro.threease.com/app.js' },
    { kind: 'pageerror', text: 'Failed to load', url: 'https://www.googletagmanager.com/gtm.js' },
    { kind: 'pageerror', text: 'blocked', url: 'https://cdn.amplitude.com/libs/amplitude.js' },
  ];
  const r = probeConsole(errs);
  assert.equal(r.errors.length, 1, 'chỉ giữ lỗi của chính app');
  assert.match(r.errors[0].url, /threease/);
  assert.equal(r.hasError, true);
  // muốn xem hết thì phải nói rõ
  assert.equal(probeConsole(errs, { includeThirdParty: true }).errors.length, 3);
  assert.equal(probeConsole([]).hasError, false);
});

// ── REGRESSION: resource-404 KHÔNG phải lỗi JS (bug oracle thật 2026-07-17) ──
test('probeConsole: resource-404 tách khỏi lỗi JS — nếu không, chromium FAIL/firefox PASS = BỊA', () => {
  // Sự thật đo được: cùng API 404, chromium ghi console-error, firefox KHÔNG ghi.
  const chromiumSaw = [
    { kind: 'console', text: 'Failed to load resource: the server responded with a status of 404 ()', url: 'https://api-dev.threease.com/api/v1/home/providers/reservation/courses' },
    { kind: 'console', text: 'Failed to load resource: the server responded with a status of 404 ()', url: 'https://api-dev.threease.com/api/v1/home/providers/reservation/calendar' },
  ];
  const firefoxSaw = []; // firefox im lặng với đúng sự cố đó

  const c = probeConsole(chromiumSaw);
  const f = probeConsole(firefoxSaw);
  assert.equal(c.hasError, false, '404 tài nguyên KHÔNG được tính là lỗi JS');
  assert.equal(f.hasError, false);
  assert.equal(c.hasError, f.hasError, 'hai engine phải ra CÙNG verdict — khác nhau chỉ vì cách ghi log là bịa');
  assert.equal(c.networkFailures.length, 2, 'vẫn phải giữ lại để báo (chuyện functional: API hỏng)');

  // lỗi JS THẬT thì vẫn phải bắt
  const real = probeConsole([{ kind: 'pageerror', text: "TypeError: Cannot read properties of undefined", url: 'https://reservation-dev.threease.com/app.js' }]);
  assert.equal(real.hasError, true, 'JS exception thật vẫn phải FAIL');
  assert.equal(real.networkFailures.length, 0);
});

// ── REGRESSION: dialog chớp nhoáng làm parity tự mâu thuẫn ──
test('detectTransient: phần tử vừa THIẾU vừa THỪA = tự mâu thuẫn = transient, không phải bug engine', () => {
  // Đúng thứ đo được: 閉じる lúc firefox thiếu (320), lúc firefox thừa (390)
  const results = [
    { diffs: [{ browser: 'firefox', missing: ['button::閉じる'], extra: [] }] },
    { diffs: [{ browser: 'firefox', missing: [], extra: ['button::閉じる'] }] },
  ];
  assert.deepEqual(detectTransient(results), ['button::閉じる']);
  // diff MỘT CHIỀU (chỉ thiếu, không bao giờ thừa) = bug THẬT, KHÔNG được coi là transient
  assert.deepEqual(detectTransient([{ diffs: [{ browser: 'webkit', missing: ['button::次へ'], extra: [] }] }]), [],
    'thiếu nhất quán = bug thật, đừng bịt miệng');
});

test('probeParity: opts.transient loại nhiễu NHƯNG không được nuốt diff thật', () => {
  const sig = (names) => ({ interactive: names.map((n) => ({ role: 'button', name: n })), title: 'T' });
  const r = probeParity(
    { chromium: sig(['予約確認', '閉じる']), firefox: sig(['予約確認']) },
    { transient: ['button::閉じる'] },
  );
  assert.deepEqual(r.diffs, [], '閉じる là nhiễu đã chứng minh -> bỏ qua');
  assert.equal(r.ignored.length, 1, 'phải BÁO RA cái đã bỏ qua, không im lặng');

  // nút thật vẫn phải bắt dù có transient list
  const r2 = probeParity(
    { chromium: sig(['予約確認', '閉じる']), firefox: sig(['閉じる']) },
    { transient: ['button::閉じる'] },
  );
  assert.deepEqual(r2.diffs[0].missing, ['button::予約確認'], 'mất nút thật -> vẫn FAIL');
});

test('verdict: không vào được màn = 未実施 (KHÔNG phải PASS)', () => {
  assert.equal(verdict({ reachable: false }), '未実施', 'không quan sát được thì không được chấm PASS');
  assert.equal(verdict({ reachable: true, reflow: { overflows: false }, console: { hasError: false } }), 'PASS');
  assert.equal(verdict({ reachable: true, reflow: { overflows: true } }), 'FAIL');
  assert.equal(verdict({ reachable: true, parity: { diffs: [{ browser: 'webkit' }] } }), 'FAIL');
  assert.equal(verdict({ reachable: true, console: { hasError: true } }), 'FAIL');
});

test('sigKey + finding chuẩn hoá', () => {
  assert.equal(sigKey({ role: 'link', name: '  予約  ' }), 'link::予約', 'trim tên, tránh diff giả do khoảng trắng');
  const f = finding({ family: 'reflow', where: 'widget', url: '/reservation', browser: 'webkit',
    viewport: 'mobile-320', severity: 'High', observed: 'tràn 100px', fix: 'responsive' });
  assert.equal(f.browser, 'webkit'); assert.equal(f.viewport, 'mobile-320'); assert.equal(f.severity, 'High');
});
