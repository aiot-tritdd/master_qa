#!/usr/bin/env python3
"""build_bug_report.py — bug-he-thong.tcs.json -> bug-he-thong.xlsx (2 sheet). CƠ KHÍ, KHÔNG reasoning.

Usage: python3 build_bug_report.py <wtf-is-this/bug-he-thong.tcs.json> <out.xlsx>
Deps:  pip install openpyxl pillow

FORMAT = theme.json (cạnh file này) — nguồn sự thật DUY NHẤT cho màu/layout/nhãn/ngưỡng-chart.

KHÁC build_evidence.py: file kia in evidence cho MỘT spec (Cover/Test Cases/Checklist).
File này in SỔ BUG TOÀN HỆ (Report + List bug). Chi tiết từng bug KHÔNG nằm ở đây —
nó đã có nguyên ở TestCase-XX.xlsx; cột "TC ref" hyperlink sang. Chép lại = nhân bản.

LUẬT (spec 2026-07-15-bug-registry-report-design.md):
  - Sheet Report: KHÔNG ô số nào hardcode. Tất cả là COUNTIF/COUNTIFS trỏ 'List bug'.
  - Bất biến: Mở + Chờ retest + Đã đóng + Tái phát == Tổng bug. Lệch => RAISE, không in file sai.
  - Chart chỉ vẽ khi dữ liệu đỡ nổi (ngưỡng ở theme.json). Dưới ngưỡng => bảng đứng thay.
  - Mọi khúc/ô có màu PHẢI kèm chữ (status palette đo được ΔE 8.4 deutan — dải sàn 8-12).
  - CHỈ 2 sheet. Chi tiết bug KHÔNG chép vào đây — đã có ở TestCase-XX.xlsx, cột TC ref link sang.
"""
import json
import re
import shutil
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
from openpyxl.formatting.rule import CellIsRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.worksheet.table import Table, TableStyleInfo

from build_evidence import LB, P, _f

BR = LB["bug_report"]
DECOR = BR.get("decor", {"enabled": False})
LIFE = LB["status_lifecycle"]
PRI = LB["priority"]
NAVY, BLUE2, WHITE, LABEL, ALT = P["navy"], P["blue"], P["white"], P["lblue"], P["alt_row"]
GREY, RH = P["border"], BR["row_h"]
FHEAD, FBODY = BR["font_head"], BR["font_body"]

# --- Kiểu ĐO TỪ TEMPLATE MICROSOFT THẬT (Book 2/3/4/7), không phải tui đoán:
#     · data rows: fill=None, bord=- (KHÔNG viền, KHÔNG nền — Table style lo việc kẻ sọc)
#     · column header: fill=None, bord=- — phân biệt bằng FONT + MÀU + CỠ, KHÔNG tô nền
#     · chỉ có DẢI TIÊU ĐỀ trên cùng là được tô màu (Book 3: B1:G5 là band, phần còn lại trắng trơn)
#     Tô nền/đóng khung là phản xạ của người không tin vào typography.
RULE = Border(bottom=Side(style="thin", color=GREY))
LEFT = Alignment(horizontal="left", vertical="center")
MID = Alignment(horizontal="center", vertical="center")


def F(size=10, bold=False, color="000000", head=False):
    return Font(name=FHEAD if head else FBODY, size=size, bold=bold, color=color)


def _p(ws, r, c, v=None, *, font=None, fill=None, align=LEFT, border=None, fmt=None):
    """Đặt ô KHÔNG viền (khác _c của build_evidence — file kia đóng khung mọi ô)."""
    x = ws.cell(row=r, column=c, value=v)
    x.font = font or F()
    if fill:
        x.fill = _f(fill)
    x.alignment = align
    if border:
        x.border = border
    if fmt:
        x.number_format = fmt
    return x

# --- cột sheet 'List bug' (1-indexed) — thứ tự khớp theme.bug_report.list_header ---
# KHÔNG có cột 'Hiện tượng quan sát' / 'Ghi chú': text dài, đã có nguyên ở TestCase-XX.xlsx.
# List bug để QUÉT (lọc/sort), không để đọc.
# Cột A = MÁNG LỀ TRÁI, cột P = MÁNG LỀ PHẢI => data ở B..O. Mọi template Microsoft
# (Book 2/3/4/7) đều có máng HAI BÊN; tui từng chỉ có bên trái.
C0 = 2  # data bắt đầu ở B
C_STT, C_BUGID, C_TCREF, C_SPEC, C_SCREEN, C_TYPE, C_PRI = 2, 3, 4, 5, 6, 7, 8
C_RESULT, C_TITLE, C_STATUS, C_FIX, C_FOUND, C_RETEST, C_AGE = 9, 10, 11, 12, 13, 14, 15
NCOL = len(BR["list_header"])          # 14 cột data
CEND = C0 + NCOL - 1                   # = O
L = {i: get_column_letter(i) for i in range(1, CEND + 2)}
SHEET = f"'{BR['sheet_names'][1]}'"   # 'Danh sách Bug' — Report/SPEC-GAP trỏ COUNTIF vào đây
HDR_ROW = 1  # Table bắt đầu ngay dòng 1 (Excel Table cần header ở dòng đầu vùng)


def _d(s):
    """'2026-07-14' -> date. '' / None -> None."""
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def _iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _db(i, default_key):
    """Màu data-bar: xanh lá của decor (theme.decor.databar[i]) khi bật; không thì mặc định."""
    if DECOR.get("enabled"):
        g = DECOR["databar"]
        return g[i % len(g)]
    return P[default_key]


def _cnt(col, val):
    return f'COUNTIF({SHEET}!${L[col]}:${L[col]},"{val}")'


def _cnt2(c1, v1, c2, v2):
    return (f'COUNTIFS({SHEET}!${L[c1]}:${L[c1]},"{v1}",'
            f'{SHEET}!${L[c2]}:${L[c2]},"{v2}")')


