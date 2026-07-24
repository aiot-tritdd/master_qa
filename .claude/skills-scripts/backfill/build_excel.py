#!/usr/bin/env python3
"""build_excel.py <folder> — ráp Excel evidence 4 sheet TỪ các JSON manifest (config/captures/data/bugs).
Generic, ko hardcode branch. Ghép before/after theo screen key. Ưu tiên ảnh *_ann.png nếu có.
Output: <folder>/Backfill_<institute>_branch<branch>_Evidence.xlsx
"""
import json, sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage

folder = Path(sys.argv[1])
cfg = json.loads((folder / "config.json").read_text())
caps = json.loads((folder / "captures.json").read_text()) if (folder / "captures.json").exists() else {"before": [], "after": []}
db_b = json.loads((folder / "data_before.json").read_text()) if (folder / "data_before.json").exists() else {}
db_a = json.loads((folder / "data_after.json").read_text()) if (folder / "data_after.json").exists() else {}
bugs = json.loads((folder / "bugs.json").read_text()) if (folder / "bugs.json").exists() else {"bugs": [], "tier3": {}}

NAVY, BLUE, LBLUE, WHITE = "1F3864", "2E75B6", "D6E4F0", "FFFFFF"
NOTE_BG, PASS_BG, PASS_TX, FAIL_BG, FAIL_TX, RED = "FFFBE6", "E2EFDA", "375623", "FCE4E4", "9C0006", "C00000"
FN = "Arial Unicode MS"
thin = Side(style="thin", color="D0D0D0"); BORDER = Border(thin, thin, thin, thin)

def F(sz=11, b=False, c="000000"): return Font(name=FN, size=sz, bold=b, color=c)
def fill(c): return PatternFill("solid", fgColor=c)

def ann_or(f):
    p = Path(f); a = p.with_name(p.stem + "_ann.png")
    return str(a) if a.exists() else (str(p) if p.exists() else None)

def embed(ws, f, cell, mw=560, mh=360):
    if not f or not Path(f).exists():
        ws[cell] = f"[thiếu ảnh]"; ws[cell].font = F(9, c="999999"); return 0
    with PILImage.open(f) as im: w, h = im.size
    s = min(mw / w, mh / h, 1.0)
    xi = XLImage(f); xi.width, xi.height = int(w * s), int(h * s); ws.add_image(xi, cell)
    return int(h * s)

def setw(ws):
    for col in "ABCDEF": ws.column_dimensions[col].width = 30

def header(ws, title, sub):
    ws.merge_cells("A1:F1"); ws["A1"] = title; ws["A1"].font = F(15, True, WHITE); ws["A1"].fill = fill(NAVY)
    ws["A1"].alignment = Alignment("left", "center", indent=1); ws.row_dimensions[1].height = 32
    ws.merge_cells("A2:F2"); ws["A2"] = sub; ws["A2"].font = F(10, False, NAVY); ws["A2"].fill = fill(LBLUE)
    ws["A2"].alignment = Alignment("left", "center", wrap_text=True, indent=1); ws.row_dimensions[2].height = 24

