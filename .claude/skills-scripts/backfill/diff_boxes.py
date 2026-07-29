#!/usr/bin/env python3
"""diff_boxes.py <folder> — SO ảnh TRƯỚC vs SAU của từng màn, tự KHOANH VÙNG chỗ khác nhau.

Vì sao cần: sếp/khách mở file ra thấy 2 ảnh giống nhau y đúc, không biết phải nhìn vào đâu.
Script này tìm đúng vùng pixel đã đổi rồi ghi toạ độ vào `captures.json` (field `boxes`), để
`annotate.py` vẽ khung đỏ lên CẢ 2 ảnh ở CÙNG một vị trí → mắt đối chiếu được ngay.

Không dùng numpy (venv không có) → diff theo LƯỚI Ô: chia ảnh thành ô ~28px, ô nào lệch quá ngưỡng
thì đánh dấu, gộp các ô liền nhau thành 1 khung. Bỏ ô lẻ (nhiễu do render/scroll).

Ghi thêm `diff_explain` (lời giải thích nghiệp vụ) lấy từ REPORT_REGISTRY.json / FUNC_CASES.json —
KHÔNG nói về code, nói cái người dùng thấy.
"""
import json, sys
from pathlib import Path
from PIL import Image

folder = Path(sys.argv[1])
SK = Path(__file__).parent.parent.parent / "skills" / "backfill"
CELL = 28           # cạnh ô lưới (px)
THRESH = 14         # lệch sáng trung bình/ô coi là "đã đổi"
MIN_CELLS = 2       # cụm nhỏ hơn số ô này = nhiễu, bỏ
MAX_BOXES = 6       # nhiều khung quá thì rối → giữ N cụm to nhất


def rj(p, d):
    return json.loads(p.read_text()) if p.exists() else d


caps = rj(folder / "captures.json", {"before": [], "after": []})
registry = {r["key"]: r for r in rj(SK / "REPORT_REGISTRY.json", {"reports": []})["reports"]}
fcases = {c["id"]: c for c in rj(SK / "FUNC_CASES.json", {"cases": []})["cases"]}


def grid_diff(pa, pb):
    """Trả (boxes dạng fraction, tỉ lệ % ô đã đổi). Ảnh khác kích thước → cắt về phần chung."""
    a = Image.open(pa).convert("L")
    b = Image.open(pb).convert("L")
    W, H = min(a.width, b.width), min(a.height, b.height)
    if W < CELL or H < CELL:
        return [], 0.0
    a = a.crop((0, 0, W, H)); b = b.crop((0, 0, W, H))
    cols, rows = W // CELL, H // CELL
    da, db = a.load(), b.load()
    marked = set()
    for gy in range(rows):
        for gx in range(cols):
            x0, y0 = gx * CELL, gy * CELL
            tot = 0
            # lấy mẫu 7x7 điểm trong ô (đủ nhạy, nhanh hơn quét hết pixel)
            step = max(1, CELL // 7)
            n = 0
            for yy in range(y0, y0 + CELL, step):
                for xx in range(x0, x0 + CELL, step):
                    tot += abs(da[xx, yy] - db[xx, yy]); n += 1
            if n and tot / n >= THRESH:
                marked.add((gx, gy))
    if not marked:
        return [], 0.0
    # gộp ô liền nhau (4 hướng) thành cụm
    seen, clusters = set(), []
    for cell in marked:
        if cell in seen:
            continue
        stack, comp = [cell], []
        seen.add(cell)
        while stack:
            cx, cy = stack.pop()
            comp.append((cx, cy))
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if (nx, ny) in marked and (nx, ny) not in seen:
                    seen.add((nx, ny)); stack.append((nx, ny))
        if len(comp) >= MIN_CELLS:
            clusters.append(comp)
    clusters.sort(key=len, reverse=True)
    boxes = []
    for comp in clusters[:MAX_BOXES]:
        xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
        x0 = min(xs) * CELL; y0 = min(ys) * CELL
        x1 = (max(xs) + 1) * CELL; y1 = (max(ys) + 1) * CELL
        boxes.append([round(x0 / W, 4), round(y0 / H, 4), round((x1 - x0) / W, 4), round((y1 - y0) / H, 4)])
    return boxes, round(100.0 * len(marked) / max(1, cols * rows), 1)


def explain(entry):
    """Lời giải thích NGHIỆP VỤ cho khác biệt — không nói code."""
    scr = entry.get("screen", "")
    if entry.get("sheet") == "2_REPORT" and scr in registry:
        return registry[scr].get("diff_explain") or ""
    cid = entry.get("case_id") or (scr.split("_")[1] if scr.startswith("func_") else None)
    if cid and cid in fcases:
        return fcases[cid].get("diff_explain") or ""
    return ""


pairs = {}
for ph in ("before", "after"):
    for e in caps.get(ph, []):
        if e.get("file"):
            pairs.setdefault(e["screen"], {})[ph] = e

n_box = n_same = 0
for screen, v in pairs.items():
    b, a = v.get("before"), v.get("after")
    if not (b and a and Path(b["file"]).exists() and Path(a["file"]).exists()):
        continue
    boxes, pct = grid_diff(b["file"], a["file"])
    ex = explain(a)
    for e in (b, a):
        e["boxes"] = boxes
        e["diff_pct"] = pct
        if boxes:
            e["diff_note"] = (f"⬛ {len(boxes)} vùng khoanh đỏ = chỗ ĐÃ ĐỔI giữa trước và sau "
                              f"({pct}% diện tích màn). " + (ex or "Xem giải thích ở dòng 📌 phía trên."))
        else:
            e["diff_note"] = "✅ Không có vùng nào đổi — màn này TRƯỚC và SAU giống nhau." + (f" {ex}" if ex else "")
    if boxes:
        n_box += 1
        print(f"  {screen}: {len(boxes)} vùng đổi ({pct}%)")
    else:
        n_same += 1

(folder / "captures.json").write_text(json.dumps(caps, indent=2, ensure_ascii=False))
print(f"OK diff_boxes.py: {n_box} màn CÓ khác biệt (đã khoanh vùng) · {n_same} màn giống hệt")