def _service(screen):
    """Service = tiền tố 'screen' trước ' —' / ' ('. Nhãn tách ở Python (như 'spec');
    SỐ vẫn là COUNTIF wildcard 'prefix*' => không hardcode. Xem theme._service_note.

    Lấy dấu tách SỚM NHẤT, không phải khớp-theo-thứ-tự-list: 'Backend/API (Hold — input rác)'
    có ' — ' NẰM TRONG ngoặc; dò ' — ' trước ' (' thì ra 'Backend/API (Hold' => service ma.
    """
    s = (screen or "").strip()
    hits = [i for i in (s.find(sep) for sep in (" — ", " —", " (", " -", "(")) if i > 0]
    return (s[:min(hits)].strip() if hits else s) or "(khác)"


# ---------------- Sheet 2: List bug ----------------
def build_list(wb, bugs):
    ws = wb.create_sheet(BR["sheet_names"][1])
    for i, w in enumerate(BR["list_cols"], 1):
        ws.column_dimensions[L[i]].width = w

    # Header: KHÔNG tô nền (Book 3 dòng 6 / Book 4 dòng 8 đều fill=None) — phân biệt bằng
    # font tiêu đề + màu. SONG NGỮ VI/JA theo mẫu công ty ({Project_Name}_テスト報告書), khách Nhật.
    for c, (vi, ja) in enumerate(zip(BR["list_header"], BR["list_header_ja"]), C0):
        _p(ws, HDR_ROW, c, vi, font=F(9, True, NAVY, head=True), align=MID)
        _p(ws, HDR_ROW + 1, c, ja, font=F(8, False, "8A97AC", head=True), align=MID, border=RULE)
    ws.row_dimensions[HDR_ROW].height = 22
    ws.row_dimensions[HDR_ROW + 1].height = 18

    r = HDR_ROW + 2
    for i, b in enumerate(bugs, 1):
        _p(ws, r, C_STT, i, align=MID, font=F(9, False, "9AA5B5"))
        _p(ws, r, C_BUGID, b["bug_id"], font=F(10, True))
        # TC ref -> hyperlink RA file evidence thật. Không chép chi tiết vào đây (nhân bản).
        tc = _p(ws, r, C_TCREF, f"{b['id']} @ {b['source']}", font=F(9, False, "2E75B6"))
        tc.hyperlink = f"{b['source']}/{b['source']}.xlsx"
        _p(ws, r, C_SPEC, b["source"], align=MID, font=F(9))
        _p(ws, r, C_SCREEN, b.get("screen", ""), font=F(9))
        _p(ws, r, C_TYPE, b.get("bug_type", ""), align=MID, font=F(9))
        _p(ws, r, C_PRI, b.get("pri", ""), align=MID, font=F(9, True, P[PRI.get(b.get("pri"), "_default")]))

        res = b.get("result", "")
        st = b.get("status", "")
        # màu LUÔN kèm chữ — status ΔE 8.4 (dải sàn), cấm mã hoá bằng màu đơn độc
        _p(ws, r, C_RESULT, res, align=MID,
           font=F(9, True, P[LB["status"][res]["tx"]]) if res in LB["status"] else F(9),
           fill=P[LB["status"][res]["bg"]] if res in LB["status"] else None)
        _p(ws, r, C_TITLE, b.get("title", ""), font=F(9))
        _p(ws, r, C_STATUS, st, align=MID,
           font=F(9, True, P[LIFE[st]["tx"]]) if st in LIFE else F(9),
           fill=P[LIFE[st]["bg"]] if st in LIFE else None)
        _p(ws, r, C_FIX, b.get("fix_note", ""), font=F(9))
        for col, key in ((C_FOUND, "found_at"), (C_RETEST, "retested_at")):
            _p(ws, r, col, _d(b.get(key)), align=MID, font=F(9), fmt="yyyy-mm-dd")
        # age: chưa đóng -> tới hôm nay; đã đóng -> tới ngày retest
        _p(ws, r, C_AGE,
           f'=IFERROR(IF(${L[C_RETEST]}{r}<>"",${L[C_RETEST]}{r}-${L[C_FOUND]}{r},'
           f'TODAY()-${L[C_FOUND]}{r}),"")', align=MID, font=F(9), fmt="0")
        ws.row_dimensions[r].height = RH["data"]   # 24 — template thật dùng 24-36; tui từng để 18
        r += 1

    last = r - 1
    ref = f"{L[C0]}{HDR_ROW + 1}:{L[CEND]}{last}"  # Table lấy dòng JA làm header (dòng VI là tiêu đề nhìn)
    t = Table(displayName="BugList", ref=ref)
    t.tableStyleInfo = TableStyleInfo(name=BR["table_style"], showRowStripes=True)
    ws.add_table(t)  # => AutoFilter mọi cột. "Tương tác" thật: lọc Spec + Status.

    # bug ủ lâu mà còn mở -> tô đỏ. Điều kiện đọc từ theme, không hardcode.
    ws.conditional_formatting.add(
        f"{L[C_AGE]}{HDR_ROW+2}:{L[C_AGE]}{last}",
        CellIsRule(operator="greaterThan", formula=[str(BR["age_warn_days"])],
                   fill=_f(P["fail_bg"]), font=Font(bold=True, color=P["fail_tx"])))

    ws.freeze_panes = f"{L[C_TCREF]}{HDR_ROW+2}"  # giữ STT + Bug ID khi cuộn ngang
    ws.sheet_view.showGridLines = False
    return last


# ---------------- Sheet 1: Report ----------------
def _sect(ws, r, c0, c1, text):
    """Nhãn section = CHỮ, không phải thanh màu. Book 4: 'BUDGET WHEEL' Century Gothic 30B,
    fill=None. Microsoft không tô thanh cho section."""
    _p(ws, r, c0, text, font=F(13, True, NAVY, head=True))
    ws.row_dimensions[r].height = RH["section"]


def _thead(ws, r, c0, names):
    """Header cột: KHÔNG nền, KHÔNG viền. Book 3 dòng 6 ('Course ID'|'Course name'...) =
    Verdana 11, fill=None, bord=-. Book 4 dòng 8 = Century Gothic 14, fill=None.
    Phân biệt với data bằng font+màu+cỡ."""
    for i, n in enumerate(names):
        _p(ws, r, c0 + i, n, font=F(9, True, "5A6B87", head=True),
           align=LEFT if i == 0 else MID, border=RULE)
    ws.row_dimensions[r].height = RH["data"]


