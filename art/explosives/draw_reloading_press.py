# Reloading press (32x48, 2 cells wide x 3 tall) in the vanilla machines' three-quarter view (chem_finisher, blender,
# heating_plate, evaporator): every block shows a lighter top face above its front face, round parts are cylinders
# with elliptical tops. Grey-green metal, teal trim, light from the top left, outline 292234.
# A single-stage press: a slab base with an output tray of brass rounds sunk into its top, a column at the back left,
# a top arm carrying the die and a clear powder hopper of white nitrocellulose, the ram with its shell holder and a
# case being pressed, and the handle with its red ball knob raised to the right.
# Writes OUT_PNG and a 4x preview between the vanilla machines.
# usage: python draw_reloading_press.py OUT_PNG VANILLA_DIR PREVIEW_PNG
import os
import sys
from PIL import Image

OUT, VAN, PREVIEW = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 32, 48


def c(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


OUTLINE = c('292234')
M_HI, M_LT, M, M_SH, M_DK = c('a8aea5'), c('88948a'), c('5f6868'), c('44464c'), c('373541')
HOLE, HOLE_DK = c('373248'), c('2f2b3a')
TEAL_DK, TEAL, TEAL_LT = c('275654'), c('45918b'), c('67aaa5')
GLASS, GLASS_LT, GLASS_HI = c('67aaa5'), c('8abfbb'), c('c8e6e2')
POWDER, POWDER_SH = c('e9e6dc'), c('c4c4b0')
BRASS_HI, BRASS, BRASS_SH = c('e0d09b'), c('bb9165'), c('8f6a4a')
COPPER_HI, COPPER, COPPER_SH = c('e07a66'), c('b26b4e'), c('9b4a3d')
KNOB_HI, KNOB, KNOB_SH = c('e07a66'), c('9b4a3d'), c('64343b')

im = Image.new('RGBA', (W, H), (0, 0, 0, 0))


def paste(layer):
    """Outline a part (dict of pixel -> colour) on its own and put it over the image."""
    mask = set(layer)
    px = im.load()
    for (x, y), col in layer.items():
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = col
    for (x, y) in mask:
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + ox, y + oy)
            if n not in mask and 0 <= n[0] < W and 0 <= n[1] < H:
                px[n[0], n[1]] = OUTLINE


def block(x0, x1, y_top, top_h, front_h, top_cols, front_cols):
    """A box seen from the front and above: top face rows, then front face rows. Corners clipped."""
    layer = {}
    hi, top = top_cols
    lt, mid, sh = front_cols
    for y in range(y_top, y_top + top_h + front_h):
        for x in range(x0, x1 + 1):
            if (x in (x0, x1)) and y in (y_top, y_top + top_h + front_h - 1):
                continue
            if y < y_top + top_h:
                col = hi if y == y_top or x == x0 else top
            else:
                col = lt if x == x0 else sh if (x == x1 or y == y_top + top_h + front_h - 1) else mid
            layer[(x, y)] = col
    return layer


