"""A3 (297 x 420 mm) printable PDF of the adult M FRONT-CHEST placement sheet.  Usage: python3 make_front.py en|kh
Needs: front_tee_clean.png (clean_front.py), art_emblem.png / art_title.png (extract_art.py),
data_<lang>.json (make_sheet.py).  The artwork is placed as separate layers, so it stays sharp."""
import base64, io, json, os, subprocess, sys
from PIL import Image
LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, f'data_{LANG}.json'))); T, FR, BK = D['T'], D['FR'], D['BK']
KM = str.maketrans('0123456789', '០១២៣៤៥៦៧៨៩')
N = (lambda v: f'{v:.1f}'.translate(KM)) if LANG == 'kh' else (lambda v: f'{v:.1f}')
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
WHITE, YEL, ACC = '#ffffff', '#ffbe28', '#ff963c'
TXT = dict(
    en=dict(title='ADULT M · FRONT CHEST', sub="Chest 51 cm · one transfer on the wearer's right chest · all dimensions in cm",
            hps='high point of shoulder (HPS)', cf='centre front (CF)'),
    kh=dict(title='អាវយឺតមនុស្សធំ ទំហំ M · ទ្រូងខាងមុខ', sub='ទទឹងទ្រូង ៥១ ស.ម · ផ្ទាំងបោះពុម្ពតែមួយ នៅលើទ្រូងខាងស្ដាំរបស់អ្នកពាក់ · ខ្នាតទាំងអស់គិតជា ស.ម',
            hps='ចំណុចខ្ពស់ស្មា (HPS)', cf='កណ្ដាលខាងមុខ (CF)'))[LANG]

# geometry in tee-photo units (1 unit = 1 px of the cleaned photo); scale from the v1 sheet: 30.0 cm = 265 px
PPC = 265 / 30.0
G = json.load(open(os.path.join(HERE, 'front_geom.json')))
HPS_Y, CF_X = 260 - 220, 472 - 37
# uploaded design, used exactly as supplied (original pixels, aspect kept); content bbox in the source image:
SRC_W, SRC_H, BX0, BY0, BX1, BY1 = 2000, 1670, 292, 107, 1758, 1541
D_W = 10.0 * PPC; s_ = D_W / (BX1 - BX0); D_H = (BY1 - BY0) * s_
d_x1 = CF_X - 5.7 * PPC; d_x0 = d_x1 - D_W; d_y = HPS_Y + 15.2 * PPC
def line(x0, y0, x1, y1, c, w=1.3, dash=None):
    return f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{c}" stroke-width="{w}"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def txt(x, y, s, c, size=11.5, anchor='start'):
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{c}" font-size="{size}" font-weight="700" text-anchor="{anchor}">{s}</text>'
def arrow_v(x, y0, y1, label, c, side='r'):
    o = line(x, y0, x, y1, c)
    for y, s in ((y0, 1), (y1, -1)):
        o += f'<polygon points="{x:.1f},{y:.1f} {x-3:.1f},{y+6*s:.1f} {x+3:.1f},{y+6*s:.1f}" fill="{c}"/>' + line(x - 4, y, x + 4, y, c)
    ym = (y0 + y1) / 2 + 4
    return o + (txt(x + 8, ym, label, c) if side == 'r' else txt(x - 8, ym, label, c, anchor='end'))
def arrow_h(y, x0, x1, label, c, above=True):
    o = line(x0, y, x1, y, c)
    for x, s in ((x0, 1), (x1, -1)):
        o += f'<polygon points="{x:.1f},{y:.1f} {x+6*s:.1f},{y-3:.1f} {x+6*s:.1f},{y+3:.1f}" fill="{c}"/>' + line(x, y - 4, x, y + 4, c)
    return o + txt((x0 + x1) / 2, y - 7 if above else y + 16, label, c, anchor='middle')

svg = line(200, HPS_Y, 660, HPS_Y, '#1c1c1c', 1.0) + txt(664, HPS_Y + 4, TXT['hps'], '#1c1c1c', 11)
svg += line(CF_X, 14, CF_X, 432, WHITE, 1.3, '6 5') + txt(CF_X + 7, 440, TXT['cf'], WHITE, 11)
svg += f'<rect x="{d_x0-2:.1f}" y="{d_y-2:.1f}" width="{D_W+4:.1f}" height="{D_H+4:.1f}" fill="none" stroke="{YEL}" stroke-width="1" stroke-dasharray="4 3.5"/>'
lx = d_x0 - 22
svg += arrow_v(lx, HPS_Y, d_y, N(15.2), WHITE, 'l') + arrow_v(lx, d_y, d_y + D_H, N(9.8), YEL, 'l')
by = d_y + D_H + 22
svg += arrow_h(by, d_x0, d_x1, N(10.0), YEL) + arrow_h(by, d_x1, CF_X, N(5.7), ACC)
svg += txt((d_x0 + d_x1) / 2, by + 40, T['overall'].format(w=N(10.0), h=N(9.8)), WHITE, 13, 'middle')

