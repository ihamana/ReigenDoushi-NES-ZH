#!/usr/bin/env python3
"""靈幻道士（Reigen Doushi, FC）繁中／簡中雙語版 一鍵建置。

用法：
    python build.py <原版ROM.nes> [輸出.nes]

原版 ROM 需為 No-Intro「Reigen Doushi (Japan).nes」
（含檔頭 CRC32 8F0EAB04；不含檔頭的 PRG CRC32 0021ED29）。本專案不提供 ROM。
頭像圖片（非必要）：放在 assets/portrait/master.png、disciple.png（見 assets/portrait/README.md）。
"""
import os, sys, zlib, runpy, argparse
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

VERSION = 'V2.6'
HERE = os.path.dirname(os.path.abspath(__file__))
GOOD_FILE = 0x8F0EAB04      # 含 16 bytes iNES 檔頭
GOOD_PRG = 0x0021ED29       # 不含檔頭（256KB PRG）

def check_rom(path):
    data = open(path, 'rb').read()
    if data[:4] != b'NES\x1a':
        sys.exit(f'錯誤：{path} 不是 iNES 格式的 .nes 檔')
    prg = data[16:16 + 0x40000]
    if len(prg) != 0x40000:
        sys.exit(f'錯誤：PRG 大小不是 256KB，請確認是《靈幻道士》日版 ROM')
    if zlib.crc32(data) != GOOD_FILE and zlib.crc32(prg) != GOOD_PRG:
        sys.exit('錯誤：ROM 的 CRC32 不符。需要 No-Intro「Reigen Doushi (Japan).nes」'
                 f'（CRC32 {GOOD_FILE:08X}）。')

def main():
    ap = argparse.ArgumentParser(description='靈幻道士 繁中／簡中雙語版 建置')
    ap.add_argument('rom', help='原版 ROM：Reigen Doushi (Japan).nes')
    ap.add_argument('out', nargs='?', default=os.path.join(HERE, 'out', f'Reigen_Doushi_(CHT_CHS)_{VERSION}.nes'))
    ap.add_argument('--text', default=os.path.join(HERE, 'text', '靈幻道士_翻譯.xlsx'), help='翻譯試算表')
    ap.add_argument('--portrait', default=os.path.join(HERE, 'assets', 'portrait'), help='頭像圖片資料夾')
    ap.add_argument('--ips', action='store_true', help='另外輸出 .ips（以原版 ROM 為基底）')
    a = ap.parse_args()

    check_rom(a.rom)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fonts = os.path.join(HERE, 'fonts')
    os.environ['REIGEN_ROM'] = os.path.abspath(a.rom)
    os.environ['REIGEN_PORTRAIT'] = os.path.abspath(a.portrait)
    os.environ['NESFONT'] = os.path.join(fonts, 'fusion-pixel-12px-monospaced-zh_tw.bdf')
    os.environ['NESFONT_SC'] = os.path.join(fonts, 'fusion-pixel-12px-monospaced-zh_hans.bdf')
    sys.argv = ['patch.py', os.path.abspath(a.text), os.path.abspath(a.out)]
    sys.path.insert(0, os.path.join(HERE, 'src'))
    runpy.run_path(os.path.join(HERE, 'src', 'patch.py'), run_name='__main__')

    out = open(a.out, 'rb').read()
    print(f'\n完成：{a.out}  ({len(out)} bytes, CRC32 {zlib.crc32(out[16:]):08X})')
    if a.ips:
        sys.path.insert(0, os.path.join(HERE, 'tools'))
        from make_ips import make_ips
        p = os.path.splitext(a.out)[0] + '.ips'
        open(p, 'wb').write(make_ips(open(a.rom, 'rb').read(), out))
        print('IPS：', p)

if __name__ == '__main__':
    main()
