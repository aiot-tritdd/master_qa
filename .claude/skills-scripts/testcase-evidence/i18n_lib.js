// i18n_lib.js — oracle CƠ KHÍ cho track i18n / Localization (black-box, mù code).
//
// Vì sao track này hợp vision "engine đa dự án": oracle KHÔNG cần ai đặt số, KHÔNG cần baseline.
// Nó neo vào các BẤT BIẾN NGÔN NGỮ phổ quát — đúng vai trò WCAG với a11y, ngưỡng Google với perf:
//
//  ① KEY-LEAK — bản dịch thiếu → app hiện KEY THÔ (`reservation.selectCourse`, `{{title}}`,
//     `__MISSING__`). Không cần chuẩn nào công nhận: key lòi ra màn LÀ hỏng, mọi ngôn ngữ.
//  ② MOJIBAKE — sai encoding → chữ vỡ (`Ã©`, `â€™`, `�`). Cũng là hỏng phổ quát.
//  ③ PARITY — đổi sang locale khác (vd /en/) mà text CHROME vẫn y hệt + còn CJK ⇒ CHƯA DỊCH.
//     Bất biến logic: cùng một nút, ở bản EN phải là tiếng Anh. Không cần chuẩn ngoài.
//  ④ LOCALE-FORMAT — ngày/tiền theo convention sai locale (`2026年…円` trên trang EN). Đây là
//     probe MỀM NHẤT (dễ nhiễu) → v1 chỉ **WARN**, KHÔNG cho thành FAIL. Nới lên FAIL là quyết định
//     của người sau khi đã tin, không phải mặc định.
//
// KIẾN TRÚC (giống security/compat/perf_lib): probe = HÀM THUẦN nhận text ĐÃ TRÍCH + ĐÃ MASK → verdict.
// Driver (inline trong command) mới là chỗ mở browser + trích DOM + mask. Tách vậy để unit-test oracle
// mà không cần dev sống.
//
// ⚠️⚠️ BẪY CHẾT NGƯỜI — data ≠ bản dịch: tên viện `AIoT院1`, tên khách, mã coupon là chữ Nhật HỢP LỆ
// trên trang EN. KHÔNG mask vùng data trước khi đưa vào đây thì probeParity/probeKeyLeak FAIL GIẢ hàng
// loạt (đúng bẫy Visual "màn data-heavy" + Security "/etc/passwd trả cùng vỏ"). ⇒ Driver BẮT BUỘC mask
// bằng `explorer.js dynamic` (visual_lib.detectDynamic) TRƯỚC khi gọi probe. Lib này chỉ soi CHROME text.

// ── CJK: hiragana + katakana + CJK ideograph + halfwidth kana. Dùng để bắt "còn tiếng Nhật trên trang EN". ──
const CJK_RE = /[぀-ヿ一-鿿ｦ-ﾟ]/;

// Key i18n thô: hoặc là chuỗi interpolation chưa render, hoặc là dotted-identifier kiểu code.
const INTERP_RE = /\{\{[^}]*\}\}|\[\[[^\]]*\]\]|\$\{[^}]*\}|__[A-Z0-9_]+__/;

// looksLikeKey(text): trimmed text CÓ PHẢI một key i18n thô không.
// Chống false-positive domain (`example.com` = all-lowercase 1 dot): CHỈ coi là key khi
//   ≥2 dấu chấm (`a.b.c`) HOẶC 1 dấu chấm mà có chữ HOA trong segment (`a.selectCourse` = camelCase key).
// Domain/filename thường all-lowercase 1 dot → KHÔNG dính.
const DOTTED_KEY_RE = /^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$/;
function looksLikeKey(text) {
  const t = String(text == null ? '' : text).trim();
  if (!t) return false;
  if (INTERP_RE.test(t)) return true;
  if (/\s/.test(t)) return false;                 // có khoảng trắng = câu, không phải key
  if (!DOTTED_KEY_RE.test(t)) return false;       // không phải dotted-ident
  const dots = (t.match(/\./g) || []).length;
  if (dots >= 2) return true;                      // a.b.c → key
  return /[A-Z]/.test(t);                          // 1 dot + camelCase (a.fooBar) → key; domain all-lower → không
}

function probeKeyLeak(texts) {
  const arr = (texts || []).map((t) => String(t == null ? '' : t));
  const ran = arr.length > 0;
  const hits = arr.filter((t) => looksLikeKey(t)).map((t) => ({ text: t.trim() }));
  return { ran, hasLeak: hits.length > 0, hits };
}

