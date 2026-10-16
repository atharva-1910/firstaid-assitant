"""Animated pictograms (SVG + CSS keyframes). Original work, CC0, Multilingual First Aid Assistant team."""
from draw import *

def anim_svg(body, css):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<style>{css}\n@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}</style>'
            f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>{body}</svg>')

def frames(name, period, events, hold=0.10, rest_scale=None):
    """Keyframes for repeated actions: events = start times (s) inside a period; each is a quick push then release."""
    pass

def strike_keys(name, period, starts, dur, a_from, a_to, prop="rotate", unit="deg", hit=0.35, hold=0.1):
    """Rest at a_from; at each start move to a_to by hit*dur, hold, then return to a_from by the end of dur."""
    pts = [(0.0, a_from)]
    for s in starts:
        pts += [(s, a_from), (s + hit * dur, a_to), (s + (hit + hold) * dur, a_to), (s + dur, a_from)]
    pts.append((period, a_from))
    seen = {}
    for t, v in pts:
        seen[round(100 * t / period, 2)] = v
    body = " ".join(f"{p}% {{ transform: {prop}({v}{unit}); }}" if prop == "rotate"
                    else f"{p}% {{ transform: translate({v[0]}px,{v[1]}px); }}" for p, v in sorted(seen.items()))
    return f"@keyframes {name} {{ {body} }}"

def opacity_keys(name, period, starts, dur, hit=0.35, hold=0.15):
    pts = [(0.0, 0)]
    for s in starts:
        pts += [(s + (hit - 0.02) * dur, 0), (s + hit * dur, 1), (s + (hit + hold) * dur, 1), (s + (hit + hold + 0.1) * dur, 0)]
    pts.append((period, 0))
    seen = {round(100 * t / period, 2): v for t, v in pts}
    return f"@keyframes {name} {{ " + " ".join(f"{p}% {{ opacity: {v}; }}" for p, v in sorted(seen.items())) + " }"

# ------------------------------------------------------------------ CPR (110 per minute)
def cpr():
    P = 60 / 110
    floor = f'<rect x="0" y="288" width="{W}" height="72" fill="{SOFT}"/>'
    # rescuer legs: kneeling behind the patient, knees on the floor
    legs = limb([(262, 206), (300, 270), (372, 274)], PANTS, 30)
    # patient, head on the left
    pat = limb([(250, 262), (400, 266)], PANTS2, 26) + limb([(250, 274), (400, 278)], PANTS2, 26)
    pat += limb([(130, 268), (255, 268)], CLOTH2, 52)
    pat += f'<circle cx="92" cy="262" r="25" fill="{SKIN}"/><path d="M67,268 a25,25 0 0 1 8,-24 q10,16 4,40z" fill="{INK}"/>'
    pat += f'<path d="M98,254 l8,0 M98,266 l8,0" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
    chest = f'<g class="chest"><ellipse cx="180" cy="248" rx="46" ry="14" fill="{CLOTH2}"/></g>'
    # rescuer upper body hinges at the hip; arms straight, shoulders over the hands
    upper = (limb([(262, 206), (196, 132)], CLOTH, 50) + head(188, 98)
             + limb([(192, 140), (182, 228)], CLOTH, 20) + limb([(204, 146), (186, 228)], CLOTH, 20)
             + f'<ellipse cx="183" cy="236" rx="17" ry="9" fill="{SKIN}"/><ellipse cx="183" cy="229" rx="15" ry="8" fill="{SKIN_D}"/>')
    push_arrow = (f'<g class="arrow">' + arrow("M128,170 L128,222", CLOTH, 6) + '</g>')
    css = (f".upper {{ transform-origin: 262px 206px; animation: push {P:.4f}s ease-in-out infinite; }}"
           f"@keyframes push {{ 0%,100% {{ transform: rotate(0deg); }} 45% {{ transform: rotate(-6deg); }} 55% {{ transform: rotate(-6deg); }} }}"
           f".chest {{ transform-origin: 180px 262px; animation: squash {P:.4f}s ease-in-out infinite; }}"
           f"@keyframes squash {{ 0%,100% {{ transform: scaleY(1); }} 45%,55% {{ transform: scaleY(0.55); }} }}"
           f".arrow {{ animation: fade {P:.4f}s ease-in-out infinite; }}"
           f"@keyframes fade {{ 0%,100% {{ opacity: 0.15; }} 45%,55% {{ opacity: 1; }} }}")
    body = floor + legs + pat + chest + f'<g class="upper">{upper}</g>' + push_arrow
    return anim_svg(body, css)