def _box(ws, r0, c0, c1, title, body):
    """Panel 'Chưa có dữ liệu' — GIỮ KHUNG mockup nhưng KHÔNG bịa số (user chọn).
    Section-label + 1 ô gộp nền xám nhạt, chữ nghiêng muted, viền mảnh. Trả về dòng kế."""
    _sect(ws, r0, c0, c1, title)
    br = r0 + 1
    ws.merge_cells(start_row=br, start_column=c0, end_row=br, end_column=c1)
    cell = ws.cell(row=br, column=c0, value=body)
    cell.font = Font(name=FBODY, size=9, italic=True, color="9AA5B5")
    cell.fill = _f(P["na_bg"])
    cell.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    thin = Side(style="thin", color=GREY)
    for cc in range(c0, c1 + 1):
        ws.cell(br, cc).border = Border(left=thin if cc == c0 else None,
                                        right=thin if cc == c1 else None, top=thin, bottom=thin)
    ws.row_dimensions[r0].height = RH["section"]
    ws.row_dimensions[br].height = 40
    ws.row_dimensions[br + 1].height = RH["gap"]   # dòng đệm _box TỰ quản: caller set gap ở r-1
    return br + 2                                  # sẽ đè height 40 của chính ô box => chữ bị nén mất


def _top_open(ws, bugs, r0, c0, c1):
    """Bảng TOP BUG ĐANG MỞ (khối phải) — High trước. Xem theme._top_open_note.

    Đây là chỗ DUY NHẤT ở sheet Tổng quan in tiêu đề bug: nó lọc+xếp hạng sẵn ('fix con nào
    trước'), khác 'Danh sách Bug' là sổ để quét/lọc. Vẫn KHÔNG chép steps/expect/actual —
    cột TC ref hyperlink sang file evidence.
    """
    rank = {"High": 0, "Medium": 1, "Low": 2}
    op = sorted((b for b in bugs if b.get("status") == "Mở"),
                key=lambda b: (rank.get(b.get("pri"), 9), b["bug_id"]))[:BR["top_open_max"]]
    _sect(ws, r0, c0, c1, BR["top_open_title"])
    r = r0 + 1
    for i, n in enumerate(BR["top_open_header"]):
        _p(ws, r, c0 + i, n, font=F(9, True, "5A6B87", head=True),
           align=LEFT if i in (0, 2) else MID, border=RULE)
    ws.row_dimensions[r].height = RH["data"]
    r += 1
    for b in op:
        _p(ws, r, c0, b["bug_id"], font=F(9, True))
        pri = b.get("pri", "")
        _p(ws, r, c0 + 1, pri, align=MID, font=F(9, True, P[PRI.get(pri, "_default")]))
        _p(ws, r, c0 + 2, b.get("title", ""), font=F(9))
        tc = _p(ws, r, c0 + 3, f'{b["id"]} @ {b["source"]}', font=F(8, False, "2E75B6"), align=MID)
        tc.hyperlink = f"{b['source']}/{b['source']}.xlsx"
        ws.row_dimensions[r].height = RH["data"]
        r += 1
    if not op:
        ws.merge_cells(start_row=r, start_column=c0, end_row=r, end_column=c1)
        _p(ws, r, c0, "Không còn bug nào đang mở.",
           font=Font(name=FBODY, size=9, italic=True, color="9AA5B5"))
        r += 1
    for c in range(c0, c1 + 1):
        ws.cell(r - 1, c).border = RULE
    return r


