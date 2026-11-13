import sys, re, json, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from asm import Asm
from openpyxl import load_workbook
from PIL import Image, ImageDraw, ImageFont
from collections import Counter

SRC=os.environ['REIGEN_ROM']                      # 原版 ROM（build.py 會檢查 CRC32）
XLSX=sys.argv[1]
OUT=sys.argv[2]
PORTRAIT_DIR=os.environ.get('REIGEN_PORTRAIT','')
LANG='dual'   # 一個 ROM 內含繁中＋簡中：文字用同一套字碼，簡中只換字形（標題選單第三行切換）
from zhconv import t2s
TT=lambda s: s
from zhconv import t2s_char
SCC=lambda s: ''.join(t2s_char(c) for c in s)   # 逐字繁→簡（字碼共用，所以必須逐字對應）
raw=open(SRC,'rb').read(); hdr=bytearray(raw[:16]); prg=bytearray(raw[16:])
assert len(prg)==0x40000

# ---------------- original messages ----------------
msgs=[];cur=0x5280
for i in range(0x5280,0x7ab0):
    if prg[i]==0x24: msgs.append((cur,i-cur+1)); cur=i+1   # (offset, length incl. terminator)

# ---------------- translations ----------------
wb=load_workbook(XLSX)
trans={}; namepre={}
for r in wb['對話'].iter_rows(min_row=2,values_only=True):
    trans[int(r[0])]=TT(r[5]) if r[5] is not None else ''
    if r[5] is not None and r[4] is not None and r[4]!='':   # 結尾換行數對齊日文原文（少了會讓選項游標錯位，例 #212）
        tn=lambda s: len(s)-len(s.rstrip('\n'))
        k=r[4] if isinstance(r[4],int) else (int(r[4]) if str(r[4]).isdigit() else tn(r[4]))   # 公開版試算表只留換行數
        trans[int(r[0])]=trans[int(r[0])].rstrip('\n')+'\n'*k
    namepre[int(r[0])]='前面接主角名字' in (r[6] or '')

# ---------------- character set & codes ----------------
KANA="をぁぃぅぇぉゃゅょっーあいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん゛゜"
DAK="がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
fixed={}   # char -> glyph id (< 0x100 direct codes)
for i,c in enumerate(KANA): fixed[c]=0xA6+i
for i,c in enumerate(DAK): fixed[c]=0x61+i
for c,v in (('。',0xA1),('「',0xA2),('」',0xA3),('、',0xA4),('・',0xA5)): fixed[c]=v
for i in range(10): fixed[str(i)]=0x30+i
TOK=re.compile(r'<等待>|<選項>|<換頁>|.',re.S)
def tokens(t): return TOK.findall(t)
cnt=Counter()
for n,t in trans.items():
    for tk in tokens(t):
        if len(tk)==1 and tk not in '\n  ' and tk not in fixed: cnt[tk]+=1
# extra chars needed elsewhere (menus) can be appended here
for c in TT('林道長師父，正英'): cnt[c]+=1
single_slots=[c for c in list(range(0x07,0x20))+[0x21,0x22,0x23]+list(range(0x25,0x30))+[0x3A,0x3C,0x3D,0x3E,0x3F]+list(range(0x41,0x61))+list(range(0x7A,0x80))+list(range(0xE0,0x100))]
order=[c for c,_ in cnt.most_common()]
code={}   # char -> bytes
gid={}    # char -> glyph id
for c,v in fixed.items(): code[c]=bytes([v]); gid[c]=v
for c,slot in zip(order,single_slots): code[c]=bytes([slot]); gid[c]=slot
rest=order[len(single_slots):]
nid=0x100
for c in rest:
    while (nid & 511)>=500: nid+=1          # keep away from bank tail (reset stub area)
    pre=0x80+((nid-0x100)>>8); b2=(nid-0x100)&0xFF
    assert pre<0xA0
    code[c]=bytes([pre,b2]); gid[c]=nid; nid+=1
