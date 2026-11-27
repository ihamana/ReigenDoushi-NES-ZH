"""繁體 → 簡體（逐字）。雙語版的繁簡共用同一套字碼，所以只做「一字對一字」轉換。

對照表 t2s_map.json 是用 ICU 的 Traditional-Simplified 轉換，對縫合像素 12px zh_tw 字型
收錄的每個字預先產生的，所以建置時不需要安裝任何轉換套件。
少數用字依大陸慣用字修正（CHARFIX）。
"""
import json, os
_MAP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't2s_map.json'), encoding='utf-8'))
CHARFIX = {'殭': '僵', '彷': '仿', '鍊': '链'}   # 殭屍→僵尸、彷彿→仿佛、鎖鍊→锁链

def t2s_char(c):
    """單字繁→簡；對照表沒有的字保持原樣。"""
    if c in CHARFIX: return CHARFIX[c]
    return _MAP.get(c, c)

def t2s(s):
    if s is None: return s
    return ''.join(t2s_char(c) for c in s)
