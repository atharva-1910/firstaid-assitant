from draw import *
def flame(x, y, s=1.0):
    return (f'<path d="M{x},{y} c{-14*s},{-10*s} {-14*s},{-30*s} 0,{-46*s} c{2*s},{14*s} {14*s},{16*s} {12*s},{30*s} c{-1*s},{10*s} {-6*s},{16*s} {-12*s},{16*s}z" fill="{FLAME}"/>'
            f'<path d="M{x},{y-2*s} c{-6*s},{-6*s} {-5*s},{-16*s} 0,{-22*s} c{2*s},{8*s} {7*s},{10*s} {5*s},{16*s} c{-1*s},{4*s} {-3*s},{6*s} {-5*s},{6*s}z" fill="{FLAME_L}"/>')
def num(x, n):
    return (f'<circle cx="{x}" cy="34" r="18" fill="{CLOTH}"/>'
            f'<text x="{x}" y="41" font-family="DejaVu Sans, sans-serif" font-size="20" font-weight="700" fill="#fff" text-anchor="middle">{n}</text>')
b = f'<rect x="0" y="300" width="{W}" height="60" fill="{SOFT}"/>'
b += f'<line x1="167" y1="20" x2="167" y2="340" stroke="{FLOOR}" stroke-width="3"/><line x1="333" y1="20" x2="333" y2="340" stroke="{FLOOR}" stroke-width="3"/>'
# 1 stop: standing still, arms at sides
x = 83
b += limb([(x-9, 200), (x-12, 296)], PANTS, 22) + limb([(x+9, 200), (x+12, 296)], PANTS, 22)
b += limb([(x, 122), (x, 196)], CLOTH, 46)
b += limb([(x-22, 128), (x-30, 196)], CLOTH, 18) + limb([(x+22, 128), (x+30, 196)], CLOTH, 18)
b += hand(x-30, 202) + hand(x+30, 202)
b += head(x, 92)
b += flame(x+18, 196, 0.9) + flame(x-14, 186, 0.6)
b += num(x, 1)
# 2 drop: kneeling, hands over face
x = 250
b += limb([(x-20, 230), (x+20, 262), (x-14, 296)], PANTS, 22)
b += limb([(x-10, 232), (x+30, 270), (x+2, 296)], PANTS2, 22)
b += limb([(x-14, 168), (x-18, 232)], CLOTH, 46)
b += limb([(x+4, 172), (x+24, 196), (x+8, 146)], CLOTH, 18)
b += head(x+4, 138)
b += hand(x+10, 140, 11)
b += flame(x-30, 232, 0.6)
b += arrow(f"M{x+52},96 L{x+52},176")
b += num(x, 2)
# 3 roll: lying on the floor, arms crossed over face, roll arrow
x = 416
b += limb([(x-58, 284), (x+30, 284)], CLOTH, 44)
b += limb([(x+30, 278), (x+70, 280)], PANTS, 22) + limb([(x+30, 290), (x+70, 292)], PANTS2, 22)
b += head(x-76, 280, 22)
b += limb([(x-40, 274), (x-70, 262)], CLOTH, 16) + hand(x-72, 262, 10)
b += arrow(f"M{x-48},210 A60,34 0 1 1 {x+40},214")
b += num(x, 3)
save("burn_stop_drop_roll", b)
