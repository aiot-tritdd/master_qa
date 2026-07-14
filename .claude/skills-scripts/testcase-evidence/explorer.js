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

module.exports = { snapshot };