def ellipse_in(x, y, cx, cy, rx, ry):
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def cylinder(cx, rx, y_top, height, ry, side_cols, top_cols):
    """Upright cylinder: elliptical top at y_top, body `height` rows, rounded bottom."""
    layer = {}
    lt, mid, sh = side_cols
    t_hi, t = top_cols
    yb = y_top + height
    for y in range(int(y_top - ry - 1), int(yb + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            in_top = ellipse_in(x, y, cx, y_top, rx, ry)
            in_body = (cx - rx <= x + 0.5 <= cx + rx) and y_top <= y + 0.5 <= yb
            in_bot = ellipse_in(x, y, cx, yb, rx, ry)
            if in_top:
                layer[(x, y)] = t_hi if (x + 0.5 - cx) + 2 * (y + 0.5 - y_top) < -rx * 0.4 else t
            elif in_body or in_bot:
                f = (x + 0.5 - (cx - rx)) / (2 * rx)
                layer[(x, y)] = lt if f < 0.3 else mid if f < 0.72 else sh
    # rim: the front edge of the top ellipse as a darker line
    for x in range(int(cx - rx), int(cx + rx) + 1):
        for y in range(int(y_top), int(y_top + ry) + 2):
            if (x, y) in layer and ellipse_in(x, y - 1, cx, y_top, rx, ry) and not ellipse_in(x, y, cx, y_top, rx, ry):
                layer[(x, y)] = side_cols[2] if x + 0.5 > cx + rx * 0.4 else side_cols[1]
    return layer


# ---- base: a slab, deep top face, short front -----------------------------------------------------------------------
base = block(1, 30, 29, 10, 6, (M_HI, M_LT), (M_LT, M, M_SH))
paste(base)
px = im.load()
# feet under the front corners
for fx in (3, 24):
    for x in range(fx, fx + 5):
        px[x, 45] = OUTLINE
        if x not in (fx, fx + 4):
            px[x, 44] = M_DK
# teal lights on the front face
for (lx, col) in ((4, TEAL_LT), (7, TEAL), (10, TEAL_DK)):
    for x in (lx, lx + 1):
        px[x, 40] = OUTLINE
        px[x, 41] = col
        px[x, 42] = OUTLINE
# a vent slot on the front face
for x in range(15, 28):
    px[x, 41] = M_SH
    px[x, 42] = M_DK if x % 2 else M_SH
# output tray sunk into the top face, front right: a dark well seen from above, its back wall showing
tray = {}
for y in range(33, 38):
    for x in range(16, 29):
        if (x in (16, 28)) and y in (33, 37):
            continue
        tray[(x, y)] = HOLE if y > 33 else HOLE_DK
paste(tray)
px = im.load()
for x in range(17, 28):
    px[x, 38] = M_HI  # the lit front lip of the well


def round_top_view(x, y):
    """A round standing in the tray, seen from above-front: copper nose over a short brass body."""
    for (dx, dy), col in (((0, 0), COPPER_HI), ((1, 0), COPPER), ((-1, 1), BRASS_HI), ((0, 1), BRASS),
                          ((1, 1), BRASS), ((2, 1), BRASS_SH), ((-1, 2), BRASS_HI), ((0, 2), BRASS), ((1, 2), BRASS_SH),
                          ((2, 2), BRASS_SH)):
        px[x + dx, y + dy] = col
    for (dx, dy) in ((-1, 0), (2, 0), (0, -1), (1, -1)):
        if px[x + dx, y + dy] != BRASS:
            px[x + dx, y + dy] = OUTLINE


# four rounds standing in the well, seen from above: copper noses over brass, dark gaps between them
for rx in (18, 21, 24, 27):
    px[rx, 34] = COPPER_HI
    px[rx + 1, 34] = COPPER_SH
    px[rx, 35] = BRASS_HI
    px[rx + 1, 35] = BRASS
    px[rx, 36] = BRASS
    px[rx + 1, 36] = BRASS_SH

# ---- column at the back left, standing on the base's top face -------------------------------------------------------
column = block(3, 9, 8, 0, 23, (M_HI, M_LT), (M_LT, M, M_SH))
paste(column)

# ---- the handle (behind the ram and arm) ---------------------------------------------------------------------------
handle = {}
pts = []
x0, y0, x1, y1 = 19, 27, 26, 18
n = max(abs(x1 - x0), abs(y1 - y0))
for t in range(n + 1):
    x = round(x0 + (x1 - x0) * t / n)
    y = round(y0 + (y1 - y0) * t / n)
    handle[(x, y)] = M_LT
    handle[(x, y + 1)] = M_SH
paste(handle)
KNOB_ROWS = [
    ".hhk.",
    "hhkkk",
    "hkkks",
    "kkkss",
    ".kss.",
]
knob = {}
for dy, row in enumerate(KNOB_ROWS):
    for dx, ch in enumerate(row):
        if ch != ".":
            knob[(25 + dx, 13 + dy)] = {"h": KNOB_HI, "k": KNOB, "s": KNOB_SH}[ch]
paste(knob)

# linkage plate from the ram to the handle root, behind the ram
paste({(x, y): (M if x < 21 else M_SH) for x in range(18, 22) for y in range(27, 30)})
# ---- ram and shell holder: a cylinder rising out of the base -------------------------------------------------------
paste(cylinder(16.5, 2.5, 26, 7, 1.0, (M_HI, M_LT, M), (M_HI, M_LT)))          # ram
paste(cylinder(16.5, 4.5, 24, 1, 1.6, (M_LT, M, M_SH), (M_HI, M_LT)))          # shell holder
# the case being pressed, standing in the shell holder
paste(cylinder(16.5, 1.5, 21, 2, 0.6, (BRASS_HI, BRASS, BRASS_SH), (BRASS_HI, BRASS)))

# ---- top arm: top face and front face, teal strip on the front -----------------------------------------------------
arm = block(3, 24, 6, 4, 6, (M_HI, M_LT), (M_LT, M, M_SH))
for x in range(8, 23):
    arm[(x, 12)] = TEAL_LT if x < 22 else TEAL
    arm[(x, 13)] = TEAL
paste(arm)

# ---- die: a short cylinder hanging under the arm --------------------------------------------------------------------
die = cylinder(16.5, 2.5, 16, 3, 0.8, (M_LT, M, M_SH), (M_LT, M))
for (x, y) in list(die):
    if y in (17, 19) and (x, y) in die:
        die[(x, y)] = M_DK
paste(die)

# ---- powder hopper: a clear cylinder of white nitrocellulose on top of the arm -------------------------------------
hop = cylinder(16.5, 3.5, 2, 5, 1.4, (GLASS_HI, GLASS_LT, GLASS), (M_LT, M_SH))
for (x, y), col in list(hop.items()):
    if y >= 4 and y <= 8 and col != OUTLINE:
        f = (x + 0.5 - 13) / 7
        hop[(x, y)] = POWDER if f < 0.65 else POWDER_SH
paste(hop)
px = im.load()
px[14, 4] = GLASS_HI
px[14, 5] = GLASS_HI

# ---- every 16x16 cell must count ------------------------------------------------------------------------------------
for cy in range(H // 16):
    for cx in range(W // 16):
        x, y = cx * 16 + 8, cy * 16 + 8
        # a lone pixel at the centre is not enough for the game: like the beer mug, fill every empty pixel of the
        # cell with a nearly invisible one (alpha 1)
        if px[x, y][3] == 0:
            for yy in range(cy * 16, cy * 16 + 16):
                for xx in range(cx * 16, cx * 16 + 16):
                    if px[xx, yy][3] == 0:
                        px[xx, yy] = (0, 0, 0, 1)

im.save(OUT)
print(OUT, im.size)

names = ['chem_finisher', 'blender', None, 'heating_plate', 'evaporator']
tiles = [im if n is None else Image.open(os.path.join(VAN, n + '.png')).convert('RGBA') for n in names]
S = 4
sheet = Image.new('RGBA', (sum(t.size[0] for t in tiles) + 12 * (len(tiles) + 1), 48 + 24), (0x44, 0x44, 0x4c, 255))
x = 12
for t in tiles:
    sheet.alpha_composite(t, (x, 12))
    x += t.size[0] + 12
sheet.resize((sheet.size[0] * S, sheet.size[1] * S), Image.NEAREST).save(PREVIEW)