maxid=nid
print('chars',len(cnt),'single',min(len(order),len(single_slots)),'double',len(rest),'max glyph id',hex(maxid))

# ---------------- font ----------------
import pixfont
FONT=pixfont.fallback_font()
PIX=pixfont.active()
def glyph(ch,lang='tc'):
    g=Image.new('1',(16,16),0); d=ImageDraw.Draw(g); d.fontmode='1'
    pf=pixfont.get(lang)
    if pf and pf.has(ch):
        # bitmap font: keep the font's own grid placement (no per-glyph centring)
        pf.draw(g,0,0,ch,cellw=8 if ch in '0123456789' else 12)
        return _pack(g)
    if PIX: pixfont.missing.add(ch)
    if FONT is None: pixfont.missing.add(ch)
    else: d.text((0,0),ch,font=FONT,fill=1)
    # horizontal alignment: centre every glyph in its cell (12px, digits 8px),
    # except brackets which keep the font's own left/right placement
    bb=g.getbbox()
    if bb and ch not in '「」『』（）〔〕【】《》〈〉()':
        cellw=8 if ch in '0123456789' else 12
        x0,y0,x1,y1=bb; gw=x1-x0
        if gw<cellw:
            c=g.crop((x0,0,x1,16)); g=Image.new('1',(16,16),0); g.paste(c,((cellw-gw)//2,0))
    return _pack(g)
def _pack(g):
    px=g.load(); L=bytearray(16); R=bytearray(16)
    for y in range(16):
        for x in range(16):
            if px[x,y]:
                if x<8: L[y]|=0x80>>x
                else: R[y]|=0x80>>(x-8)
    for y in range(16): R[y]&=0xF0          # 12px max
    return bytes(L+R)
nbanks=(maxid+511)//512; assert nbanks<=2
font=bytearray(b'\x00'*(2*0x4000)); font_sc=bytearray(b'\x00'*(2*0x4000))
for c,i in gid.items():
    o=(i>>9)*0x4000+(i&511)*32
    font[o:o+32]=glyph(c,'tc')
    font_sc[o:o+32]=glyph(SCC(c),'sc')     # 簡中字形：同一個字碼，上半部 bank 19-20

# ---------------- encode text ----------------
from layout import layout, preview
laid={}; previews={}
for n in range(1,len(msgs)+1):
    t=trans.get(n,'')
    toks,info=layout(t,namepre.get(n,False),'<選項>' in t)
    laid[n]=toks; previews[n]=preview(toks,namepre.get(n,False))
def encode(toks,n):
    out=bytearray()
    for tk in toks:
        if tk=='<等待>': out.append(0x40)
        elif tk=='<選項>': out.append(0x06)
        elif tk=='<換頁>': out.append(0x01)
        elif tk=='\n': out.append(0x3B)
        elif tk==' ': out.append(0x20)
        elif tk=='　': out.append(0xA0)
        elif tk in code: out+=code[tk]
        else: raise Exception(f'#{n}: no code for {tk!r}')
    out.append(0x24); return out
enc={n:encode(laid[n],n) for n in laid}
# ---------------- placement (packed below $BA61 in bank 1) ----------------
def refs(off):
    # only real "print text" script instructions: opcode 03 followed by the address
    p=off-0x4000+0x8000; b=bytes([p&255,p>>8])
    return [j for j in range(0x4001,0x5280) if prg[j:j+2]==b and prg[j-1]==0x03]
newprg=bytearray(prg)
TEXT_END=0x7700
for i in range(0x5280,0x7FB0): newprg[i]=0xFF
final={}; reserved=[]; moved=[]
refmap={n:refs(off) for n,(off,ln) in enumerate(msgs,1)}
for n,(off,ln) in enumerate(msgs,1):
    if not refmap[n]:
        b=enc[n]
        if len(b)>ln: raise Exception(f'#{n} has no pointer and translation is too long ({len(b)}>{ln})')
        newprg[off:off+len(b)]=b; reserved.append((off,off+ln)); final[n]=off-0x4000+0x8000
reserved.sort()
ptr=0x5280
def bump(p,size):
    changed=True
    while changed:
        changed=False
        for a_,b_ in reserved:
            if p<b_ and p+size>a_: p=b_; changed=True
    return p
for n,(off,ln) in enumerate(msgs,1):
    if not refmap[n]: continue
    b=enc[n]; ptr=bump(ptr,len(b))
    if ptr+len(b)>TEXT_END: raise Exception('out of text space at #%d'%n)
    newprg[ptr:ptr+len(b)]=b; p=ptr-0x4000+0x8000
    for j in refmap[n]: newprg[j]=p&255; newprg[j+1]=p>>8
    final[n]=p; ptr+=len(b)
print('text end',hex(ptr),'free bytes',TEXT_END-ptr)
# ---------------- engine ----------------
esrc=open(os.path.join(HERE,'engine2.s'),encoding='utf-8').read()
SP_7C=0; SP_7D=0; SP_0701=0
SP_4A=5   # 村莊編號：0 天門 1 冥州 2 永涅 3 玄省 4 呂雲 5 洛黃 6 邪都 7 武龍
SP_06FF=0b00001101          # bits: 0 靈符 1 通天鏡 2 聖劍 3 鈴鐺 4 $89 5 $8A 6-7 $7A
SP_0700=85                  # 古法書 85, bit7=0
# secret password preset: Luohuang village state (name bytes = SPNM -> shown as 林正英)
SPNM=[0xFA,0xFC,0xE9,0xE3]
SPDATA=SPNM+[SP_7C, (SP_4A<<4)|SP_7D, SP_06FF, SP_0700, SP_0701]
esrc=esrc.replace('@SPNM@',','.join(map(str,SPNM))).replace('@SPDATA@',','.join(map(str,SPDATA)))
_vt=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'village_tiles.json'),encoding='utf-8'))['villages']
esrc=esrc.replace('@QLO@',str(gid['？']&255)).replace('@QHI@',str(gid['？']>>8))
esrc=esrc.replace('@NMTAB@',','.join(str(code[c][0]) for c in 'あいうえおかきけこさしすせたてとなにねのはふまもゆよりれん'))
a=Asm(); chunks=a.assemble(esrc,0)
# bank 7 $B3E9-$BA61 held the 23 door-box layouts; they are rebuilt (deduplicated) below
for i in range(7*0x4000+0x33E9,7*0x4000+0x3A61): newprg[i]=0xFF
for org,b in chunks:
    if org>=0xC000:
        o=15*0x4000+org-0xC000; newprg[o:o+len(b)]=b
    elif org<0xB700:                       # bank-7-only code (door boxes)
        o=7*0x4000+org-0x8000; assert all(x==0xFF for x in newprg[o:o+len(b)]); newprg[o:o+len(b)]=b
    else:
        for bank in (1,7):
            o=bank*0x4000+org-0x8000
            assert all(x==0xFF for x in newprg[o:o+len(b)]) or bank==1 and org>=0xBA61, (bank,hex(org),[hex(0x8000+(o+i)%0x4000) for i,x in enumerate(newprg[o:o+len(b)]) if x!=0xFF][:5])
            newprg[o:o+len(b)]=b
