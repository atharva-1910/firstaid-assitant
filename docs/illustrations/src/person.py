from draw import *
def lying(x=90, y=262):
    """Patient on their back, head on the left."""
    s = f'<rect x="0" y="{y+24}" width="{W}" height="{H-y-24}" fill="{SOFT}"/>'
    s += limb([(x+180, y-2), (x+330, y+2)], PANTS, 24) + limb([(x+180, y+10), (x+330, y+14)], PANTS2, 24)
    s += limb([(x+44, y+4), (x+180, y+4)], CLOTH2, 50)
    s += limb([(x+60, y+22), (x+150, y+26)], CLOTH2, 16) + hand(x+156, y+26, 10)
    s += f'<circle cx="{x}" cy="{y}" r="25" fill="{SKIN}"/>'
    s += f'<path d="M{x-25},{y+6} a25,25 0 0 1 8,-24 q10,16 4,40z" fill="{INK}"/>'
    s += f'<path d="M{x+6},{y-8} l8,0 M{x+6},{y+4} l8,0" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'  # closed eyes
    return s
def kneeling_helper(x=150, top=100, lean=0):
    """Helper kneeling behind the patient, knees on the floor."""
    s = limb([(x+20, 230), (x+70, 236), (x+110, 280)], PANTS, 26)
    s += limb([(x+18, top+40), (x+20 + lean*0.2, 228)], CLOTH, 50)
    return s
