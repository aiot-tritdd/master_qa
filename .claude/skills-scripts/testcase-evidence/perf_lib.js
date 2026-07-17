// perf_lib.js — oracle CƠ KHÍ cho track Performance (black-box, mù code).
//
// Oracle = **Core Web Vitals** — ngưỡng do **Google công bố công khai** (web.dev/vitals), phổ quát,
// KHÔNG cần chủ dự án đặt số. Đúng vai trò WCAG với a11y: chuẩn ngoài, ai cũng tra được.
// ⇒ Đây là lý do Performance "0-setup" và hợp vision engine-đa-dự-án.
// (ROADMAP cũ ghi "vướng oracle, cần budget do người đặt" — SAI, đã gỡ 2026-07-17.)
//
// ⚠️⚠️ GIỚI HẠN PHẢI NÓI RA MỖI LẦN BÁO CÁO — nếu giấu là lừa người đọc:
//  ① **LAB ≠ FIELD.** Đây là đo *phòng thí nghiệm*: 1 máy, 1 đường mạng, không tải. Chuẩn CWV thật là
//    **phân vị 75 của NGƯỜI DÙNG THẬT** (CrUX) — điện thoại yếu, 4G, pin thấp. ⇒ Lab "good" **KHÔNG**
//    chứng minh người dùng thật thấy good. Nhưng lab "poor" thì **chắc chắn** là có vấn đề.
//    ⇒ Kết quả track này là **CẬN DƯỚI của mức tệ**, không phải chứng nhận nhanh.
//  ② **DEV ≠ PROD.** Đo trên dev: không CDN, cache khác, data ít, có thể còn debug build. Số ở đây
//    KHÔNG suy ra được production.
//  ③ **INP đo được ở FIELD, không đo được ở LAB** (cần tương tác của người thật). Lab dùng **TBT** làm
//    proxy — chính Google khuyến nghị vậy (web.dev/tbt). Đừng báo "INP = x ms" ở lab: đó là bịa.
//  ④ **Nhiễu cao** → phải chạy NHIỀU LẦN lấy TRUNG VỊ. 1 lần chạy không kết luận được gì.
//
// KIẾN TRÚC (giống security_lib/compat_lib): probe = HÀM THUẦN nhận số đã đo → trả verdict.
// Driver mới là chỗ mở browser/đo. Tách vậy để unit-test oracle mà không cần dev sống.

// ── Ngưỡng Google công bố. KHÔNG tự chế, KHÔNG nới. Nguồn ghi kèm để ai cũng tra lại được. ──
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000, unit: 'ms', cwv: true,
         label: 'Largest Contentful Paint — khi nội dung CHÍNH hiện ra', src: 'https://web.dev/articles/lcp' },
  CLS: { good: 0.1, poor: 0.25, unit: '', cwv: true,
         label: 'Cumulative Layout Shift — nội dung nhảy lung tung', src: 'https://web.dev/articles/cls' },
  TBT: { good: 200, poor: 600, unit: 'ms', cwv: false,
         label: 'Total Blocking Time — proxy LAB cho INP (Google khuyến nghị)', src: 'https://web.dev/articles/tbt' },
  FCP: { good: 1800, poor: 3000, unit: 'ms', cwv: false,
         label: 'First Contentful Paint — thấy pixel đầu tiên', src: 'https://web.dev/articles/fcp' },
  TTFB: { good: 800, poor: 1800, unit: 'ms', cwv: false,
          label: 'Time To First Byte — server đáp nhanh không', src: 'https://web.dev/articles/ttfb' },
};

// INP CỐ Ý không có trong THRESHOLDS: lab không đo được (cần tương tác người thật).
// Ai thêm INP vào đây là đang chuẩn bị bịa số. Dùng TBT làm proxy — đã có ở trên.
const FIELD_ONLY = ['INP'];

function rate(metric, value) {
  const t = THRESHOLDS[metric];
  if (!t) return 'unknown';
  if (typeof value !== 'number' || Number.isNaN(value)) return 'unknown';
  if (value <= t.good) return 'good';
  if (value <= t.poor) return 'needs-improvement';
  return 'poor';
}

