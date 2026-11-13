"""點陣字型（BDF）支援。
- 環境變數 NESFONT（繁體）與 NESFONT_SC（簡體）指向 .bdf 時改用點陣字型，
  依字型本身的度量（基線、字寬）放置，不逐字置中，維持原本的工整排列。
- NESFONT_DY：整體垂直位移（像素），預設 1（對齊原本字型的基線）。
- 缺字時回退到向量字型並記錄在 missing。"""
import os
from PIL import ImageDraw
DY = int(os.environ.get('NESFONT_DY', '1'))   # 與原文泉驛正黑的垂直位置對齊
missing = set()
_cache = {}
class BDF:
    def __init__(s, path):
        s.path = path; s.g = {}; s.asc = 0; cur = None; rows = None
        with open(path, encoding='latin-1') as f:
            for ln in f:
                if ln.startswith('FONT_ASCENT'): s.asc = int(ln.split()[1])
                elif ln.startswith('ENCODING'): cur = {'cp': int(ln.split()[1])}
                elif ln.startswith('DWIDTH') and cur is not None: cur['dw'] = int(ln.split()[1])
                elif ln.startswith('BBX') and cur is not None: cur['bbx'] = tuple(int(v) for v in ln.split()[1:5])
                elif ln.startswith('BITMAP') and cur is not None: rows = []
                elif ln.startswith('ENDCHAR'):
                    if cur is not None and cur['cp'] >= 0: cur['rows'] = rows; s.g[cur['cp']] = cur
                    cur = None; rows = None
                elif rows is not None: rows.append(int(ln.strip(), 16) if ln.strip() else 0)
    def has(s, ch): return ord(ch) in s.g
    def draw(s, img, x, y, ch, cellw=None, fallback=None):
        if not s.has(ch):
            if fallback is not None:
                missing.add(ch); d = ImageDraw.Draw(img); d.fontmode = '1'; d.text((x, y), ch, font=fallback, fill=1)
            return
        g = s.g[ord(ch)]; w, h, xo, yo = g['bbx']; nbytes = (w + 7) // 8
        ox = x + xo
        if cellw and g['dw'] < cellw: ox += (cellw - g['dw']) // 2
        top = y + s.asc - (h + yo) + DY
        px = img.load(); W, H = img.size
        for r, bits in enumerate(g['rows']):
            for c in range(w):
                if bits >> (nbytes * 8 - 1 - c) & 1:
                    X, Y = ox + c, top + r
                    if 0 <= X < W and 0 <= Y < H: px[X, Y] = 1
def get(lang='tc'):
    """lang 'tc' → NESFONT, 'sc' → NESFONT_SC（沒設定時用 NESFONT）。沒有設定時回傳 None。"""
    path = os.environ.get('NESFONT_SC' if lang == 'sc' else 'NESFONT') or (os.environ.get('NESFONT') if lang == 'sc' else None)
    if not path: return None
    if path not in _cache: _cache[path] = BDF(path)
    return _cache[path]
# ---- backward-compatible module API (繁體字型) ----
def active(): return get('tc') is not None
def has(ch): f = get('tc'); return bool(f and f.has(ch))
def width(ch): f = get('tc'); return f.g[ord(ch)]['dw'] if f and f.has(ch) else 12
def draw(img, x, y, ch, cellw=None, fallback=None, lang='tc'):
    f = get(lang)
    if f is None:
        if fallback is not None: d = ImageDraw.Draw(img); d.fontmode = '1'; d.text((x, y), ch, font=fallback, fill=1)
        return
    f.draw(img, x, y, ch, cellw, fallback)


def fallback_font(size=12):
    """缺字時的備用向量字型（非必要）。環境變數 NESFONT_FALLBACK 指向 .ttf/.ttc 才會使用；
    沒設定時回傳 None：缺字會列在建置結尾，畫成空白。"""
    path = os.environ.get('NESFONT_FALLBACK')
    if not path or not os.path.exists(path): return None
    from PIL import ImageFont
    return ImageFont.truetype(path, size, index=0)
