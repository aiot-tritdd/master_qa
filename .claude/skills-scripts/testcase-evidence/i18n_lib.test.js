// i18n_lib.test.js — khoá ORACLE ngôn ngữ (không cần app sống). node --test.
// Khoá 2 thứ: ① probe bắt đúng lỗi thật ② KHÔNG nuốt text hợp lệ (false-positive giết track này).
const test = require('node:test');
const assert = require('node:assert');
const L = require('./i18n_lib');

// ── probeKeyLeak: key i18n thô lòi ra màn ──
test('keyLeak: bắt dotted-ident + interpolation + sentinel', () => {
  const r = L.probeKeyLeak([
    'reservation.selectCourse',   // camelCase key (1 dot + hoa) → leak
    'common.button.submit.label', // ≥2 dots → leak
    '{{ title }}',                // vue/handlebars chưa render
    '__MISSING__',                // sentinel i18next
    '[[coupon.name]]',            // sentinel khác
  ]);
  assert.strictEqual(r.hasLeak, true);
  assert.strictEqual(r.ran, true);
  assert.strictEqual(r.hits.length, 5);
});

test('keyLeak: KHÔNG nuốt text người-đọc-được hợp lệ', () => {
  const r = L.probeKeyLeak([
    'Select a course',   // câu bình thường
    'example.com',       // domain: all-lowercase 1 dot → KHÔNG phải key
    'Version 3.5',       // số phiên bản
    'Hello. World',      // câu có dấu chấm + space
    '料金プラン',          // tiếng Nhật thật (không phải key)
    '',                   // rỗng
  ]);
  assert.strictEqual(r.hasLeak, false, `nuốt nhầm: ${JSON.stringify(r.hits)}`);
});

// ── probeMojibake: sai encoding ──
test('mojibake: bắt replacement-char + double-encoded UTF-8', () => {
  const r = L.probeMojibake([
    'cafÃ©',                          // "café" hỏng → Ã©
    'â',                       // smart-quote hỏng → â€™
    '��',                             // U+FFFD
    'ãã¹',     // katakana hỏng → ãƒ†ã‚¹
  ]);
  assert.strictEqual(r.hasMojibake, true);
  assert.strictEqual(r.ran, true);
  assert.ok(r.hits.length >= 3);
});

test('mojibake: KHÔNG nuốt accent thật + tiếng Nhật thật + tiền tệ', () => {
  const r = L.probeMojibake(['café', 'naïve', '日本語テスト', '£5', 'Ça va', '¥1,000']);
  assert.strictEqual(r.hasMojibake, false, `nuốt nhầm: ${JSON.stringify(r.hits)}`);
});

// ── probeParity: đổi /en/ nhưng chưa dịch ──
test('parity: CJK còn sót trên trang EN = chưa dịch', () => {
  const r = L.probeParity(['Home', 'コース選択', 'Next'], ['ホーム', 'コース選択', '次へ']);
  assert.strictEqual(r.inconclusive, false);
  assert.deepStrictEqual(r.untranslated, ['コース選択']);
});

test('parity: trang EN sạch (toàn latin) = 0 untranslated', () => {
  const r = L.probeParity(['Home', 'Select course', 'Next'], ['ホーム', 'コース選択', '次へ']);
  assert.strictEqual(r.inconclusive, false);
  assert.strictEqual(r.untranslated.length, 0);
});

test('parity: chỉ 1 locale → inconclusive (không so được)', () => {
  const r = L.probeParity(['ホーム', 'コース選択'], []);
  assert.strictEqual(r.inconclusive, true);
  assert.ok(r.reason);
});

// ── probeLocaleFormat: WARN-only, KHÔNG bao giờ FAIL ──
test('localeFormat: kanji date/currency trên trang EN → warn', () => {
  const r = L.probeLocaleFormat(['2026年07月21日', '1,000円', 'Total'], 'en');
  assert.strictEqual(r.warn, true);
  assert.ok(r.hits.length >= 2);
});

test('localeFormat: trang ja bình thường → không warn', () => {
  const r = L.probeLocaleFormat(['2026年07月21日', '1,000円'], 'ja');
  assert.strictEqual(r.warn, false);
});

// ── verdict tổng ──
test('verdict: leak/mojibake/untranslated → FAIL', () => {
  assert.strictEqual(L.verdict({ reachable: true, keyLeak: { hasLeak: true, ran: true } }), 'FAIL');
  assert.strictEqual(L.verdict({ reachable: true, mojibake: { hasMojibake: true, ran: true } }), 'FAIL');
  assert.strictEqual(L.verdict({ reachable: true, parity: { inconclusive: false, untranslated: ['X'] } }), 'FAIL');
});

test('verdict: probe chạy sạch → PASS', () => {
  assert.strictEqual(L.verdict({
    reachable: true,
    keyLeak: { hasLeak: false, ran: true },
    mojibake: { hasMojibake: false, ran: true },
    parity: { inconclusive: true },
  }), 'PASS');
});

test('verdict: không mở được màn / không có text → 未実施', () => {
  assert.strictEqual(L.verdict({ reachable: false }), '未実施');
  assert.strictEqual(L.verdict({ reachable: true, keyLeak: { ran: false }, mojibake: { ran: false }, parity: { inconclusive: true } }), '未実施');
});

test('verdict: localeFormat KHÔNG được làm FAIL (chỉ WARN)', () => {
  const v = L.verdict({
    reachable: true,
    keyLeak: { hasLeak: false, ran: true },
    localeFormat: { warn: true, hits: ['1,000円'] },
  });
  assert.strictEqual(v, 'PASS', 'localeFormat là WARN-only, không được kéo xuống FAIL');
});
