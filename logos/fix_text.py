"""Replace the garbled lettering on the badges with properly shaped Khmer text.

For every text region listed in badge_text.json the old lettering is masked
(pixels that don't match the region's background colours), inpainted away, and
the new text is typeset with a real Khmer font (shaped by HarfBuzz via raqm)
along the same straight line or arc. Output is rendered at SCALE x the crop size.

Usage:
    python3 logos/fix_text.py logos/badge_text.json logos/transparent logos/fixed-text \
        --font Koulen=path/to/Koulen.ttf --font Moul=path/to/Moul.ttf [--size 4] [--only 7 22]

Any font family can be swapped in by name, e.g. --font Koulen=Kh_ST_Yeaksa_Pro_V2.otf
renders every Koulen region in that font instead.
"""
import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCALE = 4
BG_TOL = 70      # RGB distance for a pixel to count as region background
INK_GROW = 1     # px (1x) the old-text mask is grown by before inpainting


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


# ---------------------------------------------------------------- geometry

class Arc:
    """Text band following a circle. Angles are clockwise from 12 o'clock."""

    def __init__(self, cx, cy, r_in, r_out, a_left, a_right):
        self.cx, self.cy, self.r_in, self.r_out = cx, cy, r_in, r_out
        self.a_left, self.a_right = a_left, a_right
        self.top = a_right > a_left  # top text reads clockwise, glyph tops outward
        self.mid = (a_left + a_right) / 2

    @property
    def h(self):
        return self.r_out - self.r_in

    @property
    def length(self):
        return math.radians(abs(self.a_right - self.a_left)) * (self.r_in + self.r_out) / 2

    def polar(self, xs, ys):
        dx, dy = xs - self.cx, ys - self.cy
        r = np.hypot(dx, dy)
        a = np.degrees(np.arctan2(dx, -dy))
        d = (a - self.mid + 180) % 360 - 180  # angle relative to the band middle
        return r, d

    def mask(self, w, h, pad, apad):
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        r, d = self.polar(xs, ys)
        half = abs(self.a_right - self.a_left) / 2 + math.degrees(apad / ((self.r_in + self.r_out) / 2))
        return (r >= self.r_in - pad) & (r <= self.r_out + pad) & (np.abs(d) <= half)

    def warp(self, strip, out_w, out_h, s):
        """Map a straight text strip (W x H, at scale s) onto the arc."""
        sh, sw = strip.shape[:2]
        ys, xs = np.mgrid[0:out_h, 0:out_w].astype(np.float32)
        r, d = self.polar(xs / s, ys / s)
        dl, dr = self.a_left - self.mid, self.a_right - self.mid
        u = (d - dl) / (dr - dl) * sw
        if self.top:
            v = (self.r_out - r) / self.h * sh
        else:
            v = (r - self.r_in) / self.h * sh
        return cv2.remap(strip, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)


