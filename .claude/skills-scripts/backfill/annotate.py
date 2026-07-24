#!/usr/bin/env python3
"""annotate.py <folder> — đọc captures.json → mỗi ảnh thêm dải caption đỏ (note) + khoanh box (nếu có).
Generic, ko hardcode branch. Box coords = fraction [fx,fy,fw,fh,label] (nếu manifest có).
Output: <file>_ann.png cạnh ảnh gốc.
"""
import json, sys
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
    p = Path(entry["file"])
    if not p.exists(): return None
    im = Image.open(p).convert("RGB")
    W, H = im.size
    strip = max(64, W // 30)
    out = Image.new("RGB", (W, H + strip), "white")
    out.paste(im, (0, strip))
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, W, strip], fill=(183, 28, 28))
    cap = f"[{entry['phase'].upper()}] {entry['screen']} — {entry.get('note','')}"
    d.text((16, strip // 2), cap[:180], fill="white", font=font(int(strip * 0.42)), anchor="lm")
    for b in entry.get("boxes", []):
        fx, fy, fw, fh = b[:4]
        x0, y0, x1, y1 = fx * W, strip + fy * H, (fx + fw) * W, strip + (fy + fh) * H
        for w in range(6):
            d.rectangle([x0 - w, y0 - w, x1 + w, y1 + w], outline=(220, 0, 0))
    dst = p.with_name(p.stem + "_ann.png")
    out.save(dst)
    return dst.name

n = 0
for phase in ("before", "after"):
    for e in manifest.get(phase, []):
        r = annotate(e)
        if r: n += 1; print("ANN", r)
print(f"OK annotate.py: {n} ảnh")
