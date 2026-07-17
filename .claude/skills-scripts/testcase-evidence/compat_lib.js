// compat_lib.js — oracle CƠ KHÍ cho track Compatibility (black-box, mù code).
//
// Vì sao track này hợp vision "engine đa dự án": oracle KHÔNG cần ai đặt số, KHÔNG cần baseline
// per-project (khác Visual). Nó neo vào 3 bất biến phổ quát:
//
//  ① REFLOW — chuẩn CÔNG BỐ: WCAG 2.1 SC 1.4.10 (Reflow, AA). Nội dung phải đọc được ở bề rộng
//    320 CSS px mà KHÔNG phải cuộn NGANG. 320px = mốc do W3C chốt, không phải tui bịa.
//    → https://www.w3.org/WAI/WCAG21/Understanding/reflow.html
//  ② PARITY — bất biến logic: CÙNG một app, CÙNG một màn, thì mọi engine phải bày ra CÙNG bộ
//    affordance. Nút có ở Chrome mà mất ở Safari = app vỡ với người dùng Safari. Không cần chuẩn
//    nào công nhận điều này — nó là định nghĩa của "chạy được".
//  ③ NO-JS-ERROR — lỗi JS chưa bắt (uncaught) là hỏng, không phải khác biệt thẩm mỹ.
//
// KIẾN TRÚC (giống security_lib): probe ở đây là HÀM THUẦN, nhận số liệu đã đo → trả verdict.
// Driver mới là chỗ mở browser/đo. Tách vậy để unit-test được oracle mà không cần dev sống.
//
// ⚠️ Cạm bẫy đã biết khi so PARITY: nhãn động (ngày tháng, số tiền) đổi theo thời điểm. Vì vậy
// signature phải chụp CÙNG MỘT LÚC trên các engine (trong 1 lần chạy) — KHÔNG so với ảnh cũ.
// Đây chính là lý do Compatibility không dính bệnh "baseline mục rữa" của Visual.

// ── Viewport chuẩn. 320 là mốc WCAG 1.4.10; còn lại là thiết bị phổ biến thật. ──
const VIEWPORTS = [
  { name: 'mobile-320', width: 320, height: 568, why: 'mốc WCAG 1.4.10 Reflow (bề rộng nhỏ nhất phải đỡ được)' },
  { name: 'mobile-390', width: 390, height: 844, why: 'iPhone 14/15 — cỡ điện thoại phổ biến nhất' },
  { name: 'tablet-768', width: 768, height: 1024, why: 'iPad dọc' },
  { name: 'desktop-1280', width: 1280, height: 800, why: 'laptop' },
];

// webkit = engine của Safari = iPhone/iPad. Với app công khai cho khách, đây là engine QUAN TRỌNG NHẤT,
// không phải "cái thứ ba cho đủ bộ".
const BROWSERS = ['chromium', 'firefox', 'webkit'];

const REFLOW_TOLERANCE = 2; // px — chống lỗi làm tròn subpixel; KHÔNG phải để nới lỏng luật

// ── ① REFLOW (WCAG 1.4.10) ──
// FAIL khi nội dung rộng hơn viewport ⇒ người dùng phải cuộn ngang mới đọc hết.
function probeReflow({ scrollWidth, innerWidth }, opts = {}) {
  const tol = typeof opts.tolerance === 'number' ? opts.tolerance : REFLOW_TOLERANCE;
  if (typeof scrollWidth !== 'number' || typeof innerWidth !== 'number') {
    return { overflows: false, inconclusive: true, reason: 'thiếu số đo' };
  }
  const overflowPx = Math.round(scrollWidth - innerWidth);
  return { overflows: overflowPx > tol, overflowPx, scrollWidth, innerWidth };
}

// ── ② PARITY giữa các engine ──
// sigs = { chromium: Signature, firefox: Signature, webkit: Signature }
// Signature = { interactive: [{role,name}], title }  (driver thu bằng page.evaluate)
// So với engine THAM CHIẾU (mặc định chromium — chỉ vì nó là mẫu số chung, KHÔNG phải "chuẩn đúng").
function sigKey(i) {
  return `${i.role}::${(i.name || '').trim()}`;
}
// ⚠️ CHỚP NHOÁNG (transient) — bẫy đo thật 2026-07-17: dialog lỗi của widget hiện/tắt tuỳ nhịp mạng.
// Kết quả: `button::閉じる` lúc firefox THIẾU (320px), lúc firefox THỪA (390px) — hai kết luận NGƯỢC nhau
// cho cùng cặp engine ⇒ chứng cứ đó tự mâu thuẫn ⇒ KHÔNG phải khác biệt engine, chỉ là nhiễu thời điểm.
// `opts.transient` = danh sách nhãn được biết là chớp nhoáng → loại khỏi signature TRƯỚC khi so.
// ⚠️ Đây là con dao hai lưỡi: nhét bừa vào đây = NUỐT diff thật. Chỉ thêm khi đã CHỨNG MINH tự-mâu-thuẫn
// (cùng phần tử vừa thiếu vừa thừa giữa các lần đo), và luôn báo ra `ignored` để người soi lại.
function probeParity(sigs, opts = {}) {
  const ref = opts.reference || 'chromium';
  const names = Object.keys(sigs || {}).filter((b) => sigs[b]);
  if (names.length < 2) return { diffs: [], inconclusive: true, reason: 'cần ≥2 engine mới so được' };
  if (!sigs[ref]) return { diffs: [], inconclusive: true, reason: `thiếu engine tham chiếu ${ref}` };

  const transient = new Set(opts.transient || []);
  const keys = (b) => new Set((sigs[b].interactive || []).map(sigKey).filter((k) => !transient.has(k)));
  const ignored = [];
  for (const b of names) for (const i of sigs[b].interactive || []) if (transient.has(sigKey(i))) ignored.push({ browser: b, key: sigKey(i) });

  const refSet = keys(ref);
  const diffs = [];
  for (const b of names) {
    if (b === ref) continue;
    const set = keys(b);
    const missing = [...refSet].filter((k) => !set.has(k));   // có ở ref, MẤT ở engine này
    const extra = [...set].filter((k) => !refSet.has(k));     // engine này có thêm
    if (missing.length || extra.length) diffs.push({ browser: b, reference: ref, missing, extra });
  }
  return { diffs, inconclusive: false, ignored };
}