assert a.syms['BOX7END']<=0xB700 and a.syms['REGC_END']<=0xFFB0 and a.syms['PORTEND']<=0xFF00
assert a.syms['FIXEDEND']<=0xF38C and a.syms['FETCHEND']<=0xFFB0 and a.syms['BANKEND']<=0xBFB0
# default player name どうし is shown as 林道長
for sym,txt in (('LINSTR',TT('林道長')),('LINSTR2',TT('林正英'))):
    lin=bytes(encode(list(txt),0)); assert len(lin)<=8
    for bank in (1,7):
        o=bank*0x4000+a.syms[sym]-0x8000; newprg[o:o+len(lin)]=lin
def hook(addr,expect,target,nops):
    o=15*0x4000+addr-0xC000; assert newprg[o:o+len(expect)]==expect,(hex(addr),newprg[o:o+len(expect)].hex())
    newprg[o:o+3]=bytes([0x20,target&255,target>>8]); newprg[o+3:o+3+nops]=b'\xea'*nops
hook(0xEEA7,bytes.fromhex('a9008d31068d3206'),a.syms['RESETTXT'],5)
hook(0xF04C,bytes.fromhex('20dcf2'),a.syms['WAITK2'],0)
hook(0xF234,bytes.fromhex('853ba000'),a.syms['NAMECHK'],1)
hook(0xF471,bytes.fromhex('a9338500'),a.syms['HOOK471'],1)
hook(0xF50B,bytes.fromhex('a001b13a'),a.syms['HOOK50B'],1)
# portrait hooks
o=7*0x4000+0xB3CE-0x8000; assert newprg[o:o+3]==bytes.fromhex('4c01f8')
x=a.syms['BOXCLOSE']; newprg[o:o+3]=bytes([0x4C,x&255,x>>8])
for addr in (0xF5DE,0xF5F2):
    o=15*0x4000+addr-0xC000; assert newprg[o:o+3]==bytes.fromhex('4c72ee'),hex(addr)
    x=a.syms['CHOICEEND']; newprg[o:o+3]=bytes([0x4C,x&255,x>>8])
