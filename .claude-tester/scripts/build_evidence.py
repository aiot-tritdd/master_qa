# -*- coding: utf-8 -*-
"""Sinh file Test Case Evidence (.xlsx) đẹp theo TestCase_Evidence_Template(2).

Dùng: python3 build_evidence.py <data.json> <out.xlsx> [<shots_dir>]

data.json:
{
  "meta": {"project":"...","module":"No.X ...","issue":"...",
            "tester":"...","date":"2026/07/04","env":"Dev ..."},
  "shots_dir": "shots/j",
  "tcs": [
    {"id":"TC-01","screen":"...","pri":"High|Medium|Low","result":"PASS|FAIL|未実施",
     "title":"...","pre":"...","steps":"1. ...\n2. ...","expect":"...",
     "actual":"...","note":"(tuỳ chọn, kỹ thuật/PR)","before":"a.png","after":"b.png"}
  ]
}
Layout: Before = cột E..L, After = cột M..T (theo theme.json); ảnh BIND in-cell (co giãn theo ô).
"""
import sys, os, json, re
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import TwoCellAnchor, AnchorMarker

JSON_PATH = sys.argv[1]
data = json.load(open(JSON_PATH, encoding='utf-8'))
OUT = sys.argv[2]
# Ưu tiên: tham số CLI (arg3) > shots_dir trong json > 'shots' cạnh file json.
_json_dir = os.path.dirname(os.path.abspath(JSON_PATH))
if len(sys.argv) > 3:
    SHOTS = sys.argv[3]
elif data.get('shots_dir'):
    SHOTS = data['shots_dir'] if os.path.isabs(data['shots_dir']) else os.path.join(_json_dir, data['shots_dir'])
else:
    SHOTS = os.path.join(_json_dir, 'shots')
meta = data.get('meta', {})
TCS = data['tcs']

# ----- theme (nguồn sự thật cho format) -----
_theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'theme.json')
THEME = json.load(open(_theme_path, encoding='utf-8'))
P = THEME['palette']; FT = THEME['fonts']; LY = THEME['layout']; LB = THEME['labels']
NAVY, BLUE, LBLUE = P['navy'], P['blue'], P['lblue']
GREEN, GREEN_TX = P['green_bg'], P['green_tx']
RED, ORANGE, GREY = P['red'], P['orange'], P['grey']
YEL, YEL_TX = P['yellow_bg'], P['yellow_tx']
FAIL_BG = P['fail_bg']
NOTE_BG, WHITE, PH_BG, PH_TX = P['note_bg'], P['white'], P['placeholder_bg'], P['placeholder_tx']
NUM_BG, NUM_TX, TS_TX = P['num_bg'], P['num_tx'], P['tester_tx']
EB0, EB1 = LY['evidence_before']   # vùng Evidence (Before), chỉ số cột 1-based
EA0, EA1 = LY['evidence_after']    # vùng Evidence (After)
LAST = EA1                          # cột cuối của sheet Test Cases

def F(color): return PatternFill('solid', fgColor=color)
thin = Side(style='thin', color=P['border'])
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical='top')
center = Alignment(horizontal='center', vertical='center', wrap_text=True)
vcenter = Alignment(horizontal='left', vertical='center', wrap_text=True)

def br(text):
    """Xuống dòng sau dấu chấm câu ('. ' hoặc '。') để nội dung dễ đọc trong ô."""
    if not text: return text
    text = re.sub(r'(?<!\d)\.\s+', '.\n', text)  # bỏ qua "1. " của danh sách bước
    return text.replace('。', '。\n').rstrip('\n')

def result_style(res):
    s = LB['status'].get(res, LB['status']['未実施'])
    return (s['text'], P[s['bg']], P[s['tx']])

def pri_color(pri):
    pr = LB['priority']
    return P[pr.get(pri, pr['_default'])]

wb = openpyxl.Workbook()