# ------------------------------------------------------------------ back blows (5, then a short pause)
def back_blows():
    period, dur = 6.0, 1.0
    starts = [0, 1, 2, 3, 4]
    floor = f'<rect x="0" y="318" width="{W}" height="42" fill="{SOFT}"/>'
    # rescuer (behind, on the right)
    resc_legs = limb([(306, 214), (296, 314)], PANTS, 24) + limb([(318, 214), (330, 314)], PANTS, 24)
    resc_body = limb([(310, 212), (300, 132)], CLOTH, 48) + head(300, 100)
    # casualty bent forward at the hips, facing left
    cas = limb([(230, 206), (222, 314)], PANTS2, 24) + limb([(242, 206), (252, 314)], PANTS2, 24)
    cas += f'<g class="jolt">' + limb([(236, 200), (152, 150)], CLOTH2, 46) + head(124, 160)
    cas += limb([(160, 156), (150, 218)], CLOTH2, 16) + hand(150, 224, 9) + '</g>'
    support_arm = limb([(296, 150), (244, 206), (180, 192)], CLOTH, 16)
    support_hand = hand(176, 190, 10)
    strike_arm = (limb([(304, 132), (250, 112), (198, 136)], CLOTH, 16)
                  + f'<ellipse cx="190" cy="140" rx="15" ry="10" fill="{SKIN}" transform="rotate(-30 190 140)"/>')
    hits = f'<g class="hit"><path d="M168,116 l-10,-12 M188,108 l0,-16 M208,114 l10,-12" stroke="{CLOTH}" stroke-width="5" stroke-linecap="round"/></g>'
    css = (".arm { transform-origin: 304px 132px; animation: strike 6s ease-in infinite; }" + strike_keys("strike", period, starts, dur, 32, 0)
           + ".hit { animation: hit 6s linear infinite; }" + opacity_keys("hit", period, starts, dur)
           + ".jolt { transform-origin: 236px 200px; animation: jolt 6s ease-out infinite; }"
           + strike_keys("jolt", period, starts, dur, 0, -2, hit=0.38, hold=0.04))
    body = floor + resc_legs + resc_body + support_arm + cas + support_hand + f'<g class="arm">{strike_arm}</g>' + hits
    return anim_svg(body, css)

# ------------------------------------------------------------------ abdominal thrusts (5, then a short pause)
def thrusts():
    period, dur = 6.0, 1.0
    starts = [0, 1, 2, 3, 4]
    floor = f'<rect x="0" y="318" width="{W}" height="42" fill="{SOFT}"/>'
    resc = limb([(262, 214), (256, 314)], PANTS, 24) + limb([(274, 214), (290, 314)], PANTS, 24)
    resc += limb([(268, 212), (264, 128)], CLOTH, 50) + head(266, 94)
    cas = limb([(228, 210), (218, 314)], PANTS2, 24) + limb([(240, 210), (248, 314)], PANTS2, 24)
    cas += f'<g class="jolt">' + limb([(234, 206), (212, 122)], CLOTH2, 50) + head(200, 90)
    cas += limb([(206, 132), (176, 168), (164, 186)], CLOTH2, 16) + hand(162, 192, 9)
    cas += f'<circle cx="203" cy="194" r="3" fill="{INK}" opacity="0.6"/></g>'  # navel
    arm = (limb([(258, 136), (246, 182), (204, 178)], CLOTH, 17)
           + f'<circle cx="197" cy="177" r="12" fill="{SKIN_D}"/>' + f'<ellipse cx="203" cy="174" rx="13" ry="9" fill="{SKIN}"/>')
    guide = f'<g class="guide">' + arrow("M170,214 Q192,206 206,166", CLOTH, 5) + '</g>'
    css = (".arm { animation: thrust 6s ease-in infinite; }" + strike_keys("thrust", period, starts, dur, (0, 0), (12, -12), prop="translate", unit="")
           + ".guide { animation: hit 6s linear infinite; }" + opacity_keys("hit", period, starts, dur, hit=0.3, hold=0.25)
           + ".jolt { transform-origin: 234px 206px; animation: jolt 6s ease-out infinite; }"
           + strike_keys("jolt", period, starts, dur, 0, 1.5, hit=0.36, hold=0.06))
    body = floor + resc + cas + f'<g class="arm">{arm}</g>' + guide
    return anim_svg(body, css)

for name, fn in [("cpr_push", cpr), ("back_blows", back_blows), ("abdominal_thrusts", thrusts)]:
    open(name + ".svg", "w").write(fn())
print("ok")
