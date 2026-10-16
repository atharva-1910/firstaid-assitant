from draw import *
b = basin(250, 268, 360)
b += forearm(150, 205, 300, 205)
b += f'<ellipse cx="250" cy="200" rx="34" ry="14" fill="#E9967A" opacity="0.9"/>'
b += tap(250, 78, 190)
b += f'<path d="M218,195 q32,22 64,0" fill="{WATER}" opacity="0.7"/>'

b += drops(250, 196, 6, 80)
b += stopwatch(430, 70)
save("burn_cool", b)