# ================= Cover =================
cov = wb.active; cov.title = 'Cover'
cov.column_dimensions['A'].width = 4
cov.column_dimensions['B'].width = 22
cov.column_dimensions['C'].width = 55
cov.column_dimensions['D'].width = 4
cov.merge_cells('B2:C3')
t = cov['B2']; t.value = 'TEST CASE EVIDENCE REPORT'
t.fill = F(NAVY); t.font = Font(bold=True, size=18, color=WHITE)
t.alignment = Alignment(horizontal='center', vertical='center')
info = [('Project', meta.get('project', '')), ('Screen / Module', meta.get('module', '')),
        ('Issue', meta.get('issue', '')), ('Tester', meta.get('tester', '')),
        ('Test Date', meta.get('date', '')), ('Environment', meta.get('env', ''))]
r = 5
for k, v in info:
    lc = cov.cell(r, 2, k); lc.fill = F(LBLUE); lc.font = Font(bold=True, size=10, color=NAVY)
    lc.alignment = vcenter
    vc = cov.cell(r, 3, v); vc.font = Font(size=10); vc.alignment = vcenter
    for c in (2, 3): cov.cell(r, c).border = border
    cov.row_dimensions[r].height = 20
    r += 1
r += 1
cov.merge_cells(f'B{r}:C{r}')
sm = cov.cell(r, 2, 'SUMMARY'); sm.fill = F(BLUE); sm.font = Font(bold=True, size=12, color=WHITE)
sm.alignment = Alignment(horizontal='center', vertical='center')
cov.row_dimensions[r].height = 22
r += 1
for lbl, formula, fill, tx in [
        ('Total TC', '=COUNTIF(\'Test Cases\'!A:A,"TC-*")', LBLUE, NAVY),
        ('PASS', '=COUNTIF(\'Test Cases\'!C:C,"PASS*")', GREEN, GREEN_TX),
        ('FAIL', '=COUNTIF(\'Test Cases\'!C:C,"FAIL*")', FAIL_BG, RED),
        ('未実施', '=COUNTIF(\'Test Cases\'!C:C,"未実施*")', YEL, YEL_TX)]:
    lc = cov.cell(r, 2, lbl); lc.fill = F(LBLUE); lc.font = Font(bold=True, size=10, color=NAVY)
    lc.alignment = vcenter
    vc = cov.cell(r, 3, formula); vc.fill = F(fill); vc.font = Font(bold=True, size=14, color=tx)
    vc.alignment = Alignment(horizontal='center', vertical='center')
    for c in (2, 3): cov.cell(r, c).border = border
    cov.row_dimensions[r].height = 22
    r += 1

# ================= Test Cases =================
ws = wb.create_sheet('Test Cases')
ws.freeze_panes = 'A3'  # cố định title (row 1) + header (row 2)
w = dict(LY['detail_cols'])
for ci in range(EB0, LAST + 1):
    w[get_column_letter(ci)] = LY['evidence_col_width']
for col, v in w.items():
    ws.column_dimensions[col].width = v

ws.merge_cells(f'A1:{get_column_letter(LAST)}1')
tt = ws['A1']; tt.value = 'TEST CASES — ' + meta.get('module', '')
tt.fill = F(NAVY); tt.font = Font(bold=True, size=16, color=WHITE)
tt.alignment = Alignment(horizontal='left', vertical='center')
ws.row_dimensions[1].height = 28

# header row 2
ws.merge_cells(start_row=2, start_column=EB0, end_row=2, end_column=EB1)
ws.merge_cells(start_row=2, start_column=EA0, end_row=2, end_column=EA1)
for coord, val, algn in [('A2', '#', center), ('B2', 'Field', vcenter),
        ('C2', LB['detail_header'], vcenter),
        (f'{get_column_letter(EB0)}2', LB['evidence_before'], center),
        (f'{get_column_letter(EA0)}2', LB['evidence_after'], center)]:
    c = ws[coord]; c.value = val; c.fill = F(NAVY); c.font = Font(bold=True, size=10, color=WHITE)
    c.alignment = algn
for c in range(1, LAST + 1): ws.cell(2, c).fill = F(NAVY); ws.cell(2, c).border = border
ws.row_dimensions[2].height = 22

FIELDS = LB['fields']
LONG_FIELDS = set(LY['detail_long_fields'])

