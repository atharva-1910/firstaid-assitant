from draw import *
# heart attack: sitting on the floor, back against a wall, knees bent, still and calm
b = f'<rect x="0" y="0" width="150" height="{H}" fill="{SOFT}"/><rect x="0" y="292" width="{W}" height="68" fill="{FLOOR}"/>'
b += limb([(190, 284), (300, 284)], PANTS, 30)            # thigh along the floor
b += limb([(300, 284), (330, 214), (372, 284)], PANTS, 26)  # bent knee
b += f'<ellipse cx="384" cy="286" rx="22" ry="9" fill="{INK}"/>'
b += limb([(176, 170), (186, 270)], CLOTH, 54)             # back against the wall, slightly reclined
b += head(178, 128)
b += limb([(186, 182), (220, 226), (204, 200)], CLOTH, 18) + hand(200, 196, 11)  # hand on chest
b += limb([(176, 186), (186, 248), (226, 262)], CLOTH, 18) + hand(232, 262, 11)
b += f'<path d="M150,168 L158,168" stroke="{INK}" stroke-width="0"/>'
save("ha_sit_calm", b)

# dog bite: wash under running water with soap
b = basin(250, 268, 360)
b += forearm(150, 205, 300, 205)
for dx in (-16, -4, 8, 20):
    b += f'<circle cx="{250+dx}" cy="{192 + (4 if dx % 8 else 0)}" r="4" fill="#B5634B"/>'
b += tap(250, 78, 190)
for (x, y, r) in [(200, 186, 12), (222, 176, 8), (288, 182, 10), (306, 196, 7), (268, 168, 6), (214, 208, 7)]:
    b += f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" stroke="{WATER}" stroke-width="3"/>'
b += f'<rect x="40" y="96" width="70" height="34" rx="14" fill="{CLOTH2}"/><rect x="52" y="104" width="30" height="8" rx="4" fill="#FFFFFF" opacity="0.6"/>'
b += drops(250, 196, 6, 80)
b += stopwatch(430, 70)
save("bite_wash", b)