def build_report(wb, meta, bugs, last_row):
    ws = wb.active
    ws.title = BR["sheet_names"][0]
    for col, w in BR["report_cols"].items():
        ws.column_dimensions[col].width = w
    # LƯỚI 2+1 (xem theme._grid_note): KHỐI TRÁI B..H (bảng 1 = B,C · bảng 2 = E,F · spec = B..H)
    # · khe I · KHỐI PHẢI J..M (chart trên, bảng 'top bug đang mở' dưới).
    END = 13   # M — mép phải băng tiêu đề/alert. Cột N = máng lề phải.
    LEND = 8   # H — mép phải khối trái (= cột cuối bảng spec)
    P2 = 5     # E — nhãn cột bảng 2
    R0 = 10    # J — mép trái khối phải
    NST = len(LIFE)
    ph = BR["placeholder"]

    # SKIN trang trí (bật ở theme.decor). Bản navy/trắng sạch = fallback khi enabled=false.
    D = DECOR if DECOR.get("enabled") else None
    band1 = D["sky_top"] if D else NAVY      # banner dòng 1
    band2 = D["sky_bot"] if D else NAVY      # banner dòng 2 (2 tầng => hiệu ứng trời)
    title_tx = D["title_tx"] if D else WHITE
    sub_tx = D["subtitle_tx"] if D else "B8C4DA"

    # ---- đầu trang: dải banner (navy sạch, hoặc "trời" 2 tầng khi bật decor) ----
    for rr, h, band in ((1, RH["banner"], band1), (2, RH["subtitle"], band2)):
        for c in range(2, END + 1):
            _p(ws, rr, c, None, fill=band)
        ws.row_dimensions[rr].height = h
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=END)
    _p(ws, 1, 2, BR["title"], font=F(24, True, title_tx, head=True), fill=band1,
       align=Alignment(horizontal="left", vertical="center", indent=1))
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=END)
    _p(ws, 2, 2, f"{meta.get('project', '')}   ·   {meta.get('env', '')}   ·   nguồn: bug-he-thong.tcs.json   ·   {date.today():%d/%m/%Y}",
       font=F(9, False, sub_tx), fill=band2,
       align=Alignment(horizontal="left", vertical="center", indent=1))
    ws.row_dimensions[3].height = RH["gap"]

    # ---- HERO: số 'đang mở' TO + sub-line (đều FORMULA, không hardcode) ----
    r = 4
    _p(ws, r, 2, f'={_cnt(C_STATUS, "Mở")}', font=F(44, True, P["fail_tx"]),
       align=Alignment(horizontal="left", vertical="center"), fmt="0")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=END)
    _p(ws, r, 3, BR["hero_suffix"], font=F(14, False, "5A6B87"),
       align=Alignment(horizontal="left", vertical="bottom"))
    ws.row_dimensions[r].height = 44
    r += 1
    sub = (f'=TEXT({_cnt(C_STATUS, "Đã đóng")},"0")&" đã đóng   ·   "&'
           f'TEXT({_cnt(C_STATUS, "Chờ retest")},"0")&" chờ retest   ·   "&'
           f'TEXT({_cnt(C_STATUS, "Tái phát")},"0")&" tái phát"')
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=END)
    _p(ws, r, 2, sub, font=F(10, False, "9AA5B5"))
    ws.row_dimensions[r].height = 18
    r += 2
    ws.row_dimensions[r - 1].height = RH["gap"]

    # ---- CHIPS: mỗi ô = 1 chip (formula ="Nhãn · "&COUNTIF), fill + chữ màu ----
    chips = [(f'="{st} · "&{_cnt(C_STATUS, st)}', LIFE[st]["bg"], LIFE[st]["tx"]) for st in LIFE]
    chips.append((f'="SPEC-GAP · "&{_cnt(C_RESULT, "SPEC-GAP")}',
                  LB["status"]["SPEC-GAP"]["bg"], LB["status"]["SPEC-GAP"]["tx"]))
    for i, (formula, bg, tx) in enumerate(chips):
        _p(ws, r, 3 + i, formula, font=F(9, True, P[tx]), fill=P[bg], align=MID)  # C..G, đều 13
    ws.row_dimensions[r].height = 22
    r += 2
    ws.row_dimensions[r - 1].height = RH["gap"]

    # ---- BANNER cảnh báo: High đang mở (số = formula) ----
    tail = BR["alert_tail"]
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=END)
    _p(ws, r, 2, f'="▸  "&{_cnt2(C_PRI, "High", C_STATUS, "Mở")}&"  {tail}"',
       font=F(10, True, P["pending_tx"]), fill=P["note_bg"],
       align=Alignment(horizontal="left", vertical="center", indent=1))
    ws.row_dimensions[r].height = RH["data"]
    r += 2
    ws.row_dimensions[r - 1].height = RH["gap"]

    # ---- 1. THEO MỨC ĐỘ  |  2. KẾT QUẢ (cạnh nhau) — chart nằm ở cột H..L cùng dải này ----
    grid_top = r
    _sect(ws, r, 2, 3, "1.  THEO MỨC ĐỘ")
    _sect(ws, r, P2, P2 + 1, "2.  KẾT QUẢ")
    r += 1
    _thead(ws, r, 2, ["Mức độ", "Số lượng"])
    _thead(ws, r, P2, ["Kết quả", "Số lượng"])
    r += 1
    pri_r0 = r
    for i, k in enumerate(("High", "Medium", "Low")):
        _p(ws, r + i, 2, k, font=F(10, False, P[PRI[k]]))
        _p(ws, r + i, 3, f'={_cnt(C_PRI, k)}', align=MID, fmt="0")
    pri_r1 = r + 2
    for i, k in enumerate(("FAIL", "SPEC-GAP")):
        _p(ws, r + i, P2, k, font=F(10, True, P[LB["status"][k]["tx"]]))
        _p(ws, r + i, P2 + 1, f'={_cnt(C_RESULT, k)}', align=MID, fmt="0")
    for i in range(3):
        ws.row_dimensions[r + i].height = RH["data"]
    ws.conditional_formatting.add(
        f"C{pri_r0}:C{pri_r1}",
        DataBarRule(start_type="num", start_value=0, end_type="max", color=_db(0, "ord_2"), showValue=True))
    r += 3
    ws.row_dimensions[r].height = RH["gap"]
    r += 1

    # ---- 3. THEO SERVICE  |  4. THEO LOẠI (cạnh nhau) ----
    services = sorted({_service(b.get("screen", "")) for b in bugs},
                      key=lambda s: -sum(1 for b in bugs if _service(b.get("screen", "")) == s))
    _sect(ws, r, 2, 3, BR["service_title"])
    _sect(ws, r, P2, P2 + 1, "4.  THEO LOẠI")
    r += 1
    _thead(ws, r, 2, ["Service", "Số lượng"])
    _thead(ws, r, P2, ["Loại", "Số lượng"])
    r += 1
    svc_r0 = r
    for i, s in enumerate(services):
        _p(ws, r + i, 2, s)
        _p(ws, r + i, 3, f'={_cnt(C_SCREEN, s + "*")}', align=MID, fmt="0")
    svc_r1 = r + len(services) - 1
    BUG_TYPES = ("Function", "UI", "Text", "Accessibility", "Visual", "Security",
                 "Performance", "Compatibility", "i18n")
    for i, k in enumerate(BUG_TYPES):
        _p(ws, r + i, P2, k)
        _p(ws, r + i, P2 + 1, f'={_cnt(C_TYPE, k)}', align=MID, fmt="0")
    nrows = max(len(services), len(BUG_TYPES))
    for i in range(nrows):
        ws.row_dimensions[r + i].height = RH["data"]
    ws.conditional_formatting.add(
        f"C{svc_r0}:C{svc_r1}",
        DataBarRule(start_type="num", start_value=0, end_type="max", color=_db(1, "blue"), showValue=True))
    r += nrows + 1
    grid_bot = r - 1
    ws.row_dimensions[r - 1].height = RH["gap"]

    # ---- KHỐI PHẢI (J..M): bảng TOP BUG ĐANG MỞ — dữ liệu THẬT, dưới chart ----
    right_r = _top_open(ws, bugs, grid_bot + 2, R0, END)

    # ---- 5. THEO SPEC (bảng 7 cột B..H) ----
    no_assignee = not any(b.get("assignee") or b.get("owner") for b in bugs)
    specs = sorted({b["source"] for b in bugs})
    _sect(ws, r, 2, LEND, "5.  THEO SPEC")
    r += 1
    spec_hdr = r
    _thead(ws, r, 2, ["Spec", "Bug góp"] + list(LIFE) + ["Spec-Gap"])
    r += 1
    spec_r0 = r
    for s in specs:
        _p(ws, r, 2, s)
        _p(ws, r, 3, f'={_cnt(C_SPEC, s)}', align=MID, fmt="0")
        for i, st in enumerate(LIFE):
            _p(ws, r, 4 + i, f'={_cnt2(C_SPEC, s, C_STATUS, st)}', align=MID, fmt="0")
        _p(ws, r, 4 + NST, f'={_cnt2(C_SPEC, s, C_RESULT, "SPEC-GAP")}', align=MID, fmt="0")
        ws.row_dimensions[r].height = RH["data"]
        r += 1
    spec_r1 = r - 1
    _p(ws, r, 2, "Tổng", font=F(10, True, NAVY, head=True), border=RULE)
    for i in range(3, 5 + NST):
        _p(ws, r, i, f"=SUM({L[i]}{spec_r0}:{L[i]}{spec_r1})", font=F(10, True, NAVY, head=True),
           align=MID, border=RULE, fmt="0")
    ws.row_dimensions[r].height = RH["data"]
    ws.conditional_formatting.add(
        f"C{spec_r0}:C{spec_r1}",
        DataBarRule(start_type="num", start_value=0, end_type="max", color=_db(2, "blue"), showValue=True))
    r += 2
    ws.row_dimensions[r - 1].height = RH["gap"]

    # ---- 6. XU HƯỚNG THEO THỜI GIAN: bảng+chart nếu đủ kỳ, KHÔNG thì ô 'Chưa có dữ liệu' ----
    weeks, months = _periods(bugs)
    wk_r0 = wk_r1 = None
    if len(weeks) >= BR["chart_min_periods"]:
        _sect(ws, r, 2, 5, ph["trend_title"])
        r += 1
        _thead(ws, r, 2, ["Kỳ", "Phát hiện", "Đã đóng", "Tồn cuối kỳ"])
        r += 1
        wk_r0 = r                       # line chart CHỈ ăn khối tuần
        for label, lo, hi in weeks + months:
            f_lo, f_hi = f'DATE({lo.year},{lo.month},{lo.day})', f'DATE({hi.year},{hi.month},{hi.day})'
            M, N = f"{SHEET}!${L[C_FOUND]}:${L[C_FOUND]}", f"{SHEET}!${L[C_RETEST]}:${L[C_RETEST]}"
            _p(ws, r, 2, label)
            _p(ws, r, 3, f'=COUNTIFS({M},">="&{f_lo},{M},"<="&{f_hi})', align=MID, fmt="0")
            _p(ws, r, 4, f'=COUNTIFS({N},">="&{f_lo},{N},"<="&{f_hi})', align=MID, fmt="0")
            _p(ws, r, 5, f'=COUNTIFS({M},"<="&{f_hi})-COUNTIFS({N},"<="&{f_hi},{N},"<>")',
               font=F(10, True), align=MID, fmt="0")
            ws.row_dimensions[r].height = RH["data"]
            r += 1
        wk_r1 = wk_r0 + len(weeks) - 1  # chỉ khối tuần, không lẫn tháng
        for c in range(2, 6):
            ws.cell(r - 1, c).border = RULE
        r += 1
        ws.row_dimensions[r - 1].height = RH["gap"]
    else:
        r = _box(ws, r, 2, LEND, ph["trend_title"],          # _box tự set dòng đệm cuối
                 ph["trend_body"].format(n=BR["chart_min_periods"]))

    # ---- 7. NGƯỜI XỬ LÝ ----
    # CẢ HAI placeholder nằm ở KHỐI TRÁI (B..H). Không đẩy sang J..M: khối phải đã có
    # chart + bảng 'Top bug đang mở' => đặt box ở đó là GHI ĐÈ lên bảng (đã dính: mất 5 bug).
    if no_assignee:
        r = _box(ws, r, 2, LEND, ph["assignee_title"], ph["assignee_body"])

    # ---- 8. MÔI TRƯỜNG · PHẠM VI (KHỐI TRÁI B..H) ----
    # merge tới LEND, KHÔNG tới END: merge C..M quét ngang qua khối phải => nuốt sạch ô
    # J..M ở mấy dòng đó (đã dính: bảng Top bug mất BUG-009/010). merge_cells biến ô bị
    # trùm thành MergedCell = None, không cảnh báo gì.
    _sect(ws, r, 2, LEND, "8.  MÔI TRƯỜNG · PHẠM VI")
    r += 1
    for k, v in (("Môi trường", meta.get("env", "")),
                 ("Tester", meta.get("tester", "")),
                 ("Phạm vi", meta.get("issue", ""))):
        _p(ws, r, 2, k, font=F(9, True, "5A6B87", head=True))
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=LEND)
        _p(ws, r, 3, v, font=F(9), align=Alignment(horizontal="left", vertical="center", wrap_text=True))
        ws.row_dimensions[r].height = RH["data"]
        r += 1

    n_slices = sum(1 for k in ("High", "Medium", "Low") if any(b.get("pri") == k for b in bugs))
    n_specs_nz = sum(1 for s in specs if any(b["source"] == s for b in bugs))
    _charts(ws, n_slices, n_specs_nz, len(weeks), len(services),
            pri_r0, pri_r1, spec_hdr, spec_r0, spec_r1, wk_r0, wk_r1, svc_r0, svc_r1,
            grid_top, right_r)
    ws.sheet_view.showGridLines = False
    ws.sheet_view.showRowColHeaders = False   # bỏ A/B/C + 1/2/3 => đọc như tài liệu, không như bảng tính

    last = max(r, right_r)
    if D:
        # NỀN KEM: tô ô CÒN TRỐNG (chưa có fill) => canvas kem, giữ nguyên ô đã tô (banner,
        # chip, status). +8 dòng đệm dưới để dải đồi cỏ có nền kem đứng lên. Máng lề A/N cũng tô.
        cream = _f(D["cream"])
        for rr in range(1, last + 9):
            for cc in range(1, END + 2):
                cell = ws.cell(rr, cc)
                if cell.fill is None or cell.fill.patternType is None:
                    cell.fill = cream
        for rr in range(last + 1, last + 9):
            ws.row_dimensions[rr].height = RH["data"]   # đệm cao đều cho dải đồi cỏ
    return last


