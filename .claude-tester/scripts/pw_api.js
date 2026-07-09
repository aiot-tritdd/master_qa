// Bắt header auth (devise-token: access-token/client/uid) từ request thật của app,
// rồi trả về hàm api(method, path, data) để gọi API backend trực tiếp.
//   API_BASE = https://api-dev.threease.com/api/v1/therapists
// require('/Users/hieulnd/.claude-tester/scripts/pw_api.js')
const { getPage } = require('./pw_lib');
const API_BASE = process.env.API_BASE || 'https://api-dev.threease.com/api/v1/therapists';
const API_HOST = API_BASE.split('/api/')[0].replace(/^https?:\/\//, '');

async function withApi(fn) {
  const { browser, ctx, page, BASE, SHOTS } = await getPage();
  let headers = null;
  page.on('request', (r) => {
    if (!headers && r.url().includes(API_HOST) && r.headers()['access-token']) {
      const h = r.headers();
      headers = {
        'access-token': h['access-token'], client: h['client'], uid: h['uid'],
        expiry: h['expiry'], 'token-type': h['token-type'], 'content-type': 'application/json',
      };
    }
  });
  await page.goto(BASE + '/reservations', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(8000);
  if (!headers) throw new Error('no auth header captured (mở 1 trang có gọi API trước)');
  const api = async (method, path, data) => {
    const res = await ctx.request.fetch(API_BASE + path, { method, headers, data });
    let body; try { body = await res.json(); } catch (e) { body = await res.text(); }
    return { status: res.status(), body };
  };
  try { await fn({ api, page, ctx, BASE, SHOTS }); } finally { await browser.close(); }
}

module.exports = { withApi };
