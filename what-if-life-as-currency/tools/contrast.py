import json, re
import numpy as np
from PIL import Image
def lin(c):
    c = c/255.0
    return np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
def L(rgb): r,g,b = lin(rgb[...,0]), lin(rgb[...,1]), lin(rgb[...,2]); return 0.2126*r+0.7152*g+0.0722*b
rep = json.load(open('contrast.json'))
for s in rep:
    bg = np.asarray(Image.open(f"shots/c-{s['n']}-bg.png").convert('RGB')).astype(float)
    print(f"--- slide {s['n']}")
    for it in s['items']:
        m = re.findall(r'[\d.]+', it['color']); tc = np.array([float(x) for x in m[:3]]); ta = (float(m[3]) if len(m) > 3 else 1.0) * it['op']
        px = np.concatenate([bg[y:y+h, x:x+w].reshape(-1,3) for x,y,w,h in it['rects'] if w>0 and h>0])
        lum = L(px)
        # bright worst-case background pixel (90th percentile)
        idx = np.argsort(lum)[int(len(lum)*0.9)]
        bgc = px[idx]
        eff = tc*ta + bgc*(1-ta)   # text alpha over that background
        Lt, Lb = float(L(eff[None])[0]), float(lum[idx])
        cr = (max(Lt,Lb)+0.05)/(min(Lt,Lb)+0.05)
        med = np.median(lum); crm = (max(Lt,med)+0.05)/(min(Lt,med)+0.05)
        flag = 'OK ' if cr >= 4.5 else ('LOW' if cr < 3 else 'mid')
        print(f"{flag} {cr:5.2f} (median bg {crm:5.2f})  {it['size']:>6}  {it['name']}")
