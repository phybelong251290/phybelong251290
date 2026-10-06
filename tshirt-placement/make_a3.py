"""A3 (297 x 420 mm) printable PDF of the adult M back placement sheet.  Usage: python3 make_a3.py en|kh
Run make_sheet.py for the same language first (writes data_<lang>.json and back_mockup_edited.png).
Everything except the tee photo is vector (text, dimension lines, table)."""
import base64, json, os, subprocess, sys
from PIL import Image
LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, f'data_{LANG}.json')))
T, FR, BK, G = D['T'], D['FR'], D['BK'], D['G']
KM = str.maketrans('0123456789', '០១២៣៤៥៦៧៨៩')
N = (lambda v: f'{v:.1f}'.translate(KM)) if LANG == 'kh' else (lambda v: f'{v:.1f}')
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
WHITE, YEL, ACC = '#ffffff', '#ffbe28', '#ff963c'

CROP_Y0, CROP_H, IMG_W = 250, 1310, 1390
cb, seam, E, Ti = G['CB_X'], G['SEAM_Y'], G['EMB'], G['TIT']
FS = 19

def line(x0, y0, x1, y1, c, w=2, dash=None):
    return f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{c}" stroke-width="{w}"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def txt(x, y, s, c, size=FS, anchor='start', w=700):
    return f'<text x="{x}" y="{y}" fill="{c}" font-size="{size}" font-weight="{w}" text-anchor="{anchor}">{s}</text>'
def arrow_v(x, y0, y1, label, c):
    o = line(x, y0, x, y1, c)
    for y, s in ((y0, 1), (y1, -1)):
        o += f'<polygon points="{x},{y} {x-5},{y+10*s} {x+5},{y+10*s}" fill="{c}"/>' + line(x-7, y, x+7, y, c)
    return o + txt(x + 12, (y0 + y1) / 2 + 7, label, c)
def arrow_h(y, x0, x1, label, c, above=True):
    o = line(x0, y, x1, y, c)
    for x, s in ((x0, 1), (x1, -1)):
        o += f'<polygon points="{x},{y} {x+10*s},{y-5} {x+10*s},{y+5}" fill="{c}"/>' + line(x, y-7, x, y+7, c)
    return o + txt((x0 + x1) / 2, y - 11 if above else y + 28, label, c, anchor='middle')

svg = line(cb, 380, cb, 1000, WHITE, 2, '8 7')
svg += txt(cb + 10, 376, T['cb'], WHITE, 17)
svg += line(cb - 90, seam, cb + 90, seam, WHITE, 2) + txt(cb - 98, seam + 6, T['seam'], WHITE, 16, 'end')
for b in (E, Ti):
    svg += f'<rect x="{b["x0"]-3}" y="{b["y0"]-3}" width="{b["x1"]-b["x0"]+6}" height="{b["y1"]-b["y0"]+6}" fill="none" stroke="{YEL}" stroke-width="1.6" stroke-dasharray="6 5"/>'
ax = Ti['x1'] + 34
svg += arrow_v(ax, seam, E['y0'], N(G['TOP_CM']), WHITE) + arrow_v(ax, E['y0'], E['y1'], N(G['EMB_H']), YEL)
svg += arrow_v(ax, E['y1'], Ti['y0'], N(G['GAP']), ACC) + arrow_v(ax, Ti['y0'], Ti['y1'], N(G['TIT_H']), YEL)
svg += arrow_h(E['y0'] - 16, E['x0'], E['x1'], N(G['EMB_W']), YEL)
svg += arrow_h(Ti['y1'] + 26, Ti['x0'], Ti['x1'], N(G['TIT_W']), YEL, False)
svg += txt(cb, Ti['y1'] + 80, T['overall'].format(w=N(G['TOT_W']), h=N(G['TOT_H'])), WHITE, 21, 'middle')

PAGE_BG = '#%02x%02x%02x' % Image.open(os.path.join(HERE, 'back_mockup_edited.png')).convert('RGB').getpixel((5, 5))
img = base64.b64encode(open(os.path.join(HERE, 'back_mockup_edited.png'), 'rb').read()).decode()
def font64(n): return base64.b64encode(open(os.path.join(HERE, 'fonts', n), 'rb').read()).decode()
rows = ''.join(f'<tr><th>{r}</th><td>{f}</td><td>{b}</td></tr>' for r, f, b in zip(T['rows'], FR, BK))
notes = ''.join(f'<p>{n}</p>' for n in T['notes'])
html = f'''<!doctype html><html lang="{'km' if LANG=='kh' else 'en'}"><meta charset="utf-8"><style>
@font-face{{font-family:NSK;font-weight:400;src:url(data:font/ttf;base64,{font64('NSK-400.ttf')})}}
@font-face{{font-family:NSK;font-weight:700;src:url(data:font/ttf;base64,{font64('NSK-700.ttf')})}}
@page{{size:297mm 420mm;margin:0}}
*{{box-sizing:border-box;margin:0}}
body{{width:297mm;height:420mm;background:{PAGE_BG};color:#1c1c1c;font-family:NSK,'DejaVu Sans',sans-serif;line-height:1.55;position:relative;overflow:hidden}}
header{{padding:12mm 14mm 0}} h1{{font-size:27pt;line-height:1.5}} .sub{{font-size:12pt;color:#505050}}
.fig{{position:absolute;left:14mm;top:34mm;width:269mm}} .fig svg{{display:block;width:100%;height:auto;font-family:NSK,'DejaVu Sans',sans-serif}}
.low{{position:absolute;left:14mm;right:14mm;top:290mm;display:flex;gap:12mm}}
.tab{{width:150mm}} h2{{font-size:16pt;margin-bottom:3mm}}
table{{border-collapse:collapse;width:100%;font-size:10.5pt}} th,td{{text-align:left;padding:1.6mm 2.5mm;font-weight:400}}
th{{font-weight:700}} thead th{{background:#d6d6d2}} tbody tr:nth-child(even){{background:#dcdcd8}}
.steps{{flex:1;font-size:10pt;color:#3c3c3c}} .steps p{{margin-bottom:2.2mm}} .leg{{font-size:8.5pt;color:#707070;margin-top:4mm}}
footer{{position:absolute;left:0;right:0;bottom:0;height:13mm;background:#1c201a;color:#d6c896;text-align:center;font-size:11pt;line-height:13mm}}
</style><body>
<header><h1>{T['title']}</h1><div class="sub">{T['sub']}</div></header>
<div class="fig"><svg viewBox="0 {CROP_Y0} {IMG_W} {CROP_H}" xmlns="http://www.w3.org/2000/svg">
<image href="data:image/png;base64,{img}" x="0" y="0" width="{IMG_W}" height="1870"/>{svg}</svg></div>
<div class="low"><div class="tab"><h2>{T['tab']}</h2><table><thead><tr><th>{T['cols'][0]}</th><th>{T['cols'][1]}</th><th>{T['cols'][2]}</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="steps"><h2>{T['hdr']}</h2>{notes}<div class="leg">{T['leg']}</div></div></div>
<footer>{T['foot']}</footer></body></html>'''
hp = os.path.join(HERE, f'_a3_{LANG}.html'); out = os.path.join(HERE, f'placement_back_A3_{LANG}.pdf')
open(hp, 'w', encoding='utf-8').write(html)
subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={out}', 'file://' + hp], check=True, capture_output=True)
os.remove(hp)
print(out)
