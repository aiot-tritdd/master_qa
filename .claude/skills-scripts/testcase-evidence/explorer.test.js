const { test } = require('node:test');
const assert = require('node:assert');
const { chromium } = require('playwright');
const { snapshot, act, nearLabel } = require('./explorer');

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

test('nearLabel: chọn control NGAY DƯỚI nhãn, không dính control xa', async () => {
  await withPage(`
    <div style="position:absolute;top:0px;left:0">お客様</div>
    <input id="near" style="position:absolute;top:30px;left:0">
    <input id="far"  style="position:absolute;top:300px;left:0">`, async (p) => {
    const loc = await nearLabel(p, 'お客様');
    await loc.fill('X');
    assert.strictEqual(await p.locator('#near').inputValue(), 'X');
    assert.strictEqual(await p.locator('#far').inputValue(), '');
  });
});
