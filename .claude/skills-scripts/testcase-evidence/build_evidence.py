#!/usr/bin/env python3
"""build_evidence.py — tcs.json (+ shots/) -> .xlsx chuẩn TEMPLATE (3 sheet). CƠ KHÍ, KHÔNG reasoning.

Usage: python3 build_evidence.py <folder>/tcs.json <folder>/<Ten>.xlsx
Deps:  pip install openpyxl pillow

Xuất 3 sheet giống TestCase_Evidence_Template.xlsx:
  - Cover      : report header + SUMMARY (COUNTIF Total/PASS/FAIL/未実施)
  - Test Cases : mỗi case = 1 BLOCK DỌC (Field: Test Case/Pre/Steps/Expected/Actual/Note)
                 + Evidence (Before) [E:J] / (After) [K:P] nhúng ẢNH TO (PNG rõ).
  - Checklist  : # | TC ID | Title | Priority | Result | Nguồn (alt-row + Total formulas)

Đọc {meta, shots_dir, tcs:[{id,screen,pri,result,title,pre,steps,expect,actual,note,before,after}]}
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

# --- palette (khớp template) ---
NAVY, BLUE2, LABEL, WHITE = "1F3864", "2E75B6", "D6E4F0", "FFFFFF"
NUMF, NOTEF, NAF, ALT = "FAFAFA", "FFFBE6", "F2F2F2", "EBF3FB"
RES_FILL = {"PASS": "E2EFDA", "FAIL": "FCE4E4", "未実施": "FFF2CC"}
RES_FONT = {"PASS": "375623", "FAIL": "9C0006", "未実施": "7F6000"}
PRI = {"High": "C00000", "Medium": "BF8F00", "Low": "548235"}
_TH = Side(style="thin", color="D0D0D0")
BORD = Border(left=_TH, right=_TH, top=_TH, bottom=_TH)

TOP = Alignment(wrap_text=True, vertical="top")
CEN = Alignment(horizontal="center", vertical="center", wrap_text=True)
IMG_W = 360  # px hiển thị ảnh evidence (to + rõ; PNG gốc ~1440px sẽ scale xuống)

FIELDS = [("1", "Test Case", "title"), ("2", "Pre-conditions", "pre"),
          ("3", "Steps", "steps"), ("4", "Expected Result", "expect"),
          ("5", "Actual Result", "actual")]


def _f(hex_):
    return PatternFill("solid", fgColor=hex_)


def _c(ws, r, c, v=None, *, font=None, fill=None, align=TOP, border=True):
    x = ws.cell(row=r, column=c, value=v)
    if font:
        x.font = font
    if fill:
        x.fill = _f(fill)
    x.alignment = align
    if border:
        x.border = BORD
    return x


def _img_size(p):
    if PILImage is None:
        return IMG_W, int(IMG_W * 0.62)
    with PILImage.open(p) as im:
        ratio = (im.height / im.width) if im.width else 0.62
    return IMG_W, int(IMG_W * ratio)


# ---------------- Cover ----------------
def build_cover(wb, meta):
    ws = wb.active
    ws.title = "Cover"
    for col, w in (("A", 4), ("B", 22), ("C", 58), ("D", 4)):
        ws.column_dimensions[col].width = w
    ws.merge_cells("B2:C3")
    _c(ws, 2, 2, "TEST CASE EVIDENCE REPORT", font=Font(bold=True, size=14, color=WHITE),
       fill=NAVY, align=CEN, border=False)
    rows = [("Project", meta.get("project", "")), ("Screen / Module", meta.get("module", "")),
            ("Issue", meta.get("issue", "")), ("Tester", meta.get("tester", "")),
            ("Test Date", meta.get("date", "")), ("Environment", meta.get("env", ""))]
    r = 5
    for k, v in rows:
        _c(ws, r, 2, k, font=Font(bold=True), fill=LABEL)
        _c(ws, r, 3, str(v))
        r += 1
    r += 1
    ws.merge_cells(f"B{r}:C{r}")
    _c(ws, r, 2, "SUMMARY", font=Font(bold=True, color=WHITE), fill=BLUE2, align=CEN)
    r += 1
    summ = [("Total TC", '=COUNTIF(\'Test Cases\'!A:A,"TC-*")', LABEL),
            ("PASS", '=COUNTIF(\'Test Cases\'!C:C,"PASS*")', RES_FILL["PASS"]),
            ("FAIL", '=COUNTIF(\'Test Cases\'!C:C,"FAIL*")', RES_FILL["FAIL"]),
            ("未実施", '=COUNTIF(\'Test Cases\'!C:C,"未実施*")', RES_FILL["未実施"])]
    for k, formula, fl in summ:
        _c(ws, r, 2, k, font=Font(bold=True), fill=LABEL)
        _c(ws, r, 3, formula, font=Font(bold=True), fill=fl)
        r += 1


# ---------------- Test Cases ----------------
def build_testcases(wb, meta, tcs, shots_dir):
    ws = wb.create_sheet("Test Cases")
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 50
    ws.column_dimensions["D"].width = 2
    for i in range(5, 17):  # E..P
        ws.column_dimensions[get_column_letter(i)].width = 9

    ws.merge_cells("A1:P1")
    _c(ws, 1, 1, f"TEST CASES — {meta.get('module', '')}",
       font=Font(bold=True, size=13, color=WHITE), fill=NAVY, align=Alignment(vertical="center"))
    hdr = Font(bold=True, color=WHITE)
    _c(ws, 2, 1, "#", font=hdr, fill=NAVY, align=CEN)
    _c(ws, 2, 2, "Field", font=hdr, fill=NAVY, align=CEN)
    _c(ws, 2, 3, "Detail / Actual Result", font=hdr, fill=NAVY, align=CEN)
    ws.merge_cells("E2:J2")
    _c(ws, 2, 5, "Evidence (Before)", font=hdr, fill=NAVY, align=CEN)
    ws.merge_cells("K2:P2")
    _c(ws, 2, 11, "Evidence (After)", font=hdr, fill=NAVY, align=CEN)

    r = 3
    for tc in tcs:
        b = r
        # -- header row (TC-id + title + priority) --
        _c(ws, b, 1, tc.get("id"), font=Font(bold=True, color=WHITE), fill=BLUE2, align=CEN)
        ws.merge_cells(start_row=b, start_column=2, end_row=b, end_column=3)
        _c(ws, b, 2, f"[{tc.get('screen', '')}]  {tc.get('title', '')}",
           font=Font(bold=True, color=WHITE), fill=BLUE2)
        pri = tc.get("pri", "")
        ws.merge_cells(start_row=b, start_column=5, end_row=b, end_column=16)
        _c(ws, b, 5, f"Priority: {pri}", font=Font(bold=True, color=WHITE),
           fill=PRI.get(pri, BLUE2), align=Alignment(vertical="center"))
        # -- field rows --
        for i, (num, label, key) in enumerate(FIELDS, 1):
            rr = b + i
            _c(ws, rr, 1, num, fill=NUMF, align=CEN)
            _c(ws, rr, 2, label, font=Font(bold=True), fill=LABEL)
            val = tc.get(key, "")
            cell = _c(ws, rr, 3, val)
            if key == "actual":
                res = tc.get("result")
                if res in RES_FILL:
                    cell.fill = _f(RES_FILL[res])
                    cell.font = Font(bold=True, color=RES_FONT[res])
        # -- note row --
        nrow = b + 6
        _c(ws, nrow, 1, "📝", fill=NOTEF, align=CEN)
        _c(ws, nrow, 2, "Note", font=Font(bold=True), fill=NOTEF)
        _c(ws, nrow, 3, tc.get("note") or "", fill=NOTEF)
        # -- evidence merged region: fields+note (b+1 .. b+6) --
        ev_top, ev_bot = b + 1, b + 6
        heights = []
        for col_start, key in ((5, "before"), (11, "after")):
            col_end = col_start + 5
            ws.merge_cells(start_row=ev_top, start_column=col_start, end_row=ev_bot, end_column=col_end)
            fname = tc.get(key)
            p = (shots_dir / fname) if fname else None
            anchor = _c(ws, ev_top, col_start, None, align=CEN)
            if p and p.exists() and PILImage is not None:
                w, h = _img_size(p)
                img = XLImage(str(p))
                img.width, img.height = w, h
                ws.add_image(img, f"{get_column_letter(col_start)}{ev_top}")
                heights.append(h)
            elif fname:
                anchor.value = f"(thiếu {fname})"
            else:
                anchor.value = "（不要 / N/A）"
                anchor.fill = _f(NAF)
        # -- row heights: chia đủ cao cho ảnh (max before/after) --
        img_h = max(heights) if heights else 0
        if img_h:
            per = max(18.0, (img_h * 0.75) / 6.0)  # px→pt, chia 6 dòng evidence
            for rr in range(ev_top, ev_bot + 1):
                ws.row_dimensions[rr].height = per
        else:
            for rr in range(ev_top, ev_bot + 1):
                ws.row_dimensions[rr].height = 26
        r = b + 8  # 7 dòng block + 1 spacer

    ws.freeze_panes = "A3"


# ---------------- Checklist ----------------
def build_checklist(wb, tcs):
    ws = wb.create_sheet("Checklist")
    for col, w in (("A", 5), ("B", 10), ("C", 62), ("D", 10), ("E", 12), ("F", 20)):
        ws.column_dimensions[col].width = w
    ws.merge_cells("A1:F1")
    _c(ws, 1, 1, "CHECKLIST", font=Font(bold=True, size=13, color=WHITE), fill=NAVY, align=Alignment(vertical="center"))
    hdr = Font(bold=True, color=WHITE)
    for c, name in enumerate(["#", "TC ID", "Test Case Title", "Priority", "Result", "Nguồn / 発生元"], 1):
        _c(ws, 3, c, name, font=hdr, fill=BLUE2, align=CEN)
    r = 4
    for i, tc in enumerate(tcs, 1):
        row_fill = WHITE if i % 2 else ALT
        _c(ws, r, 1, i, fill=row_fill, align=CEN)
        _c(ws, r, 2, tc.get("id"), fill=row_fill)
        _c(ws, r, 3, f"[{tc.get('screen', '')}] {tc.get('title', '')}", fill=row_fill)
        _c(ws, r, 4, tc.get("pri"), fill=row_fill, align=CEN)
        res = tc.get("result", "")
        rc = _c(ws, r, 5, res, fill=RES_FILL.get(res, row_fill), align=CEN)
        if res in RES_FONT:
            rc.font = Font(bold=True, color=RES_FONT[res])
        _c(ws, r, 6, tc.get("source", ""), fill=row_fill)
        r += 1
    last = r - 1
    _c(ws, r, 1, "Total", font=Font(bold=True), fill=LABEL)
    _c(ws, r, 2, f"=COUNTA(B4:B{last})", font=Font(bold=True), fill=LABEL, align=CEN)
    _c(ws, r, 3, "PASS", fill=RES_FILL["PASS"], align=CEN)
    _c(ws, r, 4, f'=COUNTIF(E4:E{last},"PASS")', fill=RES_FILL["PASS"], align=CEN)
    _c(ws, r, 5, "FAIL", fill=RES_FILL["FAIL"], align=CEN)
    _c(ws, r, 6, f'=COUNTIF(E4:E{last},"FAIL")', fill=RES_FILL["FAIL"], align=CEN)


def main():
    if len(sys.argv) < 3:
        print("usage: build_evidence.py <tcs.json> <out.xlsx>")
        sys.exit(1)
    tcs_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    data = json.loads(tcs_path.read_text(encoding="utf-8"))
    meta, tcs = data.get("meta", {}), data.get("tcs", [])
    shots_dir = tcs_path.parent / data.get("shots_dir", "shots")

    wb = Workbook()
    build_cover(wb, meta)
    build_testcases(wb, meta, tcs, shots_dir)
    build_checklist(wb, tcs)

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"OK -> {out}  ({len(tcs)} cases, 3 sheets: Cover/Test Cases/Checklist)")


if __name__ == "__main__":
    main()