# exit menu: replace the separate "師父！" print with the portrait control string
seq=bytes.fromhex('01 03 cb 96 03 eb 96 03 0c 97 03 f5 96 0b'.replace(' ',''))
k=prg.find(seq,0x4000,0x5280); assert k>0
ps=bytes([0x03])+bytes(encode(list(TT('師父，')),0)); PSTR=ptr; newprg[PSTR:PSTR+len(ps)]=ps; ptr+=len(ps)
assert ptr<=TEXT_END
p=PSTR-0x4000+0x8000; newprg[k+2]=p&255; newprg[k+3]=p>>8
# title cheat hooks
def bhook(bank,addr,expect,target,nops):
    o=bank*0x4000+addr-0x8000; assert newprg[o:o+len(expect)]==expect,(bank,hex(addr))
    newprg[o:o+3]=bytes([0x20,target&255,target>>8]); newprg[o+3:o+3+nops]=b'\xea'*nops
bhook(13,0x879C,bytes.fromhex('206fc1'),a.syms['TITLEPAD'],0)
bhook(13,0xA9EC,bytes.fromhex('85858586'),a.syms['NGHOOK'],1)
bhook(13,0xAAFC,bytes.fromhex('2081ab'),a.syms['NAMEHOOK'],0)
bhook(13,0xBBAC,bytes.fromhex('a901857b'),a.syms['PWHOOK'],1)
bhook(13,0xB034,bytes.fromhex('2052b9'),a.syms['PWDEC'],0)
bhook(0,0xB6C4,bytes.fromhex('38a586e5008586'),a.syms['COSTSUB'],4)
# cheat: zombies guarding items stay until the item is really won
hook(0xD4F6,bytes.fromhex('aab582'),a.syms['ITEMCHK'],0)
hook(0xF3D0,bytes.fromhex('a0009102'),a.syms['STHOOK'],1)
# remember the source of background tiles A1-D0 so the door portrait can give them back
hook(0xEA31,bytes.fromhex('2089c5'),a.syms['LDHOOK'],0)
# cheat: double walking speed in the village only (object types 01 master / 02 disciple; fight rooms use other types)
xs=f"""
.org $BD80
XVEL:
  JSR ADDX
  LDA $3D
  CMP #$04
  BNE xv9
  LDA $3C
  CMP #$20
  BEQ xv1
  CMP #$40
  BEQ xv1
  CMP #$60
  BNE xv9
  LDY #0
  LDA ($3C),Y
  CMP #$03
  BEQ xv2
  RTS
xv1:
  LDY #0
  LDA ($3C),Y
  BEQ xv9
  CMP #$03
  BCS xv9
xv2:
  LDA $2A
  BNE xv9
  JSR ${a.syms['CHEATON']:04X}
  BNE xv9
  JSR ADDX
xv9:
  RTS
ADDX:
  CLC
  LDA $00
  LDY #3
  ADC ($3C),Y
  STA ($3C),Y
  LDA $01
  INY
  ADC ($3C),Y
  STA ($3C),Y
  RTS
; village kid follower: original compares only the low byte of |dx| with $F0, so a gap of 256+ looks small and the kid stops for good
KIDCHK:
  LDA $01
  BEQ kc1
  CMP #$FF
  BEQ kc1
  SEC
  RTS
kc1:
  LDA $00
  CMP #$F0
  RTS
XEND:
"""
ax=Asm(); xc=ax.assemble(xs,0)
for org,bb in xc:
    o=org-0x8000; assert all(v==0xFF for v in newprg[o:o+len(bb)]); newprg[o:o+len(bb)]=bb
