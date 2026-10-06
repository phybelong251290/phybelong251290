"""Cut the emblem and the one-line title out of back_mockup_edited.png as transparent PNGs
(unmixed from the olive fabric) so they can be re-used sharply on the front."""
import os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
src = np.asarray(Image.open(os.path.join(HERE, 'back_mockup_edited.png')).convert('RGB')).astype(float)
def cut(box, name, lo=34, hi=90):
    x0, y0, x1, y1 = box
    c = src[y0:y1, x0:x1]
    ring = np.concatenate([c[:4].reshape(-1, 3), c[-4:].reshape(-1, 3), c[:, :4].reshape(-1, 3), c[:, -4:].reshape(-1, 3)])
    F = np.median(ring, 0)
    d = np.abs(c - F).sum(2)
    al = np.clip((d - lo) / (hi - lo), 0, 1)
    al = al * al * (3 - 2 * al)
    a3 = al[..., None]
    col = np.where(a3 > 0.12, (c - (1 - a3) * F) / np.maximum(a3, 0.12), c)
    col = np.clip(col, 0, 255)
    ys, xs = np.where(al > 0.25)
    bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    out = np.dstack([col, al * 255])[by0:by1, bx0:bx1].astype('uint8')
    Image.fromarray(out, 'RGBA').save(os.path.join(HERE, name))
    print(name, out.shape[1], 'x', out.shape[0], 'aspect', round(out.shape[1] / out.shape[0], 3))
cut((528, 504, 863, 803), 'art_emblem.png')
cut((503, 799, 885, 884), 'art_title.png')
