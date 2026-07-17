// security_lib.js — bất biến an ninh PHỔ QUÁT (black-box, mù code). Oracle helpers THUẦN + probe.
// KHÔNG tự gọi HTTP: probe IDOR/bypass/error nhận {status,body} do driver fetch (driver lo auth per-app).
// XSS marker = window.__SEC_XSS (bơm rồi đọc lại — chỉ quan sát browser, không đọc code).

const PAYLOADS = {
  xss: [
    '<img src=x onerror="window.__SEC_XSS=1">',
    '<svg onload="window.__SEC_XSS=1">',
    '"><script>window.__SEC_XSS=1</script>',
  ],
  sqli: ["' OR '1'='1", "'; DROP TABLE x;--", '" OR ""="'],
  template: ['${{7*7}}', '{{7*7}}', '#{7*7}'],
  csv: ['=2+2', '+2+2', '-2+2', '@SUM(1+1)'],
};

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

function probeIDOR(result) {
  const { status, body } = result || {};
  return { status, leak: status === 200 && looksLikeData(body) };
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

function finding({ family, payloadClass, where, url, severity, observed, fix, shot }) {
  return { family, payloadClass: payloadClass || '', where: where || '', url: url || '',
    severity: severity || 'Medium', observed: observed || '', fix: fix || '', shot: shot || '' };
}

module.exports = {
  PAYLOADS, isServerError, hasStackLeak, looksLikeData,
  xssFired, resetXss, probeInjection, probeIDOR, probeBypass, probeErrorDisclosure, finding,
};