o=0xB494-0x8000; assert newprg[o:o+5]==bytes.fromhex('18a500a003')
x=ax.syms['XVEL']; newprg[o:o+3]=bytes([0x4C,x&255,x>>8])
# 秘技時小殭屍（村莊跟隨者，$0460 類型 03）也兩倍速；並修正距離只比低位元組的問題（距離超過 255 會停住不跟）
o=0xADA1-0x8000; assert newprg[o:o+6]==bytes.fromhex('a500c9f09042')
k=ax.syms['KIDCHK']; newprg[o:o+6]=bytes([0x20,k&255,k>>8,0x90,0x43,0xEA])
# 武道館對答：正解改判（腳本 0B 03 選項跳轉，$90AF = 答對）。使用者 2026-11-02 指示
#   #202 正解改為第 1 項「在胸口打木樁」（原版為第 3 項 あぶらで あげる）
#   #209 正解改為第 3 項「中國日報」（原版為第 2 項 かべしんぶん）
#   #201 正解改為第 1 項「棺材」（原版為第 2 項 つぼ）。使用者 2026-11-03 指示
for q,old,new in ((201,(0x88,0xAF,0x82),(0xAF,0x88,0x82)),(202,(0x7C,0x7C,0xAF),(0xAF,0x7C,0x7C)),(209,(0x97,0xAF,0x7C),(0x97,0x7C,0xAF))):
    o=0x4E10-16+(q-200)*0x20+19
    assert newprg[o-2]==0x0B and newprg[o-1]==0x03 and tuple(newprg[o:o+6:2])==old,(q,newprg[o-2:o+6].hex())
    newprg[o:o+6:2]=bytes(new)
# door / idle boxes (bank 7)
o=7*0x4000+0xB302-0x8000; assert newprg[o:o+4]==bytes.fromhex('86008501')
hb=a.syms['HOOKBOX']; newprg[o:o+4]=bytes([0x20,hb&255,hb>>8,0xEA])
boxes={}
if '門口說明' in wb.sheetnames:
    for r in wb['門口說明'].iter_rows(min_row=2,values_only=True):
        if r[0]: boxes[int(r[0])]=TT(r[3] or '')
BOXFONT=pixfont.fallback_font()
boxdata=bytearray(b'\x00'*0x4000)
from PIL import ImageOps
from portrait import portrait_tiles
def find_portrait(name):
    for ext in ('png','jpg','jpeg','bmp','gif'):
        f=os.path.join(PORTRAIT_DIR,name+'.'+ext)
        if PORTRAIT_DIR and os.path.exists(f): return f
    return None