def b64png(path, jpg=False, scale=1):
    im = Image.open(path)
    if scale != 1: im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    buf = io.BytesIO()
    if jpg: im.convert('RGB').save(buf, 'JPEG', quality=94)
    else: im.save(buf, 'PNG')
    return base64.b64encode(buf.getvalue()).decode()
def font64(n): return base64.b64encode(open(os.path.join(HERE, 'fonts', n), 'rb').read()).decode()
tee = b64png(os.path.join(HERE, 'front_tee_clean.png'), jpg=True, scale=3)
design = base64.b64encode(open(os.path.join(HERE, 'new_design_source.webp'), 'rb').read()).decode()   # embedded byte-for-byte
rows = ''.join(f'<tr><th>{r}</th><td>{f}</td><td>{b}</td></tr>' for r, f, b in zip(T['rows'], FR, BK))
notes = ''.join(f'<p>{n}</p>' for n in T['notes'])
PAGE_BG = '#e4e4e4'
art = f'<image href="data:image/webp;base64,{design}" x="{d_x0 - BX0 * s_:.2f}" y="{d_y - BY0 * s_:.2f}" width="{SRC_W * s_:.2f}" height="{SRC_H * s_:.2f}"/>'
html = f'''<!doctype html><html lang="{'km' if LANG=='kh' else 'en'}"><meta charset="utf-8"><style>
@font-face{{font-family:NSK;font-weight:400;src:url(data:font/ttf;base64,{font64('NSK-400.ttf')})}}
@font-face{{font-family:NSK;font-weight:700;src:url(data:font/ttf;base64,{font64('NSK-700.ttf')})}}
@page{{size:297mm 420mm;margin:0}}
*{{box-sizing:border-box;margin:0}}
body{{width:297mm;height:420mm;background:{PAGE_BG};color:#1c1c1c;font-family:NSK,'DejaVu Sans',sans-serif;line-height:1.55;position:relative;overflow:hidden}}
header{{padding:12mm 14mm 0}} h1{{font-size:27pt;line-height:1.5}} .sub{{font-size:12pt;color:#505050}}
.fig{{position:absolute;left:14mm;top:34mm;width:269mm}} .fig svg{{display:block;width:100%;height:auto;font-family:NSK,'DejaVu Sans',sans-serif}}
.low{{position:absolute;left:14mm;right:14mm;top:298mm;display:flex;gap:12mm}}
.tab{{width:150mm}} h2{{font-size:16pt;margin-bottom:3mm}}
table{{border-collapse:collapse;width:100%;font-size:10.5pt}} th,td{{text-align:left;padding:1.5mm 2.5mm;font-weight:400}}
th{{font-weight:700}} thead th{{background:#d6d6d2}} tbody tr:nth-child(even){{background:#dcdcd8}}
.steps{{flex:1;font-size:10pt;color:#3c3c3c}} .steps p{{margin-bottom:2.2mm}} .leg{{font-size:8.5pt;color:#707070;margin-top:4mm}}
footer{{position:absolute;left:0;right:0;bottom:0;height:13mm;background:#1c201a;color:#d6c896;text-align:center;font-size:11pt;line-height:13mm}}
</style><body>
<header><h1>{TXT['title']}</h1><div class="sub">{TXT['sub']}</div></header>
<div class="fig"><svg viewBox="0 0 {G['w']} {G['h']}" xmlns="http://www.w3.org/2000/svg">
<image href="data:image/jpeg;base64,{tee}" x="0" y="0" width="{G['w']}" height="{G['h']}"/>{art}{svg}</svg></div>
<div class="low"><div class="tab"><h2>{T['tab']}</h2><table><thead><tr><th>{T['cols'][0]}</th><th>{T['cols'][1]}</th><th>{T['cols'][2]}</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="steps"><h2>{T['hdr']}</h2>{notes}<div class="leg">{T['leg']}</div></div></div>
<footer>{T['foot']}</footer></body></html>'''
hp = os.path.join(HERE, f'_front_{LANG}.html'); out = os.path.join(HERE, f'placement_front_A3_{LANG}.pdf')
open(hp, 'w', encoding='utf-8').write(html)
subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={out}', 'file://' + hp], check=True, capture_output=True)
os.remove(hp)
print(out)
