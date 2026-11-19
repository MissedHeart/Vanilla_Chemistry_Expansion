# Nitrocellulose: a loose white clump of fibre, like raw cotton wool, no stems. Three sizes:
#   vce_nitrocellulose_s 16x16 (1x1), vce_nitrocellulose 32x16 (2x1), vce_nitrocellulose_l 32x32 (2x2).
# Each clump is a pile of overlapping round tufts drawn back to front, each lit from the top left, with stray fibres
# poking out of the outline. Off-white from the vanilla hydrogen chloride canister, outline 292234.
# usage: python draw_nitrocellulose.py VANILLA_DIR OUT_DIR PREVIEW_PNG
#   (VANILLA_DIR holds kotton_plant_s/kotton_plant/kotton_plant_l.png, used only for the comparison sheet)
import os
import random
import sys
from PIL import Image

SRC, OUT, PREVIEW = sys.argv[1], sys.argv[2], sys.argv[3]


def c(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


OUTLINE = c('292234')
HI, BASE, MID, SHADE, DEEP = c('fbfaf4'), c('e9e6dc'), c('d3d0c6'), c('a9a69c'), c('7e7c78')

# (cx, cy, r) tufts, back to front
CLUMPS = {
    'vce_nitrocellulose_s': ((16, 16), [(6, 8, 4.2), (10, 7, 4.0), (8, 10, 4.5), (11, 11, 3.2)], 3),
    'vce_nitrocellulose': ((32, 16), [(8, 8, 4.5), (15, 6, 5.0), (23, 7, 4.8), (27, 10, 3.6), (11, 11, 4.2),
                                       (19, 11, 4.8), (5, 11, 3.0)], 6),
    'vce_nitrocellulose_l': ((32, 32), [(10, 10, 6.5), (20, 8, 7.0), (25, 15, 6.0), (8, 19, 6.5), (16, 17, 7.5),
                                         (22, 23, 6.5), (12, 25, 5.5), (5, 13, 4.0)], 10),
}


def draw(name, size, tufts, wisps):
    W, H = size
    rnd = random.Random(name)
    owner = [[-1] * W for _ in range(H)]
    for i, (cx, cy, r) in enumerate(tufts):
        for y in range(H):
            for x in range(W):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    owner[y][x] = i
    # keep a 1 px border free for the outline
    for y in range(H):
        for x in range(W):
            if x in (0, W - 1) or y in (0, H - 1):
                owner[y][x] = -1
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()

    def inside(x, y):
        return 0 <= x < W and 0 <= y < H and owner[y][x] >= 0

    for y in range(H):
        for x in range(W):
            i = owner[y][x]
            if i < 0:
                continue
            cx, cy, r = tufts[i]
            dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
            lit = dx + dy  # -: top left, +: bottom right
            # a tuft in front casts a seam on the one behind: pixels next to a later tuft go one step darker
            seam = any(inside(x + ox, y + oy) and owner[y + oy][x + ox] > i for ox, oy in ((-1, 0), (0, -1)))
            if lit < -0.75:
                col = HI
            elif lit < -0.1:
                col = BASE
            elif lit < 0.6:
                col = MID
            elif lit < 1.0:
                col = SHADE
            else:
                col = DEEP
            if seam and col in (HI, BASE):
                col = MID
            elif seam:
                col = SHADE
            px[x, y] = col
    # fibre texture: a few short strokes along the tufts, lighter on the lit side, darker in the shade
    cells = [(x, y) for y in range(2, H - 2) for x in range(2, W - 2) if inside(x, y) and inside(x + 1, y + 1)]
    rnd.shuffle(cells)
    for (x, y) in cells[:max(2, len(cells) // 14)]:
        col = px[x, y]
        stroke = MID if col in (HI, BASE) else (SHADE if col == MID else MID)
        px[x, y] = stroke
        if rnd.random() < 0.6:
            px[x + 1, y + 1] = stroke
    # outline
    for y in range(H):
        for x in range(W):
            if not inside(x, y) and any(inside(x + ox, y + oy) for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = OUTLINE
    # stray fibres: short light strands breaking the outline, each with outline under it
    edge = [(x, y) for y in range(1, H - 1) for x in range(1, W - 1) if px[x, y] == OUTLINE]
    rnd.shuffle(edge)
    placed = 0
    for (x, y) in edge:
        if placed >= wisps:
            break
        # step outward from the clump
        ox = 1 if not inside(x + 1, y) and inside(x - 1, y) else -1 if not inside(x - 1, y) and inside(x + 1, y) else 0
        oy = 1 if not inside(x, y + 1) and inside(x, y - 1) else -1 if not inside(x, y - 1) and inside(x, y + 1) else 0
        if ox == 0 and oy == 0:
            continue
        nx, ny = x + ox, y + oy
        if not (0 <= nx < W and 0 <= ny < H) or px[nx, ny][3] != 0:
            continue
        px[x, y] = BASE if oy <= 0 else MID
        px[nx, ny] = OUTLINE
        placed += 1
    # every 16x16 cell counts
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
    return im


tiles = []
for name, (size, tufts, wisps) in CLUMPS.items():
    im = draw(name, size, tufts, wisps)
    im.save(os.path.join(OUT, name + '.png'))
    print(name, im.size)
    tiles.append(im)

S = 5
vanilla = [Image.open(os.path.join(SRC, n + '.png')).convert('RGBA') for n in ('kotton_plant_s', 'kotton_plant', 'kotton_plant_l')]
W = sum(max(v.size[0], t.size[0]) for v, t in zip(vanilla, tiles)) + 12 * 4
sheet = Image.new('RGBA', (W, 32 * 2 + 36), (0x44, 0x44, 0x4c, 255))
x = 12
for v, t in zip(vanilla, tiles):
    sheet.alpha_composite(v, (x, 12))
    sheet.alpha_composite(t, (x, 56))
    x += max(v.size[0], t.size[0]) + 12
sheet.resize((sheet.size[0] * S, sheet.size[1] * S), Image.NEAREST).save(PREVIEW)
