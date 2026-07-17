const { test } = require('node:test');
const assert = require('node:assert');
const { chromium } = require('playwright');
const {
  PAYLOADS, DENY_STATUS, isServerError, statusIn, isDenied, hasStackLeak, looksLikeData, looksLikeSpaShell,
  xssFired, resetXss, probeInjection, probeIDOR, probeBypass, probeErrorDisclosure,
  checkSecurityHeaders, probeOpenRedirect, probeCsrf, probeMassAssignment, probeForceBrowse, probeSessionAfterLogout,
  probeCookieFlags, probeCors, probeSessionFixation,
  finding,
} = require('./security_lib');

test('PAYLOADS có đủ 4 họ, XSS dùng marker window.__SEC_XSS', () => {
  for (const k of ['xss', 'sqli', 'template', 'csv']) {
    assert.ok(Array.isArray(PAYLOADS[k]) && PAYLOADS[k].length >= 3, `${k} phải có ≥3 payload`);
  }
  assert.ok(PAYLOADS.xss.some(p => p.includes('__SEC_XSS')), 'XSS phải bơm marker __SEC_XSS');
});

test('isServerError chỉ true cho 5xx', () => {
  assert.equal(isServerError(500), true);
  assert.equal(isServerError(503), true);
  assert.equal(isServerError(404), false);
  assert.equal(isServerError(200), false);
});

test('hasStackLeak bắt traceback/SQL/exception, bỏ qua body sạch', () => {
  assert.equal(hasStackLeak('Traceback (most recent call last):\n  File "x.py"').leak, true);
  assert.equal(hasStackLeak('django.db.utils.IntegrityError: null value').leak, true);
  assert.equal(hasStackLeak('SQLSTATE[23000]: Integrity constraint').leak, true);
  assert.equal(hasStackLeak('{"error":"not found"}').leak, false);
  assert.equal(hasStackLeak('').leak, false);
});

test('looksLikeData: object/array có field giống record thật → true; lỗi/rỗng → false', () => {
  assert.equal(looksLikeData({ id: 5, name: 'KH khác', email: 'a@b.c' }), true);
  assert.equal(looksLikeData([{ id: 1 }, { id: 2 }]), true);
  assert.equal(looksLikeData({ error: 'forbidden' }), false);
  assert.equal(looksLikeData({}), false);
  assert.equal(looksLikeData('Not Found'), false);
});

test('probeInjection: XSS bơm vào ô CÓ execute → fired=true; ô escaped → fired=false', async () => {
  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await page.setContent('<input id="f"><button id="b">go</button><div id="out"></div>'
      + '<script>document.getElementById("b").onclick=()=>{'
      + 'document.getElementById("out").innerHTML=document.getElementById("f").value;};</script>');
    const submit = async () => { await page.click('#b'); await page.waitForTimeout(50); return null; };
    const r = await probeInjection(page, page.locator('#f'), '<img src=x onerror="window.__SEC_XSS=1">', submit);
    assert.equal(r.fired, true, 'trang echo innerHTML phải làm XSS fired');

    await page.setContent('<input id="f2"><button id="b2">go</button><div id="out2"></div>'
      + '<script>document.getElementById("b2").onclick=()=>{'
      + 'document.getElementById("out2").textContent=document.getElementById("f2").value;};</script>');
    const submit2 = async () => { await page.click('#b2'); await page.waitForTimeout(50); return null; };
    const r2 = await probeInjection(page, page.locator('#f2'), '<img src=x onerror="window.__SEC_XSS=1">', submit2);
    assert.equal(r2.fired, false, 'trang textContent KHÔNG được để XSS fired');
  } finally {
    await browser.close();
  }
});

test('probeIDOR: JSON 200+data → leak; 403 → không leak', () => {
  assert.equal(probeIDOR({ status: 200, body: { id: 9, name: 'người khác' } }).leak, true);
  assert.equal(probeIDOR({ status: 403, body: { error: 'forbidden' } }).leak, false);
  assert.equal(probeIDOR({ status: 404, body: 'Not Found' }).leak, false);
});

