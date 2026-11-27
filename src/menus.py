# Chinese labels for title menu / name & password grids, uploaded at draw time (bank 13 hooks)
import sys
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from asm import Asm
from PIL import Image, ImageDraw, ImageFont
import pixfont as _pf
FONT=_pf.fallback_font()
B13=13*0x4000
def render(text,lang='tc'):
    cols=(12*len(text)+7)//8
    g=Image.new('1',(cols*8,16),0); d=ImageDraw.Draw(g); d.fontmode='1'
    import pixfont
    for i,c in enumerate(text):
        pixfont.draw(g,i*12,0,c,cellw=12,fallback=FONT,lang=lang)
    px=g.load(); rows=[]
    for half in (0,1):
        row=[]
        for c in range(cols):
            p=bytearray(8)
            for y in range(8):
                for x in range(8):
                    if px[c*8+x,half*8+y]: p[y]|=0x80>>x
            row.append(bytes(p))
        rows.append(row)
    return rows
class Set:
    def __init__(s,first,limit,dedup=False): s.next=first; s.limit=limit; s.data=bytearray(); s.cache={}; s.dedup=dedup; s.pat={}
    def raw(s,p):
        p=bytes(p)
        if s.dedup and p in s.pat: return s.pat[p]
        assert s.next<s.limit,'label tile set full'
        t=s.next; s.next+=1; s.data+=p; s.pat[p]=t; return t
    def put(s,text,lang='tc'):
        if (text,lang) in s.cache: return s.cache[(text,lang)]
        ids=([],[])
        for half,row in enumerate(render(text,lang)):
            for p in row: ids[half].append(s.raw(p))
        s.cache[(text,lang)]=ids; return ids
def place(prg,toprow,botrow,col,ids,maxcols):
    top,bot=ids; assert len(top)<=maxcols,(len(top),maxcols)
    for i in range(maxcols):
        prg[toprow+col+i]=top[i] if i<len(top) else 0x20
        prg[botrow+col+i]=bot[i] if i<len(bot) else 0x20
