# The electrolyzer's on/off switch (18x10, drawn 1:1 like the machine UI): a rounded track with a knob.
# On = blue track, knob right; off = red track, knob left. Colours from vce_electrolyzer_lines.png.
# Writes vce_electrolyzer_switch_{on,off}[_hl].png into OUT_DIR, plus a 6x preview sheet.
# usage: python draw_switch.py OUT_DIR PREVIEW_PNG
import os, sys
from PIL import Image

OUT, PREVIEW = sys.argv[1], sys.argv[2]
W, H = 18, 10
OUTLINE = (0x29, 0x22, 0x34, 255)
TRACK = {'on': ((0x3f, 0x6f, 0xb5), (0x7a, 0xa3, 0xdc)), 'off': ((0xc2, 0x4a, 0x3d), (0xe0, 0x7a, 0x66))}
KNOB, KNOB_LIGHT, KNOB_SHADE = (0xd5, 0xd2, 0xb8, 255), (0xee, 0xec, 0xdc, 255), (0xa8, 0xae, 0xa5, 255)


def rgba(c):
    return tuple(c) + (255,)


def mix(a, b, f):
    return tuple(int(round(a[i] + (b[i] - a[i]) * f)) for i in range(3)) + (255,)


def inside(x, y):
    # rounded ends: cut the 2x2 corners down to a diagonal
    if (x, y) in ((0, 0), (1, 0), (0, 1), (W - 1, 0), (W - 2, 0), (W - 1, 1),
                  (0, H - 1), (1, H - 1), (0, H - 2), (W - 1, H - 1), (W - 2, H - 1), (W - 1, H - 2)):
        return False
    return 0 <= x < W and 0 <= y < H


def draw(state, hover):
    base, light = TRACK[state]
    fill = mix(base, (255, 255, 255), 0.15) if hover else rgba(base)
    top = mix(light, (255, 255, 255), 0.15) if hover else rgba(light)
    shade = mix(base, (0, 0, 0), 0.3)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    for y in range(H):
        for x in range(W):
            if not inside(x, y):
                continue
            edge = any(not inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            px[x, y] = OUTLINE if edge else (top if y == 1 or (y == 2 and 1 < x < W - 2) else (shade if y >= H - 2 else fill))
    # the knob: a 6x6 rounded square, right when on, left when off
    kx = W - 8 if state == 'on' else 2
    for y in range(2, 8):
        for x in range(kx, kx + 6):
            corner = (x in (kx, kx + 5)) and (y in (2, 7))
            if corner:
                continue
            ring = x in (kx, kx + 5) or y in (2, 7)
            if ring:
                px[x, y] = OUTLINE
            elif y == 3 or x == kx + 1:
                px[x, y] = KNOB_LIGHT
            elif y == 6 or x == kx + 4:
                px[x, y] = KNOB_SHADE
            else:
                px[x, y] = KNOB
    return im


os.makedirs(OUT, exist_ok=True)
tiles = []
for state in ('on', 'off'):
    for hover in (False, True):
        im = draw(state, hover)
        name = 'vce_electrolyzer_switch_%s%s.png' % (state, '_hl' if hover else '')
        im.save(os.path.join(OUT, name))
        tiles.append(im)
        print(name, im.size)
S = 6
sheet = Image.new('RGBA', ((W * S + 12) * len(tiles), H * S + 12), (0x44, 0x44, 0x4c, 255))
for i, t in enumerate(tiles):
    sheet.alpha_composite(t.resize((W * S, H * S), Image.NEAREST), (6 + i * (W * S + 12), 6))
sheet.save(PREVIEW)
