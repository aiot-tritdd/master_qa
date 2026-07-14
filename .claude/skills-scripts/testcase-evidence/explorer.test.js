const { test } = require('node:test');
const assert = require('node:assert');
const { chromium } = require('playwright');
const { snapshot } = require('./explorer');

async function withPage(html, fn) {
  const b = await chromium.launch({ headless: true });
  try {
    const p = await (await b.newContext()).newPage();
    await p.setContent(html);
    await fn(p);
  } finally { await b.close(); }
}
module.exports = { withPage };

test('snapshot trả cấu trúc trang có TÊN (a11y)', async () => {
  await withPage('<button>追加</button><div role="tab">チケット</div>', async (p) => {
    const s = await snapshot(p);
    assert.match(s, /button "追加"/);
    assert.match(s, /tab "チケット"/);
  });
});
