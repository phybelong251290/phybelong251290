"""Cut a numbered emblem contact sheet into one tile per emblem, padded to the card photo box (19:24)."""
import sys, os
import numpy as np
from PIL import Image

SHEET = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "emblems"
os.makedirs(OUT, exist_ok=True)

im = Image.open(SHEET).convert("RGB")
a = np.asarray(im).astype(int)
diff = np.abs(a - a[2, 2]).sum(axis=2) > 40

def runs(v, gap=6):
    out, s, last = [], None, None
    for i, x in enumerate(v):
        if x:
            if s is None: s = i
            last = i
        elif s is not None and i - last > gap:
            out.append((s, last)); s = None
    if s is not None: out.append((s, last))
    return out

cols = runs(diff.any(axis=0))
rows = [r for r in runs(diff.any(axis=1)) if r[1] - r[0] > 100]   # drop the thin number-label rows
W, H, BG = 380, 480, (242, 244, 248)                               # 19:24
n = 0
for (y0, y1) in rows:
    for (x0, x1) in cols:
        n += 1
        t = im.crop((x0, y0, x1 + 1, y1 + 1))
        k = min(W * 0.86 / t.width, H * 0.86 / t.height)
        t = t.resize((round(t.width * k), round(t.height * k)), Image.LANCZOS)
        tile = Image.new("RGB", (W, H), BG)
        tile.paste(t, ((W - t.width) // 2, (H - t.height) // 2))
        tile.save(f"{OUT}/{n:02d}.jpg", quality=93)
print("tiles:", n)
