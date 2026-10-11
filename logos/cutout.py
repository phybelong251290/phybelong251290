"""Cut a badge out of a dark product photo with GrabCut. Usage: cutout.py <src_dir> <list.txt> <out_dir>"""
import sys
import cv2
import numpy as np
from PIL import Image

src, listf, out = sys.argv[1], sys.argv[2], sys.argv[3]
names = [l.strip() for l in open(listf) if l.strip()]
W = 512
for i, n in enumerate(names, 1):
    img = cv2.imread(f"{src}/{n}")
    small = cv2.resize(img, (W, W), interpolation=cv2.INTER_AREA)
    mask = np.zeros((W, W), np.uint8)
    m = int(W * 0.025)
    rect = (m, m, W - 2 * m, W - 2 * m)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(small, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep the biggest blob, fill its holes, smooth the outline
    nlab, lab, stats, _ = cv2.connectedComponentsWithStats(fg)
    if nlab > 1:
        big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        fg = np.where(lab == big, 255, 0).astype(np.uint8)
    cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(fg)
    cv2.drawContours(filled, cnts, -1, 255, -1)
    filled = cv2.morphologyEx(filled, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    alpha = cv2.resize(filled, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    alpha = cv2.GaussianBlur(alpha, (5, 5), 0)
    rgba = np.dstack([cv2.cvtColor(img, cv2.COLOR_BGR2RGB), alpha])
    ys, xs = np.nonzero(alpha > 10)
    pad = 8
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, img.shape[1]), min(ys.max() + pad, img.shape[0]))
    Image.fromarray(rgba, "RGBA").crop(box).save(f"{out}/metal_{i:02d}.png")
    print(i, box, round((alpha > 128).mean(), 3))