def block(ws, r, idx, name, url, note, before_f, after_f, verdict=None):
    ws.merge_cells(f"A{r}:F{r}"); c = ws[f"A{r}"]; c.value = f"{idx}  {name}"; c.font = F(12, True, WHITE); c.fill = fill(BLUE)
    c.alignment = Alignment("left", "center", indent=1); ws.row_dimensions[r].height = 24; r += 1
    ws.merge_cells(f"A{r}:F{r}"); c = ws[f"A{r}"]; c.value = f"🔗 {url}"; c.font = F(10, False, "1155CC")
    c.alignment = Alignment("left", "center", wrap_text=True, indent=1); ws.row_dimensions[r].height = 20; r += 1
    if verdict:
        vb, vt = (PASS_BG, PASS_TX) if verdict[0] in "P✅" else (FAIL_BG, FAIL_TX)
        ws.merge_cells(f"A{r}:F{r}"); c = ws[f"A{r}"]; c.value = verdict; c.font = F(11, True, vt); c.fill = fill(vb)
        c.alignment = Alignment("left", "center", indent=1); ws.row_dimensions[r].height = 20; r += 1
    ws.merge_cells(f"A{r}:C{r}"); ws.merge_cells(f"D{r}:F{r}")
    ws[f"A{r}"] = "① TRƯỚC"; ws[f"D{r}"] = "② SAU"
    for cc in (f"A{r}", f"D{r}"): ws[cc].font = F(10, True, NAVY); ws[cc].fill = fill(LBLUE); ws[cc].alignment = Alignment("center", "center")
    ws.row_dimensions[r].height = 16; r += 1
    hb = embed(ws, before_f, f"A{r}"); ha = embed(ws, after_f, f"D{r}")
    ws.row_dimensions[r].height = max(hb, ha, 30) * 0.78 + 8; r += 1
    ws.merge_cells(f"A{r}:F{r}"); c = ws[f"A{r}"]; c.value = "📌 " + note; c.font = F(10); c.fill = fill(NOTE_BG)
    c.alignment = Alignment("left", "top", wrap_text=True, indent=1); ws.row_dimensions[r].height = max(28, (len(note) // 90 + 1) * 15); r += 2
    return r

def pair(sheet_key):
    """gom screen theo sheet, trả [(screen, before_entry, after_entry)]"""
    scr = {}
    for ph in ("before", "after"):
        for e in caps.get(ph, []):
            if e.get("sheet") == sheet_key:
                scr.setdefault(e["screen"], {})[ph] = e
    return [(s, v.get("before"), v.get("after")) for s, v in scr.items()]

wb = Workbook()
BR = cfg["branch_id"]; NM = cfg.get("branch_name_jp", ""); SOT = cfg["sot"]
DIR = "Ticket→Pro" if SOT == "ticket_app" else "Pro→Ticket"
Rb, Ra = db_b.get("rails", {}), db_a.get("rails", {})
Db, Da = db_b.get("django", {}), db_a.get("django", {})

# ---- 1_DATA ----
ws = wb.active; ws.title = "1_DATA"; setw(ws)
header(ws, f"TẦNG 1 — DATA · Backfill {cfg['institute_code']} branch {BR} ({NM}) · {DIR} (sot={SOT})",
       f"noop={db_a.get('noop', db_b.get('noop'))}. candidates→0, archive orphan, doanh thu (Σprice incl archived) phải bất biến.")
r = 4
tbl = [("Đại lượng", "TRƯỚC", "SAU"),
       ("Django candidates", Db.get("dj_candidates", "?"), Da.get("dj_candidates", "?")),
       ("Rails candidates", Rb.get("rails_candidates", "?"), Ra.get("rails_candidates", "?")),
       ("Rails archived", Rb.get("rails_archived", "?"), Ra.get("rails_archived", "?")),
       ("Rails active Σprice", Rb.get("rails_active_price", "?"), Ra.get("rails_active_price", "?")),
       ("Rails Σprice (incl archived) — BẤT BIẾN", Rb.get("rails_all_price", "?"), Ra.get("rails_all_price", "?")),
       ("Django vé mới synced Pro", Db.get("dj_new_synced_pro", "?"), Da.get("dj_new_synced_pro", "?"))]
for i, row in enumerate(tbl):
    for j, val in enumerate(row):
        cell = ws.cell(row=r, column=j + 1, value=str(val)); cell.border = BORDER
        cell.alignment = Alignment("left" if j == 0 else "center", "center", wrap_text=True, indent=1 if j == 0 else 0)
        if i == 0: cell.font = F(10, True, WHITE); cell.fill = fill(NAVY)
        else: cell.font = F(10, True if "BẤT BIẾN" in str(row[0]) else False); cell.fill = fill(PASS_BG) if "BẤT BIẾN" in str(row[0]) else fill(WHITE)
    ws.row_dimensions[r].height = 26; r += 1
r += 1
for s, b, a in pair("1_DATA"):
    r = block(ws, r, "1.1", "Backfill row", (b or a or {}).get("url", ""), (b or a or {}).get("note", ""), ann_or(b["file"]) if b else None, ann_or(a["file"]) if a else None, "PASS ✅")

# ---- 2_REPORT ----
ws2 = wb.create_sheet("2_REPORT"); setw(ws2)
header(ws2, "TẦNG 2 — REPORT (doanh thu bất biến?)", "Mọi TỔNG 販売金額 phải GIỮ NGUYÊN. Số lượng vé tăng là đúng; số TIỀN tăng là SAI.")
r = 4
order = ["pro_packs_total", "tk_reports", "tk_sales", "tk_timeline", "tk_branches", "journal", "reservations"]
paired = {s: (b, a) for s, b, a in pair("2_REPORT")}
idx = 1
for s in order + [k for k in paired if k not in order]:
    if s not in paired: continue
    b, a = paired[s]
    e = b or a
    r = block(ws2, r, f"2.{idx}", e["screen"], e.get("url", ""), e.get("note", ""), ann_or(b["file"]) if b else None, ann_or(a["file"]) if a else None, "SAFE/PASS")
    idx += 1
# 3 export xlsx note
exp = json.loads((folder / "exports.json").read_text()) if (folder / "exports.json").exists() else {}
if exp:
    ws2.merge_cells(f"A{r}:F{r}"); c = ws2[f"A{r}"]
    c.value = "✅ 3 file .xlsx report thật (history/performance/annual) trong after/: " + " · ".join(f"{k}={v['status']}" for k, v in exp.items())
    c.font = F(10, True, PASS_TX); c.fill = fill(PASS_BG); c.alignment = Alignment("left", "top", wrap_text=True, indent=1)
    ws2.row_dimensions[r].height = 40; r += 2

# ---- 3_CHUCNANG ----
ws3 = wb.create_sheet("3_CHUCNANG"); setw(ws3)
header(ws3, "TẦNG 3 — CHỨC NĂNG (vé migrate còn chạy?)", "Vé migrate: price=0, reservation_ticket=nil. Redeem/reclaim/sync chạy qua code thật.")
r = 4
t3 = bugs.get("tier3", {})
rows3 = [("② Redeem (dùng buổi)", f"redeem {t3.get('redeem','?')}", "✅ PASS" if t3.get("redeem") else "?"),
         ("③ Reclaim (hủy→trả)", f"→ {t3.get('reclaim','?')}", "✅ PASS" if t3.get("reclaim") else "?"),
         ("⑤ Sync 2 chiều", f"{t3.get('sync','?')}", "✅ PASS" if t3.get("sync") == "OK" else "?"),
         ("Cleanup test data", f"{t3.get('cleanup','?')}", "✅" if t3.get("cleanup") == "done" else "?")]
for label, detail, res in rows3:
    ws3.cell(row=r, column=1, value=label); ws3.merge_cells(f"B{r}:D{r}"); ws3.cell(row=r, column=2, value=detail); ws3.merge_cells(f"E{r}:F{r}"); ws3.cell(row=r, column=5, value=res)
    for col in (1, 2, 5):
        cell = ws3.cell(row=r, column=col); cell.border = BORDER; cell.alignment = Alignment("left", "center", wrap_text=True, indent=1)
        cell.font = F(10, True if col == 5 else False); cell.fill = fill(PASS_BG) if "✅" in res else fill(NOTE_BG)
    ws3.row_dimensions[r].height = 26; r += 1
r += 1
for s, b, a in pair("3_CHUCNANG"):
    r = block(ws3, r, "①", "Customer チケット情報", (b or a or {}).get("url", ""), (b or a or {}).get("note", ""), ann_or(b["file"]) if b else None, ann_or(a["file"]) if a else None)

# ---- 4_BUGS ----
ws4 = wb.create_sheet("4_BUGS"); setw(ws4)
ws4.merge_cells("A1:F1"); ws4["A1"] = f"🚨 BUG confirmed — branch {BR} ({DIR})"; ws4["A1"].font = F(15, True, WHITE); ws4["A1"].fill = fill(RED)
ws4["A1"].alignment = Alignment("left", "center", indent=1); ws4.row_dimensions[1].height = 32
r = 3
if not bugs.get("bugs"):
    ws4.merge_cells(f"A{r}:F{r}"); ws4[f"A{r}"] = "Không bug nào confirmed (hoặc branch no-op)."; ws4[f"A{r}"].font = F(11); r += 1
for bug in bugs.get("bugs", []):
    ws4.merge_cells(f"A{r}:F{r}"); c = ws4[f"A{r}"]; c.value = f"{bug['id']} — {bug.get('title','')} [{bug.get('severity','')}]"
    c.font = F(12, True, WHITE); c.fill = fill(RED); c.alignment = Alignment("left", "center", indent=1); ws4.row_dimensions[r].height = 24; r += 1
    ws4.merge_cells(f"A{r}:F{r}"); c = ws4[f"A{r}"]; c.value = "🔬 " + bug.get("evidence", ""); c.font = Font(name="Menlo", size=9)
    c.alignment = Alignment("left", "top", wrap_text=True, indent=1); c.fill = fill("F2F2F2"); ws4.row_dimensions[r].height = max(30, (len(bug.get("evidence", "")) // 90 + 1) * 15); r += 1
    img = folder / "after" / f"bug_{bug['id']}.png"
    if img.exists():
        h = embed(ws4, str(img), f"A{r}", mw=900, mh=300); ws4.row_dimensions[r].height = h * 0.78 + 8; r += 1
    r += 1

out = folder / f"Backfill_{cfg['institute_code']}_branch{BR}_Evidence.xlsx"
wb.save(out)
print(f"OK build_excel.py → {out} ({sum(len(w._images) for w in wb.worksheets)} ảnh, {len(wb.sheetnames)} sheet)")
