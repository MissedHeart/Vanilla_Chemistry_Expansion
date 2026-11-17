# Handbook bookmark tabs: one coloured tab per chapter, sticking out of the notebook's right edge, with the chapter's
# icon on it. Each tab comes in two lengths: normal and "on" (the chapter being read pokes out further).
#
# The tab body is drawn at the notebook's own pixel size (1 art pixel = 1 design unit = 2 screen pixels) and then
# doubled; the icon is pasted at screen resolution, like the icons on the handbook pages (a 48 px icon in 24 design
# units). So every PNG here is twice the tab's design size.
#
# usage: python draw_bookmarks.py PAPER_DIR VANILLA_SPRITES_DIR OUT_DIR PREVIEW_PNG
import os, sys
from PIL import Image

PAPER, VANILLA, OUT, PREVIEW = sys.argv[1:5]

OUTLINE = (0x29, 0x22, 0x34, 255)
TAB_W, TAB_W_ON, TAB_H = 22, 28, 27   # design units
ICON_BOX = (30, 38)                   # screen px available for the icon

# sprite name suffix (the note's NameKey, "cover" for the first page, "ext" for other mods' sections),
# fill colour, icon file (Paper dir first, then the exported vanilla sprites)
TABS = [
    ("cover",                   "b8a07a", "chemical1"),
    ("formula_name",            "c8524a", "dream_cap"),
    ("ore_notes_name",          "8f8f99", "ore1"),
    ("making_notes_name",       "9a5bb0", "icon_fermenter"),
    ("selling_notes_name",      "c45f95", "bottle5"),
    ("beer_notes_name",         "d98a3d", "icon_beer"),
    ("beer_table_name",         "d9b84a", "red_beer"),
    ("nc_notes_name",           "8fb544", "icon_nuclear_waste"),
    ("crackine_notes_name",     "e0d8c0", "icon_crackine"),
    ("lantern_notes_name",      "b5463f", "icon_lantern"),
    ("electrolysis_notes_name", "4aa8c8", "icon_electrolyzer"),
    ("antibiotic_notes_name",   "4f72c0", "icon_antibiotic"),
    ("ext",                     "8a8a80", "book2"),
]


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def mix(c, t, f):
    return tuple(int(round(c[i] + (t[i] - c[i]) * f)) for i in range(3)) + (255,)


def body(fill, width):
    """Tab body at design resolution: open on the left (it comes out from under the page), rounded on the right."""
    im = Image.new('RGBA', (width, TAB_H), (0, 0, 0, 0))
    px = im.load()
    light = mix(fill, (255, 255, 255), 0.35)
    shade = mix(fill, (0, 0, 0), 0.22)
    dark = mix(fill, (0, 0, 0), 0.38)
    w, h = width, TAB_H
    for y in range(h):
        for x in range(w):
            # 2 px rounded corners on the right
            if x == w - 1 and (y < 2 or y > h - 3):
                continue
            if x == w - 2 and (y == 0 or y == h - 1):
                continue
            edge = (y == 0 or y == h - 1 or x == w - 1
                    or (x == w - 2 and (y == 1 or y == h - 2)))
            if edge:
                px[x, y] = OUTLINE
            elif x < 2:
                px[x, y] = dark                    # the page's shadow on the tab
            elif y == 1 or (x == w - 2 and y < h // 2):
                px[x, y] = light                   # light from the top left
            elif y >= h - 3 or x == w - 2:
                px[x, y] = shade
            else:
                px[x, y] = fill
    return im.resize((w * 2, h * 2), Image.NEAREST)


def load_icon(name):
    for folder in (PAPER, VANILLA, VANILLA + '_ore'):
        path = os.path.join(folder, name + '.png')
        if os.path.exists(path):
            im = Image.open(path).convert('RGBA')
            # vanilla sprites carry near-invisible shape pixels: crop to what is actually drawn
            alpha = im.getchannel('A').point(lambda a: 255 if a > 16 else 0)
            return im.crop(alpha.getbbox())
    raise SystemExit('icon not found: ' + name)


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


def tab(fill, icon, width):
    im = body(rgb(fill), width)
    # icon centred on the part that shows (right of the 2-unit shadow, left of the outline)
    left, right = 2 * 2, (width - 1) * 2
    x = left + (right - left - icon.width) // 2
    y = (TAB_H * 2 - icon.height) // 2
    im.alpha_composite(icon, (x, y))
    return im


os.makedirs(OUT, exist_ok=True)
made = []
for key, fill, icon_name in TABS:
    icon = fit_icon(load_icon(icon_name))
    normal = tab(fill, icon, TAB_W)
    on = tab(fill, icon, TAB_W_ON)
    normal.save(os.path.join(OUT, 'vce_tab_' + key + '.png'))
    on.save(os.path.join(OUT, 'vce_tab_' + key + '_on.png'))
    made.append((normal, on))
    print(key, normal.size, on.size, 'icon', icon.size)

# Preview: the notebook (x2) with the 12 chapter tabs as the handbook lays them out, chapter 4 open.
bg = Image.open(os.path.join(PAPER, 'notebook_manual.png')).convert('RGBA')
bg = bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST)
sheet = Image.new('RGBA', (bg.width + 90, bg.height), (60, 56, 66, 255))
sheet.alpha_composite(bg, (0, 0))
top, step, open_tab = 20, 30, 3
for i, (normal, on) in enumerate(made[:12]):
    im = on if i == open_tab else normal
    sheet.alpha_composite(im, (314 * 2, (top + i * step) * 2))
sheet.save(PREVIEW)
