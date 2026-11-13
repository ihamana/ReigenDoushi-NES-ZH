#!/usr/bin/env python3
"""把自己的圖片（jpg/png…）轉成門口頭像，並產生預覽。

用法：
    python tools/portrait_tool.py master   我的道長.jpg
    python tools/portrait_tool.py disciple 我的文才.png

規格（遊戲內固定）：
    master   師父（道長）: 48 x 64 像素（6 x 8 圖塊），調查房屋時出現
    disciple 弟子（文才）: 32 x 32 像素（4 x 4 圖塊），門口對話時出現
    顏色：4 階灰。

做法：裁掉四周 4%，從中間裁成目標長寬比，縮小到上面的尺寸，自動對比，量化成 4 階灰。
輸出：
    assets/portrait/<master|disciple>.png          遊戲尺寸的灰階圖（建置時直接使用，可再用繪圖軟體修）
    assets/portrait/preview_<master|disciple>.png  放大 4 倍、實際 4 階灰的預覽
之後執行 python build.py <原版ROM> 就會把頭像放進 ROM。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import portrait

def main():
    if len(sys.argv) != 3 or sys.argv[1] not in portrait.SIZES:
        sys.exit(__doc__)
    kind, src = sys.argv[1], sys.argv[2]
    w, h = portrait.SIZES[kind]
    outdir = os.path.join(HERE, '..', 'assets', 'portrait'); os.makedirs(outdir, exist_ok=True)
    im = portrait.prepare(src, w, h)
    q = portrait.quantize(im)
    # 存成量化後的灰階（四個固定亮度），建置時看到的就是這張
    from PIL import Image
    out = Image.new('L', (w, h)); px = out.load()
    for y in range(h):
        for x in range(w): px[x, y] = portrait.LV[q[y][x]]
    p1 = os.path.join(outdir, f'{kind}.png'); out.save(p1)
    p2 = os.path.join(outdir, f'preview_{kind}.png')
    portrait.preview(portrait.to_tiles(q), w, h).save(p2)
    print(f'{kind}: {w}x{h} 像素 → {p1}\n預覽（4 倍）→ {p2}')

if __name__ == '__main__':
    main()
