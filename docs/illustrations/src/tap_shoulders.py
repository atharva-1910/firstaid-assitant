from person import *
floor = f'<rect x="0" y="286" width="{W}" height="74" fill="{SOFT}"/>'
helper = limb([(215, 236), (280, 262), (340, 262)], PANTS, 28)  # thigh to knee, shin flat behind patient
helper += limb([(200, 140), (214, 232)], CLOTH, 52)
helper += head(190, 104)
pat = lying().replace(f'<rect x="0" y="286" width="{W}" height="74" fill="{SOFT}"/>', "")
arms = limb([(192, 150), (160, 210), (136, 244)], CLOTH, 18) + hand(132, 246, 11)
arms += limb([(214, 156), (190, 216), (162, 248)], CLOTH, 18) + hand(158, 250, 11)
shout = "".join(f'<path d="M{158},{104+dy*0.5} L{132},{104+dy}" stroke="{CLOTH}" stroke-width="6" stroke-linecap="round"/>' for dy in (-22, 0, 22))
taps = f'<path d="M112,214 l-8,-14 M134,208 l0,-16 M156,214 l8,-14" stroke="{CLOTH}" stroke-width="5" stroke-linecap="round"/>'
save("unr_tap_shout", floor + helper + pat + arms + shout + taps)

# look at the chest for breathing: helper's head turned down near the patient's face, watching the chest
helper2 = limb([(235, 236), (300, 262), (360, 262)], PANTS, 28)
helper2 += limb([(190, 176), (234, 232)], CLOTH, 52)
helper2 += head(160, 160)
arms2 = limb([(200, 186), (214, 236), (226, 252)], CLOTH, 18) + hand(228, 254, 11)
eye = f'<circle cx="150" cy="170" r="4" fill="{INK}"/>'
sight = f'<path d="M150,176 Q190,200 220,226" stroke="{CLOTH}" stroke-width="4" stroke-dasharray="4 8" fill="none" stroke-linecap="round"/>'
rise = arrow("M250,230 L250,186") + arrow("M280,186 L280,230")
save("unr_check_breathing", floor + helper2 + pat + arms2 + eye + sight + rise + stopwatch(430, 70))
