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
    wb.save(out_path)
    print(f"✅ a11y report: {out_path} ({r - 2} vi phạm)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: build_a11y_report.py <results.json> <out.xlsx>")
    build(sys.argv[1], sys.argv[2])
