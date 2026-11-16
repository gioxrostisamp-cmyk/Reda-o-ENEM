#!/usr/bin/env python3
"""Build the standalone, offline deck.

Reads  src/deck.html  and writes  dist/what-if-life-as-currency.html  with
every font and image inlined, so the file works with no internet.

For each scene referenced in the template as {{IMG:<name>:<layer>}} it makes:
  sharp  the photo, extended 15% on every side with mirrored edges, so the
         camera can pull back below 100% during transitions without gaps
  blur   a radial zoom blur centred on the scene's focus point (motion blur
         shown at the camera's peak speed)
  lit    the photo with its own warm light boosted (screen-composite of a
         blurred map of the orange pixels). Cross-fading sharp -> lit is
         exactly a screen blend at that opacity, without a blend mode.
  dark   (optional) blurred and darkened version, for data slides

Focus points come from the template: data-scene="name" data-focus="fx fy".
"""
import base64
import io
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "deck.html"
OUT = ROOT / "dist" / "what-if-life-as-currency.html"
SCENES = ROOT / "assets" / "scenes"
FONTS = ROOT / "assets" / "fonts"
EXT = 0.15  # mirrored margin on each side, as a fraction of the frame


def b64(data: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def jpeg(img: Image.Image, q: int) -> str:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q, optimize=True, subsampling=0 if q >= 88 else 2)
    return b64(buf.getvalue(), "image/jpeg")


def extend(img: Image.Image) -> Image.Image:
    a = np.asarray(img)
    h, w = a.shape[:2]
    px, py = round(w * EXT), round(h * EXT)
    return Image.fromarray(np.pad(a, ((py, py), (px, px), (0, 0)), mode="symmetric"))


def focus_px(ext: Image.Image, src_size, focus):
    """Focus (fractions of the original frame) -> pixel coords in the extended image."""
    w, h = src_size
    px, py = round(w * EXT), round(h * EXT)
    return px + focus[0] * w, py + focus[1] * h


