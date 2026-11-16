# packs.py SPRITES_DIR OUT_DIR : 64x96 (4x6 cells) shrink-wrapped bundles of vanilla supply bottles, one per
# Cartel Network product, on a kraft cardboard tray.
import os, sys
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

W, H = 64, 96
OUTLINE = (0x29, 0x22, 0x34, 255)

def hexc(h, a=255):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

# product -> (bottle sprite, label colour light, label colour dark)
PRODUCTS = [
    ("acid", "med_bottle_red", "c8505a", "8a2f3e"),
    ("base", "med_bottle_blue", "4f6fa8", "2f4374"),
    ("reducing_agent", "med_bottle_orange", "d0743e", "94482c"),
    ("lipobond_agent", "med_bottle_small_pink", "c07aa0", "84506e"),
    ("alcohol", "mini", "b8c8d0", "7a8c98"),
    ("n_solution", "med_bottle_violet", "8a62a8", "5a3e78"),
]

KRAFT = hexc("b98552")
KRAFT_LIGHT = hexc("d1a06a")
KRAFT_DARK = hexc("8a5a3a")
KRAFT_SHADE = hexc("6e4430")
PAPER = hexc("e8e0c8")
PAPER_SHADE = hexc("c4baa0")
INK = hexc("3a3040")
INTERIOR = hexc("4a3a3c")

def put(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c)