class Line:
    """Straight, possibly rotated, text band from p1 to p3."""

    def __init__(self, p1, p3, h):
        self.p1, self.p3, self.hh = np.array(p1, float), np.array(p3, float), h
        self.angle = math.degrees(math.atan2(p3[1] - p1[1], p3[0] - p1[0]))

    @property
    def h(self):
        return self.hh

    @property
    def length(self):
        return float(np.linalg.norm(self.p3 - self.p1))

    def local(self, xs, ys):
        c = (self.p1 + self.p3) / 2
        t = math.radians(self.angle)
        dx, dy = xs - c[0], ys - c[1]
        return dx * math.cos(t) + dy * math.sin(t), -dx * math.sin(t) + dy * math.cos(t)

    def mask(self, w, h, pad, apad):
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        u, v = self.local(xs, ys)
        return (np.abs(u) <= self.length / 2 + pad + apad) & (np.abs(v) <= self.hh / 2 + pad)

    def warp(self, strip, out_w, out_h, s):
        sh, sw = strip.shape[:2]
        ys, xs = np.mgrid[0:out_h, 0:out_w].astype(np.float32)
        u, v = self.local(xs / s, ys / s)
        mx = ((u / self.length + 0.5) * sw).astype(np.float32)
        my = ((v / self.hh + 0.5) * sh).astype(np.float32)
        return cv2.remap(strip, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def circle_through(p1, p2, p3):
    (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-6:
        return None
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    return ux, uy, math.hypot(x1 - ux, y1 - uy)


def geometry(region):
    if "ring" in region:
        return Arc(*region["ring"])
    p1, p2, p3 = region["path"]
    h = region["h"]
    # sagitta: how far the middle point sits off the straight chord
    chord = np.array(p3, float) - np.array(p1, float)
    off = np.array(p2, float) - np.array(p1, float)
    sag = abs(chord[0] * off[1] - chord[1] * off[0]) / np.linalg.norm(chord)
    circ = circle_through(p1, p2, p3) if sag >= 2 else None
    if circ is None:
        return Line(p1, p3, h)
    cx, cy, r = circ
    ang = lambda p: math.degrees(math.atan2(p[0] - cx, -(p[1] - cy)))
    wrap = lambda a: (a + 180) % 360 - 180
    a1 = ang(p1)
    a2 = a1 + wrap(ang(p2) - a1)
    a3 = a2 + wrap(ang(p3) - a2)
    return Arc(cx, cy, r - h / 2, r + h / 2, a1, a3)


# ---------------------------------------------------------------- text

def fit_font(path, text, max_w, max_h):
    lo, hi = 4, 600
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = ImageFont.truetype(path, mid, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l <= max_w and b - t <= max_h:
            lo = mid
        else:
            hi = mid - 1
    return ImageFont.truetype(path, lo, layout_engine=ImageFont.Layout.RAQM)


def text_strip(region, geo, fonts, s):
    """RGBA strip (glyphs upright, centred) the size of the band at scale s."""
    W, H = max(int(geo.length * s), 1), max(int(geo.h * s), 1)
    stroke = region.get("stroke")
    sw = int(round(stroke[0] * s)) if stroke else 0
    fit = region.get("fit", 0.8)
    font = fit_font(fonts[region.get("font", "Koulen")], region["text"],
                    W * region.get("width", 0.97) - 2 * sw, H * fit - 2 * sw)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    l, t, r, b = font.getbbox(region["text"], language="km", stroke_width=sw)
    x = (W - (r - l)) / 2 - l
    y = (H - (b - t)) / 2 - t
    ImageDraw.Draw(img).text((x, y), region["text"], font=font, fill=region.get("fill", "#ffffff"),
                             language="km", stroke_width=sw,
                             stroke_fill=stroke[1] if stroke else None)
    return np.asarray(img)


# ---------------------------------------------------------------- badge

def shifted(region, k):
    """Copy of region moved by k px: down for straight/curved paths, outward for rings."""
    r = dict(region)
    if "ring" in r:
        cx, cy, ri, ro, a, b = r["ring"]
        r["ring"] = [cx, cy, ri + k, ro + k, a, b]
    else:
        r["path"] = [[x, y + k] for x, y in r["path"]]
    return r


def near(rgb, colours, where):
    """True where a pixel is close to one of the colours (shades refined from `where`)."""
    px = rgb.astype(np.float32)
    hit = np.zeros(rgb.shape[:2], bool)
    for c in colours:
        target = hex_rgb(c)
        close = (np.linalg.norm(px - target, axis=2) < BG_TOL * 1.4) & where
        if close.any():  # refine the shade from the badge itself
            target = np.median(px[close], axis=0)
        hit |= np.linalg.norm(px - target, axis=2) < BG_TOL
    return hit


def locate(region, letters, search):
    """Nudge the region onto the old lettering: the shift whose band holds most letter pixels."""
    h, w = letters.shape
    best, best_k = -1, 0
    for k in sorted(range(-search, search + 1), key=abs):
        score = (geometry(shifted(region, k)).mask(w, h, 0, 0) & letters).sum()
        if score > best:
            best, best_k = score, k
    return shifted(region, best_k), best_k


def old_text_mask(rgb, interior, region):
    h, w = rgb.shape[:2]
    ink = interior & ~near(rgb, region["bg"], interior)
    k = 0
    if region.get("search", 8):
        start = geometry(region).mask(w, h, 6, 6) & interior
        letters = interior & near(rgb, region.get("ink", [region.get("fill", "#ffffff")]), start)
        region, k = locate(region, letters, region.get("search", 8))
    geo = geometry(region)
    area = geo.mask(w, h, region.get("pad", 5), region.get("apad", 10)) & interior
    grow = region.get("grow", INK_GROW)
    k3 = np.ones((2 * grow + 1,) * 2, np.uint8)
    old = cv2.dilate((ink & area).astype(np.uint8), k3) & area.astype(np.uint8)
    for x0, y0, x1, y1 in region.get("keep", []):  # boxes of badge art to leave alone
        old[y0:y1, x0:x1] = 0
    for x0, y0, x1, y1 in region.get("clear", []):  # extra boxes to wipe
        box = np.zeros_like(old)
        box[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
        old |= cv2.dilate(box, k3) & interior.astype(np.uint8)
    return old, geo, k


def flat_colour(rgb, old, interior, region):
    """Median shade of the region's first background colour, taken next to the old text."""
    ring = cv2.dilate(old, np.ones((7, 7), np.uint8)).astype(bool) & ~old.astype(bool) & interior
    near_first = near(rgb, region["bg"][:1], ring) & ring
    px = rgb[near_first] if near_first.any() else rgb[ring]
    return np.median(px.astype(np.float32), axis=0)


def process(n, spec, src_dir, fonts):
    src = Image.open(src_dir / f"logo_{n:02d}.png").convert("RGBA")
    w, h = src.size
    rgb = np.asarray(src)[..., :3]
    big = np.asarray(src.resize((w * SCALE, h * SCALE), Image.LANCZOS)).copy()

    regions = spec.get("regions", [])
    if regions:
        alpha = np.asarray(src)[..., 3]
        edge = spec.get("edge", 6)
        interior = cv2.erode((alpha > 200).astype(np.uint8), np.ones((2 * edge + 1,) * 2, np.uint8)) > 0
        mask = np.zeros((h, w), np.uint8)
        flat = []  # (mask, colour) for regions repainted with a flat colour instead
        geos = []
        for i, region in enumerate(regions):
            old, geo, k = old_text_mask(rgb, interior, region)
            geos.append(geo)
            if region.get("flat"):
                flat.append((old, flat_colour(rgb, old, interior, region)))
            else:
                mask |= old
            print(f"  #{n:02d} region {i + 1}: shifted {k:+d}px")
        upscale = lambda m: cv2.dilate(cv2.resize(m * 255, (w * SCALE, h * SCALE), interpolation=cv2.INTER_NEAREST),
                                       np.ones((5, 5), np.uint8))
        bgr = cv2.cvtColor(big[..., :3], cv2.COLOR_RGB2BGR)
        bgr = cv2.inpaint(bgr, upscale(mask), 7, cv2.INPAINT_TELEA)
        big[..., :3] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        for m, colour in flat:
            a = cv2.GaussianBlur(upscale(m).astype(np.float32) / 255, (5, 5), 0)[..., None]
            big[..., :3] = (big[..., :3] * (1 - a) + colour * a).round().astype(np.uint8)

        out = Image.fromarray(big, "RGBA")
        for region, geo in zip(regions, geos):
            if not region.get("text"):
                continue  # wipe only
            strip = text_strip(region, geo, fonts, SCALE)
            layer = geo.warp(strip, w * SCALE, h * SCALE, SCALE)
            out.alpha_composite(Image.fromarray(layer, "RGBA"))
        big = np.asarray(out)
    return Image.fromarray(big, "RGBA")


def contact_sheet(images, path, tile=300, cols=8):
    rows = -(-len(images) // cols)
    sheet = Image.new("RGB", (cols * tile, rows * tile), (60, 64, 72))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        t = im.copy()
        t.thumbnail((tile - 24, tile - 30), Image.LANCZOS)
        sheet.paste(t, (c * tile + (tile - t.width) // 2, r * tile + 24 + (tile - 24 - t.height) // 2), t)
        d.text((c * tile + 6, r * tile + 4), f"#{i + 1:02d}", fill=(255, 255, 255))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("src_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--font", action="append", default=[], help="Name=path.ttf")
    ap.add_argument("--only", type=int, nargs="*")
    ap.add_argument("--size", type=float, default=2,
                    help="output size as a multiple of the crop (text is rendered at 4x, then resized)")
    args = ap.parse_args()

    fonts = dict(f.split("=", 1) for f in args.font)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    done = []
    for n in range(1, 41):
        if args.only and n not in args.only:
            continue
        img = process(n, config.get(f"{n:02d}", {}), Path(args.src_dir), fonts)
        if args.size != SCALE:
            f = args.size / SCALE
            img = img.resize((round(img.width * f), round(img.height * f)), Image.LANCZOS)
        img.save(out_dir / f"logo_{n:02d}.png", optimize=True)
        done.append(img)
        print(f"logo_{n:02d}: {img.width}x{img.height}")
    if not args.only:
        contact_sheet(done, out_dir / "contact_sheet.png")


if __name__ == "__main__":
    main()