def _periods(bugs):
    """(weeks, months) — mỗi cái [(nhãn, ngày_đầu, ngày_cuối)], chỉ kỳ thực sự có dữ liệu.

    TÁCH tuần/tháng, KHÔNG gộp 1 list: line chart vẽ chung sẽ ra trục x = [2026-W29, 2026-07]
    — hai đơn vị thời gian trên cùng một trục = vô nghĩa. Bảng ⑤ hiện cả hai (bảng thì được);
    line chart CHỈ ăn tuần.
    """
    ds = [_d(b["found_at"]) for b in bugs if b.get("found_at")]
    ds += [_d(b["retested_at"]) for b in bugs if b.get("retested_at")]
    weeks, months = [], []
    for w in sorted({_iso_week(d) for d in ds}):
        y, wk = int(w[:4]), int(w[6:])
        weeks.append((w, date.fromisocalendar(y, wk, 1), date.fromisocalendar(y, wk, 7)))
    for m in sorted({f"{d:%Y-%m}" for d in ds}):
        y, mo = int(m[:4]), int(m[5:])
        hi = date(y + (mo == 12), mo % 12 + 1, 1)
        months.append((m, date(y, mo, 1), date.fromordinal(hi.toordinal() - 1)))
    return weeks, months


def _gp(hexcolor):
    return GraphicalProperties(solidFill=hexcolor,
                               ln=LineProperties(solidFill=WHITE, w=25400))  # khe 2px


