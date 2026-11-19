# A bundle of dynamite (3 cells wide x 2 tall, 48x32): three red sticks lying on their side, ends to the left, the
# top one set back a little, tied with two dark bands; a fuse out of each end joins into one that trails off to the
# top left. Vanilla palette (the reds of the hydrogen canister, the grey of the vanilla c4 straps), outline 292234,
# light from the top left. Writes OUT_PNG and a 6x preview next to the vanilla c4 sprite.
# usage: python draw_raw_explosive.py OUT_PNG VANILLA_C4_PNG PREVIEW_PNG
import sys
from PIL import Image

OUT, VANILLA, PREVIEW = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 48, 32


def c(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


OUTLINE = c('292234')
RED_HI, RED_LT, RED, RED_SH, RED_DK = c('e8917a'), c('e07a66'), c('c24a3d'), c('9b4a3d'), c('64343b')
BAND_HI, BAND, BAND_SH = c('5f6868'), c('44464c'), c('373541')
FUSE, FUSE_SH = c('a8aea5'), c('88948a')

im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
px = im.load()

STICK_H = 8  # outline to outline; stacked sticks share an outline row
# row shading down a stick, light from the top
BODY = [OUTLINE, RED_HI, RED_LT, RED, RED, RED_SH, RED_DK, OUTLINE]
# the round end facing left, seen a little from the side: rim, lighter face, dark core where the fuse goes in
CAP = [
    ".###.",
    "#hhf#",
    "#hff#",
    "#hoo#",
    "#foo#",
    "#ffs#",
    "#fsd#",
    ".###.",
]
CAP_COLOURS = {'#': OUTLINE, 'f': RED_LT, 'h': RED_HI, 's': RED, 'd': RED_SH, 'o': OUTLINE}


def stick(x0, x1, top):
    for x in range(x0 + 3, x1 + 1):
        for i, col in enumerate(BODY):
            px[x, top + i] = col
    for i in range(1, STICK_H - 1):
        px[x1, top + i] = OUTLINE
    # rounded right end
    px[x1, top] = (0, 0, 0, 0) if px[x1, top + 0] == OUTLINE and top == 0 else px[x1, top]
    for dy, row in enumerate(CAP):
        for dx, ch in enumerate(row):
            if ch != '.':
                px[x0 + dx, top + dy] = CAP_COLOURS[ch]
    return (x0 + 2, top + 3)  # the fuse hole


# the top stick sits back (drawn first, shifted right); the two below are flush
holes = [stick(11, 45, 7), stick(8, 42, 14), stick(8, 42, 21)]

# ---- two bands round the bundle, a pixel proud of it top and bottom ----------------------------------------------
y_top, y_bottom = 7, 28
for band_x in (19, 32):
    for y in range(y_top - 1, y_bottom + 2):
        for dx, col in ((0, BAND_HI), (1, BAND), (2, BAND_SH)):
            x = band_x + dx
            if y in (y_top - 1, y_bottom + 1):
                px[x, y] = OUTLINE
            elif px[x, y] == OUTLINE and y not in (y_top, y_bottom):
                continue  # keep the seams between the sticks
            else:
                px[x, y] = col
    for y in range(y_top - 1, y_bottom + 2):
        for x in (band_x - 1, band_x + 3):
            if px[x, y][3] == 0:
                px[x, y] = OUTLINE


# ---- fuses: out of each end to a knot on the left, then one fuse curling up and away -----------------------------
def line(a, b, col):
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        px[x0, y0] = col
        if (x0, y0) == (x1, y1):
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


KNOT = (3, 15)
for hole in holes:
    line((hole[0] - 2, hole[1] + 1), KNOT, FUSE)
px[KNOT[0], KNOT[1]] = OUTLINE
px[KNOT[0], KNOT[1] + 1] = OUTLINE
line((KNOT[0] - 1, KNOT[1] - 1), (1, 9), FUSE)
line((1, 8), (3, 5), FUSE)
px[4, 4] = FUSE_SH

# ---- every 16x16 cell must count: a nearly invisible pixel at each cell centre left empty ------------------------
for cy in range(H // 16):
    for cx in range(W // 16):
        x, y = cx * 16 + 8, cy * 16 + 8
        if px[x, y][3] == 0:
            px[x, y] = (0, 0, 0, 2)

im.save(OUT)
print(OUT, im.size)

S = 6
van = Image.open(VANILLA).convert('RGBA')
sheet = Image.new('RGBA', ((48 + 48) * S + 36, 48 * S + 24), (0x44, 0x44, 0x4c, 255))
sheet.alpha_composite(van.resize((48 * S, 48 * S), Image.NEAREST), (12, 12))
sheet.alpha_composite(im.resize((W * S, H * S), Image.NEAREST), (48 * S + 24, 12 + 8 * S))
sheet.save(PREVIEW)