test('probeIDOR HTML: 200 trang thật (không deny) → leak; 200 trang deny → không; 302 → không', () => {
  const realPage = '<html><body><h1>顧客詳細</h1><div>顧客ID AIOTT99 お名前 KH-KHÁC</div></body></html>';
  assert.equal(probeIDOR({ status: 200, body: realPage }).leak, true);
  // 200 nhưng render trang "権限がありません" (app dùng 200 cho deny)
  assert.equal(probeIDOR({ status: 200, body: '<html><body>権限がありません</body></html>' }).leak, false);
  assert.equal(probeIDOR({ status: 302, body: '' }).leak, false);
});

test('probeBypass: UI chặn mà API KHÔNG chặn → parityOk=false (FAIL)', () => {
  assert.equal(probeBypass({ uiBlocks: true, apiStatus: 200 }).parityOk, false);
  assert.equal(probeBypass({ uiBlocks: true, apiStatus: 403 }).parityOk, true);
  assert.equal(probeBypass({ uiBlocks: false, apiStatus: 200 }).parityOk, true);
});

test('probeErrorDisclosure: 500 hoặc stack leak → disclosed', () => {
  assert.equal(probeErrorDisclosure({ status: 500, body: 'x' }).disclosed, true);
  assert.equal(probeErrorDisclosure({ status: 200, body: 'Traceback (most recent call last):' }).disclosed, true);
  assert.equal(probeErrorDisclosure({ status: 404, body: '{"detail":"not found"}' }).disclosed, false);
});

test('checkSecurityHeaders: thiếu header phòng thủ → missing; đủ → ok; HSTS bỏ qua khi http; CSP frame-ancestors thay X-Frame', () => {
  const none = checkSecurityHeaders({});
  assert.equal(none.ok, false);
  assert.ok(none.missing.some(m => m.header === 'content-security-policy'));
  const full = checkSecurityHeaders({
    'Content-Security-Policy': "default-src 'self'", 'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
    'Strict-Transport-Security': 'max-age=63072000',
  });
  assert.equal(full.ok, true, JSON.stringify(full.missing));
  // http → HSTS không tính thiếu
  assert.ok(!checkSecurityHeaders({}, { https: false }).missing.some(m => m.header === 'strict-transport-security'));
  // CSP frame-ancestors thay được X-Frame-Options
  const cspFa = checkSecurityHeaders({ 'Content-Security-Policy': "frame-ancestors 'none'" });
  assert.ok(!cspFa.missing.some(m => m.header === 'x-frame-options'));
});

test('probeOpenRedirect: final host == host tấn công → vulnerable', () => {
  assert.equal(probeOpenRedirect({ finalUrl: 'https://evil.com/x', attackerHost: 'evil.com' }).vulnerable, true);
  assert.equal(probeOpenRedirect({ finalUrl: 'https://ticket-dev.threease.com/home', attackerHost: 'evil.com' }).vulnerable, false);
  assert.equal(probeOpenRedirect({ finalUrl: 'not-a-url', attackerHost: 'evil.com' }).vulnerable, false);
});

test('probeCsrf: POST thiếu token mà 2xx → vulnerable', () => {
  assert.equal(probeCsrf({ status: 200 }).vulnerable, true);
  assert.equal(probeCsrf({ status: 403 }).vulnerable, false);
  assert.equal(probeCsrf({ status: 302 }).vulnerable, false);
});

test('probeMassAssignment: field đặc quyền ghi được → vulnerable', () => {
  assert.equal(probeMassAssignment({ accepted: true }).vulnerable, true);
  assert.equal(probeMassAssignment({ accepted: false }).vulnerable, false);
});

test('probeForceBrowse: 200+resource → leak; 200 trang deny (HTML) → không; 403 → không', () => {
  assert.equal(probeForceBrowse({ status: 200, body: { id: 1, name: 'x' } }).leak, true);
  assert.equal(probeForceBrowse({ status: 200, body: '<html>報告 顧客ID AIOTT01 データ</html>' }).leak, true);   // HTML thật → leak
  assert.equal(probeForceBrowse({ status: 200, body: '<html>権限がありません</html>' }).leak, false);            // 200 deny page
  assert.equal(probeForceBrowse({ status: 403, body: {} }).leak, false);
});

test('probeSessionAfterLogout: sau logout còn 200 → vulnerable', () => {
  assert.equal(probeSessionAfterLogout({ status: 200 }).vulnerable, true);
  assert.equal(probeSessionAfterLogout({ status: 401 }).vulnerable, false);
  assert.equal(probeSessionAfterLogout({ status: 302 }).vulnerable, false);
});