import portrait
_m=find_portrait('master'); _d=find_portrait('disciple')
pm=portrait_tiles(_m,48,64) if _m else portrait.placeholder('道長',48,64)
pd=portrait_tiles(_d,32,32) if _d else portrait.placeholder('文才',32,32)
assert len(pm)==768 and len(pd)==256
print('portraits: master',_m or '(placeholder)',' disciple',_d or '(placeholder)')
boxdata[0x1800:0x1800+768]=pm; boxdata[0x1B00:0x1B00+256]=pd
for v in range(8):   # door portrait: tiles each village never shows (48 per village, $BA00+v*64)
    boxdata[0x3A00+v*64:0x3A00+v*64+48]=bytes(int(t,16) for t in _vt[str(v)]['portrait_tiles'])
layouts=[]
for n in range(1,24):
    lines=(boxes.get(n,'') or '').split('\n')[:2]
    while len(lines)<2: lines.append('')
    lay=bytearray(prg[7*0x4000+0x33E9+(n-1)*72:7*0x4000+0x33E9+n*72]); base=0
    tid=0xE0; blob=bytearray(); blobs=bytearray()
    for li,text in enumerate(lines):
        text=text.strip(); cols=(12*len(text)+7)//8
        assert cols<=10, f'門口說明 #{n} 第{li+1}行太長'
        g=Image.new('1',(max(cols,1)*8,16),0); d=ImageDraw.Draw(g); d.fontmode='1'
        gs=Image.new('1',(max(cols,1)*8,16),0)
        for i,c in enumerate(text):
            pixfont.draw(g,i*12,0,c,cellw=12,fallback=BOXFONT,lang='tc')
            pixfont.draw(gs,i*12,0,SCC(c),cellw=12,fallback=BOXFONT,lang='sc')
        px=g.load(); pxs=gs.load(); top=12*(1+2*li); bot=top+12
        for c in range(10):
            if c<cols:
                for half,row in ((0,top),(1,bot)):
                    p=bytearray(8); q=bytearray(8)
                    for y in range(8):
                        for x in range(8):
                            if px[c*8+x,half*8+y]: p[y]|=0x80>>x
                            if pxs[c*8+x,half*8+y]: q[y]|=0x80>>x
                    blob+=p; blobs+=q; lay[row+1+c]=tid; tid+=1
            else:
                lay[top+1+c]=0x20; lay[bot+1+c]=0x20
    assert tid<=0x100, f'門口說明 #{n} 太長（圖塊超過 32 個）'
    boxdata[(n-1)*256:(n-1)*256+len(blob)]=blob
    boxdata[0x2000+(n-1)*256:0x2000+(n-1)*256+len(blobs)]=blobs   # 簡中
    layouts.append(bytes(lay))
variants=sorted(set(layouts),key=layouts.index); assert len(variants)<=7,len(variants)
B7=7*0x4000-0x8000
for n,l in enumerate(layouts): newprg[B7+0xB3E9+n]=variants.index(l)
for v,l in enumerate(variants):
    adr=0xB400+v*72; newprg[B7+adr:B7+adr+72]=l
    newprg[B7+a.syms['VLO']+v]=adr&255; newprg[B7+a.syms['VHI']+v]=adr>>8
assert 0xB400+len(variants)*72<=0xB600
# call sites (fixed bank): JSR $F7F9 / .dw layout  ->  .dw $B3E9+n
F=15*0x4000-0xC000; cnt=0
for j in range(15*0x4000,16*0x4000-4):
    if newprg[j:j+3]==bytes([0x20,0xF9,0xF7]):
        p=newprg[j+3]|newprg[j+4]<<8; n=(p-0xB3E9)//72; assert (p-0xB3E9)%72==0 and 0<=n<23
        q=0xB3E9+n; newprg[j+3]=q&255; newprg[j+4]=q>>8; cnt+=1
assert cnt==23,cnt
print('door box layouts',len(variants),'variants')

# ---------------- menus ----------------
import menus
lab={}
for r in wb['選單與介面'].iter_rows(min_row=2,values_only=True):
    if r[3] and r[5]: lab[r[3].strip()]=r[5]