def rect(img, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(img, x, y, c)

def blend(base, over, a):
    return tuple(int(base[i] * (1 - a) + over[i] * a) for i in range(3)) + (base[3],)

def outline(img):
    # 1 px outline around every opaque pixel (alpha > 8), drawn outside the shape.
    px = img.load()
    edge = []
    for y in range(H):
        for x in range(W):
            if px[x, y][3] > 8:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and px[nx, ny][3] > 8 and px[nx, ny] != OUTLINE:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = OUTLINE

def bottles_layer(img, bottle, x0, y_bottom, cols, rows_h):
    # Place a row of bottles whose bottoms sit on y_bottom.
    for i in range(cols):
        img.alpha_composite(bottle, (x0 + i * bottle.width, y_bottom - bottle.height + 1))

def draw(name, sprite, light, dark):
    bottle = Image.open(os.path.join(src, sprite + ".png")).convert("RGBA")
    # Trim the bottle to its opaque box so columns pack edge to edge.
    bb = bottle.getbbox()
    bottle = bottle.crop(bb)
    lab = hexc(light)
    lab_dark = hexc(dark)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    tray_top = 72          # cardboard tray front panel top
    tray_bottom = 93
    inner_x0, inner_x1 = 4, 59

    # Bottles: tiers stacked on cardboard sheets, three or four across.
    bw, bh = bottle.size
    cols = max(1, (inner_x1 - inner_x0 + 1) // bw)
    span = cols * bw
    bx = inner_x0 + (inner_x1 - inner_x0 + 1 - span) // 2
    tiers = []
    y = tray_top + 4       # bottom tier stands inside the tray, its feet hidden behind the front panel
    sheet = 2
    while True:
        top = y - bh + 1
        if top < 9:
            break
        tiers.append(y)
        y = top - 1 - sheet
    # back row (slightly offset, darker) for depth, then front row
    for ty in tiers:
        back = Image.new("RGBA", bottle.size)
        bp = bottle.load()
        for yy in range(bh):
            for xx in range(bw):
                c = bp[xx, yy]
                if c[3]:
                    back.putpixel((xx, yy), blend(c, OUTLINE, 0.45))
        for i in range(cols):
            img.alpha_composite(back, (bx + i * bw + bw // 2, ty - bh - 1))
    for ty in tiers:
        bottles_layer(img, bottle, bx, ty, cols, bh)
    # cardboard sheets between tiers
    for ty in tiers[:-1] if len(tiers) > 1 else []:
        pass
    for i, ty in enumerate(tiers):
        if i == 0:
            continue
        sy = ty + 1
        rect(img, inner_x0 - 1, sy, inner_x1 + 1, sy + sheet - 1, KRAFT)
        rect(img, inner_x0 - 1, sy, inner_x1 + 1, sy, KRAFT_LIGHT)

    content_top = tiers[-1] - bh + 1

    # Shrink wrap: a pale film over everything above the tray, puckered at the top.
    film_top = min(10, content_top - 2)
    px = img.load()
    for yy in range(film_top, tray_top):
        for xx in range(inner_x0 - 2, inner_x1 + 3):
            c = px[xx, yy]
            film = (232, 240, 244)
            if c[3] > 8:
                px[xx, yy] = blend(c, film + (255,), 0.18)
            else:
                px[xx, yy] = blend(INTERIOR, (210, 226, 234, 255), 0.22)
    # film edges, darker
    for yy in range(film_top, tray_top):
        for xx in (inner_x0 - 2, inner_x1 + 2):
            px[xx, yy] = (150, 170, 182, 230)
    # gathered knot at the top
    cx = W // 2
    for k, half in enumerate((10, 7, 4, 3, 4)):
        yy = film_top - 1 - k
        for xx in range(cx - half, cx + half):
            px[xx, yy] = (206, 222, 230, 210)
    for xx in range(cx - 3, cx + 3):
        px[xx, film_top - 6] = (220, 232, 238, 230)
        px[xx, film_top - 7] = (220, 232, 238, 230)
    # pucker folds from the knot down the shoulders
    for k in range(3):
        put(img, cx - 8 + k, film_top + k, (245, 250, 252, 230))
        put(img, cx + 7 - k, film_top + k, (170, 190, 200, 230))
    # diagonal highlight streaks across the film
    for s0, length in ((inner_x0 + 3, 22), (inner_x0 + 9, 10), (inner_x1 - 14, 16)):
        for k in range(length):
            xx, yy = s0 + k // 2, film_top + 6 + k
            if yy < tray_top - 1 and px[xx, yy][3] > 8:
                px[xx, yy] = blend(px[xx, yy], (255, 255, 255, 255), 0.55)

    # Tray front panel.
    rect(img, inner_x0 - 2, tray_top, inner_x1 + 2, tray_bottom, KRAFT)
    rect(img, inner_x0 - 2, tray_top, inner_x1 + 2, tray_top, KRAFT_LIGHT)
    rect(img, inner_x0 - 2, tray_top + 1, inner_x1 + 2, tray_top + 1, KRAFT_LIGHT)
    rect(img, inner_x0 - 2, tray_bottom - 1, inner_x1 + 2, tray_bottom, KRAFT_DARK)
    rect(img, inner_x1 + 1, tray_top + 2, inner_x1 + 2, tray_bottom, KRAFT_DARK)
    # hand hole
    rect(img, cx - 6, tray_top + 4, cx + 5, tray_top + 5, KRAFT_SHADE)
    # coloured band and paper label
    rect(img, inner_x0 - 2, tray_top + 8, inner_x1 + 2, tray_top + 15, lab)
    rect(img, inner_x0 - 2, tray_top + 15, inner_x1 + 2, tray_top + 15, lab_dark)
    rect(img, 9, tray_top + 7, 30, tray_top + 17, PAPER)
    rect(img, 9, tray_top + 17, 30, tray_top + 17, PAPER_SHADE)
    rect(img, 30, tray_top + 8, 30, tray_top + 17, PAPER_SHADE)
    rect(img, 11, tray_top + 9, 22, tray_top + 10, INK)
    rect(img, 11, tray_top + 12, 26, tray_top + 12, lab_dark)
    rect(img, 11, tray_top + 14, 18, tray_top + 14, INK)
    # hazard diamond on the band
    for k in range(4):
        rect(img, 44 - k, tray_top + 8 + k, 44 + k, tray_top + 8 + k, PAPER)
        rect(img, 44 - k, tray_top + 15 - k, 44 + k, tray_top + 15 - k, PAPER)
    rect(img, 44, tray_top + 10, 44, tray_top + 12, lab_dark)
    # stencil arrows (this way up)
    for k in range(3):
        put(img, inner_x1 - 3, tray_top + 3 + k, KRAFT_SHADE)
    put(img, inner_x1 - 4, tray_top + 4, KRAFT_SHADE)
    put(img, inner_x1 - 2, tray_top + 4, KRAFT_SHADE)

    outline(img)

    # Every 16x16 cell must count toward the grid shape: give empty cell centres a nearly invisible pixel.
    for cyc in range(H // 16):
        for cxc in range(W // 16):
            x, y = cxc * 16 + 8, cyc * 16 + 8
            if px[x, y][3] == 0:
                px[x, y] = (0, 0, 0, 2)

    img.save(os.path.join(out, "vce_cartel_pack_" + name + ".png"))

for p in PRODUCTS:
    draw(*p)
print("ok")
