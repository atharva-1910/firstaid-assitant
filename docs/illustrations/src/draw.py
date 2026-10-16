"""Flat pictograms for first aid steps. Original work, released CC0 by the project team."""
import cairosvg, io, sys
from PIL import Image

W, H = 500, 360
SKIN = "#E3B08C"; SKIN_D = "#C98F6A"
CLOTH = "#2F6F8F"; CLOTH2 = "#7FA7BC"; PANTS = "#41505E"; PANTS2 = "#5D6B78"
INK = "#1F2933"; WATER = "#5DB3D9"; WATER_L = "#BFE4F3"; METAL = "#9AA5B1"; FLOOR = "#D9E2EC"
FLAME = "#F2A93B"; FLAME_L = "#F8D27A"; SOFT = "#E6F0F5"

def limb(pts, color, w=22):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'

def head(x, y, r=24, hair=True, face=0):
    s = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{SKIN}"/>'
    if hair:
        s += f'<path d="M{x-r},{y-2} a{r},{r} 0 0 1 {2*r},0 q-{r},-{r*0.5} -{2*r},0z" fill="{INK}"/>'
    return s

def hand(x, y, r=10):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{SKIN}"/>'

def svg(body, bg="#FFFFFF"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="{bg}"/>{body}</svg>')

def save(name, body):
    s = svg(body)
    open(name + ".svg", "w").write(s)
    png = cairosvg.svg2png(bytestring=s.encode(), output_width=W, output_height=H)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    im.save(name + ".webp", "WEBP", quality=88, method=6)
    im.save(name + ".png")

def tap(x, y, flow_to):
    """Wall tap with water falling to flow_to (y)."""
    s = f'<rect x="{x-70}" y="{y-34}" width="90" height="22" rx="8" fill="{METAL}"/>'
    s += f'<rect x="{x-14}" y="{y-34}" width="28" height="44" rx="8" fill="{METAL}"/>'
    s += f'<rect x="{x-30}" y="{y-54}" width="60" height="12" rx="6" fill="{METAL}"/>'
    s += f'<rect x="{x-11}" y="{y+6}" width="22" height="{flow_to-y-6}" rx="8" fill="{WATER}" opacity="0.85"/>'
    s += f'<rect x="{x-5}" y="{y+10}" width="5" height="{flow_to-y-20}" rx="2" fill="#FFFFFF" opacity="0.6"/>'
    return s

def drops(cx, cy, n=5, spread=70):
    s = ""
    import math
    for i in range(n):
        a = math.pi * (0.15 + 0.7 * i / max(1, n - 1))
        x = cx + spread * math.cos(a) * (1 if i % 2 else -1) * 0.8
        y = cy + 18 + 14 * (i % 3)
        s += f'<path d="M{x},{y-9} q6,9 0,13 q-6,-4 0,-13z" fill="{WATER}"/>'
    return s

def basin(cx, y, w=300):
    return (f'<path d="M{cx-w/2},{y} h{w} q-8,52 -50,58 h-{w-100} q-42,-6 -50,-58z" fill="{SOFT}" stroke="{FLOOR}" stroke-width="4"/>'
            f'<ellipse cx="{cx}" cy="{y}" rx="{w/2}" ry="10" fill="{FLOOR}"/>')

def stopwatch(x, y, r=26):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" stroke="{CLOTH}" stroke-width="6"/>'
            f'<rect x="{x-7}" y="{y-r-12}" width="14" height="10" rx="3" fill="{CLOTH}"/>'
            f'<path d="M{x},{y} L{x},{y-r+9} M{x},{y} L{x+12},{y+6}" stroke="{CLOTH}" stroke-width="5" stroke-linecap="round"/>')

def arrow(path, color=CLOTH, w=6):
    return (f'<defs><marker id="ah{abs(hash(path))%9999}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10z" fill="{color}"/></marker></defs>'
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" marker-end="url(#ah{abs(hash(path))%9999})"/>')

def forearm(x0, y0, x1, y1, sleeve=CLOTH):
    """Horizontal forearm from elbow (x0,y0) to wrist (x1,y1) with a hand."""
    s = limb([(x0 - 70, y0 + 30), (x0, y0)], sleeve, 46)
    s += limb([(x0, y0), (x1, y1)], SKIN, 38)
    s += f'<ellipse cx="{x1+30}" cy="{y1+4}" rx="36" ry="22" fill="{SKIN}"/>'
    s += limb([(x1 + 52, y1 - 6), (x1 + 74, y1 - 2)], SKIN, 12)
    s += limb([(x1 + 54, y1 + 4), (x1 + 78, y1 + 8)], SKIN, 12)
    s += limb([(x1 + 50, y1 + 14), (x1 + 72, y1 + 18)], SKIN, 12)
    s += limb([(x1 + 34, y1 - 16), (x1 + 52, y1 - 24)], SKIN, 12)
    return s
