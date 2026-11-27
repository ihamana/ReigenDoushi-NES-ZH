"""門口頭像圖片 → NES 圖塊（師父 48×64、弟子 32×32，4 階灰）。"""
from PIL import Image, ImageOps, ImageDraw

LV = [0, 84, 152, 236]          # 4 階灰的參考亮度
SIZES = {'master': (48, 64), 'disciple': (32, 32)}

def prepare(src, w, h):
    """讀圖 → 裁切 → 縮小 → 自動對比，回傳 w x h 的灰階圖（尚未量化）。"""
    im = Image.open(src).convert('L'); W, H = im.size
    if (W, H) == (w, h):            # 已經是遊戲尺寸（例如 portrait_tool.py 的輸出）：照原樣使用
        return im
    t = int(min(W, H) * 0.04); im = im.crop((t, t, W - t, H - t))
    W, H = im.size; ar = w / h
    if W / H > ar:
        nw = int(H * ar); im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:
        nh = int(W / ar); im = im.crop((0, 0, W, nh))
    return ImageOps.autocontrast(im.resize((w, h), Image.LANCZOS), cutoff=1)

def quantize(im):
    """灰階圖 → 每個像素 0..3。"""
    px = im.load(); w, h = im.size
    return [[min(range(4), key=lambda i: abs(LV[i] - px[x, y])) for x in range(w)] for y in range(h)]

def to_tiles(q):
    """0..3 的二維陣列 → NES 2bpp 圖塊（由左到右、由上到下）。"""
    h = len(q); w = len(q[0]); out = bytearray()
    for ty in range(h // 8):
        for tx in range(w // 8):
            p0 = bytearray(8); p1 = bytearray(8)
            for y in range(8):
                for x in range(8):
                    k = q[ty * 8 + y][tx * 8 + x]
                    if k & 1: p0[y] |= 0x80 >> x
                    if k & 2: p1[y] |= 0x80 >> x
            out += p0 + p1
    return bytes(out)

def portrait_tiles(src, w, h):
    return to_tiles(quantize(prepare(src, w, h)))

def preview(tiles, w, h, scale=4):
    """圖塊 → 預覽圖（4 階灰，放大 scale 倍）。"""
    im = Image.new('L', (w, h)); px = im.load(); i = 0
    for ty in range(h // 8):
        for tx in range(w // 8):
            p0 = tiles[i:i + 8]; p1 = tiles[i + 8:i + 16]; i += 16
            for y in range(8):
                for x in range(8):
                    k = ((p0[y] >> (7 - x)) & 1) | (((p1[y] >> (7 - x)) & 1) << 1)
                    px[tx * 8 + x, ty * 8 + y] = LV[k]
    return im.resize((w * scale, h * scale), Image.NEAREST)
