# Side tab for the explosives chapter (GuideBook.SideTabs): drawn like the column tabs (draw_bookmarks.py, same body),
# but 40 design units long (46 when open) and tucked behind the first two column tabs, halfway between them, so only
# its far end shows past the column: with the cover and formula tabs it makes a sideways 品. The icon, the dynamite
# bundle, sits on that far end. Writes the two PNGs (at twice the design size, like the others) and a preview of the
# top of the notebook, built from the tab PNGs already in PAPER_DIR.
# usage: python draw_side_tab.py PAPER_DIR ITEMS_DIR PREVIEW_PNG
import os
import sys
from PIL import Image

PAPER, ITEMS, PREVIEW = sys.argv[1:4]

OUTLINE = (0x29, 0x22, 0x34, 255)
TAB_W, TAB_H = 22, 27            # column tab, design units
SIDE_W, SIDE_W_ON = 40, 46       # GuideBook.SIDE_TAB_WIDTH / SIDE_TAB_WIDTH_ON
FILL = '77814e'                  # olive drab
KEY = 'explosives_notes_name'
ICON = 'vce_dynamite'
ICON_BOX = (32, 38)              # screen px on the part that shows


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def mix(c, t, f):
    return tuple(int(round(c[i] + (t[i] - c[i]) * f)) for i in range(3)) + (255,)


def body(fill, width):
    """Same as draw_bookmarks.body: open on the left, rounded on the right, light from the top left."""
    im = Image.new('RGBA', (width, TAB_H), (0, 0, 0, 0))
    px = im.load()
    light = mix(fill, (255, 255, 255), 0.35)
    shade = mix(fill, (0, 0, 0), 0.22)
    dark = mix(fill, (0, 0, 0), 0.38)
    w, h = width, TAB_H
    for y in range(h):
        for x in range(w):
            if x == w - 1 and (y < 2 or y > h - 3):
                continue
            if x == w - 2 and (y == 0 or y == h - 1):
                continue
            edge = (y == 0 or y == h - 1 or x == w - 1
                    or (x == w - 2 and (y == 1 or y == h - 2)))
            if edge:
                px[x, y] = OUTLINE
            elif x < 2:
                px[x, y] = dark
            elif y == 1 or (x == w - 2 and y < h // 2):
                px[x, y] = light
            elif y >= h - 3 or x == w - 2:
                px[x, y] = shade
            else:
                px[x, y] = fill
    return im.resize((w * 2, h * 2), Image.NEAREST)


def load_icon():
    im = Image.open(os.path.join(ITEMS, ICON + '.png')).convert('RGBA')
    alpha = im.getchannel('A').point(lambda a: 255 if a > 16 else 0)
    return im.crop(alpha.getbbox())


def fit_icon(icon):
    bw, bh = ICON_BOX
    w, h = icon.size
    for whole in (3, 2, 1):
        if w * whole <= bw and h * whole <= bh:
            return icon.resize((w * whole, h * whole), Image.NEAREST)
    s = min(bw / w, bh / h)
    small = icon.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    a = small.getchannel('A').point(lambda v: 255 if v > 110 else 0)
    small.putalpha(a)
    return small


def tab(icon, width):
    im = body(rgb(FILL), width)
    # the part that shows starts where the column tabs end
    left, right = TAB_W * 2, (width - 1) * 2
    x = left + (right - left - icon.width) // 2
    y = (TAB_H * 2 - icon.height) // 2
    im.alpha_composite(icon, (x, y))
    return im


icon = fit_icon(load_icon())
normal = tab(icon, SIDE_W)
on = tab(icon, SIDE_W_ON)
normal.save(os.path.join(PAPER, 'vce_tab_' + KEY + '.png'))
on.save(os.path.join(PAPER, 'vce_tab_' + KEY + '_on.png'))
print(KEY, normal.size, on.size, 'icon', icon.size)

# Preview: the top right of the notebook, side tab behind the cover and formula tabs; left closed, right open.
bg = Image.open(os.path.join(PAPER, 'notebook_manual.png')).convert('RGBA')
bg = bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST)
column = ['cover', 'formula_name', 'ore_notes_name', 'making_notes_name']
TOP, STEP = 20, 30
frames = []
for side in (normal, on):
    sheet = Image.new('RGBA', (bg.width + 120, 300), (60, 56, 66, 255))
    sheet.alpha_composite(bg.crop((0, 0, bg.width, 300)), (0, 0))
    sheet.alpha_composite(side, (314 * 2, int((TOP + STEP / 2) * 2)))
    for i, key in enumerate(column):
        t = Image.open(os.path.join(PAPER, 'vce_tab_' + key + '.png')).convert('RGBA')
        sheet.alpha_composite(t, (314 * 2, (TOP + i * STEP) * 2))
    frames.append(sheet.crop((bg.width - 160, 0, bg.width + 120, 300)))
out = Image.new('RGBA', (frames[0].width * 2 + 20, frames[0].height), (60, 56, 66, 255))
out.alpha_composite(frames[0], (0, 0))
out.alpha_composite(frames[1], (frames[0].width + 20, 0))
out.save(PREVIEW)
