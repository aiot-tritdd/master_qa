// pw_api.js — gọi API Hệ thống Lõi (Rails) bằng CHÍNH phiên đăng nhập của app. CƠ KHÍ, không reasoning.
//
// ⚠️ Auth KHÔNG phải Bearer token. Rails dùng devise_token_auth = 5 header:
//    access-token, client, uid, expiry, token-type
// Ta KHÔNG tự dựng token và KHÔNG đọc code để biết cách auth. Ta mở 1 trang thật của app,
// NGHE LÉN header của request mà chính app gửi đi, rồi tái sử dụng.
// => Đây là quan sát app (black-box), không phải đọc app. Hợp lệ với Tường thép #2.
//
// Dùng:
//   const { withApi } = require('<repo>/.claude/skills-scripts/testcase-evidence/pw_api');
//   await withApi(async ({ api, page }) => {
//     const r = await api.get(`/branches/${b}/customers/${c}/ticket_packs`);
//     console.log(r.status, r.body);          // <- status DÙNG ĐƯỢC (case chống bypass: 403 vs 204)
//   });
//
// Env: API_BASE (mặc định api-dev.threease.com/api/v1/therapists) · WARM_PATH (trang để bắt header)
const { getPage } = require('./pw_lib');

const API_BASE = process.env.API_BASE || 'https://api-dev.threease.com/api/v1/therapists';
const API_HOST = API_BASE.split('/api/')[0].replace(/^https?:\/\//, '');
const WARM_PATH = process.env.WARM_PATH || '/reservations';

async function withApi(fn, target = 'pro') {
  const { browser, context, page, BASE } = await getPage(target);

  let headers = null;
  page.on('request', (r) => {
    if (headers) return;
    const h = r.headers();
    if (r.url().includes(API_HOST) && h['access-token']) {
      headers = {
        'access-token': h['access-token'],
        client: h['client'],
        uid: h['uid'],
        expiry: h['expiry'],
        'token-type': h['token-type'],
        'content-type': 'application/json',
      };
    }
  });

  // Mở 1 trang có gọi API để app tự phát request -> ta bắt header từ đó.
  await page.goto(BASE + WARM_PATH, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
  for (let i = 0; i < 20 && !headers; i++) await page.waitForTimeout(500); // tối đa 10s

  if (!headers) {
    await browser.close();
    throw new Error(
      `pw_api: không bắt được header auth từ ${API_HOST}. ` +
      `Thử WARM_PATH=<trang có gọi API>, hoặc NO_STATE=1 nếu session cache đã hết hạn.`
    );
  }

  const call = async (method, path, data) => {
    const res = await context.request.fetch(API_BASE + path, { method, headers, data });
    let body;
    try { body = await res.json(); } catch { body = await res.text(); }
    return { status: res.status(), body, ok: res.ok() };
  };

  const api = {
    get:  (p)       => call('GET', p),
    post: (p, data) => call('POST', p, data),
    put:  (p, data) => call('PUT', p, data),
    del:  (p)       => call('DELETE', p),
    call,                     // method tuỳ ý
    raw: context.request,
  };

  try {
    return await fn({ api, page, context, BASE });
  } finally {
    await browser.close();
  }
}

module.exports = { withApi, API_BASE };
