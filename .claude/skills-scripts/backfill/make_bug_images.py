#!/usr/bin/env python3
"""make_bug_images.py <folder> — đọc bugs.json → mỗi bug 1 ảnh evidence panel (title+severity+evidence).
Generic. Output: after/bug_<id>.png
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

folder = Path(sys.argv[1])
after = folder / "after"; after.mkdir(exist_ok=True)
data = json.loads((folder / "bugs.json").read_text()) if (folder / "bugs.json").exists() else {"bugs": []}

def font(sz, mono=False):
    paths = (["/System/Library/Fonts/Menlo.ttc"] if mono else []) + ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/System/Library/Fonts/Hiragino Sans GB.ttc"]
    for p in paths:
        try: return ImageFont.truetype(p, sz)
        except Exception: continue
    return ImageFont.load_default()

def wrap(txt, n=90):
    out = []
    for line in str(txt).split("\n"):
        while len(line) > n:
            out.append(line[:n]); line = line[n:]
        out.append(line)
    return out

def panel(bug):
    W = 1500
    evi = wrap(bug.get("evidence", ""))
    H = 130 + len(evi) * 26 + 30
    im = Image.new("RGB", (W, H), (245, 246, 248)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 50], fill=(183, 28, 28))
    d.text((20, 25), f"{bug['id']} — {bug.get('title','')}", fill="white", font=font(22), anchor="lm")
    d.rectangle([20, 62, W - 20, 100], fill=(255, 242, 204))
    d.text((32, 81), f"Mức độ: {bug.get('severity','?')}  ·  Trạng thái: {'CONFIRMED' if bug.get('confirmed') else 'nghi ngờ'}", fill=(127, 96, 0), font=font(16), anchor="lm")
    d.rectangle([20, 110, W - 20, H - 12], fill=(250, 250, 250), outline=(200, 200, 200))
    y = 130
    d.text((32, y), "Bằng chứng (console/DB):", fill=(31, 56, 100), font=font(15)); y += 26
    for line in evi:
        d.text((44, y), line, fill=(20, 20, 20), font=font(14, True)); y += 26
    dst = after / f"bug_{bug['id']}.png"
    im.save(dst); return dst.name

n = 0
for b in data.get("bugs", []):
    print("IMG", panel(b)); n += 1
print(f"OK make_bug_images.py: {n} ảnh bug")
