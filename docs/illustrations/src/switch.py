from draw import *
b = f'<rect x="0" y="0" width="{W}" height="{H}" fill="#F5F8FA"/>'
# switch board
b += f'<rect x="120" y="50" width="260" height="250" rx="16" fill="#FFFFFF" stroke="{METAL}" stroke-width="6"/>'
b += f'<rect x="150" y="80" width="200" height="40" rx="6" fill="{FLOOR}"/>'
for i, x in enumerate([170, 215, 260, 305]):
    b += f'<rect x="{x}" y="150" width="30" height="100" rx="6" fill="{FLOOR}"/>'
    up = i != 0
    b += f'<rect x="{x+4}" y="{156 if up else 200}" width="22" height="44" rx="5" fill="{PANTS if up else CLOTH}"/>'
# OFF lever: index finger pushing it down
b += limb([(110, 330), (150, 230)], CLOTH, 40)
b += f'<ellipse cx="164" cy="214" rx="26" ry="20" fill="{SKIN}"/>'
b += limb([(176, 206), (186, 196)], SKIN, 13)
b += arrow("M100,150 L100,220")
# lightning icon with a slash: power off
b += (f'<g transform="translate(420,80)"><circle r="34" fill="{SOFT}"/>'
      f'<path d="M4,-22 L-12,4 L0,4 L-4,24 L12,-4 L0,-4z" fill="{PANTS}"/>'
      f'<line x1="-24" y1="24" x2="24" y2="-24" stroke="{CLOTH}" stroke-width="6" stroke-linecap="round"/></g>')
save("elec_switch_off", b)
