const { test } = require('node:test');
const assert = require('node:assert');
const { chromium } = require('playwright');
const {
  PAYLOADS, isServerError, hasStackLeak, looksLikeData,
  xssFired, resetXss, probeInjection, probeIDOR, probeBypass, probeErrorDisclosure, finding,
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

test('probeIDOR: 200+data → leak; 403 → không leak', () => {
  assert.equal(probeIDOR({ status: 200, body: { id: 9, name: 'người khác' } }).leak, true);
  assert.equal(probeIDOR({ status: 403, body: { error: 'forbidden' } }).leak, false);
  assert.equal(probeIDOR({ status: 404, body: 'Not Found' }).leak, false);
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

test('finding chuẩn hoá đủ field', () => {
  const f = finding({ family: 'xss', payloadClass: 'xss', where: 'ô Tên', url: '/coupons/new/',
    severity: 'High', observed: 'payload execute', fix: 'escape output', shot: 'shots/x.png' });
  assert.equal(f.family, 'xss'); assert.equal(f.severity, 'High'); assert.equal(f.shot, 'shots/x.png');
});
