"""Lay the rendered SPECIMEN cards out on A4 landscape contact sheets (5 officers per page: fronts above backs)."""
import json, sys
from PIL import Image, ImageDraw, ImageFont

SRC = sys.argv[1] if len(sys.argv) > 1 else "png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "specimen_cards_100.pdf"
idx = json.load(open(f"{SRC}/index.json"))

W, H, PER = 2339, 1654, 5                      # A4 landscape @ 200 dpi
BG, INK = (11, 21, 48), (201, 207, 221)
try: font = ImageFont.load_default(size=24)
except TypeError: font = ImageFont.load_default()
cw = (W - 2 * 60) // PER
ch = int(cw * 85.6 / 54)

pages = []
for p in range(0, len(idx), PER):
    page = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(page)
    d.text((60, 26), f"SPECIMEN - design concept, not valid credentials - cards {p + 1}-{min(p + PER, len(idx))} of {len(idx)}", fill=(255, 138, 128), font=font)
    for k, e in enumerate(idx[p:p + PER]):
        x = 60 + k * cw
        for row, side in enumerate(("front", "back")):
            im = Image.open(f"{SRC}/{e['file']}_{side}.png").convert("RGBA").resize((cw - 24, ch - 24), Image.LANCZOS)
            page.paste(im, (x + 12, 80 + row * (ch + 20)), im)
        d.text((x + 12, 80 + 2 * (ch + 20) + 4), f"KH-SPEC-{e['file']}  {e['name']}", fill=INK, font=font)
    pages.append(page)
pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=200, quality=78)
print(len(pages), "pages ->", OUT)
