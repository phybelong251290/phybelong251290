"""Adult M back placement sheet (EN / KH).  Usage: python3 make_sheet.py en|kh

Inputs : back_mockup.webp  (tee photo with the lockup already printed on it)
Fonts  : fonts/NSK-400.ttf, NSK-700.ttf (Noto Sans Khmer), DejaVu Sans for Latin
Output : placement_back_<lang>.png
Measured from the mockup (13.7 px/cm): emblem 22.0 wide, title ~26.0 wide,
overall 26 x 29.5, top of emblem 8.0 below the back collar seam.
Emblem height / gap / title height are read off the pixels and sum to 29.5.
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont

LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
DJV = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'

PXCM = 13.7
CB_X, SEAM_Y = 695, 411
EMB = dict(x0=545, x1=846, y0=521, y1=788)           # px in the mockup
TIT = dict(x0=518, x1=870, y0=811, y1=923)
TOP_CM, EMB_W, TIT_W, TOT_W, TOT_H = 8.0, 22.0, 26.0, 26.0, 29.5
EMB_H, GAP, TIT_H = 19.6, 1.7, 8.2

TXT = dict(
    en=dict(title='ADULT M · BACK', sub='One transfer, centred on CB · all dimensions in cm',
            cb='CB', seam='back collar seam', overall='{w} × {h} cm', tab='PLACEMENT MEASUREMENTS (cm)',
            cols=('Measurement', 'Front chest', 'Back'),
            rows=['Transfer overall (W × H)', 'Emblem (W × H)', 'Title (W × H)', 'Gap emblem → title',
                  'Horizontal position', 'Top of emblem', 'Top of title', 'Centre mark from transfer left edge'],
            side='side by side', stacked='stacked', centred='centred on CB',
            hdr='HEAT PRESS', leg='HPS = high point of shoulder · CF = centre front · CB = centre back',
            notes=['1. Pre-press the shirt 5 s to remove moisture, then 2 s to smooth the surface.',
                   '2. FRONT: mark CF on the transfer 15.0 from its left edge (inside the gap); align to the CF crease, top of emblem 15.2 below HPS.',
                   '3. BACK: crease the centre back (CB); mark 13.0 from the transfer left edge; top of emblem 8.0 below the back collar seam.',
                   '4. Keep each transfer level (square to the crease). Tack with heat tape.',
                   '5. Press 160 °C, 15 s, medium-firm. Peel per film. Finish 10 s under parchment. Press the front first; cover it with parchment when pressing the back.',
                   "Front: emblem on the wearer's RIGHT chest, title on the wearer's LEFT chest."],
            foot='All Right Reserved By Personnel Department, General Command, 2026'),
    kh=dict(title='អាវយឺតមនុស្សធំ ទំហំ M · ខាងក្រោយ', sub='ផ្ទាំងបោះពុម្ពតែមួយ ដាក់ចំកណ្ដាលខ្នង (CB) · ខ្នាតទាំងអស់គិតជា ស.ម',
            cb='កណ្ដាលខ្នង (CB)', seam='ថ្នេរកអាវខាងក្រោយ', overall='{w} × {h} ស.ម', tab='ខ្នាត និងទីតាំងដាក់ (ស.ម)',
            cols=('ការវាស់', 'ទ្រូងខាងមុខ', 'ខាងក្រោយ'),
            rows=['ទំហំផ្ទាំងបោះពុម្ពសរុប (ទទឹង × កម្ពស់)', 'និមិត្តសញ្ញា (ទទឹង × កម្ពស់)', 'ចំណងជើង (ទទឹង × កម្ពស់)',
                  'គម្លាតពីនិមិត្តសញ្ញា ដល់ចំណងជើង', 'ទីតាំងផ្ដេក', 'គែមលើនិមិត្តសញ្ញា', 'គែមលើចំណងជើង',
                  'សញ្ញាកណ្ដាល ពីគែមឆ្វេងផ្ទាំងបោះពុម្ព'],
            side='នៅក្បែរគ្នា', stacked='នៅលើក្រោម', centred='ចំកណ្ដាល CB',
            hdr='វិធីអ៊ុតផ្ទាំងរូប (Heat Press)', leg='HPS = ចំណុចខ្ពស់ស្មា · CF = បន្ទាត់កណ្ដាលខាងមុខ · CB = បន្ទាត់កណ្ដាលខាងក្រោយ',
            notes=['១. អ៊ុតអាវមុន ៥ វិនាទី បន្ទាប់មកអ៊ុត ២ វិនាទី ដើម្បីឲ្យផ្ទៃរាបស្មើ។',
                   '២. ខាងមុខ៖ គូសសញ្ញា CF លើផ្ទាំងបោះពុម្ព ១៥.០ ពីគែមខាងឆ្វេង (ក្នុងចន្លោះទំនេរ)។ តម្រឹមនឹងស្នាម CF ហើយគែមលើនិមិត្តសញ្ញា ១៥.២ ពី HPS ចុះក្រោម។',
                   '៣. ខាងក្រោយ៖ បង្កើតស្នាមកណ្ដាលខ្នង (CB)។ គូសសញ្ញា ១៣.០ ពីគែមឆ្វេងផ្ទាំងបោះពុម្ព។ គែមលើនិមិត្តសញ្ញា ៨.០ ពីថ្នេរកអាវខាងក្រោយចុះក្រោម។',
                   '៤. រក្សាផ្ទាំងបោះពុម្ពនីមួយៗឲ្យត្រង់ (កែងនឹងស្នាមកណ្ដាល)។ បិទដោយស្កុតធន់កម្ដៅ។',
                   '៥. អ៊ុត ១៦០ °C រយៈពេល ១៥ វិនាទី សម្ពាធមធ្យម-ខ្លាំង។ ហែកហ្វីលតាមប្រភេទហ្វីល។ អ៊ុតបញ្ចប់ ១០ វិនាទី ដោយគ្របក្រដាសការពារ។ អ៊ុតខាងមុខមុន ហើយគ្របវាដោយក្រដាសការពារ ពេលអ៊ុតខាងក្រោយ។',
                   'ខាងមុខ៖ និមិត្តសញ្ញានៅលើទ្រូងខាងស្ដាំរបស់អ្នកពាក់ ចំណងជើងនៅលើទ្រូងខាងឆ្វេងរបស់អ្នកពាក់។'],
            foot='All Right Reserved By ទីចាត់ការបុគ្គលិក, អគ្គបញ្ជាការ ២០២៦'))
T = TXT[LANG]

KM = str.maketrans('0123456789', '០១២៣៤៥៦៧៨៩')
def N(v, plain=False):
    s = f'{v:.1f}' if isinstance(v, float) else str(v)
    return s.translate(KM) if LANG == 'kh' else s

KHRUN = re.compile(r'([ក-៿​]+(?:[ ·×()/.,:\-0-9A-Za-z°]*[ក-៿​]+)*)')
_fc = {}
def font(kind, size, khmer=False):
    k = (kind, size, khmer)
    if k not in _fc:
        if khmer:
            _fc[k] = ImageFont.truetype(os.path.join(FONTS, 'NSK-700.ttf' if kind == 'Bold' else 'NSK-400.ttf'), size)
        else:
            _fc[k] = ImageFont.truetype(DJV % ('-Bold' if kind == 'Bold' else ''), size)
    return _fc[k]

def runs(s):
    out = []
    for part in KHRUN.split(s):
        if part:
            out.append((part, bool(re.search(r'[ក-៿]', part))))
    return out

def tw(s, kind, size):
    return sum(font(kind, size, k).getlength(t) for t, k in runs(s))

def text(d, xy, s, kind, size, fill, anchor='l'):
    x, y = xy
    w = tw(s, kind, size)
    if anchor == 'm':
        x -= w / 2
    elif anchor == 'r':
        x -= w
    for t, k in runs(s):
        f = font(kind, size, k)
        d.text((x, y), t, font=f, fill=fill, anchor='ls')
        x += f.getlength(t)
    return w

def dashed(d, a, b, fill, w=1, dash=7):
    (x0, y0), (x1, y1) = a, b
    L = max(abs(x1 - x0), abs(y1 - y0)); n = int(L // dash)
    for i in range(0, n, 2):
        t0, t1 = i / n, min((i + 1) / n, 1)
        d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=fill, width=w)

def arrow_v(d, x, y0, y1, label, fill, side='r'):
    d.line([(x, y0), (x, y1)], fill=fill, width=2)
    for y, s in ((y0, 1), (y1, -1)):
        d.polygon([(x, y), (x - 4, y + 8 * s), (x + 4, y + 8 * s)], fill=fill)
        d.line([(x - 6, y), (x + 6, y)], fill=fill, width=2)
    ym = (y0 + y1) / 2 + 5
    if side == 'r':
        text(d, (x + 10, ym), label, 'Bold', 15, fill)
    else:
        text(d, (x - 10, ym), label, 'Bold', 15, fill, 'r')

def arrow_h(d, y, x0, x1, label, fill, above=True):
    d.line([(x0, y), (x1, y)], fill=fill, width=2)
    for x, s in ((x0, 1), (x1, -1)):
        d.polygon([(x, y), (x + 8 * s, y - 4), (x + 8 * s, y + 4)], fill=fill)
        d.line([(x, y - 6), (x, y + 6)], fill=fill, width=2)
    text(d, ((x0 + x1) / 2, y - 9 if above else y + 22), label, 'Bold', 15, fill, 'm')

WHITE, YEL, INK, ACC = (255, 255, 255), (255, 190, 40), (28, 28, 28), (255, 150, 60)

# ---------- back panel ----------
img = Image.open(os.path.join(HERE, 'back_mockup.webp')).convert('RGB')
img.paste(img.crop((600, 985, 790, 1020)), (600, 930))          # remove the baked-in size label
d = ImageDraw.Draw(img)
dashed(d, (CB_X, 380), (CB_X, 975), WHITE)
text(d, (CB_X + 8, 376), T['cb'], 'Bold', 14, WHITE)
d.line([(CB_X - 90, SEAM_Y), (CB_X + 90, SEAM_Y)], fill=WHITE, width=2)
text(d, (CB_X - 96, SEAM_Y + 5), T['seam'], 'Bold', 13, WHITE, 'r')
for b in (EMB, TIT):
    p = [(b['x0'] - 3, b['y0'] - 3), (b['x1'] + 3, b['y0'] - 3), (b['x1'] + 3, b['y1'] + 3), (b['x0'] - 3, b['y1'] + 3)]
    for i in range(4):
        dashed(d, p[i], p[(i + 1) % 4], YEL)
ax = TIT['x1'] + 34
arrow_v(d, ax, SEAM_Y, EMB['y0'], N(TOP_CM), WHITE)
arrow_v(d, ax, EMB['y0'], EMB['y1'], N(EMB_H), YEL)
arrow_v(d, ax, EMB['y1'], TIT['y0'], N(GAP), ACC)
arrow_v(d, ax, TIT['y0'], TIT['y1'], N(TIT_H), YEL)
arrow_h(d, EMB['y0'] - 16, EMB['x0'], EMB['x1'], N(EMB_W), YEL)
arrow_h(d, TIT['y1'] + 26, TIT['x0'], TIT['x1'], N(TIT_W), YEL, above=False)
text(d, (CB_X, TIT['y1'] + 70), T['overall'].format(w=N(TOT_W), h=N(TOT_H)), 'Bold', 17, WHITE, 'm')
panel = img.crop((0, 250, img.width, 1560))
BG = img.getpixel((5, 5))

# ---------- sheet ----------
W = 1390; S = 1
head_h = 120
rows_n = len(T['rows']) + 1
tab_h = 40 + 52 + 40 + len(T['rows']) * 46 + 30
notes_h = 70 + 44 * len(T['notes']) + 50
H = head_h + panel.height + max(tab_h, notes_h) + 70
sheet = Image.new('RGB', (W, H), BG); sd = ImageDraw.Draw(sheet)
text(sd, (46, 62), T['title'], 'Bold', 44, INK)
text(sd, (46, 100), T['sub'], 'Regular', 20, (80, 80, 80))
sheet.paste(panel, (0, head_h))
y = head_h + panel.height + 40

# table: front values (arithmetic-checked from the v1 sheet) vs back values
FR = [f"{N(30.0)} × {N(7.6)}", f"{N(8.6)} × {N(7.6)}", f"{N(12.2)} × {N(3.6)}", f"{N(9.2)} ({T['side']})",
      f"CF→ {N(6.4)} / {N(2.8)}", 'HPS ↓ ' + N(15.2), 'HPS ↓ ' + N(18.0), N(15.0)]
BK = [f"{N(TOT_W)} × {N(TOT_H)}", f"{N(EMB_W)} × {N(EMB_H)}", f"{N(TIT_W)} × {N(TIT_H)}", f"{N(GAP)} ({T['stacked']})",
      T['centred'], ('seam ↓ ' if LANG == 'en' else 'ថ្នេរ ↓ ') + N(TOP_CM),
      ('seam ↓ ' if LANG == 'en' else 'ថ្នេរ ↓ ') + N(TOP_CM + EMB_H + GAP), N(TOT_W / 2)]
text(sd, (46, y + 20), T['tab'], 'Bold', 24, INK)
y += 52
cx = [46, 390, 548]
sd.rectangle([30, y, 710, y + 40], fill=(214, 214, 210))
for x, c in zip(cx, T['cols']):
    text(sd, (x, y + 28), c, 'Bold', 17, INK)
y += 40
for i, (r, f, b) in enumerate(zip(T['rows'], FR, BK)):
    if i % 2:
        sd.rectangle([30, y, 710, y + 46], fill=(224, 224, 220))
    text(sd, (cx[0], y + 30), r, 'Bold', 16, INK)
    text(sd, (cx[1], y + 30), f, 'Regular', 17, (50, 50, 50))
    text(sd, (cx[2], y + 30), b, 'Regular', 17, (50, 50, 50))
    y += 46

ny = head_h + panel.height + 60
text(sd, (750, ny), T['hdr'], 'Bold', 24, INK)
ny += 14
for n in T['notes']:
    ny += 34
    # simple wrap
    words, line = n.split(' '), ''
    for w_ in words:
        if tw(line + ' ' + w_, 'Regular', 15) > 590 and line:
            text(sd, (750, ny), line, 'Regular', 15, (60, 60, 60)); ny += 24; line = w_
        else:
            line = (line + ' ' + w_).strip()
    text(sd, (750, ny), line, 'Regular', 15, (60, 60, 60))
ny += 40
text(sd, (750, ny), T['leg'], 'Regular', 13, (110, 110, 110))

sd.rectangle([0, H - 70, W, H], fill=(28, 32, 26))
text(sd, (W / 2, H - 28), T['foot'], 'Regular', 17, (214, 200, 150), 'm')
out = os.path.join(HERE, f'placement_back_{LANG}.png')
sheet.save(out)
print(out, sheet.size)