def _noline(o):
    """Bỏ viền quanh chart — 'borders sparingly'. Phải set CẢ graphical_properties (chart area)
    LẪN plot area; set mỗi cái ngoài thì Excel vẫn vẽ khung (đã dính)."""
    gp = GraphicalProperties(ln=LineProperties(noFill=True), noFill=True)
    o.graphical_properties = gp
    return o


def _labels(**on):
    """dLbls TẮT HẾT rồi bật đúng cái cần. Mặc định Excel bật lung tung =>
    'Series1; Low; 9; 27%' chồng lên nhau (đã dính)."""
    d = DataLabelList()
    for k in ("showSerName", "showCatName", "showVal", "showPercent",
              "showLegendKey", "showBubbleSize"):
        setattr(d, k, on.get(k, False))
    d.numFmt = "0"
    return d


def _style(ch, w=11, h=7):
    ch.height, ch.width = h, w
    ch.style = None
    _noline(ch)
    for ax in (getattr(ch, "x_axis", None), getattr(ch, "y_axis", None)):
        if ax is None:
            continue
        ax.majorGridlines = None          # 'recessive grid' — mặc định Excel kẻ đen đậm
        ax.txPr = None
        ax.spPr = GraphicalProperties(ln=LineProperties(solidFill=P["border"], w=9525))
    if ch.legend:
        ch.legend.position = "b"
        ch.legend.overlay = False
    return ch


def _charts(ws, n_slices, n_specs, n_periods, n_services,
            pri_r0, pri_r1, spec_hdr, spec_r0, spec_r1, per_r0, per_r1, svc_r0, svc_r1,
            grid_top, right_r):
    """Vẽ CHỈ KHI dữ liệu đỡ nổi. Ngưỡng ở theme.json, không ở trí nhớ ai.

    n_slices/n_specs/n_services = số hạng mục KHÁC 0 (không phải số dòng). Đếm dòng là sai:
    High/Medium/Low = 3 dòng, nhưng Low=0 => pie chỉ 2 lát = anti-pattern dataviz.

    Chart NEO TRONG LƯỚI (cột H..L, cao bằng dải section 1-4), KHÔNG thả lơ lửng ngoài
    vùng nội dung => nửa màn phải hết trống.
    """
    AC = "J"   # mép trái KHỐI PHẢI (J..M = 12+12+58+14 = 96 đơn vị ~ 672px ~ 17.7cm)

    # THEO SERVICE — CỘT ĐỨNG, MỘT hue. Service là nominal + so-magnitude => sequential 1 màu
    # (luật dataviz 'compare magnitude → bar, one hue'), KHÔNG tô mỗi cột một màu (rainbow).
    if n_services >= BR["chart_min_categories"] and svc_r0:
        ch = BarChart()
        ch.type, ch.gapWidth = "col", 55
        ch.title = "Bug theo service"
        ch.add_data(Reference(ws, min_col=3, min_row=svc_r0, max_row=svc_r1), titles_from_data=False)
        ch.set_categories(Reference(ws, min_col=2, min_row=svc_r0, max_row=svc_r1))
        ch.series[0].graphicalProperties = _gp(P["navy"])
        ch.dLbls = _labels(showVal=True)
        ch.legend = None
        # 17.5cm ~ J..M · 8.6cm ~ chiều cao dải section 1-4
        ws.add_chart(_style(ch, 17.5, 8.6), f"{AC}{grid_top}")

    # mức độ — BAR NGANG, không phải doughnut. Hai lý do, cả hai từ luật dataviz:
    #   1. "❌ A donut/pie for comparing close values → ✅ A bar, or the numbers" — 14/11/9 sát nhau.
    #   2. High/Medium/Low là thang CÓ THỨ TỰ => ordinal ramp (1 hue đậm→nhạt), KHÔNG phải
    #      đèn giao thông đỏ/vàng/lục (3 hue rời rạc cho 1 thang bậc = sai loại mã hoá).
    if n_slices >= BR["chart_min_slices"]:
        ch = BarChart()
        ch.type, ch.gapWidth = "bar", 45
        ch.title = "Bug theo mức độ"
        ch.add_data(Reference(ws, min_col=3, min_row=pri_r0, max_row=pri_r1), titles_from_data=False)
        ch.set_categories(Reference(ws, min_col=2, min_row=pri_r0, max_row=pri_r1))
        ch.series[0].data_points = [
            DataPoint(idx=i, spPr=_gp(P[k]))   # DataPoint dùng spPr; graphicalProperties chỉ ở Series
            for i, k in enumerate(("ord_1", "ord_2", "ord_3"))]
        ch.dLbls = _labels(showVal=True)
        ch.legend = None          # 1 series — title đã gọi tên nó
        ws.add_chart(_style(ch, 17.5, 6), f"{AC}{right_r + 1}")

    # 📊 spec × status — stacked bar NGANG (tên category dài)
    if n_specs >= BR["chart_min_categories"]:
        ch = BarChart()
        ch.type, ch.grouping, ch.overlap, ch.gapWidth = "bar", "stacked", 100, 55
        ch.title = "Bug theo spec × trạng thái"
        ch.add_data(Reference(ws, min_col=4, max_col=3 + len(LIFE), min_row=spec_hdr, max_row=spec_r1),
                    titles_from_data=True)
        ch.set_categories(Reference(ws, min_col=2, min_row=spec_r0, max_row=spec_r1))
        # Màu chart DỊU (ch_*), không phải màu chữ bão hoà. Đo được: dịu = CVD ΔE 20.0 ALL PASS;
        # bão hoà = 8.4 FAILED. Vừa đỡ chói vừa an toàn mù màu hơn — không đánh đổi.
        for s, key in zip(ch.series, ("ch_open", "ch_wait", "ch_closed", "ch_reopen")):
            s.graphicalProperties = _gp(P[key])
        ch.dLbls = _labels(showVal=True)
        ch.dLbls.numFmt = "0;;;"   # khúc = 0 thì KHÔNG in nhãn (nhãn '0' treo ngoài cột = rác)
        ws.add_chart(_style(ch, 17.5, 6), f"{AC}{right_r + 14}")

    # 📈 xu hướng — chart DUY NHẤT trả lời "bug đang tích lại hay tiêu đi"
    if n_periods >= BR["chart_min_periods"] and per_r0:
        ch = LineChart()
        ch.title = "Bug tồn cuối kỳ"
        ch.add_data(Reference(ws, min_col=5, min_row=per_r0 - 1, max_row=per_r1), titles_from_data=True)
        ch.set_categories(Reference(ws, min_col=2, min_row=per_r0, max_row=per_r1))
        ch.varyColors = False   # bật => Excel tô mỗi ĐIỂM một màu + nhồi cả 7 tuần vào legend (đã dính)
        ch.legend = None        # 1 series thì không cần legend — title đã gọi tên nó (luật dataviz)
        s = ch.series[0]
        s.graphicalProperties = GraphicalProperties(ln=LineProperties(solidFill=NAVY, w=25400))
        s.smooth = False
        ws.add_chart(_style(ch, 17.5, 6), f"{AC}{right_r + 27}")


