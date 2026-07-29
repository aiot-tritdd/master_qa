#!/usr/bin/env python3
"""annotate.py <folder> — đọc captures.json → mỗi ảnh thêm:
  · dải tiêu đề đỏ (màn nào, trước/sau)
  · KHUNG ĐỎ ĐÁNH SỐ ở đúng vùng đã đổi (toạ độ do diff_boxes.py tính, cùng vị trí trên cả 2 ảnh)
  · dải chú thích vàng bên dưới: giải thích khác biệt bằng NGÔN NGỮ NGHIỆP VỤ (không nói code)

Chạy SAU diff_boxes.py. Output: <file>_ann.png cạnh ảnh gốc.
"""
import json, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

folder = Path(sys.argv[1])
manifest = json.loads((folder / "captures.json").read_text()) if (folder / "captures.json").exists() else {"before": [], "after": []}


def font(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/System/Library/Fonts/Hiragino Sans GB.ttc"]:
        try: return ImageFont.truetype(p, sz)
        except Exception: continue
    return ImageFont.load_default()


def annotate(entry):
    # entry có thể KHÔNG có ảnh: màn lỗi HTTP, report chỉ-có-CSV, entry ref_screen (dùng ảnh sheet khác)
    if not entry.get("file"): return None
    p = Path(entry["file"])
    if not p.exists(): return None
    im = Image.open(p).convert("RGB")
    W, H = im.size
    top = max(64, W // 30)
    boxes = entry.get("boxes") or []
    note = entry.get("diff_note") or ""
    # dải chú thích dưới: cao theo số dòng chữ
    fs = max(15, int(top * 0.34))
    wrap_at = max(40, W // (fs // 2 + 4))
    lines = textwrap.wrap(note, wrap_at) if note else []
    bot = (len(lines) * int(fs * 1.5) + 22) if lines else 0

    out = Image.new("RGB", (W, H + top + bot), "white")
    out.paste(im, (0, top))
    d = ImageDraw.Draw(out)

    # tiêu đề
    d.rectangle([0, 0, W, top], fill=(183, 28, 28))
    cap = f"[{entry['phase'].upper()}] {entry['screen']} — {entry.get('note','')}"
    d.text((16, top // 2), cap[:190], fill="white", font=font(int(top * 0.42)), anchor="lm")

    # khung đỏ + số thứ tự vùng (vẽ ở CÙNG toạ độ trên ảnh trước và sau → mắt so được)
    for i, b in enumerate(boxes, start=1):
        fx, fy, fw, fh = b[:4]
        x0, y0 = fx * W, top + fy * H
        x1, y1 = (fx + fw) * W, top + (fy + fh) * H
        pad = max(3, W // 500)
        for w in range(pad):
            d.rectangle([x0 - w, y0 - w, x1 + w, y1 + w], outline=(230, 0, 0))
        # nhãn số: nền đỏ, chữ trắng, đặt góc trên-trái khung
        r = max(16, W // 90)
        d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=(230, 0, 0))
        d.text((x0, y0), str(i), fill="white", font=font(int(r * 1.2)), anchor="mm")

    # chú thích nghiệp vụ
    if lines:
        d.rectangle([0, H + top, W, H + top + bot], fill=(255, 249, 219))
        y = H + top + 10
        for ln in lines:
            d.text((16, y), ln, fill=(90, 60, 0), font=font(fs))
            y += int(fs * 1.5)

    dst = p.with_name(p.stem + "_ann.png")
    out.save(dst)
    return dst.name


n = nb = 0
for phase in ("before", "after"):
    for e in manifest.get(phase, []):
        r = annotate(e)
        if r:
            n += 1
            if e.get("boxes"): nb += 1
print(f"OK annotate.py: {n} ảnh ({nb} ảnh có khoanh vùng khác biệt)")