labels={'なまえ とうろく':lab.get('なまえ とうろく','登錄名字'),'とうしの こころ':lab.get('とうしの こころ','道士之心'),
 'はやい':lab.get('はやい','快'),'ふつう':lab.get('ふつう','普通'),'おそい':lab.get('おそい','慢'),
 'すすむ':'下一步','もどる':'返回','おわる':'結束','まちかいかあります':lab.get('まちかいかあります','密碼錯誤')}
for k,v in list(labels.items()):
    m=re.search(r'(すすむ|もどる|おわる)=(\S+)',lab.get(next((x for x in lab if 'すすむ' in x),''),'') or '')
for blk in [v for k,v in lab.items() if 'すすむ' in k]:
    for m in re.finditer(r'(すすむ|もどる|おわる)=(\S+)',blk): labels[m.group(1)]=m.group(2)
labels={k:TT(v) for k,v in labels.items()}
labels_sc={k:SCC(v) for k,v in labels.items()}
print('menu labels',labels)
print('menu sets (title end, grid end, code end):',[hex(x) for x in menus.apply(newprg,labels,labels_sc,boxdata,a.syms)])

# ---------------- 512KB SUROM image ----------------
upper=bytearray()
for b in range(16):
    bank=bytearray(newprg[b*0x4000:(b+1)*0x4000])
    if b==2:
        fb=bytearray(boxdata); fb[0x3FB0:]=bank[0x3FB0:]; bank=fb
    elif b in (0,1,3,4):
        fb=bytearray((font if b<2 else font_sc)[(b%3)*0x4000:((b%3)+1)*0x4000])
        fb[0x3FB0:]=bank[0x3FB0:]           # keep reset stub
        bank=fb
    upper+=bank
full=newprg+upper
hdr[4]=32
hdr[10]=0x07   # NES 2.0: 8KB volatile PRG-RAM (engine work area at $6000)
open(OUT,'wb').write(bytes(hdr)+bytes(full))
TEST=globals().get('TESTHOOK')
print('wrote',OUT,len(full))

# ---------------- title credit line ----------------
def add_credit(path,text='TRANSLATED BY MANA'):
    data=bytearray(open(path,'rb').read()); H=16; B13=H+13*0x4000
    def w(addr,expect,new):
        o=B13+addr-0x8000; assert data[o:o+len(expect)]==expect,hex(addr); data[o:o+len(new)]=new
    # move copyright lines up one row: rows 23/25/27 -> 22/24/26
    w(0x86BA,bytes.fromhex('a9e5'),bytes.fromhex('a9c5'))
    w(0x86D0,bytes.fromhex('a925'),bytes.fromhex('a905'))
    w(0x86E6,bytes.fromhex('a965'),bytes.fromhex('a945'))
    enc={' ':0x8C,'.':0x8A}
    for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'): enc[c]=0x91+i
    s=bytes(enc[c] for c in text)+b'\xff'
    col=(32-len(text))//2; ppu=0x2380+col
    src=f'''
.org $BF70
CREDIT:
  JSR $C25E
  LDA #<CSTR
  STA $00
  LDA #>CSTR
  STA $01
  LDA #${ppu&255:02X}
  STA $02
  LDA #${ppu>>8:02X}
  STA $03
  JSR $C44C
  JMP $C25E
CSTR:
  .db {",".join(str(b) for b in s)}
CEND:
'''
    a=Asm(); ch=a.assemble(src,0)
    for org,b in ch:
        o=B13+org-0x8000; assert all(x==0xFF for x in data[o:o+len(b)]); data[o:o+len(b)]=b
    assert a.syms['CEND']<=0xBFB0
    w(0x86F1,bytes.fromhex('4c5ec2'),bytes([0x4C,0x70,0xBF]))
    open(path,'wb').write(data)
add_credit(OUT)
print('credit added')
print('fonts: tc',os.environ.get('NESFONT'),' sc',os.environ.get('NESFONT_SC'),' missing glyphs:', ''.join(sorted(pixfont.missing)) or 'none')
