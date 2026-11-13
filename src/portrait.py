"""門口頭像：把一張圖片轉成 NES 圖塊（2bpp，4 階灰）。

頭像規格（遊戲內固定，不能改）：
  師父（道長） master   : 48 x 64 像素 = 6 x 8 個 8x8 圖塊（768 bytes）
  弟子（文才） disciple : 32 x 32 像素 = 4 x 4 個 8x8 圖塊（256 bytes）
  顏色：4 階灰（由暗到亮 0/1/2/3），實際顏色由遊戲調色盤決定。

圖片剛好是上面的尺寸時照原樣量化；其他尺寸的圖片：會先裁掉四周 4%，再從中間裁成上面的長寬比、縮小、
自動對比、量化成 4 階。建議用臉部置中、背景單純的圖片。
"""
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

def placeholder(text, w, h):
    """沒有提供頭像圖片時的預設圖：框線＋文字（用專案內的縫合像素字型）。"""
    import pixfont
    q = [[1] * w for _ in range(h)]
    for x in range(w): q[0][x] = q[h - 1][x] = 3
    for y in range(h): q[y][0] = q[y][w - 1] = 3
    g = Image.new('1', (12 * len(text), 12), 0)
    for i, c in enumerate(text): pixfont.draw(g, i * 12, 0, c, cellw=12, lang='tc')
    if h >= 48:                                   # 直排、放大兩倍
        cells = [g.crop((i * 12, 0, i * 12 + 12, 12)).resize((24, 24), Image.NEAREST) for i in range(len(text))]
        tot = 24 * len(cells); y0 = (h - tot) // 2
        for i, c in enumerate(cells):
            px = c.load(); x0 = (w - 24) // 2
            for y in range(24):
                for x in range(24):
                    if px[x, y]: q[y0 + i * 24 + y][x0 + x] = 3
    else:
        px = g.load(); x0 = (w - g.width) // 2; y0 = (h - 12) // 2
        for y in range(12):
            for x in range(g.width):
                if px[x, y]: q[y0 + y][x0 + x] = 3
    return to_tiles(q)

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
