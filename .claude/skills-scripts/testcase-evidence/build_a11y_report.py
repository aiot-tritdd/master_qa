#!/usr/bin/env python3
"""build_a11y_report.py — a11y.results.json -> <Case>.a11y.xlsx (1 sheet 'Accessibility').
Oracle = WCAG (axe), KHÔNG phải spec. CƠ KHÍ, không reasoning."""
import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage

IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}
IMPACT_FILL = {"critical": "C0392B", "serious": "E67E22", "moderate": "F1C40F", "minor": "BDC3C7"}
HEADERS = ["Màn", "App", "URL", "Rule", "Mức", "WCAG", "Số phần tử", "Gợi ý fix", "Evidence"]

def build(results_path, out_path):
    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)
    base = os.path.dirname(os.path.abspath(results_path))
    wb = Workbook(); ws = wb.active; ws.title = "Accessibility"
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(1, c, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2C3E50")
    r = 2
    for scr in data.get("screens", []):
        for v in sorted(scr.get("violations", []), key=lambda x: IMPACT_ORDER.get(x.get("impact"), 9)):
            ws.cell(r, 1, scr.get("name", "")); ws.cell(r, 2, scr.get("app", "")); ws.cell(r, 3, scr.get("url", ""))
            ws.cell(r, 4, v.get("rule", ""))
            mc = ws.cell(r, 5, v.get("impact", ""))
            mc.fill = PatternFill("solid", fgColor=IMPACT_FILL.get(v.get("impact"), "BDC3C7"))
            ws.cell(r, 6, v.get("wcag", "")); ws.cell(r, 7, len(v.get("nodes", [])))
            ws.cell(r, 8, v.get("help", "")); ws.cell(r, 8).alignment = Alignment(wrap_text=True)
            shot = v.get("shot")
            if shot and os.path.exists(os.path.join(base, shot)):
                img = XLImage(os.path.join(base, shot)); img.width = 240; img.height = 150
                ws.add_image(img, f"I{r}"); ws.row_dimensions[r].height = 120
            r += 1
    if r == 2:
        ws.cell(2, 1, "Không có vi phạm a11y nào ở các màn đã quét.")
    for col, w in zip("ABCDEFGHI", (16, 12, 22, 18, 10, 8, 10, 40, 34)):
        ws.column_dimensions[col].width = w

    # Sheet 2: bản ghi ĐỘ PHỦ — mỗi màn + verdict (phân biệt "quét & sạch" vs "chưa quét")
    sw = wb.create_sheet("Màn quét")
    meta = data.get("meta", {})
    sw.cell(1, 1, f"A11Y · {meta.get('case','')} · {meta.get('date','')} · {meta.get('tester','')}").font = Font(bold=True)
    for c, h in enumerate(["Màn", "App", "URL", "Verdict", "Vi phạm crit+serious"], 1):
        cell = sw.cell(3, c, h); cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2C3E50")
    rr = 4
    for scr in data.get("screens", []):
        vs = scr.get("violations", [])
        cs = sum(1 for v in vs if v.get("impact") in ("critical", "serious"))
        sw.cell(rr, 1, scr.get("name", "")); sw.cell(rr, 2, scr.get("app", "")); sw.cell(rr, 3, scr.get("url", ""))
        sw.cell(rr, 4, scr.get("result", "")); sw.cell(rr, 5, cs)
        rr += 1
    for col, w in zip("ABCDE", (18, 12, 24, 10, 20)):
        sw.column_dimensions[col].width = w

    wb.save(out_path)
    print(f"✅ a11y report: {out_path} ({r - 2} vi phạm)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: build_a11y_report.py <results.json> <out.xlsx>")
    build(sys.argv[1], sys.argv[2])
