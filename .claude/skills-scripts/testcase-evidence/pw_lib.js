// pw_lib.js — Playwright helper cho Threease dev. CƠ KHÍ, không reasoning.
// getPage(target) -> { browser, context, page, BASE }. Mặc định đăng nhập Pro.
// Đổi hệ khác qua env: BASE_URL, BASIC_USER/PASS, INST/THER/PW, HEADED=1 để xem browser.
const { chromium } = require('playwright');

const CFG = {
  pro: {
    BASE: process.env.BASE_URL || 'https://develop.pro.threease.com',
    basic: { username: process.env.BASIC_USER || 'threesides', password: process.env.BASIC_PASS || 'threesides' },
    login: {
      inst: process.env.INST || 'TESTSEED001',
      ther: process.env.THER || 'STAFF001',
      pw:   process.env.PW   || 'password123',
    },
  },
  reservation: {
    BASE: process.env.BASE_URL || 'https://reservation-dev.threease.com',
    basic: { username: process.env.BASIC_USER || 'threesides', password: process.env.BASIC_PASS || 'threesides' },
    login: null,
  },
  admin: {
    BASE: process.env.BASE_URL || 'https://admin-dev.threease.com',
    basic: null,
    login: null, // admin@example.com/password123 — form riêng, điền trong script khi cần
  },
  ticket_admin: {
    BASE: process.env.TICKET_ADMIN_URL || 'https://ticket-dev.threease.com',
    basic: null,
    django_admin: {
      user: process.env.TK_ADMIN_USER || 'admin',
      pass: process.env.TK_ADMIN_PASS || 'password123',
    },
  },
};

async function getPage(target = 'pro') {
  const c = CFG[target] || CFG.pro;
  const browser = await chromium.launch({ headless: !process.env.HEADED });
  const context = await browser.newContext({
    httpCredentials: c.basic ? { username: c.basic.username, password: c.basic.password } : undefined,
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  // Django admin (ticket-dev) — form login riêng, không phải Nuxt data-cy.
  if (c.django_admin) {
    await page.goto(c.BASE + '/admin/login/', { waitUntil: 'domcontentloaded' });
    if (await page.locator('#id_username').count()) {
      await page.fill('#id_username', c.django_admin.user);
      await page.fill('#id_password', c.django_admin.pass);
      await page.click('input[type=submit]');
      await page.waitForTimeout(3000);
    }
    return { browser, context, page, BASE: c.BASE };
  }

  await page.goto(c.BASE + '/', { waitUntil: 'domcontentloaded' });

  // Login form Pro/Ticket (data-cy) — chờ Vue render form rồi mới điền (nếu chưa đăng nhập).
  if (c.login) {
    await page.locator('input[data-cy=institute_code]')
      .waitFor({ state: 'visible', timeout: 8000 }).catch(() => {});
  }
  if (c.login && await page.locator('input[data-cy=institute_code]').count()) {
    await page.fill('input[data-cy=institute_code]', c.login.inst);
    await page.fill('input[data-cy=therapist_code]', c.login.ther);
    await page.fill('input[data-cy=password]', c.login.pw);
    await page.click('[data-cy=loginButton]');
    await page.waitForTimeout(5000);
  }
  return { browser, context, page, BASE: c.BASE };
}

module.exports = { getPage, CFG };
