"""Crop head-and-shoulders portraits (19:24, the card photo box) from the full-length photo set in _sp.zip."""
import zipfile, io, sys
from PIL import Image

ZIP = sys.argv[1] if len(sys.argv) > 1 else "../_sp.zip"
OUT = sys.argv[2] if len(sys.argv) > 2 else "portraits"
import os; os.makedirs(OUT, exist_ok=True)

with zipfile.ZipFile(ZIP) as z:
    for name in sorted(n for n in z.namelist() if n.lower().endswith(".jpg")):
        im = Image.open(io.BytesIO(z.read(name))).convert("RGB")
        w, h = im.size
        ch = int(h * 0.215)                 # head + shoulders, stops above the chest name tape
        cw = int(ch * 19 / 24)
        left = (w - cw) // 2
        im.crop((left, int(h * 0.012), left + cw, int(h * 0.012) + ch)).save(f"{OUT}/{os.path.splitext(os.path.basename(name))[0]}.jpg", quality=92)
print("ok")
