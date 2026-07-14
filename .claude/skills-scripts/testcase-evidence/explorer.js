// explorer.js — Bộ dò-đường tự-lái, BUILD-TIME. CƠ KHÍ (Claude là đầu, file này là tay).
// Bọc mỏng native Playwright: ariaSnapshot (nhìn) + getByRole/Label (bấm). Tái dùng pw_lib cho login.
// ⚠️ CẤM dùng lúc /testcase-run (đây là đồ build-time). Nav block chỉ ghi HOW, không WHAT.
const fs = require('fs');
const { getPage, shot } = require('./pw_lib');

// snapshot(page): trả cấu trúc trang bằng CHỮ (button/combobox/tab + tên). Thay tấm-ảnh-mù bằng danh-sách-chữ.
async function snapshot(page, opts = {}) {
  const region = opts.region || 'body';
  return await page.locator(region).ariaSnapshot();
}

// resolve(page, step): step ngữ nghĩa -> Locator. Ưu tiên nearLabel > role+name > label > text.
async function resolve(page, step) {
  if (step.via === 'nearLabel') return nearLabel(page, step.label);
  if (step.role) return page.getByRole(step.role, { name: step.name, exact: false });
  if (step.label) return page.getByLabel(step.label);
  if (step.text) return page.getByText(step.text, { exact: false });
  throw new Error('step thiếu selector ngữ nghĩa (role/label/text) hoặc via');
}

// act(page, step): làm MỘT bước. Retry 3 lần vì Vuetify hay detach giữa chừng (mẫu từ pw_lib.fillSafe).
// Toạ độ (action:'coord') CHỈ chạy khi step.fragile===true — ép luật "không lén đóng dấu toạ độ".
async function act(page, step) {
  if (step.action === 'coord') {
    if (!step.fragile) throw new Error('bước toạ độ bắt buộc fragile:true (a11y không thấy được element)');
    await page.mouse.click(step.x, step.y);
    return;
  }
  const T = step.timeout || 10000;
  for (let i = 0; i < 3; i++) {
    try {
      const loc = (await resolve(page, step)).first();
      await loc.waitFor({ state: 'visible', timeout: T });
      if (step.action === 'fill') await loc.fill(String(step.value), { timeout: T });
      else await loc.click({ timeout: T });
      return;
    } catch (e) {
      if (i === 2) throw e;
      await page.waitForTimeout(Math.min(800, T)); // đợi re-render rồi thử lại
    }
  }
}

module.exports = { snapshot, act };
