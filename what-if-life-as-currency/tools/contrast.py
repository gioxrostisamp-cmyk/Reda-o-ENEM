import json, re, sys, os
import numpy as np
from PIL import Image
os.chdir(sys.argv[1] if len(sys.argv) > 1 else '.')
def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def L(rgb): return 0.2126 * lin(rgb[..., 0]) + 0.7152 * lin(rgb[..., 1]) + 0.0722 * lin(rgb[..., 2])
worst = []
for s in json.load(open('contrast.json')):
    bg = np.asarray(Image.open(f"shots/c-{s['n']}-bg.png").convert('RGB')).astype(float)
    print(f"--- slide {s['n']}")
    for it in s['items']:
        m = re.findall(r'[\d.]+', it['color']); tc = np.array([float(x) for x in m[:3]])
        ta = (float(m[3]) if len(m) > 3 else 1.0) * it['op']
        px = np.concatenate([bg[max(0, y):y + h, max(0, x):x + w].reshape(-1, 3) for x, y, w, h in it['rects']])
        if not len(px): continue
        lum = L(px); idx = np.argsort(lum)[int(len(lum) * 0.9)]
        bgc = px[idx]; eff = tc * ta + bgc * (1 - ta)
        Lt, Lb = float(L(eff[None])[0]), float(lum[idx])
        cr = (max(Lt, Lb) + 0.05) / (min(Lt, Lb) + 0.05)
        flag = 'OK ' if cr >= 4.5 else ('LOW' if cr < 3 else 'mid')
        print(f"{flag} {cr:5.2f}  {it['size']:>6}  {it['name']}")
        if cr < 4.5: worst.append((s['n'], round(cr, 2), it['name']))
print('below 4.5:1 →', worst if worst else 'none')