test('PAYLOADS có pathTraversal', () => {
  assert.ok(Array.isArray(PAYLOADS.pathTraversal) && PAYLOADS.pathTraversal.length >= 3);
  assert.ok(PAYLOADS.pathTraversal.some(p => /etc\/passwd|etc%2fpasswd/i.test(p)));
});

test('statusIn / isDenied: tập mã hợp lệ + redirect = denied; 200/500 = không denied', () => {
  assert.equal(statusIn(403, DENY_STATUS), true);
  assert.equal(statusIn(200, DENY_STATUS), false);
  assert.equal(isDenied(401), true);
  assert.equal(isDenied(404), true);
  assert.equal(isDenied(302), true);   // redirect (login) = từ chối hợp lệ
  assert.equal(isDenied(200), false);
  assert.equal(isDenied(500), false);  // server-error KHÔNG phải "từ chối hợp lệ"
});

test('probeCookieFlags: cookie phiên thiếu HttpOnly/SameSite/Secure → weak; đủ cờ → ok; cookie thường bỏ qua', () => {
  const weak = probeCookieFlags(['sessionid=abc; Path=/']);
  assert.equal(weak.ok, false);
  assert.deepEqual(weak.weak[0].missing.sort(), ['HttpOnly', 'SameSite', 'Secure'].sort());
  const full = probeCookieFlags(['sessionid=abc; Path=/; HttpOnly; SameSite=Lax; Secure']);
  assert.equal(full.ok, true, JSON.stringify(full.weak));
  // http → Secure không tính thiếu
  assert.ok(!probeCookieFlags(['sessionid=abc; HttpOnly; SameSite=Lax'], { https: false })
    .weak.some(w => w.missing.includes('Secure')));
  // cookie không phải phiên (vd preference) → không soi
  assert.equal(probeCookieFlags(['theme=dark; Path=/']).ok, true);
  // cookie CSRF thiếu HttpOnly là BY-DESIGN (JS phải đọc) → chỉ đòi SameSite+Secure, không flag HttpOnly
  assert.equal(probeCookieFlags(['csrftoken=abc; Path=/; SameSite=Lax; Secure']).ok, true);
  assert.deepEqual(probeCookieFlags(['csrftoken=abc; Path=/']).weak[0].missing.sort(), ['SameSite', 'Secure'].sort());
});

