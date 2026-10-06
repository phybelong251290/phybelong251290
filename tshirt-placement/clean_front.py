"""Lift a clean adult-M FRONT tee photo out of the old annotated sheet (images/1.webp):
removes dimension lines/labels and the old print, flattens the background.
Writes front_tee_clean.png (tee only, no artwork) and front_geom.json."""
import json, os, sys
import cv2, numpy as np
from scipy import ndimage as ndi
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
im = Image.open(SRC).convert('RGB').crop((0, 130, 945, 1420))
a = np.asarray(im).copy()
R, G, B = [a[..., i].astype(int) for i in range(3)]
fab = (np.abs(R - G) < 22) & ((G - B) > 8) & (G > 45) & (G < 135)
sil = ndi.binary_fill_holes(ndi.binary_closing(fab, structure=np.ones((3, 3)), iterations=6))
lab, n = ndi.label(sil); sil = lab == (np.argmax(ndi.sum(sil, lab, range(1, n + 1))) + 1)
# thin annotations inside the chest area -> inpaint
reg = np.zeros_like(sil); reg[255:675, 225:705] = True
boxes = [(325, 382, 428, 474), (484, 408, 618, 462)]               # old emblem / title boxes (+margin)
bm = np.zeros_like(sil)
for x0, y0, x1, y1 in boxes: bm[y0:y1, x0:x1] = True
thin = sil & reg & ~fab & ~bm
thin = ndi.binary_dilation(thin, iterations=2)
thin &= ~bm
out = cv2.inpaint(a, thin.astype('uint8') * 255, 4, cv2.INPAINT_TELEA)
# print boxes: bilinear (Coons) fill from the cleaned border + fabric noise
rng = np.random.default_rng(3)
for x0, y0, x1, y1 in boxes:
    h, w = y1 - y0, x1 - x0
    f = out.astype(float)
    L = f[y0:y1, x0 - 6:x0 - 2].mean(1); Rr = f[y0:y1, x1 + 2:x1 + 6].mean(1)
    T = f[y0 - 6:y0 - 2, x0:x1].mean(0); Bt = f[y1 + 2:y1 + 6, x0:x1].mean(0)
    wx = np.linspace(0, 1, w)[None, :, None]; wy = np.linspace(0, 1, h)[:, None, None]
    fill = ((1 - wx) * L[:, None] + wx * Rr[:, None] + (1 - wy) * T[None] + wy * Bt[None]
            - ((1 - wx) * (1 - wy) * T[0] + wx * (1 - wy) * T[-1] + (1 - wx) * wy * Bt[0] + wx * wy * Bt[-1]))
    ref = f[y1 + 8:y1 + 40, x0:x1]; nz = (ref - ref.mean(1, keepdims=True)).std()
    out[y0:y1, x0:x1] = np.clip(fill + rng.normal(0, nz, (h, w, 3)), 0, 255).astype('uint8')
# flat background outside the tee silhouette (soft edge)
fabc = (np.abs(out[..., 0].astype(int) - out[..., 1]) < 22) & ((out[..., 1].astype(int) - out[..., 2]) > 8) & (out[..., 1] > 45) & (out[..., 1] < 135)
s2 = ndi.binary_fill_holes(ndi.binary_closing(fabc, structure=np.ones((3, 3)), iterations=4))
lab, n = ndi.label(s2); s2 = lab == (np.argmax(ndi.sum(s2, lab, range(1, n + 1))) + 1)
alpha = cv2.GaussianBlur(ndi.binary_erosion(s2, iterations=1).astype('float32'), (0, 0), 1.0)[..., None]
BG = np.array([228, 228, 228], float)
res = out * alpha + BG * (1 - alpha)
ys, xs = np.where(s2); x0, x1, y0, y1 = xs.min() - 40, xs.max() + 40, ys.min() - 40, ys.max() + 40
res = res[y0:y1, x0:x1].astype('uint8')
Image.fromarray(res).save(os.path.join(HERE, 'front_tee_clean.png'))
print('crop origin (panel px):', x0, y0, 'size', res.shape[1], res.shape[0])
json.dump(dict(x0=int(x0), y0=int(y0), w=int(res.shape[1]), h=int(res.shape[0])), open(os.path.join(HERE, 'front_geom.json'), 'w'))
