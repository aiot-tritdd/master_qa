#!/usr/bin/env python3
"""build_a11y_report.py — a11y.results.json -> <Case>.a11y.xlsx (1 sheet 'Accessibility').
Oracle = WCAG (axe), KHÔNG phải spec. CƠ KHÍ, không reasoning."""
import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage

IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}
IMPACT_FILL = {"critical": "C0392B", "serious": "E67E22", "moderate": "F1C40F", "minor": "BDC3C7"}
# Thứ tự cột theo cách ĐỌC HIỂU LỖI: mã → kiểm gì → CHI TIẾT (đo được) → CÁCH FIX (tách riêng) → tài liệu → file ảnh → ảnh.
HEADERS = ["Màn", "App", "URL", "Mã lỗi (rule)", "WCAG", "Mức", "Số chỗ",
           "Lỗi gì (rule kiểm gì)", "Chi tiết (axe đo được)", "Cách fix", "Tài liệu", "File ảnh", "Evidence"]

# Gợi ý fix theo rule — kiến thức WCAG PHỔ QUÁT (không dính code sản phẩm → không phá tường black-box).
# (detail_fallback, fix). Rule không có ở đây → detail dùng axe, fix trỏ helpUrl.
RULE_GUIDE = {
    "color-contrast": ("Tương phản chữ/nền dưới ngưỡng (số đo ở cột này).",
        "Tăng tương phản ≥ 4.5:1 (chữ thường) hoặc ≥ 3:1 (chữ ≥24px / ≥18.66px in đậm): đổi màu chữ đậm hơn hoặc đổi nền."),
    "select-name": ("Thẻ <select> không có accessible name → screen-reader chỉ đọc 'combobox', không rõ chọn gì.",
        "Thêm <label> (bọc hoặc for=id), hoặc aria-label / aria-labelledby / title cho <select>."),
    "label": ("Ô nhập (input) không có nhãn liên kết.",
        "Gắn <label for=id> hoặc aria-label cho mỗi input."),
    "scrollable-region-focusable": ("Vùng cuộn được nhưng không nhận focus bàn phím → người dùng keyboard không cuộn hết.",
        'Thêm tabindex="0" cho vùng cuộn (hoặc để phần tử con focus được).'),
    "button-name": ("Nút không có text/nhãn đọc được.", "Thêm text trong <button> hoặc aria-label."),
    "image-alt": ("Ảnh <img> thiếu alt.", 'Thêm alt mô tả (hoặc alt="" nếu ảnh trang trí).'),
    "link-name": ("Link không có text đọc được.", "Thêm text trong <a> hoặc aria-label."),
}


def _measured_line(fs):
    """Trích dòng có SỐ ĐO cụ thể trong failureSummary (contrast/ratio). Rule không đo được → ''."""
    for line in (fs or "").splitlines():
        s = line.strip()
        if "contrast of" in s or ("ratio of" in s and any(ch.isdigit() for ch in s)):
            return s
    return ""


def _detail_and_fix(v):
    """Tách CHI TIẾT (vì sao lỗi, ưu tiên số đo axe) và CÁCH FIX (riêng) — vừa phải, dễ đọc."""
    nodes = v.get("nodes") or []
    fs = nodes[0].get("failureSummary") if nodes else ""
    measured = _measured_line(fs)
    guide = RULE_GUIDE.get(v.get("rule"))
    if guide:
        detail = measured or guide[0]
        fix = guide[1]
    else:
        detail = measured or (v.get("description") or v.get("help") or "").strip()
        url = v.get("helpUrl", "")
        fix = f"Xem hướng dẫn: {url}" if url else (v.get("help") or "")
    return detail, fix

def build(results_path, out_path):
    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)
    base = os.path.dirname(os.path.abspath(results_path))
    wb = Workbook(); ws = wb.active; ws.title = "Accessibility"
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(1, c, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2C3E50")
    top = Alignment(wrap_text=True, vertical="top")
    r = 2
    for scr in data.get("screens", []):
        for v in sorted(scr.get("violations", []), key=lambda x: IMPACT_ORDER.get(x.get("impact"), 9)):
            nodes = v.get("nodes", [])
            ws.cell(r, 1, scr.get("name", "")); ws.cell(r, 2, scr.get("app", "")); ws.cell(r, 3, scr.get("url", ""))
            ws.cell(r, 4, v.get("rule", ""))                       # mã lỗi
            ws.cell(r, 5, v.get("wcag", ""))                       # WCAG SC
            mc = ws.cell(r, 6, v.get("impact", ""))                # mức
            mc.fill = PatternFill("solid", fgColor=IMPACT_FILL.get(v.get("impact"), "BDC3C7"))
            ws.cell(r, 7, len(nodes))                              # số chỗ dính
            # Lỗi gì: rule kiểm cái gì (description; fallback help)
            ws.cell(r, 8, v.get("description") or v.get("help", "")).alignment = top
            detail, fix = _detail_and_fix(v)
            ws.cell(r, 9, detail).alignment = top                  # CHI TIẾT (vì sao — đo được)
            ws.cell(r, 10, fix).alignment = top                    # CÁCH FIX (tách riêng)
            ws.cell(r, 11, v.get("helpUrl", "")).alignment = top   # tài liệu (helpUrl axe — version-matched)
            shot = v.get("shot")
            fname = os.path.basename(shot) if shot else ""
            ws.cell(r, 12, fname).alignment = top                  # File ảnh: dò ngược vào shots/ được
            if shot and os.path.exists(os.path.join(base, shot)):
                img = XLImage(os.path.join(base, shot)); img.width = 240; img.height = 150
                ws.add_image(img, f"M{r}")
            ws.row_dimensions[r].height = 150
            r += 1
    if r == 2:
        ws.cell(2, 1, "Không có vi phạm a11y nào ở các màn đã quét.")
    for col, w in zip("ABCDEFGHIJKLM", (16, 10, 20, 15, 8, 9, 6, 28, 40, 40, 30, 34, 34)):
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
