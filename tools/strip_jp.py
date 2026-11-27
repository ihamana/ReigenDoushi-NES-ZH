"""把本機的完整翻譯試算表（含日文原文）轉成可公開的版本（不含遊戲原文）。

  python tools/strip_jp.py <完整版.xlsx> text/靈幻道士_翻譯.xlsx

會做的事：
  對話       「日文原文」換成「日文結尾換行數」（建置時用來對齊選項位置），刪掉「原始HEX」
  門口說明   清空「日文原文」
  選單與介面 保留（只有幾個字的介面標籤，建置時當作對照用的鍵）
其他分頁、中文翻譯、備註都原樣保留。
"""
import sys
from openpyxl import load_workbook

def strip(src, dst):
    wb = load_workbook(src)
    ws = wb['對話']
    hdr = [c.value for c in ws[1]]
    jp = hdr.index('日文原文') + 1 if '日文原文' in hdr else None
    if jp:
        ws.cell(1, jp).value = '日文結尾換行數'
        for r in range(2, ws.max_row + 1):
            v = ws.cell(r, jp).value
            if isinstance(v, str):
                ws.cell(r, jp).value = len(v) - len(v.rstrip('\n'))
    if '原始HEX' in hdr:
        ws.delete_cols(hdr.index('原始HEX') + 1)
    if '門口說明' in wb.sheetnames:
        ws = wb['門口說明']; hdr = [c.value for c in ws[1]]
        if '日文原文' in hdr:
            k = hdr.index('日文原文') + 1
            ws.cell(1, k).value = '日文原文（公開版不收錄）'
            for r in range(2, ws.max_row + 1): ws.cell(r, k).value = None
    wb.save(dst)

if __name__ == '__main__':
    strip(sys.argv[1], sys.argv[2])
    print('wrote', sys.argv[2])
