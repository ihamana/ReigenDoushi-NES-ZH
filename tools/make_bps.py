"""BPS 修補檔產生器（附自我驗證）。

IPS 只能「寫入新資料」，MMC1 SUROM 擴充時上半部 256KB 需要原版程式的複本，
所以 IPS 會夾帶大量原版遊戲程式碼。BPS 可以「從原版 ROM 複製」，
修補檔只含中文化新增的資料，適合公開散布。

    python tools/make_bps.py 原版.nes 中文版.nes 輸出.bps
"""
import sys, zlib

def _num(n):
    out = bytearray()
    while True:
        x = n & 0x7F; n >>= 7
        if n == 0: out.append(0x80 | x); return bytes(out)
        out.append(x); n -= 1

def make_bps(src, tgt, meta=b''):
    out = bytearray(b'BPS1') + _num(len(src)) + _num(len(tgt)) + _num(len(meta)) + meta
    srel = 0                      # SourceCopy 的相對位置
    i = 0; pending = bytearray()
    def flush():
        nonlocal pending
        if pending:
            out.extend(_num(((len(pending) - 1) << 2) | 1)); out.extend(pending); pending = bytearray()
    def run(off):                 # 從原版 off 開始與目標 i 相同的長度
        n = 0
        while i + n < len(tgt) and 0 <= off + n < len(src) and tgt[i + n] == src[off + n]: n += 1
        return n
    while i < len(tgt):
        same = run(i) if i < len(src) else 0
        best_off, best = None, 0
        for off in (i - 0x40000, i - 0x40000 + 0x4000 * 0):   # 上半部 256KB 是下半部的複本
            if 0 <= off < len(src):
                n = run(off)
                if n > best: best_off, best = off, n
        if same >= 4 and same >= best:
            flush(); out.extend(_num(((same - 1) << 2) | 0)); i += same
        elif best >= 8:
            flush(); d = best_off - srel
            out.extend(_num(((best - 1) << 2) | 2)); out.extend(_num((abs(d) << 1) | (d < 0)))
            srel = best_off + best; i += best
        else:
            pending.append(tgt[i]); i += 1
    flush()
    out += zlib.crc32(src).to_bytes(4, 'little') + zlib.crc32(tgt).to_bytes(4, 'little')
    out += zlib.crc32(out).to_bytes(4, 'little')
    return bytes(out)

def apply_bps(src, p):
    assert p[:4] == b'BPS1'; pos = 4
    def num():
        nonlocal pos
        d = 0; s = 1
        while True:
            x = p[pos]; pos += 1; d += (x & 0x7F) * s
            if x & 0x80: return d
            s <<= 7; d += s
    ss, ts, ms = num(), num(), num(); pos += ms
    assert ss == len(src) and zlib.crc32(src) == int.from_bytes(p[-12:-8], 'little')
    t = bytearray(); sr = tr = 0
    while pos < len(p) - 12:
        a = num(); mode = a & 3; n = (a >> 2) + 1
        if mode == 0: t += src[len(t):len(t) + n]
        elif mode == 1: t += p[pos:pos + n]; pos += n
        elif mode == 2:
            d = num(); sr += -(d >> 1) if d & 1 else (d >> 1); t += src[sr:sr + n]; sr += n
        else:
            d = num(); tr += -(d >> 1) if d & 1 else (d >> 1)
            for _ in range(n): t.append(t[tr]); tr += 1
    assert len(t) == ts and zlib.crc32(t) == int.from_bytes(p[-8:-4], 'little')
    return bytes(t)

if __name__ == '__main__':
    a = open(sys.argv[1], 'rb').read(); b = open(sys.argv[2], 'rb').read()
    p = make_bps(a, b); assert apply_bps(a, p) == b
    open(sys.argv[3], 'wb').write(p); print('bps', len(p), 'bytes')