test('probeCors: echo origin tấn công (± creds) hoặc *+creds → vulnerable; origin cố định → không', () => {
  const atk = 'https://evil.example';
  assert.equal(probeCors({ 'Access-Control-Allow-Origin': atk }, { attackerOrigin: atk }).vulnerable, true);
  assert.equal(probeCors({ 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Credentials': 'true' }).vulnerable, true);
  assert.equal(probeCors({ 'Access-Control-Allow-Origin': 'https://app.threease.com' }, { attackerOrigin: atk }).vulnerable, false);
  assert.equal(probeCors({}).vulnerable, false);   // không có CORS header
});

test('probeSessionFixation: id không xoay sau login → vuln; xoay → an toàn; thiếu vế → inconclusive', () => {
  assert.equal(probeSessionFixation({ before: 'sameid', after: 'sameid' }).vulnerable, true);
  assert.equal(probeSessionFixation({ before: 'old', after: 'new' }).vulnerable, false);
  assert.equal(probeSessionFixation({ before: null, after: 'x' }).inconclusive, true);
});

// ── REGRESSION: vỏ SPA chưa render KHÔNG được chấm leak (bug thật 2026-07-17, pro+reservation) ──
// Vỏ Nuxt THẬT lấy từ reservation-dev: server trả y hệt vỏ này cho /reservation (hợp lệ) LẪN
// /../../../../etc/passwd (traversal). Không có root:x:. DOM sau render mới ra "404 Not Found".
const NUXT_SHELL = `<!doctype html>
<html lang="ja" data-n-head="%7B%22lang%22"><head><title>Threease</title>
<meta charset="utf-8"><style>#nuxt-loading{background:#fff;visibility:hidden}</style></head>
<body><div id="__nuxt"><style>#nuxt-loading{opacity:0}</style><div id="nuxt-loading"></div></div>
<script>window.__NUXT__={};</script></body></html>`;

test('looksLikeSpaShell: nhận ra vỏ chưa render, KHÔNG nhầm trang có nội dung thật', () => {
  assert.equal(looksLikeSpaShell(NUXT_SHELL), true, 'vỏ Nuxt thật phải bị nhận ra');
  assert.equal(looksLikeSpaShell('<html><body><h1>顧客 700006</h1><p>email: a@b.com</p></body></html>'), false,
    'trang HTML có nội dung server-render KHÔNG phải vỏ');
  assert.equal(looksLikeSpaShell('root:x:0:0:root:/root:/bin/bash'), false, 'body không phải HTML');
  assert.equal(looksLikeSpaShell({ id: 1 }), false, 'JSON không phải vỏ');
  // ⚠️ false-NEGATIVE guard: trang LỘ THẬT nhưng NGẮN (24 ký tự) không được nhầm là vỏ.
  // Chỉ dựa "text ngắn" là fail ca này → phải đòi thêm vân tay hydration SPA.
  assert.equal(looksLikeSpaShell('<html><body><h1>顧客 700006</h1>email a@b.com</body></html>'), false,
    'trang ngắn nhưng KHÔNG có mount-point SPA ⇒ không phải vỏ (nếu nuốt = bỏ sót lỗ hổng)');
});

test('probeIDOR: vỏ SPA → inconclusive, KHÔNG phải leak (chống FAIL giả hàng loạt)', () => {
  const r = probeIDOR({ status: 200, body: NUXT_SHELL });
  assert.equal(r.leak, false, 'vỏ SPA tuyệt đối không được chấm leak');
  assert.equal(r.inconclusive, true, 'phải báo inconclusive để driver quan sát DOM đã render');
  // probeForceBrowse dùng chung oracle → cùng hành vi
  assert.equal(probeForceBrowse({ status: 200, body: NUXT_SHELL }).inconclusive, true);
  // nhưng lộ THẬT thì vẫn phải bắt được
  assert.equal(probeIDOR({ status: 200, body: '<html><body><h1>顧客 700006</h1>email a@b.com</body></html>' }).leak, true);
  assert.equal(probeIDOR({ status: 200, body: { id: 7, email: 'a@b.com' } }).leak, true);
});

// Vỏ Pro THẬT: có 56 ký tự text server-render ⇒ heuristic looksLikeSpaShell TRƯỢT.
// Chỉ cửa baselineBody (so byte) mới bắt được. Ca này khoá đúng khoảng trống đó.
const PRO_SHELL = `<!doctype html><html><head><title>threease_pro - threease_pro</title></head>
<body><div id="__nuxt"></div><div>ログイン</div><div>ワークスペースの準備が整うまでお待ちください。</div>
<script>window.__NUXT__={};</script></body></html>`;

test('probeIDOR: baselineBody bắt được catch-all mà heuristic vỏ TRƯỢT (ca Pro thật)', () => {
  assert.equal(looksLikeSpaShell(PRO_SHELL), false, 'vỏ Pro có text server-render ⇒ heuristic không bắt (đúng như đo thật)');
  // không baseline → probe phán leak (FAIL giả — chính là bug 2026-07-17)
  assert.equal(probeIDOR({ status: 200, body: PRO_SHELL }).leak, true);
  // có baseline giống hệt → inconclusive, KHÔNG phán leak
  const r = probeIDOR({ status: 200, body: PRO_SHELL }, { baselineBody: PRO_SHELL });
  assert.equal(r.leak, false);
  assert.equal(r.inconclusive, true);
  assert.match(r.reason, /catch-all/);
  // probeForceBrowse phải CHUYỂN TIẾP opts (từng quên → cửa bị nuốt)
  assert.equal(probeForceBrowse({ status: 200, body: PRO_SHELL }, { baselineBody: PRO_SHELL }).inconclusive, true);
  // baseline KHÁC → vẫn phán bình thường (không nuốt leak thật)
  assert.equal(probeIDOR({ status: 200, body: '<html><body><h1>顧客 700006</h1>email a@b.com</body></html>' },
    { baselineBody: PRO_SHELL }).leak, true);
});

test('finding chuẩn hoá đủ field', () => {
  const f = finding({ family: 'xss', payloadClass: 'xss', where: 'ô Tên', url: '/coupons/new/',
    severity: 'High', observed: 'payload execute', fix: 'escape output', shot: 'shots/x.png' });
  assert.equal(f.family, 'xss'); assert.equal(f.severity, 'High'); assert.equal(f.shot, 'shots/x.png');
});