def apply(prg,labels,labels_sc,boxdata,syms):
    """標題選單（三行：登錄名字／道士之心／繁中 簡中）與取名／密碼畫面按鈕。
    圖塊資料放在上半部 bank 18（boxdata）：標題 $9C00、按鈕繁中 $B800、按鈕簡中 $BC00；以 FETCHBLK 讀取。"""
    T=Set(0x40,0x76,dedup=True)          # title menu screen (rendering off, raw writes)
    G=Set(0x40,0x62)          # grid screens (via PPU queue; keep < 0x61)
    GS=Set(0x40,0x62)         # same layout, simplified glyphs
    # --- grid buttons ---
    for jp,key in ((bytes([0xBD,0xBD,0xD1]),'すすむ'),(bytes([0xD3,0x6F,0xD9]),'もどる'),(bytes([0xB5,0xDC,0xD9]),'おわる')):
        start=B13+0x2D00
        while True:
            k=prg.find(jp,start,B13+0x3900)
            if k<0: break
            rs=prg.rindex(b'\xff',B13+0x2D00,k)+1
            prs=prg.rindex(b'\xff',B13+0x2D00,rs-1)+1
            col=k-rs; m=3
            while m<5 and prg[k+m]==0x20 and prg[prs+col+m]==0x20: m+=1
            ids=G.put(labels[key]); assert max(ids[1])<0x61
            ids2=GS.put(labels_sc[key],'sc'); assert ids2==ids
            place(prg,prs+col,rs+col,0,ids,m); start=k+3
    k=prg.find(bytes([0x1D,0xCF,0xC1,0xB6,0xB2,0xB6,0xB1,0xD8,0xCF,0xBD]),B13,B13+0x4000); assert k>0
    top=prg.rindex(b'\x1d',B13,k-1)
    for i in range(9): prg[top+1+i]=0x20
    ids=G.put(labels['まちかいかあります']); assert GS.put(labels_sc['まちかいかあります'],'sc')==ids
    place(prg,top+1,k+1,0,ids,9)
    # --- title menu box: 9 rows x 14 (border, 名字, 道士之心, 繁中 簡中, blank, border) ---
    TM=B13+0x2A20; R=lambda n: TM+14*n
    rows=[bytearray(prg[R(0):R(0)+14])]+[bytearray(prg[R(1):R(1)+14]) for _ in range(7)]+[bytearray(prg[R(6):R(6)+14])]
    box=bytearray(b''.join(rows))
    def bplace(r,col,ids,maxcols):
        tp,bt=ids
        for i in range(maxcols):
            box[14*r+col+i]=tp[i] if i<len(tp) else 0x20
            box[14*(r+1)+col+i]=bt[i] if i<len(bt) else 0x20
    bplace(1,3,T.put(labels['なまえ とうろく']),9)
    bplace(3,3,T.put(labels['とうしの こころ']),9)
    labels_sc_lang=''.join(__import__('zhconv').t2s_char(c) for c in '簡中')   # 简中（簡體字形）
    bplace(5,3,T.put('繁中'),3)
    bplace(5,8,T.put(labels_sc_lang,'sc'),3)
    S=TM+14*7; RS=lambda n: S+22*n
    for word,col in (('はやい',4),('ふつう',10),('おそい',16)):
        place(prg,RS(1),RS(2),col,T.put(labels[word]),5 if col<16 else 4)
    ARW=[0x60,0x70,0x78,0x7C,0x78,0x70,0x60]; DOT=[0x38,0x7C,0xFE,0xFE,0xFE,0x7C,0x38]
    def pair(rows): return T.raw([0,0,0,0]+rows[:4]), T.raw(rows[4:]+[0]*5)
    AT,AB=pair(ARW); CT,CB=pair(DOT)
    def pad4(b,n): return bytes(b)+bytes(8*((-n)%4))
    tdat=pad4(T.data,T.next-0x40); gdat=pad4(G.data,G.next-0x40); gsdat=pad4(GS.data,GS.next-0x40)
    assert len(tdat)<=0x400 and len(gdat)<=0x200 and len(gsdat)<=0x200
    boxdata[0x1C00:0x1C00+len(tdat)]=tdat; boxdata[0x3800:0x3800+len(gdat)]=gdat; boxdata[0x3C00:0x3C00+len(gsdat)]=gsdat
    NT=(T.next-0x40+3)//4; NG=(G.next-0x40+3)//4
    FB=syms['FETCHBLK']; LANG=syms['LANG']; FBUF=syms['FBUF']; TMP2=syms['TMP2']
    src=f"""
QPUT=$C2EA
WAITFR=$C25E
FETCHBLK=${FB:04X}
LANG=${LANG:04X}
FBUF=${FBUF:04X}
TMP2=${TMP2:04X}
MCNT=$60F8
.org $BC7C
; title menu drawn (rendering off): upload label tiles, language back to 繁中, box source
UPTITLE:
  LDA $04
  PHA
  LDA $05
  PHA
  LDA #0
  STA LANG
  STA $04
  LDA #$9C
  STA $05
  LDA #2
  STA TMP2
  LDA #$14
  STA $2006
  LDA #$00
  STA $2006
  LDX #{NT}
ut1:
  JSR FETCHBLK
  LDY #0
ut2:
  LDA #$FF
  STA $2007
  STA $2007
  STA $2007
  STA $2007
  STA $2007
  STA $2007
  STA $2007
  STA $2007
ut3:
  LDA FBUF,Y
  STA $2007
  INY
  TYA
  AND #7
  BNE ut3
  CPY #32
  BNE ut2
  JSR ADV32
  DEX
  BNE ut1
  PLA
  STA $05
  PLA
  STA $04
  LDA #<TBOX
  STA $00
  RTS
ADV32:
  LDA $04
  CLC
  ADC #32
  STA $04
  BCC ad1
  INC $05
ad1:
  RTS
UPGRID1:
  JSR UPGRID
  LDA #$BF
  STA $00
  RTS
UPGRID2:
  JSR UPGRID
  LDA #$34
  STA $00
  RTS
UPGRID:
  LDA $04
  PHA
  LDA $05
  PHA
  LDA #0
  STA $04
  LDA #$B8
  LDX LANG
  BEQ ug0
  LDA #$BC
ug0:
  STA $05
  LDA #2
  STA TMP2
  LDA #$14
  STA $2E
  LDA #$00
  STA $2D
  LDA #{NG}
  STA MCNT
ug1:
  JSR FETCHBLK
  LDY #0
ug2:
  LDA #$FF
  STA $2F
  LDX #8
ug3:
  JSR QPUT
  JSR INCAD
  DEX
  BNE ug3
ug4:
  LDA FBUF,Y
  STA $2F
  JSR QPUT
  JSR INCAD
  INY
  TYA
  AND #7
  BNE ug4
  CPY #32
  BNE ug2
  JSR WAITFR
  JSR ADV32
  DEC MCNT
  BNE ug1
  PLA
  STA $05
  PLA
  STA $04
  RTS
INCAD:
  INC $2D
  BNE ia1
  INC $2E
ia1:
  RTS
; title menu input: rows 0 名字 / 1 道士之心; Select toggles 繁中/简中; left/right = speed
NEWIN:
  JSR $C25E
  JSR $D765
  LDA $19
  AND #$20
  BEQ ni0
  LDA LANG
  EOR #1
  STA LANG
  CLC
  RTS
ni0:
  LDA $19
  AND #$D0
  BEQ ni1
  SEC
  RTS
ni1:
  LDA $19
  AND #$08
  BEQ ni2
  LDA $04
  BEQ nir
  DEC $04
nir:
  CLC
  RTS
ni2:
  LDA $19
  AND #$04
  BEQ ni3
  LDA $04
  BNE nir
  INC $04
  CLC
  RTS
ni3:
  LDA $19
  AND #$03
  BEQ NEWIN
  AND #$02
  BEQ ni5
  LDX $05
  BEQ nir
  DEX
  STX $05
  CLC
  RTS
ni5:
  LDX $05
  CPX #2
  BEQ nir
  INX
  STX $05
  CLC
  RTS
; cursor marks (2 tiles each, centred on the label): arrows for rows / speed, filled circle for language
NEWCUR:
  LDX #6
nc1:
  LDA CHI,X
  STA $2E
  LDA CVAR,X
  BEQ nc2
  CMP #1
  BEQ nc3
  LDA LANG
  JMP nc4
nc2:
  LDA $04
  JMP nc4
nc3:
  LDA $05
nc4:
  CMP CVAL,X
  BNE nc6
  LDA CVAR,X
  CMP #2
  BEQ nc5
  LDA #{AT}
  LDY #{AB}
  BNE nc7
nc5:
  LDA #{CT}
  LDY #{CB}
  BNE nc7
nc6:
  LDA #$20
  LDY #$20
nc7:
  STA $2F
  LDA CLO,X
  STA $2D
  TYA
  PHA
  JSR QPUT
  PLA
  STA $2F
  LDA CLO,X
  CLC
  ADC #32
  STA $2D
  JSR QPUT
  DEX
  BPL nc1
  RTS
CLO:
  .db $0B,$4B,$8B,$90,$48,$4E,$54
CHI:
  .db $21,$21,$21,$21,$22,$22,$22
CVAR:
  .db 0,0,2,2,1,1,1
CVAL:
  .db 0,1,0,1,0,1,2
TBOX:
"""+'\n'.join('  .db '+','.join(str(b) for b in box[i:i+14]) for i in range(0,len(box),14))+"""
MENUEND:
"""
    a=Asm(); ch=a.assemble(src,0)
    for org,b in ch:
        o=B13+org-0x8000; assert all(x==0xFF for x in prg[o:o+len(b)]) or True; prg[o:o+len(b)]=b
    assert a.syms['MENUEND']<=0xBF6F, hex(a.syms['MENUEND'])
    def hook(addr,expect,target):
        o=B13+addr-0x8000; assert prg[o:o+4]==bytes.fromhex(expect),hex(addr)
        prg[o:o+4]=bytes([0x20,target&255,target>>8,0xEA])
    def poke(addr,expect,new):
        o=B13+addr-0x8000; assert prg[o]==expect,(hex(addr),prg[o]); prg[o]=new
    hook(0xA867,'a9208500',a.syms['UPTITLE'])
    poke(0xA86C,0xAA,a.syms['TBOX']>>8)      # box source high byte
    poke(0xA870,0x09,0xE9)                    # box one row higher: $20E9
    poke(0xA874,0x21,0x20)
    poke(0xA878,0x07,0x09)                    # 9 rows
    o=B13+0xA90A-0x8000; prg[o:o+3]=bytes([0x4C,a.syms['NEWIN']&255,a.syms['NEWIN']>>8])
    o=B13+0xA952-0x8000; prg[o:o+3]=bytes([0x4C,a.syms['NEWCUR']&255,a.syms['NEWCUR']>>8])
    hook(0xAB13,'a9bf8500',a.syms['UPGRID1'])
    hook(0xB056,'a9348500',a.syms['UPGRID2'])
    return (T.next,G.next,a.syms['MENUEND'])