def _inject_decor(out_path, last_row):
    """Splice hình trang trí (asset bug_report_decor.xml) vào drawing1.xml SAU khi save.
    openpyxl KHÔNG đẻ preset shape (mây/mặt trời/đồi cỏ) được => can thiệp thẳng zip.

    · banner shapes: neo dòng 0-1 => CỐ ĐỊNH, giữ nguyên.
    · land shapes (đồi cỏ/cây): SHIFT dòng theo delta = (last_row+gap) - land_base_row
      => dải phong cảnh luôn tụt xuống ĐÁY nội dung thật, không lệch khi thêm bug/spec.
    Chỉ sheet 'Tổng quan' có chart => chỉ 1 drawing part (drawing1.xml).
    """
    if not DECOR.get("enabled"):
        return
    raw = (Path(__file__).parent / "bug_report_decor.xml").read_text(encoding="utf-8")
    banner = raw.split("<!--BANNER-->")[1].split("<!--LAND-->")[0].strip()
    land = raw.split("<!--LAND-->")[1].strip()
    delta = (last_row + DECOR["land_gap"]) - DECOR["land_base_row"]
    land = re.sub(r"<xdr:row>(\d+)</xdr:row>",
                  lambda m: f"<xdr:row>{int(m.group(1)) + delta}</xdr:row>", land)
    shapes = banner + "\n" + land + "\n"
    # openpyxl viết drawing với namespace spreadsheetDrawing là MẶC ĐỊNH (KHÔNG prefix 'xdr:'),
    # đóng bằng </wsDr>. Asset dùng prefix xdr: => bỏ prefix cho khớp, không thì XML hỏng (prefix
    # xdr không khai báo). 'a:'/'r:' vẫn giữ (openpyxl có khai báo 2 cái đó ở root).
    shapes = shapes.replace("xdr:", "")

    dn = "xl/drawings/drawing1.xml"
    with zipfile.ZipFile(out_path) as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}
    if dn not in data:
        raise SystemExit(f"LỖI DECOR: không thấy {dn} — sheet Tổng quan phải có ít nhất 1 chart để có drawing part.")
    xml = data[dn].decode("utf-8")
    if "</wsDr>" not in xml:
        raise SystemExit("LỖI DECOR: drawing1.xml không có </wsDr>.")
    data[dn] = xml.replace("</wsDr>", shapes + "</wsDr>").encode("utf-8")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])