def bind_image(name, col0, row0, col1, row1):
    for ext in (name, os.path.splitext(name)[0] + '.jpg', os.path.splitext(name)[0] + '.png'):
        full = os.path.join(SHOTS, ext)
        if os.path.exists(full):
            xi = XLImage(full)
            xi.anchor = TwoCellAnchor(editAs='twoCell',
                _from=AnchorMarker(col=col0, colOff=20000, row=row0, rowOff=20000),
                to=AnchorMarker(col=col1, colOff=-20000, row=row1, rowOff=-20000))
            ws.add_image(xi); return True
    return False

row = 3
for tc in TCS:
    base = row
    status_txt, status_fill, status_tx = result_style(tc['result'])
    # --- title row ---
    idc = ws.cell(base, 1, tc['id']); idc.fill = F(BLUE); idc.font = Font(bold=True, size=10, color=WHITE)
    idc.alignment = center
    ws.merge_cells(start_row=base, start_column=2, end_row=base, end_column=3)
    ti = ws.cell(base, 2, f"[{tc.get('screen','')}]  {tc.get('title','')}")
    ti.fill = F(BLUE); ti.font = Font(bold=True, size=11, color=WHITE); ti.alignment = vcenter
    ws.cell(base, 4).fill = F(BLUE)
    # Priority badge E:G, status H:J, tester K:P
    ws.merge_cells(start_row=base, start_column=5, end_row=base, end_column=7)
    pr = ws.cell(base, 5, f"Priority: {tc.get('pri','')}")
    pr.fill = F(pri_color(tc.get('pri', ''))); pr.font = Font(bold=True, size=10, color=WHITE); pr.alignment = center
    ws.merge_cells(start_row=base, start_column=8, end_row=base, end_column=10)
    st = ws.cell(base, 8, status_txt); st.fill = F(status_fill)
    st.font = Font(bold=True, size=10, color=status_tx); st.alignment = center
    ws.merge_cells(start_row=base, start_column=11, end_row=base, end_column=LAST)
    tsr = ws.cell(base, 11, LB['tester']); tsr.fill = F(PH_BG)
    tsr.font = Font(size=9, color=TS_TX); tsr.alignment = vcenter
    for c in range(1, LAST + 1): ws.cell(base, c).border = border
    ws.row_dimensions[base].height = 30

    # --- detail rows ---
    vals = [tc.get('title', ''), br(tc.get('pre', '')), br(tc.get('steps', '')),
            br(tc.get('expect', '')), br(tc.get('actual', ''))]
    for i, (fld, val) in enumerate(zip(FIELDS, vals)):
        rr = base + 1 + i
        nc = ws.cell(rr, 1, str(i + 1)); nc.fill = F(NUM_BG); nc.font = Font(size=9, color=NUM_TX); nc.alignment = center
        lc = ws.cell(rr, 2, fld); lc.fill = F(LBLUE); lc.font = Font(bold=True, size=10, color=NAVY); lc.alignment = wrap
        dc = ws.cell(rr, 3, val); dc.font = Font(size=10); dc.alignment = wrap
        dc.fill = F(status_fill if fld == 'Actual Result' else WHITE)
        if fld == 'Actual Result' and tc['result'] != 'FAIL':
            dc.font = Font(size=10, color=(GREEN_TX if tc['result'] == 'PASS' else YEL_TX))
        elif fld == 'Actual Result':
            dc.font = Font(size=10, bold=True, color=WHITE)
        for c in (1, 2, 3): ws.cell(rr, c).border = border
        ws.row_dimensions[rr].height = LY['row_heights']['detail_long'] if fld in LONG_FIELDS else LY['row_heights']['detail_short']

    # --- evidence areas (Before/After theo theme layout) ---
    ws.merge_cells(start_row=base + 1, start_column=EB0, end_row=base + 5, end_column=EB1)
    ws.merge_cells(start_row=base + 1, start_column=EA0, end_row=base + 5, end_column=EA1)
    for c1, img, lbl in [(EB0, tc.get('before'), 'Before'), (EA0, tc.get('after'), 'After')]:
        cell = ws.cell(base + 1, c1); cell.alignment = center; cell.fill = F(PH_BG)
        cell.font = Font(size=11, color=PH_TX)
        if not img:
            cell.value = LB['placeholder_na'] if tc['result'] == 'PASS' else LB['placeholder_none']
        else:
            cell.value = None
    for rr in range(base + 1, base + 6):
        for c in range(EB0, LAST + 1): ws.cell(rr, c).border = border
    if tc.get('before'): bind_image(tc['before'], EB0 - 1, base, EB1, base + 5)
    if tc.get('after'): bind_image(tc['after'], EA0 - 1, base, EA1, base + 5)

    # --- note row ---
    nrow = base + 6
    na = ws.cell(nrow, 1, '📝'); na.fill = F(NOTE_BG); na.font = Font(size=12); na.alignment = center
    nb = ws.cell(nrow, 2, LB['note']); nb.fill = F(NOTE_BG); nb.font = Font(bold=True, size=10, color=YEL_TX); nb.alignment = vcenter
    ws.merge_cells(start_row=nrow, start_column=3, end_row=nrow, end_column=LAST)
    nc = ws.cell(nrow, 3, tc.get('note', '') or ''); nc.fill = F(NOTE_BG)
    nc.font = Font(size=9, color=TS_TX); nc.alignment = wrap
    for c in range(1, LAST + 1): ws.cell(nrow, c).border = border
    ws.row_dimensions[nrow].height = 32
    # spacer
    ws.row_dimensions[base + 7].height = 6
    row = base + 8