// Trung vị, KHÔNG phải trung bình: 1 lần chạy dính GC/mạng lag sẽ kéo lệch trung bình.
function median(values) {
  const v = (values || []).filter((x) => typeof x === 'number' && !Number.isNaN(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

// Gộp N lần chạy -> trung vị + xếp hạng + spread (để biết số có đáng tin không).
function aggregate(runs) {
  const out = {};
  for (const metric of Object.keys(THRESHOLDS)) {
    const vals = (runs || []).map((r) => (r || {})[metric]).filter((x) => typeof x === 'number');
    const med = median(vals);
    out[metric] = {
      median: med,
      rating: rate(metric, med),
      runs: vals.length,
      min: vals.length ? Math.min(...vals) : null,
      max: vals.length ? Math.max(...vals) : null,
      // spread rộng = số nhiễu, đừng tin chắc. Báo ra để người đọc tự giảm niềm tin.
      unstable: vals.length >= 2 && med > 0 && (Math.max(...vals) - Math.min(...vals)) > med,
    };
  }
  return out;
}

// ── Verdict ──
// Ngưỡng "good" của Google LÀ mốc đạt. Không đạt = FAIL (poor→High, needs-improvement→Medium).
// Vì sao không nới "needs-improvement cho qua": đó là tự hạ chuẩn công bố xuống theo ý mình —
// đúng cái bệnh mà track này sinh ra để tránh. Muốn nới thì phải là quyết định của người, ghi rõ.
const SEV = { poor: 'High', 'needs-improvement': 'Medium' };

// Làm tròn để người ĐỌC được. `0.1804399642965267` là số máy nhả ra, không phải số để báo cáo —
// 16 chữ số thập phân không thêm thông tin nào, chỉ làm dev hiểu là "máy in bừa".
// ms -> số nguyên (lẻ 0.4ms vô nghĩa) · CLS (không đơn vị) -> 3 chữ số (ngưỡng là 0.1/0.25).
function fmt(metric, v) {
  if (typeof v !== 'number' || Number.isNaN(v)) return '—';
  return THRESHOLDS[metric] && THRESHOLDS[metric].unit === 'ms' ? String(Math.round(v)) : String(Math.round(v * 1000) / 1000);
}
function verdict(agg, opts = {}) {
  if (!agg || !Object.keys(agg).length) return '未実施';
  const only = opts.cwvOnly ? Object.keys(THRESHOLDS).filter((m) => THRESHOLDS[m].cwv) : Object.keys(THRESHOLDS);
  const seen = only.map((m) => (agg[m] || {}).rating).filter((r) => r && r !== 'unknown');
  if (!seen.length) return '未実施';                       // không đo được cái nào -> KHÔNG được PASS
  return seen.some((r) => r !== 'good') ? 'FAIL' : 'PASS';
}

function findings(agg, ctx = {}) {
  const out = [];
  for (const [metric, d] of Object.entries(agg || {})) {
    if (!d || d.rating === 'good' || d.rating === 'unknown') continue;
    const t = THRESHOLDS[metric];
    out.push({
      family: 'core-web-vitals',
      metric,
      severity: SEV[d.rating] || 'Medium',
      where: ctx.where || '',
      url: ctx.url || '',
      observed: `${metric} (trung vị ${d.runs} lần chạy) = ${fmt(metric, d.median)}${t.unit} → "${d.rating}". `
        + `Ngưỡng Google: good ≤ ${t.good}${t.unit}, poor > ${t.poor}${t.unit}. `
        + `Dao động ${fmt(metric, d.min)}–${fmt(metric, d.max)}${t.unit}${d.unstable ? ' ⚠️ spread > trung vị: số NHIỄU, đừng tin con số chính xác' : ''}.`,
      fix: `${t.label}. Chuẩn + cách sửa: ${t.src}`,
      shot: ctx.shot || '',
    });
  }
  return out;
}

module.exports = { THRESHOLDS, FIELD_ONLY, rate, median, aggregate, verdict, findings, fmt, SEV };
