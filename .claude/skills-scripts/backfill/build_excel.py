#!/usr/bin/env python3
"""build_excel.py <folder> — ráp Excel evidence 5 SHEET từ các JSON manifest.

  0_SUMMARY   ← summary.json   (sếp đọc rồi call khách — ngôn ngữ khách hàng, có hyperlink)
  1_DATA      ← data_before/after.json
  2_REPORT    ← REPORT_REGISTRY.json + captures.json + exports_<phase>.json  (+ banner coverage)
  3_CHUCNANG  ← FUNC_CASES.json + bugs.json.cases + captures.json            (+ banner coverage)
  4_BUGS      ← bugs.json.bugs (ảnh UI thật trước, panel kỹ thuật sau)

Generic, ko hardcode branch. Ưu tiên ảnh *_ann.png. notes.json (người sửa tay) được merge vào cột
Status/Note — build lại KHÔNG xoá ghi chú người review.
"""
import json, sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage

folder = Path(sys.argv[1])
SK = Path(__file__).resolve().parent.parent.parent / "skills" / "backfill"


def rj(p, d):
    return json.loads(p.read_text()) if p.exists() else d


cfg = json.loads((folder / "config.json").read_text())
caps = rj(folder / "captures.json", {"before": [], "after": []})
db_b = rj(folder / "data_before.json", {})
db_a = rj(folder / "data_after.json", {})
bugs = rj(folder / "bugs.json", {"bugs": [], "cases": []})
notes = rj(folder / "notes.json", {})
summary = rj(folder / "summary.json", {})
registry = rj(SK / "REPORT_REGISTRY.json", {"reports": []})["reports"]
func_cases = rj(SK / "FUNC_CASES.json", {"cases": []})["cases"]
exp_b = rj(folder / "exports_before.json", {})
exp_a = rj(folder / "exports_after.json", rj(folder / "exports.json", {}))

NAVY, BLUE, LBLUE, WHITE = "1F3864", "2E75B6", "D6E4F0", "FFFFFF"
NOTE_BG, PASS_BG, PASS_TX, FAIL_BG, FAIL_TX, RED = "FFFBE6", "E2EFDA", "375623", "FCE4E4", "9C0006", "C00000"
WARN_BG, WARN_TX, GREY = "FFF2CC", "7F6000", "F2F2F2"
FN = "Arial Unicode MS"
thin = Side(style="thin", color="D0D0D0")
BORDER = Border(thin, thin, thin, thin)


def F(sz=11, b=False, c="000000"):
    return Font(name=FN, size=sz, bold=b, color=c)


def fill(c):
    return PatternFill("solid", fgColor=c)


def ann_or(f):
    if not f:
        return None
    p = Path(f); a = p.with_name(p.stem + "_ann.png")
    return str(a) if a.exists() else (str(p) if p.exists() else None)


def embed(ws, f, cell, mw=560, mh=360):
    if not f or not Path(f).exists():
        ws[cell] = "[thiếu ảnh]"; ws[cell].font = F(9, c="999999"); return 0
    with PILImage.open(f) as im:
        w, h = im.size
    s = min(mw / w, mh / h, 1.0)
    xi = XLImage(f); xi.width, xi.height = int(w * s), int(h * s)
    ws.add_image(xi, cell)
    return int(h * s)


def setw(ws, widths=None):
    for i, col in enumerate("ABCDEF"):
        ws.column_dimensions[col].width = (widths[i] if widths and i < len(widths) else 30)


def header(ws, title, sub, color=NAVY):
    ws.merge_cells("A1:F1"); ws["A1"] = title
    ws["A1"].font = F(15, True, WHITE); ws["A1"].fill = fill(color)
    ws["A1"].alignment = Alignment("left", "center", indent=1); ws.row_dimensions[1].height = 32
    ws.merge_cells("A2:F2"); ws["A2"] = sub
    ws["A2"].font = F(10, False, NAVY); ws["A2"].fill = fill(LBLUE)
    ws["A2"].alignment = Alignment("left", "center", wrap_text=True, indent=1); ws.row_dimensions[2].height = 26


def bar(ws, r, text, bg=BLUE, tx=WHITE, sz=12, h=24):
    ws.merge_cells(f"A{r}:F{r}"); c = ws[f"A{r}"]; c.value = text
    c.font = F(sz, True, tx); c.fill = fill(bg)
    c.alignment = Alignment("left", "center", wrap_text=True, indent=1); ws.row_dimensions[r].height = h
    return r + 1