# ---------------- Sheet 3: SPEC-GAP ----------------
def build_specgap(wb, bugs):
    """FILTER của 'Danh sách Bug' nơi result=SPEC-GAP. Sheet RIÊNG vì đây là việc của BA
    (đính chính tài liệu), không phải bug dev. Ở đây MỚI in 'actual' (quan sát) — vì với
    SPEC-GAP chính quan sát là deliverable cho BA, người không mở file evidence."""
    sg = BR["specgap"]
    ws = wb.create_sheet(BR["sheet_names"][2])
    for i, w in enumerate(sg["cols"], 1):
        ws.column_dimensions[L[i]].width = w
    gaps = [b for b in bugs if b.get("result") == "SPEC-GAP"]

    ws.merge_cells("B1:G1")
    _p(ws, 1, 2, sg["title"], font=F(15, True, P["specgap_tx"], head=True),
       align=Alignment(horizontal="left", vertical="center", indent=1))
    ws.row_dimensions[1].height = RH["section"]
    ws.merge_cells("B2:G2")
    _p(ws, 2, 2, sg["info"], font=F(9, False, "5A6B87"), fill=P["specgap_bg"],
       align=Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True))
    ws.row_dimensions[2].height = 46
    ws.row_dimensions[3].height = RH["gap"]

    hr = 4
    for c, name in enumerate(sg["header"], 2):
        _p(ws, hr, c, name, font=F(9, True, NAVY, head=True),
           align=LEFT if c == 2 else MID, border=RULE)
    ws.row_dimensions[hr].height = RH["data"]

    r = hr + 1
    TOP = Alignment(horizontal="left", vertical="top", wrap_text=True)
    for b in gaps:
        _p(ws, r, 2, b["bug_id"], font=F(10, True), align=Alignment(vertical="top"))
        _p(ws, r, 3, b.get("screen", ""), font=F(9), align=TOP)
        tc = _p(ws, r, 4, f'{b["id"]} @ {b["source"]}', font=F(9, False, "2E75B6"), align=Alignment(vertical="top"))
        tc.hyperlink = f"{b['source']}/{b['source']}.xlsx"
        _p(ws, r, 5, b.get("title", ""), font=F(9), align=TOP)
        _p(ws, r, 6, b.get("actual", ""), font=F(9, False, "444444"), align=TOP)
        _p(ws, r, 7, sg["default_doc_status"], align=MID,
           font=F(9, True, P["pending_tx"]), fill=P["pending_bg"])
        ws.row_dimensions[r].height = 110
        r += 1

    if not gaps:
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=7)
        _p(ws, r, 2, "Không có SPEC-GAP nào — mọi finding đều chấm được theo spec.",
           font=Font(name=FBODY, size=9, italic=True, color="9AA5B5"))
        ws.row_dimensions[r].height = RH["data"]

    ws.freeze_panes = "B5"
    ws.sheet_view.showGridLines = False
    ws.sheet_view.showRowColHeaders = False
    return len(gaps)


def main():
    if len(sys.argv) < 3:
        print("usage: build_bug_report.py <bug-he-thong.tcs.json> <out.xlsx>")
        sys.exit(1)
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    data = json.loads(src.read_text(encoding="utf-8"))
    meta, bugs = data.get("meta", {}), data.get("tcs", [])

    # --- BẤT BIẾN: lệch => KHÔNG in file. Thà không có file còn hơn có file nói dối. ---
    bad = [b.get("id") for b in bugs if b.get("status") not in LIFE]
    if bad:
        raise SystemExit(f"LỖI: status không hợp lệ ở {bad}. Hợp lệ: {list(LIFE)}")
    missing = [b.get("id") for b in bugs if not b.get("bug_id") or not b.get("found_at")]
    if missing:
        raise SystemExit(f"LỖI: thiếu bug_id/found_at ở {missing}")
    ids = [b["bug_id"] for b in bugs]
    if len(set(ids)) != len(ids):
        raise SystemExit(f"LỖI: bug_id TRÙNG: {[i for i in ids if ids.count(i) > 1]}")

    wb = Workbook()
    last = build_list(wb, bugs)          # 'Danh sách Bug' trước: Report + SPEC-GAP trỏ COUNTIF vào nó
    last_row = build_report(wb, meta, bugs, last)   # dòng cuối nội dung -> neo dải đồi cỏ
    build_specgap(wb, bugs)              # sheet 3: filter SPEC-GAP cho BA

    # --- BẤT BIẾN LAYOUT: sổ bug đang mở phải in ĐỦ. Lỗi lưới (merge trùm ngang qua khối
    #     phải) nuốt ô mà KHÔNG báo gì — đã dính 2 lần. Đếm lại trên file thật, lệch => raise.
    rep = wb[BR["sheet_names"][0]]
    n_open = sum(1 for b in bugs if b.get("status") == "Mở")
    shown = sum(1 for row in rep.iter_rows(min_col=10, max_col=10)
                for c in row if isinstance(c.value, str) and c.value.startswith("BUG-"))
    want = min(n_open, BR["top_open_max"])
    if shown != want:
        raise SystemExit(f"LỖI LAYOUT: bảng 'Top bug đang mở' in {shown} dòng, phải {want}. "
                         f"Nhiều khả năng một merge_cells trùm ngang qua khối phải (J..M).")
    # Thứ tự sheet = ĐẶT THẲNG theo theme, không move_sheet(-1) (offset TƯƠNG ĐỐI: 'Tổng quan'
    # vốn ở index 0, dời -1 nữa là nó chạy ngược ra sau => sếp mở file thấy bảng thô). active=0
    # để file luôn mở ở Tổng quan dù ai lưu lúc đang đứng sheet nào.
    wb._sheets = [wb[n] for n in BR["sheet_names"]]
    wb.active = 0

    # Thuộc tính file: mặc định openpyxl ghi creator='openpyxl' — bấm xem info là lộ ngay
    # file do máy đẻ. Đây là deliverable của QA, ghi đúng tên chủ.
    wb.properties.creator = meta.get("tester", "QA-Server")
    wb.properties.lastModifiedBy = meta.get("tester", "QA-Server")
    wb.properties.title = f"{BR['title']} — {meta.get('project', '')}"
    wb.properties.description = "Sinh từ bug-he-thong.tcs.json. Đừng sửa tay: sửa JSON rồi build lại."

    # In: khổ A4, vừa bề ngang 1 trang, List bug lặp header mỗi trang + số trang.
    # (Mẫu của sếp KHÔNG có mấy cái này — đây là làm hơn, không phải bắt chước.)
    for ws in wb.worksheets:
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
        ws.print_options.horizontalCentered = True
        ws.oddFooter.right.text = "&P / &N"
        ws.oddFooter.left.text = meta.get("project", "")
    wb[BR["sheet_names"][1]].print_title_rows = f"{HDR_ROW}:{HDR_ROW + 1}"

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    _inject_decor(out, last_row)   # splice mây/mặt trời/đồi cỏ vào drawing1.xml (nếu decor bật)
    n_life = {st: sum(1 for b in bugs if b["status"] == st) for st in LIFE}
    skin = "decor ON (trời+kem+đồi cỏ)" if DECOR.get("enabled") else "sạch (navy/trắng)"
    print(f"OK -> {out}  ({len(bugs)} bug, {len(BR['sheet_names'])} sheet: {'/'.join(BR['sheet_names'])}) · {skin}")
    print(f"   {' · '.join(f'{k} {v}' for k, v in n_life.items())}")


if __name__ == "__main__":
    main()