# ================= Checklist =================
ck = wb.create_sheet('Checklist')
ck.merge_cells('A1:F1')
h1 = ck['A1']; h1.value = 'CHECKLIST'; h1.fill = F(NAVY); h1.font = Font(bold=True, size=14, color=WHITE)
h1.alignment = Alignment(horizontal='left', vertical='center')
ck.row_dimensions[1].height = 24
ck.freeze_panes = 'A4'  # cố định tới hết header (row 3)
for col, v in LY['checklist_cols'].items():
    ck.column_dimensions[col].width = v
for i, hh in enumerate(['#', 'TC ID', 'Test Case Title', 'Priority', 'Result', 'Nguồn / 発生元']):
    c = ck.cell(3, i + 1, hh); c.fill = F(NAVY); c.font = Font(bold=True, size=10, color=WHITE)
    c.alignment = center; c.border = border
ck.row_dimensions[3].height = 20
for i, tc in enumerate(TCS):
    rr = 4 + i
    ck.cell(rr, 1, i + 1).alignment = center
    ck.cell(rr, 2, tc['id']).font = Font(bold=True, color=BLUE)
    cc = ck.cell(rr, 3, f"[{tc.get('screen','')}] {tc.get('title','')}"); cc.alignment = wrap
    pc = ck.cell(rr, 4, tc.get('pri', '')); pc.alignment = center
    pc.font = Font(bold=True, color=pri_color(tc.get('pri', '')))
    stt, sfill, stx = result_style(tc['result'])
    rc = ck.cell(rr, 5, stt); rc.fill = F(sfill); rc.font = Font(bold=True, color=stx); rc.alignment = center
    src = tc.get('source', '') or ''
    sc = ck.cell(rr, 6, src); sc.alignment = wrap
    if src:
        sc.fill = F(YEL); sc.font = Font(bold=True, size=9, color=YEL_TX)
    for c in range(1, 7): ck.cell(rr, c).border = border
last = 3 + len(TCS)
for i, (lbl, formula, fill, tx) in enumerate([
        ('Total', f'=COUNTA(E4:E{last})', LBLUE, NAVY),
        ('PASS', f'=COUNTIF(E4:E{last},"'+LB['status']['PASS']['count_match']+'")', GREEN, GREEN_TX),
        ('FAIL', f'=COUNTIF(E4:E{last},"'+LB['status']['FAIL']['count_match']+'")', FAIL_BG, RED),
        ('未実施', f'=COUNTIF(E4:E{last},"'+LB['status']['未実施']['count_match']+'")', YEL, YEL_TX)]):
    rr = last + 2 + i
    lc = ck.cell(rr, 4, lbl); lc.fill = F(fill); lc.font = Font(bold=True, color=tx); lc.border = border
    lc.alignment = center
    vc = ck.cell(rr, 5, formula); vc.fill = F(fill); vc.font = Font(bold=True, color=tx); vc.border = border
    vc.alignment = center

wb.save(OUT)
print(f'saved {OUT} | tcs={len(TCS)} images={len(ws._images)}')
