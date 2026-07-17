// security_lib.js — bất biến an ninh PHỔ QUÁT (black-box, mù code). Oracle helpers THUẦN + probe.
// KHÔNG tự gọi HTTP: probe IDOR/bypass/error nhận {status,body} do driver fetch (driver lo auth per-app).
// XSS marker = window.__SEC_XSS (bơm rồi đọc lại — chỉ quan sát browser, không đọc code).
//
// OWASP mapping = Top 10 **2025** (owasp.org/Top10/2025). Đổi so với 2021: A02 Misconfig lên cao,
// A03 = Supply-Chain (whitebox), A10 = Mishandling Exceptional Conditions, SSRF gộp A01/A06.
// Nguồn kỹ thuật probe: qa-skills/security-testing (kindlmann, MIT) — phần black-box; phần
// DAST/SCA/SAST/JWT là whitebox (xem ROADMAP §4).

const PAYLOADS = {
  xss: [
    '<img src=x onerror="window.__SEC_XSS=1">',
    '<svg onload="window.__SEC_XSS=1">',
    '"><script>window.__SEC_XSS=1</script>',
  ],
  sqli: ["' OR '1'='1", "'; DROP TABLE x;--", '" OR ""="'],
  template: ['${{7*7}}', '{{7*7}}', '#{7*7}'],
  csv: ['=2+2', '+2+2', '-2+2', '@SUM(1+1)'],
  pathTraversal: ['../../../../etc/passwd', '..%2f..%2f..%2f..%2fetc%2fpasswd', '....//....//....//etc/passwd'],
};

// ── Acceptable-status-set (qa-skills): 1 phép chấm thường có NHIỀU mã hợp lệ — đừng ép 1 status.
// "Từ chối hợp lệ" = {400,401,403,404,422} hoặc redirect 3xx. Dùng cho probe + assertion test.
const DENY_STATUS = [400, 401, 403, 404, 422];
function statusIn(status, allowed) {
  return typeof status === 'number' && Array.isArray(allowed) && allowed.includes(status);
}
function isDenied(status) {
  return statusIn(status, DENY_STATUS) || (typeof status === 'number' && status >= 300 && status < 400);
}

function isServerError(status) {
  return typeof status === 'number' && status >= 500 && status < 600;
}

