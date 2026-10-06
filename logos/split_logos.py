"""Split the two 5x4 badge grids into 40 individual logo files.

Usage: python3 logos/split_logos.py logos/source/grid_01-20.jpg logos/source/grid_21-40.jpg logos
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

COLS, ROWS = 5, 4
LABEL_BOX = (0, 0, 21, 14)  # "#NN" index label in each cell's top-left corner
PAD = 6                     # transparent margin kept around each logo
FILL_THRESH = 48            # sum of |RGB - white| still treated as background
# Background showing through enclosed gaps (cell coords) that the border flood can't reach
HOLE_SEEDS = {18: [(72, 170), (227, 170)]}


def cells(img):
    w, h = img.size
    cw, ch = w / COLS, h / ROWS
    for r in range(ROWS):
        for c in range(COLS):
            box = (round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch))
            yield img.crop(box)


def remove_label(cell):
    cell = cell.copy()
    ImageDraw.Draw(cell).rectangle(LABEL_BOX, fill=(255, 255, 255))
    return cell


def background_mask(cell, holes=()):
    """True where the pixel is white background reachable from the cell border."""
    w, h = cell.size
    padded = Image.new("RGB", (w + 4, h + 4), (255, 255, 255))
    padded.paste(cell, (2, 2))
    for x, y in [(-2, -2), *holes]:
        ImageDraw.floodfill(padded, (x + 2, y + 2), (255, 0, 255), thresh=FILL_THRESH)
    p = np.asarray(padded)[2:-2, 2:-2]
    return (p[..., 0] == 255) & (p[..., 1] == 0) & (p[..., 2] == 255)


def to_rgba(cell, bg):
    rgb = np.asarray(cell).astype(np.float32)
    alpha = np.where(bg, 0.0, 1.0)

    # Soft edge: foreground pixels touching the background get alpha from how
    # far they are from white, and their colour is un-mixed from the white.
    fg_img = Image.fromarray(((~bg) * 255).astype(np.uint8))
    inner = np.asarray(fg_img.filter(ImageFilter.MinFilter(5))) > 0
    edge = (~bg) & (~inner)
    darkness = (255.0 - rgb.min(axis=2)) / 110.0
    alpha = np.where(edge, np.clip(darkness, 0.0, 1.0), alpha)
    a = np.maximum(alpha, 1e-3)[..., None]
    unmixed = np.clip((rgb - (1.0 - a) * 255.0) / a, 0, 255)
    rgb = np.where(edge[..., None], unmixed, rgb)

    out = np.dstack([rgb, alpha * 255.0]).round().astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def tight_box(alpha, w, h):
    ys, xs = np.nonzero(alpha > 8)
    return (max(xs.min() - PAD, 0), max(ys.min() - PAD, 0),
            min(xs.max() + PAD + 1, w), min(ys.max() + PAD + 1, h))


def contact_sheet(logos, out_path, tile=220, cols=8):
    rows = -(-len(logos) // cols)
    sheet = Image.new("RGB", (cols * tile, rows * tile), (60, 64, 72))
    d = ImageDraw.Draw(sheet)
    for i, logo in enumerate(logos):
        r, c = divmod(i, cols)
        x0, y0 = c * tile, r * tile
        # checkerboard shows where the background was removed
        for yy in range(0, tile, 16):
            for xx in range(0, tile, 16):
                if (xx // 16 + yy // 16) % 2:
                    d.rectangle((x0 + xx, y0 + yy, x0 + xx + 15, y0 + yy + 15), fill=(80, 84, 94))
        im = logo.copy()
        im.thumbnail((tile - 30, tile - 30), Image.LANCZOS)
        sheet.paste(im, (x0 + (tile - im.width) // 2, y0 + 22 + (tile - 22 - im.height) // 2), im)
        d.text((x0 + 6, y0 + 4), f"#{i + 1:02d}", fill=(255, 255, 255))
    sheet.save(out_path)


def main():
    grid1, grid2, out_dir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    (out_dir / "transparent").mkdir(parents=True, exist_ok=True)
    (out_dir / "white-background").mkdir(parents=True, exist_ok=True)

    logos = []
    n = 0
    for grid in (grid1, grid2):
        img = Image.open(grid).convert("RGB")
        for cell in cells(img):
            n += 1
            cell = remove_label(cell)
            bg = background_mask(cell, HOLE_SEEDS.get(n, ()))
            rgba = to_rgba(cell, bg)
            box = tight_box(np.asarray(rgba)[..., 3], *cell.size)

            rgba.crop(box).save(out_dir / "transparent" / f"logo_{n:02d}.png", optimize=True)
            cell.crop(box).save(out_dir / "white-background" / f"logo_{n:02d}.png", optimize=True)
            logos.append(rgba.crop(box))
            print(f"logo_{n:02d}: {box[2] - box[0]}x{box[3] - box[1]}")

    contact_sheet(logos, out_dir / "contact_sheet.png")


if __name__ == "__main__":
    main()
