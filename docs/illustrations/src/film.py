from draw import *
b = f'<rect x="0" y="262" width="{W}" height="98" fill="{SOFT}"/>'
b += "<g transform=\"translate(0,-40)\">" + forearm(140, 200, 310, 200)
b += f'<ellipse cx="240" cy="196" rx="38" ry="14" fill="#E9967A" opacity="0.9"/>'
# loose film laid lengthwise
b += f'<path d="M175,168 L330,170 Q338,200 330,232 L175,230 Q166,200 175,168z" fill="{WATER_L}" opacity="0.55" stroke="{WATER}" stroke-width="2"/>'
b += f'<path d="M190,176 L260,177 M196,222 L300,223" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" opacity="0.9"/>'
# film roll
b += f'<rect x="355" y="282" width="120" height="40" rx="20" fill="{WATER_L}" stroke="{WATER}" stroke-width="3"/>'
b += f'<ellipse cx="365" cy="302" rx="10" ry="20" fill="#FFFFFF" stroke="{WATER}" stroke-width="3"/>'
b += f'<path d="M365,282 Q330,240 300,200" fill="none" stroke="{WATER}" stroke-width="3" stroke-dasharray="6 6"/>'
b = b.replace("<rect x=\"355\"", "</g><rect x=\"355\"", 1)
save("burn_cover", b)