// Phát hiện phần tử TỰ MÂU THUẪN qua nhiều lần đo (nhiều viewport/lượt): cùng 1 key mà chỗ thì thiếu,
// chỗ thì thừa ⇒ transient. Dùng để ĐỀ XUẤT `opts.transient`, KHÔNG tự động bịt miệng.
function detectTransient(parityResults) {
  const miss = new Set(), extra = new Set();
  for (const r of parityResults || []) for (const d of (r && r.diffs) || []) {
    for (const k of d.missing || []) miss.add(k);
    for (const k of d.extra || []) extra.add(k);
  }
  return [...miss].filter((k) => extra.has(k)); // vừa thiếu vừa thừa = tự mâu thuẫn
}

// ── ③ Lỗi JS uncaught ──
// Lọc nhiễu ngoài app (analytics/ads/extension) — lỗi của bên thứ ba KHÔNG phải bug của sản phẩm.
const THIRD_PARTY_RE = /googletagmanager|google-analytics|doubleclick|amplitude|cloudwatch|rum|hotjar|facebook\.net|gtm\.js/i;

// ⚠️⚠️ CHỈ nhận `pageerror` (JS exception chưa bắt). TUYỆT ĐỐI KHÔNG nhận console-error chung.
// Vì sao (đo thật 2026-07-17, reservation widget): API 404 → **chromium** ghi "Failed to load resource: 404"
// ra console, **firefox KHÔNG ghi**. Cùng một app, cùng một sự cố, hai engine log khác nhau.
// ⇒ Đem console-error đi so parity là đang đo **CÁCH BROWSER GHI LOG**, không phải "app có vỡ không"
// → chromium FAIL / firefox PASS = kết luận BỊA. Chỉ `pageerror` mới có ngữ nghĩa giống nhau mọi engine.
// Resource 404 vẫn đáng quan tâm, nhưng nó là chuyện FUNCTIONAL (API hỏng) → trả riêng ở `networkFailures`,
// KHÔNG cho vào verdict compat.
const RESOURCE_ERR_RE = /failed to load resource|net::ERR_|ERR_ABORTED|the server responded with a status/i;
function probeConsole(errors, opts = {}) {
  const all = (errors || []).filter((e) => {
    const s = typeof e === 'string' ? e : `${e.text || ''} ${e.url || ''}`;
    if (opts.includeThirdParty) return true;
    return !THIRD_PARTY_RE.test(s);
  });
  const isResource = (e) => RESOURCE_ERR_RE.test(typeof e === 'string' ? e : (e.text || ''));
  const isPageError = (e) => (typeof e === 'object' && e.kind === 'pageerror');
  // JS thật = pageerror; nếu driver không gắn kind thì suy luận ngược: không phải resource-error.
  const jsErrors = all.filter((e) => (isPageError(e) || (typeof e === 'object' && !('kind' in e) && !isResource(e)) || (typeof e === 'string' && !isResource(e))));
  const networkFailures = all.filter(isResource);
  return { errors: jsErrors, hasError: jsErrors.length > 0, networkFailures };
}

// ── Verdict 1 ô (màn × engine × viewport) ──
// 未実施 khi không quan sát được (không mở nổi màn/engine).
function verdict({ reflow, parity, console: cons, reachable }) {
  if (reachable === false) return '未実施';
  const bad =
    (reflow && reflow.overflows) ||
    (parity && parity.diffs && parity.diffs.length > 0) ||
    (cons && cons.hasError);
  return bad ? 'FAIL' : 'PASS';
}

function finding({ family, where, url, browser, viewport, severity, observed, fix, shot }) {
  return {
    family, where, url,
    browser: browser || '', viewport: viewport || '',
    severity: severity || 'Medium',
    observed: observed || '', fix: fix || '', shot: shot || '',
  };
}

module.exports = {
  VIEWPORTS, BROWSERS, REFLOW_TOLERANCE, THIRD_PARTY_RE, RESOURCE_ERR_RE,
  probeReflow, probeParity, probeConsole, detectTransient, verdict, finding, sigKey,
};