// hasStackLeak: dấu hiệu lộ stack/SQL/traceback ra client (bất biến: KHÔNG được lộ).
const LEAK_PATTERNS = [
  [/Traceback \(most recent call last\)/, 'python-traceback'],
  [/\b(django\.\w+\.\w+Error|IntegrityError|OperationalError|ProgrammingError)\b/, 'django-exception'],
  [/SQLSTATE\[|SQL syntax|psql:|pg_query|near "/i, 'sql-error'],
  [/\b(NoMethodError|ActiveRecord::|RuntimeError|StandardError)\b/, 'ruby-exception'],
  [/ at .+\(.+:\d+:\d+\)/, 'js-stack'],
];
function hasStackLeak(body) {
  const s = typeof body === 'string' ? body : JSON.stringify(body || '');
  for (const [re, kind] of LEAK_PATTERNS) {
    const m = re.exec(s);
    if (m) return { leak: true, kind, snippet: s.slice(Math.max(0, m.index - 10), m.index + 80) };
  }
  return { leak: false, kind: '', snippet: '' };
}

// looksLikeData: body TRÔNG NHƯ record thật (object/array có field định danh) → IDOR có thể lộ data.
const DATA_KEYS = ['id', 'name', 'email', 'customer', 'uid', 'phone', 'code', 'title'];
function looksLikeData(body) {
  const recordLike = (o) =>
    o && typeof o === 'object' && !('error' in o) && Object.keys(o).some(k => DATA_KEYS.includes(k.toLowerCase()));
  if (Array.isArray(body)) return body.length > 0 && body.some(recordLike);
  return recordLike(body);
}

async function xssFired(page) {
  return await page.evaluate(() => window.__SEC_XSS === 1);
}
async function resetXss(page) {
  await page.evaluate(() => { try { delete window.__SEC_XSS; } catch (_) { window.__SEC_XSS = undefined; } });
}

// probeInjection: reset marker → điền payload → submit → quan sát fired/serverError/phản-chiếu-dạng-text.
async function probeInjection(page, fieldLocator, payload, submit) {
  await resetXss(page);
  await fieldLocator.fill(payload, { timeout: 8000 });
  let status = null;
  try { const s = await submit(); status = s && typeof s.status === 'number' ? s.status : null; } catch (_) {}
  const fired = await xssFired(page);
  const reflectedAsText = await page.evaluate((p) => document.body && document.body.innerText.includes(p), payload)
    .catch(() => false);
  return { payload, fired, serverError: isServerError(status), reflectedAsText };
}

// looksDenied: body TRÔNG NHƯ trang từ chối/không-thấy (403/404/redirect-login) — access-control OK.
const DENY_MARKERS = [
  /forbidden|unauthorized|access denied|not found|permission/i,
  /権限|見つかりません|アクセスできません|ログイン(?:して|が必要)|ページが存在/,
  /\b(403|404|401)\b/,
];
function looksDenied(body) {
  const s = typeof body === 'string' ? body : JSON.stringify(body || '');
  return DENY_MARKERS.some(re => re.test(s));
}

// probeIDOR: request tài nguyên KHÔNG được phép. status≠200 (403/404/302) = access-control OK.
// status===200: JSON → looksLikeData; HTML → 200 mà KHÔNG phải trang deny = nghi lộ (evidence xác nhận).
function probeIDOR(result) {
  const { status, body } = result || {};
  if (status !== 200) return { status, leak: false };
  const isObj = body && typeof body === 'object';
  const leak = isObj ? looksLikeData(body) : !looksDenied(body);
  return { status, leak };
}

function probeBypass({ uiBlocks, apiStatus }) {
  const apiBlocks = typeof apiStatus === 'number' && apiStatus >= 400 && apiStatus < 500;
  return { uiBlocks: !!uiBlocks, apiBlocks, parityOk: !uiBlocks || apiBlocks };
}

function probeErrorDisclosure(result) {
  const { status, body } = result || {};
  const leak = hasStackLeak(body);
  return { disclosed: isServerError(status) || leak.leak, kind: leak.kind, snippet: leak.snippet };
}

// ── A05 Security headers — bất biến: header phòng thủ NÊN có (defense-in-depth). ──
const EXPECTED_HEADERS = {
  'content-security-policy': 'CSP (chống XSS/inject)',
  'x-frame-options': 'chống clickjacking (hoặc CSP frame-ancestors)',
  'x-content-type-options': 'nosniff (chống MIME-sniff)',
  'referrer-policy': 'kiểm soát rò referrer',
  'strict-transport-security': 'HSTS (ép https)',
};
function checkSecurityHeaders(headers, opts = {}) {
  const https = opts.https !== false;
  const h = {};
  for (const k in (headers || {})) h[k.toLowerCase()] = headers[k];
  const missing = [];
  for (const [key, label] of Object.entries(EXPECTED_HEADERS)) {
    if (key === 'strict-transport-security' && !https) continue;               // HSTS chỉ áp cho https
    if (key === 'x-frame-options' && /frame-ancestors/i.test(h['content-security-policy'] || '')) continue; // CSP thay thế
    if (!h[key]) missing.push({ header: key, label });
  }
  return { missing, ok: missing.length === 0 };
}

// ── A01 Open-redirect — final host == host tấn công → vuln. ──
function probeOpenRedirect({ finalUrl, attackerHost }) {
  try { return { vulnerable: new URL(finalUrl).host === attackerHost }; }
  catch (_) { return { vulnerable: false }; }
}

// ── A05/A01 CSRF — state-changing POST thiếu token/credential → PHẢI KHÔNG 2xx. ──
function probeCsrf({ status }) {
  return { vulnerable: typeof status === 'number' && status >= 200 && status < 300 };
}

// ── A01 Mass-assignment — field đặc quyền KHÔNG có trên form mà GHI được → vuln. ──
function probeMassAssignment({ accepted }) {
  return { vulnerable: !!accepted };
}

// ── A01 Force-browse / path-traversal — URL cấm/traversal trả 200 kèm resource → leak. ──
// Cùng oracle với IDOR (xử được cả JSON lẫn HTML: 200 + không phải trang deny = nghi lộ).
function probeForceBrowse(result) {
  return probeIDOR(result);
}

// ── A07 Session-after-logout — sau logout, request bảo vệ PHẢI 401/302-login, KHÔNG 200. ──
function probeSessionAfterLogout({ status }) {
  return { vulnerable: status === 200 };
}

// ── A02/A04 Cookie flags — cookie PHIÊN phải có HttpOnly + SameSite (+ Secure khi https). ──
// Nhận mảng chuỗi Set-Cookie thô (driver đọc từ response header). Chỉ soi cookie phiên/định-danh.
// ⚠️ Cookie CSRF (csrf/xsrf) CỐ TÌNH đọc-được-bởi-JS (double-submit) → KHÔNG đòi HttpOnly (live-verify
//    2026-07-17: Django csrftoken thiếu HttpOnly là by-design, không phải lỗi). Chỉ đòi SameSite+Secure.
const SESSION_COOKIE_RE = /(session|sessionid|_session|sess|sid|csrf|xsrf|token|auth|remember)/i;
const CSRF_COOKIE_RE = /(csrf|xsrf)/i;
function probeCookieFlags(setCookies, opts = {}) {
  const https = opts.https !== false;
  const list = Array.isArray(setCookies) ? setCookies : (setCookies ? [setCookies] : []);
  const weak = [];
  for (const c of list) {
    if (typeof c !== 'string') continue;
    const name = (c.split('=')[0] || '').trim();
    if (!SESSION_COOKIE_RE.test(name)) continue;
    const f = c.toLowerCase();
    const missing = [];
    if (!CSRF_COOKIE_RE.test(name) && !/;\s*httponly/.test(f)) missing.push('HttpOnly');
    if (!/;\s*samesite=/.test(f)) missing.push('SameSite');
    if (https && !/;\s*secure/.test(f)) missing.push('Secure');
    if (missing.length) weak.push({ cookie: name, missing });
  }
  return { weak, ok: weak.length === 0 };
}

// ── A02 CORS misconfig — server PHẢN CHIẾU Origin tấn công (echo bất kỳ origin), tệ hơn nếu kèm
// Allow-Credentials=true; hoặc '*' + credentials. Nhận header response của 1 request gửi Origin lạ. ──
function probeCors(headers, opts = {}) {
  const h = {};
  for (const k in (headers || {})) h[k.toLowerCase()] = headers[k];
  const acao = h['access-control-allow-origin'] || null;
  const credentials = /true/i.test(h['access-control-allow-credentials'] || '');
  const attacker = opts.attackerOrigin || 'https://evil.example';
  const reflectsAttacker = acao === attacker;                 // echo đúng origin mình gửi = tin mọi origin
  const wildcardWithCreds = acao === '*' && credentials;      // spec cấm '*'+creds nhưng vài server bỏ qua
  return { acao, credentials, vulnerable: reflectsAttacker || wildcardWithCreds };
}

// ── A07 Session-fixation — session id TRƯỚC login PHẢI khác SAU login (server xoay session). ──
// before/after = giá trị cookie phiên quan sát 2 thời điểm. Thiếu 1 vế → inconclusive (未実施).
function probeSessionFixation({ before, after }) {
  const has = before != null && after != null && before !== '' && after !== '';
  if (!has) return { vulnerable: false, inconclusive: true };
  return { vulnerable: before === after, inconclusive: false };
}

function finding({ family, payloadClass, where, url, severity, observed, fix, shot }) {
  return { family, payloadClass: payloadClass || '', where: where || '', url: url || '',
    severity: severity || 'Medium', observed: observed || '', fix: fix || '', shot: shot || '' };
}

module.exports = {
  PAYLOADS, DENY_STATUS, isServerError, statusIn, isDenied, hasStackLeak, looksLikeData, looksDenied, EXPECTED_HEADERS,
  xssFired, resetXss, probeInjection, probeIDOR, probeBypass, probeErrorDisclosure,
  checkSecurityHeaders, probeOpenRedirect, probeCsrf, probeMassAssignment, probeForceBrowse, probeSessionAfterLogout,
  probeCookieFlags, probeCors, probeSessionFixation,
  finding,
};