def zoom_blur(img: Image.Image, center, amount=0.13, steps=22) -> Image.Image:
    w, h = img.size
    cx, cy = center
    acc = np.zeros((h, w, 3), np.float32)
    for i in range(steps):
        s = 1 + amount * i / (steps - 1)
        big = img.resize((round(w * s), round(h * s)), Image.BILINEAR)
        left, top = cx * s - cx, cy * s - cy
        crop = big.crop((round(left), round(top), round(left) + w, round(top) + h))
        acc += np.asarray(crop, np.float32)
    out = Image.fromarray(np.clip(acc / steps, 0, 255).astype(np.uint8))
    return out.filter(ImageFilter.GaussianBlur(1.2))


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def glow_map(img: Image.Image, strength=1.0, box=None) -> Image.Image:
    """box: (x0, y0, x1, y1) in img pixels; only light inside it is boosted."""
    a = np.asarray(img, np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # warm orange: red dominant, green in between, blue low
    hue_ok = smooth(0.05, 0.25, r - b) * smooth(0.0, 0.08, r - g) * smooth(-0.02, 0.1, g - b)
    mask = hue_ok * smooth(0.35, 0.65, sat) * smooth(0.42, 0.85, mx)
    if box:
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        f = 10
        mask = mask * smooth(box[0] - f, box[0] + f, xx) * (1 - smooth(box[2] - f, box[2] + f, xx)) \
                    * smooth(box[1] - f, box[1] + f, yy) * (1 - smooth(box[3] - f, box[3] + f, yy))
    src = Image.fromarray(np.clip(a * mask[..., None] * 255, 0, 255).astype(np.uint8))
    tight = np.asarray(src.filter(ImageFilter.GaussianBlur(3)), np.float32)
    wide = np.asarray(src.filter(ImageFilter.GaussianBlur(18)), np.float32)
    out = (tight * 0.9 + wide * 1.6) * strength
    out[out < 3] = 0
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def dark_variant(img: Image.Image, level=0.3) -> Image.Image:
    a = img.filter(ImageFilter.GaussianBlur(10))
    return Image.fromarray(np.clip(np.asarray(a, np.float32) * level, 0, 255).astype(np.uint8))


def build_scene(name, focus, layers, box=None):
    src = Image.open(SCENES / f"{name}.jpg").convert("RGB")
    ext = extend(src)
    half = ext.resize((ext.width // 2, ext.height // 2), Image.LANCZOS)
    fx, fy = focus_px(ext, src.size, focus)
    out = {}
    if "sharp" in layers:
        out["sharp"] = jpeg(ext, 86)
    if "blur" in layers:
        out["blur"] = jpeg(zoom_blur(half, (fx / 2, fy / 2)), 74)
    if "lit" in layers:
        ebox = None
        if box:  # glow box: fractions of the original frame -> pixels of the extended image
            w, h = src.size
            px, py = round(w * EXT), round(h * EXT)
            ebox = (px + box[0] * w, py + box[1] * h, px + box[2] * w, py + box[3] * h)
        g = glow_map(half, box=tuple(v / 2 for v in ebox) if ebox else None)
        g = np.asarray(g.resize(ext.size, Image.BILINEAR), np.float32) / 255
        a = np.asarray(ext, np.float32) / 255
        lit = Image.fromarray((np.clip(1 - (1 - a) * (1 - g), 0, 1) * 255).astype(np.uint8))
        out["litpos"] = ""
        if ebox:  # only ship (and draw) the patch that actually changes
            m = 80
            x0, y0 = max(0, int(ebox[0] - m)), max(0, int(ebox[1] - m))
            x1, y1 = min(ext.width, int(ebox[2] + m)), min(ext.height, int(ebox[3] + m))
            lit = lit.crop((x0, y0, x1, y1))
            W, H = ext.size
            out["litpos"] = (f"left:{x0 / W * 100:.4f}%;top:{y0 / H * 100:.4f}%;"
                             f"width:{(x1 - x0) / W * 100:.4f}%;height:{(y1 - y0) / H * 100:.4f}%")
        out["lit"] = jpeg(lit, 86)
    if "dark" in layers:
        out["dark"] = jpeg(dark_variant(ext), 80)
    return out


def main():
    html = SRC.read_text(encoding="utf-8")

    # fonts
    def font(m):
        return b64((FONTS / f"{m.group(1)}.woff2").read_bytes(), "font/woff2")

    html = re.sub(r"\{\{FONT:([\w.-]+)\}\}", font, html)

    # scenes: focus points from the template
    focus = {}
    for m in re.finditer(r'data-scene="([\w-]+)"[^>]*?data-focus="([\d.]+) ([\d.]+)"', html):
        focus[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    boxes = {}
    for m in re.finditer(r'data-scene="([\w-]+)"[^>]*?data-glow-box="([\d. ]+)"', html):
        boxes[m.group(1)] = tuple(float(v) for v in m.group(2).split())
    wanted = {}
    for m in re.finditer(r"\{\{IMG:([\w-]+):(\w+)\}\}", html):
        wanted.setdefault(m.group(1), set()).add(m.group(2))
    built = {}
    for name, layers in wanted.items():
        if name not in focus:
            raise SystemExit(f"scene {name} has no data-focus in the template")
        print(f"scene {name}: {sorted(layers)}")
        built[name] = build_scene(name, focus[name], layers, boxes.get(name))

    html = re.sub(r"\{\{IMG:([\w-]+):(\w+)\}\}", lambda m: built[m.group(1)][m.group(2)], html)
    html = re.sub(r"\{\{LITPOS:([\w-]+)\}\}", lambda m: built[m.group(1)]["litpos"], html)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1e6:.1f} MB)")

    # --web PATH: the same page without <!doctype>/<html>/<head>/<body>, for hosts
    # that wrap the page in their own document (charset + viewport come from the host)
    if "--web" in sys.argv:
        web = Path(sys.argv[sys.argv.index("--web") + 1])
        # strip only the page's own skeleton (the notes window's HTML string inside the script stays intact)
        head, rest = html.split("<body>", 1)
        rest, tail = rest.rsplit("</body>", 1)
        head = re.sub(r"<!doctype html>\s*|<html[^>]*>\s*|</?head>\s*|<meta (charset|name=\"viewport\")[^>]*>\s*", "", head, flags=re.I)
        frag = head + rest
        web.parent.mkdir(parents=True, exist_ok=True)
        web.write_text(frag, encoding="utf-8")
        print(f"wrote {web}  ({web.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
