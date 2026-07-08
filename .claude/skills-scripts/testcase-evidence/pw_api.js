// pw_api.js — gọi API backend Threease dev. CƠ KHÍ, không reasoning.
// withApi(fn) -> tạo request context (kèm basic-auth) rồi chạy fn(api). api.get/post/put/del trả JSON.
// Env: API_BASE (mặc định api-dev.threease.com), BASIC_USER/PASS cho gateway nếu cần.
const { request } = require('playwright');

const API_BASE = process.env.API_BASE || 'https://api-dev.threease.com';

async function withApi(fn) {
  const ctx = await request.newContext({
    baseURL: API_BASE,
    httpCredentials: (process.env.BASIC_USER)
      ? { username: process.env.BASIC_USER, password: process.env.BASIC_PASS || '' }
      : undefined,
    extraHTTPHeaders: process.env.API_TOKEN ? { Authorization: `Bearer ${process.env.API_TOKEN}` } : {},
  });
  const jsonOr = async (resp) => {
    const t = await resp.text();
    try { return JSON.parse(t); } catch { return { _status: resp.status(), _raw: t }; }
  };
  const api = {
    async get(path, opts)        { return jsonOr(await ctx.get(path, opts)); },
    async post(path, data, opts) { return jsonOr(await ctx.post(path, { data, ...(opts || {}) })); },
    async put(path, data, opts)  { return jsonOr(await ctx.put(path, { data, ...(opts || {}) })); },
    async del(path, opts)        { return jsonOr(await ctx.delete(path, opts)); },
    raw: ctx,
  };
  try { return await fn(api); } finally { await ctx.dispose(); }
}

module.exports = { withApi, API_BASE };