def para(ws, r, text, bg=NOTE_BG, tx="000000", mono=False):
    ws.merge_cells(f"A{r}:F{r}"); c = ws[f"A{r}"]; c.value = text
    c.font = Font(name="Menlo", size=9) if mono else F(10, False, tx)
    c.fill = fill(bg); c.alignment = Alignment("left", "top", wrap_text=True, indent=1)
    ws.row_dimensions[r].height = max(26, (len(str(text)) // 95 + str(text).count("\n") + 1) * 15)
    return r + 1


def table(ws, r, rows, widths=None, head_bg=NAVY):
    """rows[0] = header. Mỗi row là list; cột cuối cùng auto-màu theo ✅/❌."""
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = ws.cell(row=r, column=j + 1, value=("" if val is None else str(val)))
            cell.border = BORDER
            cell.alignment = Alignment("left", "center" if i == 0 else "top", wrap_text=True, indent=1)
            if i == 0:
                cell.font = F(10, True, WHITE); cell.fill = fill(head_bg)
            else:
                s = " ".join(str(x) for x in row)
                cell.font = F(10)
                cell.fill = fill(PASS_BG if "✅" in s else (FAIL_BG if ("❌" in s or "🔴" in s) else (WARN_BG if "⚠️" in s else WHITE)))
        ws.row_dimensions[r].height = max(24, (max(len(str(v or "")) for v in row) // 40 + 1) * 15)
        r += 1
    return r


def imgpair(ws, r, label_b, label_a, fb, fa, mw=560, mh=360):
    ws.merge_cells(f"A{r}:C{r}"); ws.merge_cells(f"D{r}:F{r}")
    ws[f"A{r}"] = label_b; ws[f"D{r}"] = label_a
    for cc in (f"A{r}", f"D{r}"):
        ws[cc].font = F(10, True, NAVY); ws[cc].fill = fill(LBLUE)
        ws[cc].alignment = Alignment("center", "center")
    ws.row_dimensions[r].height = 16; r += 1
    hb = embed(ws, fb, f"A{r}", mw, mh); ha = embed(ws, fa, f"D{r}", mw, mh)
    ws.row_dimensions[r].height = max(hb, ha, 30) * 0.78 + 8
    return r + 1


# ---------- manifest lookup ----------
def entry(sheet, screen, phase):
    for e in caps.get(phase, []):
        if e.get("sheet") == sheet and e.get("screen") == screen:
            return e
    return None


def files_for(sheet, screen):
    b, a = entry(sheet, screen, "before"), entry(sheet, screen, "after")
    return b, a


def xlsx_metric(path_str):
    """Đọc file xlsx export → (số dòng, tổng cột 販売金額 nếu tìm được). Không tìm được thì trả None,
    KHÔNG bịa số."""
    if not path_str or not Path(path_str).exists():
        return None
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path_str, data_only=True, read_only=True)
        ws = wb.worksheets[0]
        rows = list(ws.iter_rows(values_only=True))
        col = None
        hdr_i = None
        for i, row in enumerate(rows[:8]):
            for j, v in enumerate(row or []):
                if v and "販売金額" in str(v):
                    col, hdr_i = j, i
                    break
            if col is not None:
                break
        total = None
        if col is not None:
            total = 0
            for row in rows[hdr_i + 1:]:
                v = row[col] if row and len(row) > col else None
                if isinstance(v, (int, float)):
                    total += v
        return {"rows": max(0, len(rows) - 1), "sales_total": total, "size": Path(path_str).stat().st_size}
    except Exception as e:
        return {"rows": None, "sales_total": None, "error": str(e)[:60]}


wb = Workbook()
BR = cfg["branch_id"]; NM = cfg.get("branch_name_jp", ""); SOT = cfg["sot"]
DIR = "Ticket→Pro" if SOT == "ticket_app" else "Pro→Ticket"
SRC, DST = ("Ticket App", "Pro") if SOT == "ticket_app" else ("Pro", "Ticket App")
Rb, Ra = db_b.get("rails", {}), db_a.get("rails", {})
Db, Da = db_b.get("django", {}), db_a.get("django", {})
anchors = {}   # key → (sheet_name, row)


# ⛔ A-8 (2026-07-29): group text trong FUNC_CASES.json HARDCODE giả định chiều sot=ticket_app
# (nhóm A app=ticket luôn ghi "NGUỒN", nhóm B app=pro luôn ghi "ĐÍCH"). Với sot=pro thì NGƯỢC LẠI —
# branch 66 (sot=pro) từng xuất Excel với nhãn nguồn/đích SAI. App vật lý của case (ticket/pro) không
# đổi (route Django luôn nằm ở Ticket app) — chỉ VAI TRÒ (nguồn tạo vé / đích nhận vé) đổi theo SOT.
def group_label(c):
    g = c.get("group", "")
    # Chỉ nhóm A/B (thuần 1 hệ, do ticket_app hoặc pro tạo vé) mới cần lật vai trò theo SOT.
    # Nhóm E (VÉ MỚI CÓ DÙNG ĐƯỢC KHÔNG) trộn cả 2 hệ trong 1 nhóm — không có 1 vai trò duy nhất
    # để lật, giữ nguyên chữ gốc.
    if not (g.startswith("A ·") or g.startswith("B ·")):
        return g
    app = c.get("app")
    if app == "ticket":
        role = "NGUỒN (tạo vé)" if SOT == "ticket_app" else "ĐÍCH (được sync qua)"
        letter = g.split("·", 1)[0].strip() if "·" in g else "A"
        return f"{letter} · Bên {role} — Ticket app"
    if app == "pro":
        role = "ĐÍCH (được sync qua)" if SOT == "ticket_app" else "NGUỒN (tạo vé)"
        letter = g.split("·", 1)[0].strip() if "·" in g else "B"
        return f"{letter} · Bên {role} — Pro"
    return g

# =====================================================================================
# 1_DATA
# =====================================================================================
ws = wb.active; ws.title = "1_DATA"; setw(ws)
header(ws, f"TẦNG 1 — DATA · Backfill {cfg['institute_code']} branch {BR} ({NM}) · {DIR} (sot={SOT})",
       f"noop={db_a.get('noop', db_b.get('noop'))}. Vé mồ côi phải về 0 · vé cũ được archive · "
       f"Σprice (tính CẢ vé archived) phải BẤT BIẾN = doanh thu không đổi.")
r = 4
inv_ok = Rb.get("rails_all_price") == Ra.get("rails_all_price") and Ra.get("rails_all_price") is not None
rows = [("Đại lượng", "TRƯỚC", "SAU", "Nhận xét", "", ""),
        ("Vé mồ côi bên Ticket (Django)", Db.get("dj_candidates", "?"), Da.get("dj_candidates", "?"), "phải về 0", "", ""),
        ("Vé mồ côi bên Pro (Rails)", Rb.get("rails_candidates", "?"), Ra.get("rails_candidates", "?"), "phải về 0", "", ""),
        ("Vé đã archive bên Pro", Rb.get("rails_archived", "?"), Ra.get("rails_archived", "?"), "tăng = đã khoá vé cũ", "", ""),
        ("Σprice vé active bên Pro", Rb.get("rails_active_price", "?"), Ra.get("rails_active_price", "?"), "có thể giảm (vé cũ bị khoá)", "", ""),
        ("Σprice CẢ archived bên Pro — BẤT BIẾN", Rb.get("rails_all_price", "?"), Ra.get("rails_all_price", "?"),
         "✅ giữ nguyên" if inv_ok else "❌ ĐÃ ĐỔI — phải điều tra", "", ""),
        ("Vé mới đã sync sang Pro", Db.get("dj_new_synced_pro", "?"), Da.get("dj_new_synced_pro", "?"), "= số vé tạo lại", "", "")]
r = table(ws, r, rows)
r += 1
b, a = files_for("1_DATA", "bf_row")
if b or a:
    e = b or a
    r = bar(ws, r, f"1.1  Dòng branch trên màn backfill — {e.get('note', '')}")
    r = imgpair(ws, r, "① TRƯỚC", "② SAU", ann_or(b.get("file")) if b else None, ann_or(a.get("file")) if a else None)

# =====================================================================================
# 2_REPORT — theo REPORT_REGISTRY
# =====================================================================================
ws2 = wb.create_sheet("2_REPORT"); setw(ws2)
header(ws2, "TẦNG 2 — BÁO CÁO (tiền có đổi không?)",
       f"Soi ĐỦ {len(registry)} báo cáo trong PHASE7_BAO_CAO_ANH_HUONG.md ∪ route thật. "
       f"Mọi TỔNG 販売金額 phải GIỮ NGUYÊN. Số LƯỢNG vé tăng là đúng; số TIỀN tăng là SAI.")
r = 4
have_rep = set()
STATUS_TX = {"OK": "✅ dùng giá gốc", "WARN": "⚠️ hiển thị dễ gây hiểu nhầm, tổng KHÔNG sai",
             "FIXED": "🔧 đã sửa code", "SAFE": "✅ đã xác minh an toàn",
             "NA": "➖ không liên quan giá vé", "EXTRA": "➕ PHASE7 bỏ sót — vẫn soi"}
idx = 0
for rg in registry:
    idx += 1
    key = rg["key"]
    b, a = files_for("2_REPORT", key)
    anchors[f"rep_{key}"] = ("2_REPORT", r)
    r = bar(ws2, r, f"2.{idx}  [{rg['system'].upper()}] {rg['name_vi']} — {rg['name_jp']}")
    r = para(ws2, r, f"🔗 {rg['url']}   ·   {STATUS_TX.get(rg['phase7_status'], rg['phase7_status'])}", bg=LBLUE, tx="1F3864")
    r = para(ws2, r, f"📌 PHASE7: {rg['phase7_note']}")
    if rg.get("capture") == "ref":
        r = para(ws2, r, f"🖼 Ảnh xem ở sheet 3_CHUCNANG (case {rg.get('ref', '')}) — cùng một màn, không chụp lại.", bg=GREY)
        if entry("3_CHUCNANG", rg.get("ref", ""), "before") or entry("3_CHUCNANG", rg.get("ref", ""), "after"):
            have_rep.add(key)
    elif rg.get("capture") == "xlsx":
        mb = xlsx_metric((exp_b.get(f"{rg['xlsx_name']}_before.xlsx") or {}).get("file"))
        ma = xlsx_metric((exp_a.get(f"{rg['xlsx_name']}_after.xlsx") or {}).get("file")
                         or (exp_a.get(f"{rg['xlsx_name']}_after.xlsx") or {}).get("file"))
        def fmt(m):
            if not m: return "chưa sinh được file"
            t = m.get("sales_total")
            return (f"{m.get('rows')} dòng · 販売金額 tổng = " + (f"{t:,.0f}" if isinstance(t, (int, float)) else "KHÔNG tìm thấy cột 販売金額")
                    + f" · {m.get('size', 0):,} bytes")
        same = mb and ma and mb.get("sales_total") == ma.get("sales_total") and mb.get("sales_total") is not None
        # Khác nhau thì phải NÓI RÕ khác bao nhiêu và VÌ SAO, đừng ghi "chưa đối chiếu được" cho xong.
        if mb and ma and not same and isinstance(mb.get("sales_total"), (int, float)) and isinstance(ma.get("sales_total"), (int, float)):
            d_row = (ma.get("rows") or 0) - (mb.get("rows") or 0)
            d_sum = ma["sales_total"] - mb["sales_total"]
            concl = (f"⚠️ Số dòng {d_row:+,} · tiền trong file {d_sum:+,.0f}. "
                     f"KHÔNG phải mất tiền: các vé CŨ đã khoá không còn được xuất ra file nữa (để 1 khách "
                     f"không hiện 2 vé cho cùng số buổi). Tiền tổng của cơ sở vẫn nguyên — xem sheet 1_DATA.")
        elif same:
            concl = "✅ tổng tiền trong file GIỮ NGUYÊN"
        elif mb and ma:
            concl = "⚠️ có cả 2 file nhưng không đọc được cột 販売金額 để so — cần mở file xem tay"
        elif mb:
            concl = "⏳ mới có bản TRƯỚC (chưa migrate)"
        else:
            concl = "❌ thiếu file"
        r = table(ws2, r, [("File xlsx thật", "TRƯỚC", "SAU", "Kết luận", "", ""),
                           (rg["xlsx_name"] + ".xlsx", fmt(mb), fmt(ma), concl, "", "")])
        if mb or ma:
            have_rep.add(key)
    elif rg.get("capture") == "download":
        lb = (b or {}).get("csv_lines"); la = (a or {}).get("csv_lines")
        okdl = (b or {}).get("csv") or (a or {}).get("csv")
        r = table(ws2, r, [("File CSV thật", "TRƯỚC", "SAU", "Kết luận", "", ""),
                           (f"{key}.csv", f"{lb} dòng" if lb else "chưa tải được",
                            f"{la} dòng" if la else "chưa tải được",
                            ("✅ tải được, số dòng ghi rõ" if okdl else "❌ chưa tải được file"), "", "")])
        if okdl:
            have_rep.add(key)
        else:
            r = para(ws2, r, f"❌ {(a or b or {}).get('note', 'không tải được CSV')}", bg=FAIL_BG, tx=FAIL_TX)
    else:
        fb = ann_or(b.get("file")) if b and b.get("file") else None
        fa = ann_or(a.get("file")) if a and a.get("file") else None
        if fb or fa:
            if rg.get("diff_explain"):
                r = para(ws2, r, f"👉 Khác biệt trước/sau, nói dễ hiểu: {rg['diff_explain']}", bg=NOTE_BG)
            r = imgpair(ws2, r, "① TRƯỚC", "② SAU", fb, fa)
            have_rep.add(key)
        else:
            why = (a or b or {}).get("note", "")
            r = para(ws2, r, f"❌ 未撮影 — CHƯA CHỤP ĐƯỢC MÀN NÀY. {why}", bg=FAIL_BG, tx=FAIL_TX)
    r += 1

miss_rep = [rg["key"] for rg in registry if rg["key"] not in have_rep]
r = bar(ws2, r, (f"COVERAGE BÁO CÁO: {len(have_rep)}/{len(registry)} ✅ ĐỦ" if not miss_rep
                 else f"COVERAGE BÁO CÁO: {len(have_rep)}/{len(registry)} ❌ THIẾU {len(miss_rep)}: {', '.join(miss_rep)}"),
           bg=(PASS_BG if not miss_rep else RED), tx=(PASS_TX if not miss_rep else WHITE), sz=12, h=30)

# =====================================================================================
# 3_CHUCNANG — mọi flow đụng vé, mỗi case có ảnh
# =====================================================================================
ws3 = wb.create_sheet("3_CHUCNANG"); setw(ws3, [26, 34, 34, 18, 28, 20])
header(ws3, "TẦNG 3 — CHỨC NĂNG (sau khi đồng bộ, mọi thứ còn chạy không?)",
       f"Phủ {len(func_cases)} flow đụng vé ở CẢ 2 HỆ + app khách + đường sync. "
       f"Vé được tạo lại: price=0 (không tính doanh thu mới), không gắn booking → đây là các đường dễ vỡ nhất. "
       f"Mỗi case có ảnh TRƯỚC/SAU bên dưới bảng.")
r = 4
scored = {c["id"]: c for c in bugs.get("cases", [])}
VERDICT_TX = {"observed-PASS": "✅ CHẠY TỐT (đã chạy + thấy)", "observed-API": "✅ ĐÚNG (kiểm ở tầng API)",
              "observed-FAIL": "🔴 LỖI (đã chạy + thấy lỗi)", "ui-only": "✅ màn mở bình thường (chấm bằng ảnh)",
              "traced-only": "⚠️ chỉ đọc code, CHƯA chạy", "未実施": "⚠️ chưa kiểm được"}


def case_http(cid, phase=None):
    phs = (phase,) if phase else ("before", "after")
    codes = [e.get("http") for ph in phs for e in caps.get(ph, [])
             if e.get("sheet") == "3_CHUCNANG" and str(e.get("screen", "")).startswith(f"func_{cid}")
             and isinstance(e.get("http"), int) and e["http"] > 0]
    return max(codes) if codes else None


def verdict_label(cid, v):
    """'ui-only' + HTTP >= 400 thì KHÔNG được ghi 'màn mở bình thường' (A1 lỗi 500 mà báo OK là sai)."""
    if v == "ui-only":
        h = case_http(cid)
        if h is not None and h >= 400:
            hb = case_http(cid, "before")
            pre = " — lỗi CÓ TRƯỚC khi đồng bộ, không do việc đồng bộ" if (hb and hb >= 400) else ""
            return f"🔴 MÀN LỖI (HTTP {h}){pre}"
        return f"✅ màn mở bình thường (HTTP {h})" if h else VERDICT_TX[v]
    return VERDICT_TX.get(v, v)
r = para(ws3, r, "Cách đọc: mỗi case gồm 1 bảng (kiểm cái gì · quan sát được gì · kết luận) và NGAY BÊN DƯỚI "
                 "là ảnh TRƯỚC/SAU của chính case đó. Vùng khoanh đỏ có số ①②③ = chỗ đã đổi; đọc dòng chữ "
                 "vàng dưới ảnh để biết đổi cái gì và nghĩa là gì.", bg=LBLUE, tx="1F3864")
r += 1

# ảnh từng case.
# ⚠️ Chỉ case có UI mới bị đòi ảnh. Case driver='code'/'api' (vd dùng buổi qua service, kiểm outbox,
# app khách chưa login được) KHÔNG có màn nào để chụp → đòi ảnh là đòi thứ không tồn tại, và tệ hơn
# là dụ người ta dựng ảnh giả. Chúng được chấm bằng kết quả CHẠY THẬT ở confirm_bugs.py.
ui_cases = [c for c in func_cases if "ui" in (c.get("driver") or "")]
code_cases = [c for c in func_cases if "ui" not in (c.get("driver") or "")]
have_func = set()
last_group = None
for c in func_cases:
    cid = c["id"]
    screens = sorted({e["screen"] for ph in ("before", "after") for e in caps.get(ph, [])
                      if e.get("sheet") == "3_CHUCNANG" and (e.get("screen") == f"func_{cid}" or e.get("screen", "").startswith(f"func_{cid}_"))})
    if c.get("group") != last_group:
        r = bar(ws3, r, f"■ {group_label(c)}", bg=NAVY, sz=13, h=26)
        last_group = c.get("group")
    anchors[f"func_{cid}"] = ("3_CHUCNANG", r)
    sc = scored.get(cid, {})
    ov = (notes.get("func", {}).get(cid, {}) or {})
    v = sc.get("verdict", "未実施")
    vlabel = verdict_label(cid, v)
    r = bar(ws3, r, f"{cid}  {c['name_vi']} ({c['name_jp']})  —  {vlabel}",
            bg=(RED if (v == "observed-FAIL" or vlabel.startswith("🔴")) else BLUE))
    # bảng của RIÊNG case này, ảnh nằm ngay bên dưới (không dồn hết ảnh xuống cuối sheet)
    r = table(ws3, r, [("Kiểm cái gì / kỳ vọng", "Quan sát được gì", "", "Kết luận", "Status", "Note"),
                       (f"{c['mechanism']}\n→ kỳ vọng: {c['expect']}",
                        sc.get("observed", "chưa có dữ liệu quan sát"), "",
                        vlabel, ov.get("status", ""), ov.get("note", ""))])
    if c.get("diff_explain"):
        r = para(ws3, r, f"👉 Khác biệt trước/sau, nói dễ hiểu: {c['diff_explain']}", bg=NOTE_BG)
    if not screens:
        if c in code_cases:
            r = para(ws3, r, f"⚙️ Case này KHÔNG có màn UI để chụp (driver={c.get('driver')}) — chấm bằng CHẠY CODE THẬT: "
                             f"{sc.get('observed', 'chưa có dữ liệu')}", bg=GREY)
        else:
            r = para(ws3, r, f"❌ 未撮影 — case CÓ UI mà CHƯA chụp được. Kỳ vọng: {c['expect']}", bg=FAIL_BG, tx=FAIL_TX)
        r += 1
        continue
    got = False
    for s in screens:
        b, a = files_for("3_CHUCNANG", s)
        e = a or b
        ref = (e or {}).get("ref_screen")
        if ref:
            # ref có thể trỏ sang case chức năng khác (func_*) HOẶC sang 1 report ở sheet 2_REPORT
            src_sheet = "3_CHUCNANG" if str(ref).startswith("func_") else "2_REPORT"
            rb, ra = files_for(src_sheet, ref)
            fb = ann_or(rb.get("file")) if rb and rb.get("file") else None
            fa = ann_or(ra.get("file")) if ra and ra.get("file") else None
            r = para(ws3, r, f"🖼 {s} — cùng một màn với {src_sheet}/{ref}, dùng lại ảnh đó (khỏi chụp 2 lần).", bg=GREY)
        else:
            fb = ann_or(b.get("file")) if b and b.get("file") else None
            fa = ann_or(a.get("file")) if a and a.get("file") else None
        if not (fb or fa):
            r = para(ws3, r, f"❌ {s}: {(e or {}).get('note', 'không có ảnh')}", bg=FAIL_BG, tx=FAIL_TX)
            continue
        r = para(ws3, r, f"📌 {(e or {}).get('note', '')}")
        r = imgpair(ws3, r, f"① TRƯỚC ({s})", f"② SAU ({s})", fb, fa)
        got = True
    if got:
        have_func.add(cid)
    r += 1

miss_func = [c["id"] for c in ui_cases if c["id"] not in have_func]
n_ui = len(ui_cases)
scored_code = sum(1 for c in code_cases if scored.get(c["id"], {}).get("verdict"))
r = bar(ws3, r, (f"COVERAGE CHỨC NĂNG: ảnh UI {len(have_func & {c['id'] for c in ui_cases})}/{n_ui} ✅ ĐỦ · "
                 f"case chạy-code {scored_code}/{len(code_cases)} đã chấm · tổng {len(func_cases)} flow"
                 if not miss_func else
                 f"COVERAGE CHỨC NĂNG: ảnh UI {n_ui - len(miss_func)}/{n_ui} ❌ THIẾU: {', '.join(miss_func)} · "
                 f"case chạy-code {scored_code}/{len(code_cases)}"),
           bg=(PASS_BG if not miss_func else RED), tx=(PASS_TX if not miss_func else WHITE), sz=12, h=30)
cl = bugs.get("cleanup", {})
r = para(ws3, r, f"🧹 Dọn dữ liệu test: Pro cleanup={cl.get('rails', '?')} · Ticket rollback={cl.get('django_rollback', '?')} · "
                 f"rác còn sót={cl.get('django_garbage_rows', '?')} (phải = 0). Data test mang marker {bugs.get('mark', 'AIOT-TEST-BF-*')}.",
         bg=(PASS_BG if str(cl.get("django_garbage_rows")) == "0" else WARN_BG))

# ⛔ BANNER RIÊNG — "có ẢNH" ≠ "chạy TRỌN VẸN được người dùng thật xác nhận" (bài học BUG-041: branch
# 66 từng có ảnh UI 17/17 xanh trong khi vé không dùng được — ảnh chỉ chứng minh MÀN MỞ ĐƯỢC, không
# chứng minh THAO TÁC CHẠY ĐƯỢC). "observed-PASS(data-only)" (xem confirm_bugs.py) KHÔNG được tính vào
# end-to-end — nó chỉ chứng minh tầng dữ liệu, không chứng minh nhân viên bấm được.
e2e_total = len(func_cases)
e2e_pass = sum(1 for c in func_cases if scored.get(c["id"], {}).get("verdict") == "observed-PASS")
e2e_data_only = sum(1 for c in func_cases if str(scored.get(c["id"], {}).get("verdict", "")).endswith("(data-only)"))
r = bar(ws3, r, (f"LUỒNG END-TO-END: {e2e_pass}/{e2e_total} case đã XÁC NHẬN người dùng thật làm được "
                 f"(quan sát trực tiếp qua UI/API thật, KHÔNG suy luận)"
                 + (f" · {e2e_data_only} case CHỈ xác nhận ở tầng DỮ LIỆU (data-only, xem cột Status) — "
                    f"KHÔNG được tính là end-to-end" if e2e_data_only else "")
                 + (f" · {e2e_total - e2e_pass - e2e_data_only} case còn lại: FAIL hoặc chưa kiểm được"
                    if e2e_total - e2e_pass - e2e_data_only else "")),
           bg=(PASS_BG if e2e_pass == e2e_total else RED),
           tx=(PASS_TX if e2e_pass == e2e_total else WHITE), sz=12, h=30)

# =====================================================================================
# 4_BUGS — ảnh UI thật trước, panel kỹ thuật sau
# =====================================================================================
ws4 = wb.create_sheet("4_BUGS"); setw(ws4)
header(ws4, f"🚨 BUG đã xác nhận — branch {BR} ({DIR})",
       "Bằng chứng CHÍNH = ảnh UI thật (người dùng thấy gì). Stacktrace/DB để bên dưới, dành cho dev.",
       color=RED)
r = 4
blist = bugs.get("bugs", [])
if not blist:
    r = para(ws4, r, "✅ Không có bug nào được xác nhận trong lần đồng bộ này (hoặc branch trống).", bg=PASS_BG, tx=PASS_TX)
for bug in blist:
    ov = (notes.get("bugs", {}).get(bug["id"], {}) or {})
    anchors[f"bug_{bug['id']}"] = ("4_BUGS", r)
    r = bar(ws4, r, f"{bug['id']} — {bug.get('title', '')}  [mức độ: {bug.get('severity', '')}]", bg=RED, h=26)
    # Gộp who+when+sees thành 1 dòng "Triệu chứng" — 5 dòng rời đọc bị loãng (sếp phản hồi 2026-07-29).
    trieu_chung = " ".join(x for x in [
        f"{bug.get('who', '')}".rstrip(". ") + "." if bug.get("who") else "",
        bug.get("when", ""), bug.get("sees", "")] if x)
    r = table(ws4, r, [("Mục", "Nội dung", "", "Status", "Assignee", "Note"),
                       ("😣 Triệu chứng", trieu_chung or "—", "",
                        ov.get("status", "Mở"), ov.get("assignee", ""), ov.get("note", "")),
                       ("🙋 Ảnh hưởng tới KHÁCH", bug.get("impact_customer", "—"), "", "", "", ""),
                       ("🩹 Cách xoay xở tạm", bug.get("workaround", "—"), "", "", "", "")])

    # ── CÁCH TÁI HIỆN — để người khác (sếp/dev) tự làm lại bằng tay, không phải đoán.
    # Bắt buộc có: URL + account cụ thể (từ DEV-ACCOUNTS.xlsx) + branch + khách/vé mẫu + từng bước.
    rp = bug.get("repro") or {}
    if rp:
        r = bar(ws4, r, "🔁 CÁCH TÁI HIỆN — làm đúng thứ tự dưới đây", bg="1F4E79", h=22)
        meta = [("Mục", "Nội dung", "", "", "", "")]
        for lbl, key in [("🌐 Mở ở đâu", "env"), ("🔑 Đăng nhập bằng", "login"),
                         ("🏥 Chi nhánh", "branch"), ("🧪 Dữ liệu mẫu", "data")]:
            if rp.get(key):
                meta.append((lbl, rp[key], "", "", "", ""))
        r = table(ws4, r, meta)
        for i, step in enumerate(rp.get("steps", []), start=1):
            r = para(ws4, r, f"  Bước {i}. {step}", bg="FFFFFF")
        if rp.get("expect"):
            r = para(ws4, r, f"✅ KỲ VỌNG (đúng ra phải vậy): {rp['expect']}", bg=PASS_BG, tx=PASS_TX)
        if rp.get("actual"):
            r = para(ws4, r, f"❌ THỰC TẾ (quan sát được): {rp['actual']}", bg=WARN_BG, tx=WARN_TX)
        if rp.get("control"):
            r = para(ws4, r, f"🔬 ĐỐI CHỨNG (để loại trừ nghi ngờ): {rp['control']}", bg=GREY)
    ui = bug.get("ui_capture") or []
    if ui:
        r = para(ws4, r, f"🖼 BẰNG CHỨNG UI: {bug.get('ui_note', '')}", bg=LBLUE, tx="1F3864")
        for i, f in enumerate(ui):
            h = embed(ws4, ann_or(f), f"A{r}", mw=1000, mh=380)
            ws4.row_dimensions[r].height = h * 0.78 + 8
            r += 1
    else:
        r = para(ws4, r, f"⚠️ KHÔNG có ảnh UI: {bug.get('ui_note', 'không quan sát được trên UI')}", bg=WARN_BG, tx=WARN_TX)
    r = para(ws4, r, "🔬 Chi tiết kỹ thuật (cho dev):", bg=GREY)
    r = para(ws4, r, bug.get("evidence", ""), bg=GREY, mono=True)
    panel = folder / "after" / f"bug_{bug['id']}.png"
    if panel.exists():
        h = embed(ws4, str(panel), f"A{r}", mw=900, mh=260)
        ws4.row_dimensions[r].height = h * 0.78 + 8
        r += 1
    r += 1

# =====================================================================================
# 0_SUMMARY — sheet đầu tiên (sếp đọc → call khách)
# =====================================================================================
ws0 = wb.create_sheet("0_SUMMARY"); setw(ws0, [30, 24, 24, 34, 22, 18])
S = summary


def link(ws, r, col, text, key):
    """Ô hyperlink nội bộ tới sheet khác."""
    tgt = anchors.get(key)
    cell = ws.cell(row=r, column=col, value=text)
    if tgt:
        cell.hyperlink = f"#'{tgt[0]}'!A{tgt[1]}"
        cell.font = Font(name=FN, size=10, color="1155CC", underline="single")
    else:
        cell.font = F(10)
    cell.border = BORDER
    cell.alignment = Alignment("left", "top", wrap_text=True, indent=1)


header(ws0, f"BÁO CÁO ĐỒNG BỘ DỮ LIỆU VÉ — {NM} (branch {BR} · {cfg['institute_code']})",
       "Sheet này viết cho người KHÔNG làm kỹ thuật. Chi tiết + ảnh ở các sheet sau (bấm vào link màu xanh để nhảy tới).")
r = 4
r = bar(ws0, r, "① KẾT LUẬN", bg=NAVY, sz=13, h=26)
r = para(ws0, r, S.get("headline", "(chưa chạy summarize.py)"),
         bg=(PASS_BG if not S.get("bugs") else WARN_BG), tx=(PASS_TX if not S.get("bugs") else WARN_TX))
r += 1

r = bar(ws0, r, "② CHÚNG TÔI ĐÃ LÀM GÌ", bg=NAVY, sz=13, h=26)
d = S.get("did", {})
r = para(ws0, r, d.get("direction_vi", ""), bg=NOTE_BG)
r = table(ws0, r, [("Nội dung", "Số liệu", "", "Giải thích", "", ""),
                   ("Cơ sở được xử lý", d.get("branch", ""), "", "", "", ""),
                   ("Chiều đồng bộ", d.get("direction", ""), "", f"Bản chuẩn lấy từ {S.get('src', '')}", "", ""),
                   ("Vé lẻ trước khi làm", f"Ticket {d.get('orphan_before', {}).get('ticket_app', '?')} · Pro {d.get('orphan_before', {}).get('pro', '?')}", "",
                    "Vé chỉ tồn tại ở 1 bên → 2 hệ không khớp nhau", "", ""),
                   ("Vé lẻ sau khi làm", f"Ticket {d.get('orphan_after', {}).get('ticket_app', '?')} · Pro {d.get('orphan_after', {}).get('pro', '?')}", "",
                    "Phải về 0 = 2 hệ đã khớp", "", ""),
                   ("Số vé được tạo lại", d.get("packs_created", "?"), "", f"Tạo bên {S.get('dst', '')} tương ứng vé cũ", "", ""),
                   ("Số vé cũ được khoá lại", d.get("packs_archived", "?"), "", "Khoá để không bị tính 2 lần, KHÔNG xoá dữ liệu", "", ""),
                   ("Trạng thái", d.get("status", "?"), "", "", "", "")])
r += 1

r = bar(ws0, r, "③ ẢNH HƯỞNG TỚI KHÁCH HÀNG", bg=NAVY, sz=13, h=26)
rows = [("Cái gì của khách", "TRƯỚC", "SAU", "Nghĩa là gì với khách", "Kết luận", "")]
for it in S.get("impact", []):
    rows.append((it["what"], it["before"], it["after"], it["means"], "✅ không ảnh hưởng" if it["ok"] else "⚠️ cần đọc mục ⑤", ""))
r = table(ws0, r, rows)
r += 1

r = bar(ws0, r, "④ NHỮNG PHẦN VẪN CHẠY BÌNH THƯỜNG (đã kiểm từng cái, có ảnh)", bg=NAVY, sz=13, h=26)
ws0.cell(row=r, column=1, value="Chức năng").font = F(10, True, WHITE)
for j, h in enumerate(["Chức năng", "Kết quả quan sát", "", "Xem ảnh ở đâu", "Status", "Note"]):
    c = ws0.cell(row=r, column=j + 1, value=h); c.font = F(10, True, WHITE); c.fill = fill(NAVY)
    c.border = BORDER; c.alignment = Alignment("left", "center", indent=1)
r += 1
if not S.get("works"):
    r = para(ws0, r, "(chưa có case nào được chấm PASS — xem sheet 3_CHUCNANG)", bg=WARN_BG)
for w in S.get("works", []):
    ws0.cell(row=r, column=1, value=f"{w['id']} {w['name']}")
    ws0.cell(row=r, column=2, value=w["observed"][:300])
    link(ws0, r, 4, f"→ 3_CHUCNANG {w['id']}", f"func_{w['id']}")
    ws0.cell(row=r, column=5, value=w.get("status", ""))
    ws0.cell(row=r, column=6, value=w.get("note", ""))
    for j in (1, 2, 3, 5, 6):
        c = ws0.cell(row=r, column=j); c.border = BORDER; c.font = F(10)
        c.fill = fill(PASS_BG); c.alignment = Alignment("left", "top", wrap_text=True, indent=1)
    ws0.row_dimensions[r].height = max(24, (len(w["observed"][:300]) // 40 + 1) * 14)
    r += 1
r += 1

r = bar(ws0, r, "⑤ NHỮNG ĐIỂM CẦN BIẾT (lệch / chưa kiểm được / là bug)", bg=RED, sz=13, h=26)
for j, h in enumerate(["Nội dung", "Quan sát được gì", "", "Đọc chi tiết ở đâu", "Status", "Note"]):
    c = ws0.cell(row=r, column=j + 1, value=h); c.font = F(10, True, WHITE); c.fill = fill(RED)
    c.border = BORDER; c.alignment = Alignment("left", "center", indent=1)
r += 1
if not S.get("deviations") and not S.get("bugs"):
    r = para(ws0, r, "✅ Không có điểm nào cần lưu ý.", bg=PASS_BG, tx=PASS_TX)
for b in S.get("bugs", []):
    ws0.cell(row=r, column=1, value=f"🔴 {b['id']} {b['title']} (mức độ {b['severity']})")
    ws0.cell(row=r, column=2, value="LÀ BUG — đã xác nhận bằng cách chạy thật." + ("" if b["has_ui"] else " (không có ảnh UI, xem chi tiết kỹ thuật)"))
    link(ws0, r, 4, f"→ 4_BUGS {b['id']}", f"bug_{b['id']}")
    ws0.cell(row=r, column=5, value=b.get("status", "Mở"))
    ws0.cell(row=r, column=6, value=b.get("note", ""))
    for j in (1, 2, 3, 5, 6):
        c = ws0.cell(row=r, column=j); c.border = BORDER; c.font = F(10); c.fill = fill(FAIL_BG)
        c.alignment = Alignment("left", "top", wrap_text=True, indent=1)
    r += 1
for dv in S.get("deviations", []):
    is_bug = dv["verdict"] == "observed-FAIL"
    ws0.cell(row=r, column=1, value=f"{'🔴' if is_bug else '⚠️'} {dv['id']} {dv['name']}")
    ws0.cell(row=r, column=2, value=dv["observed"][:300])
    if dv.get("link_sheet") == "2_REPORT":
        link(ws0, r, 4, f"→ 2_REPORT {dv['id']}", f"rep_{dv['id']}")
    else:
        link(ws0, r, 4, f"→ {dv.get('link_sheet', '3_CHUCNANG')} {dv['id']}", f"func_{dv['id']}")
    ws0.cell(row=r, column=5, value=dv.get("status", "") or ("Mở" if is_bug else "Cần xác nhận"))
    ws0.cell(row=r, column=6, value=dv.get("note", ""))
    for j in (1, 2, 3, 5, 6):
        c = ws0.cell(row=r, column=j); c.border = BORDER; c.font = F(10)
        c.fill = fill(FAIL_BG if is_bug else WARN_BG)
        c.alignment = Alignment("left", "top", wrap_text=True, indent=1)
    ws0.row_dimensions[r].height = max(24, (len(dv["observed"][:300]) // 40 + 1) * 14)
    r += 1
r += 1

r = bar(ws0, r, "⑥ CHÚNG TÔI ĐÃ XỬ LÝ NHỮNG GÌ", bg=NAVY, sz=13, h=26)
rows = [("Phần đã sửa", "Sửa cái gì (nói dễ hiểu)", "", "Đã kiểm thế nào", "File code", "")]
for f_ in S.get("fixes", []):
    rows.append((f_["what"], f_["plain"], "", f_["verified"], f_["file"], ""))
r = table(ws0, r, rows)
r = para(ws0, r, "⚠️ LƯU Ý TRƯỚC KHI BÁO KHÁCH:\n" + "\n".join(f"• {c}" for c in S.get("caveats", [])),
         bg=WARN_BG, tx=WARN_TX)
cov = S.get("coverage", {})
r = para(ws0, r, f"Phạm vi kiểm tra: báo cáo {cov.get('reports', {}).get('have', '?')}/{cov.get('reports', {}).get('need', '?')} · "
                 f"chức năng {cov.get('func', {}).get('have', '?')}/{cov.get('func', {}).get('need', '?')} có ảnh · "
                 f"{cov.get('cases_scored', '?')} case được chấm bằng quan sát thật.", bg=LBLUE, tx="1F3864")

# đưa 0_SUMMARY lên đầu
wb.move_sheet("0_SUMMARY", offset=-(len(wb.sheetnames) - 1))

out = folder / f"Backfill_{cfg['institute_code']}_branch{BR}_Evidence.xlsx"
wb.save(out)
print(f"OK build_excel.py → {out}")
print(f"  {len(wb.sheetnames)} sheet: {' · '.join(wb.sheetnames)} | {sum(len(w._images) for w in wb.worksheets)} ảnh")
print(f"  coverage báo cáo {len(have_rep)}/{len(registry)}" + (f" THIẾU: {', '.join(miss_rep)}" if miss_rep else " ✅"))
print(f"  coverage chức năng: ảnh UI {n_ui - len(miss_func)}/{n_ui}" + (f" THIẾU: {', '.join(miss_func)}" if miss_func else " ✅")
      + f" · case chạy-code {scored_code}/{len(code_cases)} đã chấm")