// ── ② MOJIBAKE ──
// U+FFFD (replacement char) HOẶC dấu vết UTF-8-giải-mã-nhầm-Latin1: một ký tự Latin-1 cao (À-ÿ, À-ÿ
// = lead byte đa-byte bị đọc sai) NGAY SAU đó là ký tự -¿ (continuation-byte / C1). Tổ hợp này
// gần như KHÔNG xuất hiện trong text thật, nhưng LUÔN có trong mojibake.
// → `café` (é=é đứng cuối, không theo sau bởi -¿) KHÔNG dính. `Ã©` (Ã+©) dính.
// → Tiếng Nhật thật (぀+) KHÔNG nằm trong À-ÿ nên không dính.
const MOJIBAKE_RE = /�|[À-ÿ][-¿]/;
function probeMojibake(texts) {
  const arr = (texts || []).map((t) => String(t == null ? '' : t));
  const ran = arr.length > 0;
  const hits = arr.filter((t) => MOJIBAKE_RE.test(t)).map((t) => ({ text: t.trim() }));
  return { ran, hasMojibake: hits.length > 0, hits };
}

// ── ③ PARITY ──
// enTexts / jaTexts = chrome text ĐÃ MASK của trang locale-EN và locale-ja (cùng màn, cùng lúc).
// Untranslated = text chrome trên trang EN còn chứa CJK. (jaTexts để tăng độ tin: xác nhận cùng chuỗi
// xuất hiện ở ja — nhưng data đã mask nên chỉ cần CJK-trên-EN là đủ tín hiệu.)
// < 2 locale → inconclusive (app 1 ngôn ngữ, không có gì để so).
function probeParity(enTexts, jaTexts) {
  const en = (enTexts || []).map((t) => String(t == null ? '' : t).trim()).filter(Boolean);
  const ja = (jaTexts || []).map((t) => String(t == null ? '' : t).trim()).filter(Boolean);
  if (!en.length || !ja.length) {
    return { inconclusive: true, untranslated: [], reason: 'cần ≥2 locale (vd /en/ và ja) mới so được' };
  }
  const untranslated = [...new Set(en.filter((t) => CJK_RE.test(t)))];
  return { inconclusive: false, untranslated };
}

// ── ④ LOCALE-FORMAT (WARN-only) ──
// Trên trang locale KHÔNG-ja (vd 'en'): ngày kanji (年/月/日) hoặc tiền kanji (円) là dấu hiệu format chưa
// địa phương hoá. CHỈ cảnh báo — không kéo verdict xuống FAIL (probe này nhiễu nhất, xem header).
const JP_DATE_RE = /\d{1,4}\s*年|\d{1,2}\s*月|\d{1,2}\s*日/;
const JP_CURRENCY_RE = /\d[\d,]*\s*円/;
function probeLocaleFormat(texts, locale) {
  const arr = (texts || []).map((t) => String(t == null ? '' : t));
  if (locale === 'ja' || locale === 'ja-JP') return { warn: false, hits: [], skipped: true };
  const hits = arr.filter((t) => JP_DATE_RE.test(t) || JP_CURRENCY_RE.test(t)).map((t) => ({ text: t.trim() }));
  return { warn: hits.length > 0, hits };
}

// ── Verdict 1 ô (màn × locale) ──
// 未実施 khi không mở được màn HOẶC không probe nào chạy được (không có text).
// localeFormat CỐ Ý không nằm trong điều kiện FAIL — nó là WARN.
function verdict(r) {
  if (!r || r.reachable === false) return '未実施';
  const failed =
    (r.keyLeak && r.keyLeak.hasLeak) ||
    (r.mojibake && r.mojibake.hasMojibake) ||
    (r.parity && r.parity.inconclusive === false && (r.parity.untranslated || []).length > 0);
  if (failed) return 'FAIL';
  const ran =
    (r.keyLeak && r.keyLeak.ran) ||
    (r.mojibake && r.mojibake.ran) ||
    (r.parity && r.parity.inconclusive === false);
  return ran ? 'PASS' : '未実施';
}

// severity: key-leak / mojibake = lỗi hiển thị rõ ràng (High); untranslated = Medium.
const SEV = { keyLeak: 'High', mojibake: 'High', parity: 'Medium', localeFormat: 'Low' };

function finding({ family, where, url, locale, severity, observed, fix, shot }) {
  return {
    family, where: where || '', url: url || '', locale: locale || '',
    severity: severity || 'Medium', observed: observed || '', fix: fix || '', shot: shot || '',
  };
}

module.exports = {
  CJK_RE, INTERP_RE, MOJIBAKE_RE, DOTTED_KEY_RE, SEV,
  looksLikeKey, probeKeyLeak, probeMojibake, probeParity, probeLocaleFormat, verdict, finding,
};
