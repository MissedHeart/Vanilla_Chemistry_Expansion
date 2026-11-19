# The nitric oxide canister: the hydrogen canister with its red band recoloured violet.
# usage: python draw_no_canister.py H2_PNG OUT_PNG
import sys
from PIL import Image

SWAP = {
    (0xc2, 0x4a, 0x3d): (0x7a, 0x5a, 0xa6),  # band
    (0xe0, 0x7a, 0x66): (0xa5, 0x8b, 0xcf),  # band highlight
    (0x64, 0x34, 0x3b): (0x3f, 0x2d, 0x5a),  # band shade
}
im = Image.open(sys.argv[1]).convert('RGBA')
px = im.load()
for y in range(im.size[1]):
    for x in range(im.size[0]):
        r, g, b, a = px[x, y]
        if (r, g, b) in SWAP:
            px[x, y] = SWAP[(r, g, b)] + (a,)
im.save(sys.argv[2])
print(sys.argv[2], im.size)
