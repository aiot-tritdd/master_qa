const { test } = require('node:test');
const assert = require('node:assert');
const { chromium } = require('playwright');
const { snapshot, act } = require('./explorer');

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

test('act: click theo role+name', async () => {
  await withPage(`<button onclick="this.textContent='clicked'">追加</button>`, async (p) => {
    await act(p, { action: 'click', role: 'button', name: '追加' });
    assert.strictEqual(await p.getByRole('button').textContent(), 'clicked');
  });
});

test('act: fill theo label', async () => {
  await withPage('<label>お客様<input></label>', async (p) => {
    await act(p, { action: 'fill', label: 'お客様', value: 'AIOTTEST-KH3' });
    assert.strictEqual(await p.getByLabel('お客様').inputValue(), 'AIOTTEST-KH3');
  });
});

test('act: click theo text', async () => {
  await withPage(`<a href="#" onclick="this.dataset.hit='1'">AIOT-TEST-TK10</a>`, async (p) => {
    await act(p, { action: 'click', text: 'AIOT-TEST-TK10' });
    assert.strictEqual(await p.getByText('AIOT-TEST-TK10').getAttribute('data-hit'), '1');
  });
});

test('act: toạ độ KHÔNG fragile -> ném lỗi (ép luật gắn cờ)', async () => {
  await withPage('<div></div>', async (p) => {
    await assert.rejects(act(p, { action: 'coord', x: 10, y: 10 }), /fragile/);
  });
});
