; ===== Chinese text engine v2 (scrolling, ring tile pool, indoor/outdoor) =====
QPUT   = $C2EA
WAITFR = $C25E
READPAD= $C16F
SCRIPT = $EE72
ROW    = $0632
SPEED  = $06C4
TX     = $6000
LASTT  = $6002
LASTB  = $6003
LASTC  = $6004
MAXR   = $6005
GL     = $6006
GH     = $6007
GW     = $6008
TMP    = $6009
TMP2   = $600A
SAVY   = $600B
CC     = $600C
CT     = $600D
CB     = $600E
SAVY2  = $600F
COLBUF = $6010
LASTBUF= $6020
GBL    = $6030
GBR    = $6040
RHEAD  = $6050
RTAIL  = $6051
RFREE  = $6052
RMIN   = $6053
RMAX   = $6054
SEEN   = $6055
DIRTY  = $6056
TMP3   = $6057
ROWSTART = $6058
MAP    = $6100
FBUF   = $6180
FONTBANK = 0

; ================= fixed bank: print loop =================
.org $F238
PLOOP:
  LDA ($02),Y
  CMP #$24
  BNE p1
  JMP SCRIPT
p1:
  INY
  CMP #$3B
  BNE p2
  JSR NEWLINE
  JMP PLOOP
p2:
  CMP #$40
  BNE p3
  JSR WAITMARK
  JMP PLOOP
p3:
  CMP #$20
  BNE p4
  LDX $03
  CPX #$80
  BCC PLOOP
  LDA #8
  JSR ADVSPACE
  JMP PLOOP
p4:
  CMP #$A0
  BNE p5
  LDA #12
  JSR ADVSPACE
  JMP PLOOP
p5:
  CMP #$07
  BCS p6
  JSR CTRL
  JMP PLOOP
p6:
  LDX $03
  CPX #$05
  BNE p6n
  LDX $02
  CPX #$80
  BNE p6n
  JSR NAMEMAP
  JMP glyph
p6n:
  CMP #$80
  BCC single
  CMP #$A0
  BCS single
  SEC
  SBC #$7F
  TAX
  LDA ($02),Y
  INY
  JMP glyph
single:
  LDX #0
glyph:
  JSR PUTGLYPH
  JMP PLOOP

; copy 32 bytes from upper-half bank TMP2, address ($04) -> MAP ($0700)
FETCHBLK:
  LDA $13
  AND #$7F
  STA $2000
  LDA #$10
  JSR SETCHR
  LDA TMP2
  JSR SETPRG
  LDY #31
fb1:
  LDA ($04),Y
  STA FBUF,Y
  DEY
  BPL fb1
  LDA $35
  JSR SETPRG
  LDA #0
  JSR SETCHR
  LDA $13
  STA $2000
  RTS
; ---------- title cheat: Up Up Down Down Left Right Left Right ----------
CHEAT_A = $60F0
CHEAT_B = $60F1
SEQI    = $60F2
REAL    = $60F3
TITLEPAD:
  JSR $C16F
  LDA $19
  AND #$0F
  BEQ tp_done
  LDX SEQI
  CPX #8
  BCC tp1
  LDX #0
tp1:
  CMP SEQTAB,X
  BEQ tp_ok
  LDX #0
  CMP SEQTAB
  BNE tp_store
  INX
  BNE tp_store
tp_ok:
  INX
  CPX #8
  BNE tp_store
  LDA #$A5
  STA CHEAT_A
  LDA #$5A
  STA CHEAT_B
  LDA #$1B
  JSR $EDF5
  LDX #0
tp_store:
  STX SEQI
tp_done:
  RTS
SEQTAB:
  .db $08,$08,$04,$04,$02,$01,$02,$01
CHEATON:
  LDA CHEAT_A
  CMP #$A5
  BNE co1
  LDA CHEAT_B
  CMP #$5A
co1:
  RTS
APPLYCHEAT:
; remember which items the player really has (new game: none; password: its items)
  LDX #3
ac0:
  LDA $82,X
  STA REAL,X
  DEX
  BPL ac0
  JSR CHEATON
  BNE ac1
  LDA #1
  STA $82
  STA $83
  STA $84
  STA $85
  LDA #99
  STA $86
ac1:
  RTS
NGHOOK:
  STA $85
  STA $86
  JMP APPLYCHEAT
NAMEHOOK:
  JSR $AB81
  JMP APPLYCHEAT
PWHOOK:
  LDA #1
  STA $7B
  JMP APPLYCHEAT
COSTSUB:
  JSR CHEATON
  BEQ cs1
  SEC
  LDA $86
  SBC $00
  STA $86
cs1:
  RTS
; zombie-defeated check (D4F6): with the cheat, only items really won count
ITEMCHK:
  TAX
  JSR CHEATON
  BEQ ic1
  LDA $82,X
  RTS
ic1:
  LDA REAL,X
  RTS
; script opcode 05 store (F3D0): keep REAL in step with item gains / losses
STHOOK:
  LDY #0
  STA ($02),Y
  LDX $03
  BNE sh9
  LDX $02
  CPX #$82
  BCC sh9
  CPX #$86
  BCS sh9
  STA REAL-$82,X
sh9:
  RTS
FIXEDEND:

; ================= fixed bank: glyph fetch =================
.org $FF06
FETCH:
  LDA $00
  PHA
  LDA $01
  PHA
  LDA GL
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  STA $00
  LDA GL
  LSR A
  LSR A
  LSR A
  STA TMP
  LDA GH
  AND #1
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  ORA #$80
  CLC
  ADC TMP
  STA $01
  LDA GH
  LSR A
  CLC
  ADC #FONTBANK
  STA TMP2
  LDA $13
  AND #$7F
  STA $2000
  LDA #$10
  JSR SETCHR
  LDA TMP2
  JSR SETPRG
  LDY #31
f1:
  LDA ($00),Y
  STA GBL,Y
  DEY
  BPL f1
  LDA $35
  JSR SETPRG
  LDA #0
  JSR SETCHR
  LDA $13
  STA $2000
  PLA
  STA $01
  PLA
  STA $00
  RTS
SETCHR:
  STA $A000
  LSR A
  STA $A000
  LSR A
  STA $A000
  LSR A
  STA $A000
  LSR A
  STA $A000
  RTS
SETPRG:
  STA $E000
  LSR A
  STA $E000
  LSR A
  STA $E000
  LSR A
  STA $E000
  LSR A
  STA $E000
  RTS
FETCHEND:

; ================= banked code (identical copy in banks 1 and 7) =================
.org $B700
MUL14:
  .db 0,14,28,42,56,70,84,98
ADVSPACE:
  CLC
  ADC TX
  STA TX
  CMP #113
  BCC as1
  JSR NEWLINE
as1:
  RTS

NEWLINE:
  LDA #0
  STA TX
  LDA #$FF
  STA LASTC
  LDA ROW
  CMP #7
  BCS nl1
  INC ROW
  LDX ROW
  CPX #7
  BCS nl1
  LDA RTAIL
  STA ROWSTART,X
nl1:
  RTS

; script opcode 02 wait: skipped once right after a portrait menu choice
WAITK2:
  LDA SKIPW
  BEQ WAITKEY
  LDA #0
  STA SKIPW
  RTS
WAITKEY:
  JSR WAITFR
  JSR READPAD
  LDA $1A
  AND #$C0
  BEQ WAITKEY
  LDX ROW
  LDA TX
  BEQ wk1
  INX
wk1:
  STX SEEN
  RTS

HOOK471:
  LDA #7
  STA SEEN
  LDA #9
  STA TMP
  LDA ROW
  ASL A
  CLC
  ADC #8
  JSR NTADDR
  LDA #6
  STA $2F
  JSR QPUT
  LDA #$33
  STA $00
  RTS
HOOK50B:
  LDA #7
  STA SEEN
  LDY #1
  LDA ($3A),Y
  RTS

CTRL:
  CMP #$03
  BNE ctr0
  JMP SHOWIN
ctr0:
  CMP #$06
  BEQ PUTCURSOR
  CMP #$01
  BNE ctr1
  JMP PAGEBREAK
ctr1:
  RTS

; A = tile, X = column, row = min(ROW,6)
PUTFIXED:
  STA $2F
  TXA
  CLC
  ADC #9
  STA TMP
  LDA ROW
  CMP #7
  BCC pf1
  LDA #6
pf1:
  ASL A
  CLC
  ADC #10
  JSR NTADDR
  JMP QPUT

NTADDR:
  PHA
  LSR A
  LSR A
  LSR A
  CLC
  ADC #$20
  STA $2E
  PLA
  AND #7
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  CLC
  ADC TMP
  STA $2D
  RTS

ENSUREROW:
  LDA ROW
  CMP #7
  BCC er1
  JSR SCROLL
er1:
  RTS

PUTCURSOR:
  JSR ENSUREROW
  LDA TX
  CLC
  ADC #7
  LSR A
  LSR A
  LSR A
  TAX
  STX TMP2
  LDA #6
  JSR PUTFIXED
  LDA TMP2
  ASL A
  ASL A
  ASL A
  CLC
  ADC #8
  STA TX
  LDA #$FF
  STA LASTC
  RTS

WAITMARK:
  LDA TX
  CLC
  ADC #7
  LSR A
  LSR A
  LSR A
  CMP #14
  BCC wm1
  LDA #13
wm1:
  TAX
  LDA #9
  JSR PUTFIXED
  JMP WAITKEY

PAGEBREAK:
  STY SAVY2
  LDX #13
  LDA #9
  JSR PUTFIXED
  JSR WAITKEY
  JSR CLEARWIN
  JSR RESETVARS
  LDY SAVY2
  RTS

RESETTXT:
  LDA #0
  STA $0631
  LDA DIRTY
  BEQ RESETVARS
  STY SAVY2
  JSR CLEARWIN
  LDY SAVY2
RESETVARS:
  LDA #0
  STA FRESH
  STA ROW
  STA TX
  STA SEEN
  STA MAXR
  STA DIRTY
  LDA #$FF
  STA LASTC
  LDA $2A
  BEQ rv_out
  LDA #$41
  LDX #$7F
  BNE rv_set
rv_out:
  LDA #$A1
  LDX #$DF
rv_set:
  STA RMIN
  STA RHEAD
  STA RTAIL
  STA ROWSTART
  STX RMAX
  TXA
  SEC
  SBC RMIN
  STA RFREE
  LDA #0
  LDX #97
rv1:
  STA MAP,X
  DEX
  BPL rv1
  RTS

CLEARWIN:
  LDA MAXR
  CMP #7
  BCC cw0
  LDA #6
  STA MAXR
cw0:
  LDX #0
cw1:
  TXA
  PHA
  ASL A
  CLC
  ADC #9
  JSR CLEARROW
  PLA
  PHA
  ASL A
  CLC
  ADC #10
  JSR CLEARROW
  JSR WAITFR
  PLA
  TAX
  INX
  CPX MAXR
  BCC cw1
  BEQ cw1
  RTS
CLEARROW:
  LDX #9
  STX TMP
  JSR NTADDR
  LDA #$20
  STA $2F
  LDX #14
cr1:
  JSR QPUT
  INC $2D
  DEX
  BNE cr1
  RTS

; scroll window up one line (drops row 0)
SCROLL:
  LDA ROW
  BNE sc0
  RTS
sc0:
  STY SAVY2
  LDA SEEN
  BNE sc1
  LDX #13
  LDA #9
  JSR PUTFIXED
  JSR WAITKEY
sc1:
  LDA ROWSTART+1
  SEC
  SBC ROWSTART
  BCS sc2
  STA TMP
  LDA RMAX
  SEC
  SBC RMIN
  CLC
  ADC TMP
sc2:
  CLC
  ADC RFREE
  STA RFREE
  LDA ROWSTART+1
  STA RHEAD
  LDX #0
sc3:
  LDA ROWSTART+1,X
  STA ROWSTART,X
  INX
  CPX #6
  BNE sc3
  LDA RTAIL
  STA ROWSTART+6
  LDX #0
sc4:
  LDA MAP+14,X
  STA MAP,X
  INX
  CPX #84
  BNE sc4
  LDA #0
sc5:
  STA MAP,X
  INX
  CPX #98
  BNE sc5
  DEC ROW
  LDA SEEN
  BEQ sc6
  DEC SEEN
sc6:
  LDA #0
sc7:
  PHA
  JSR DRAWROW
  JSR WAITFR
  PLA
  CLC
  ADC #1
  CMP #7
  BNE sc7
  LDA #6
  STA MAXR
  LDY SAVY2
  RTS

DRAWROW:
  STA TMP3
  ASL A
  CLC
  ADC #9
  LDX #9
  STX TMP
  JSR NTADDR
  LDX TMP3
  LDA MUL14,X
  TAX
  LDA #14
  STA TMP2
dr1:
  LDA MAP,X
  BNE dr2
  LDA #$20
dr2:
  STA $2F
  JSR QPUT
  INC $2D
  INX
  DEC TMP2
  BNE dr1
  LDA TMP3
  ASL A
  CLC
  ADC #10
  LDX #9
  STX TMP
  JSR NTADDR
  LDX TMP3
  LDA MUL14,X
  TAX
  LDA #14
  STA TMP2
dr3:
  LDA MAP,X
  BEQ dr4
  CLC
  ADC #1
  BNE dr5
dr4:
  LDA #$20
dr5:
  STA $2F
  JSR QPUT
  INC $2D
  INX
  DEC TMP2
  BNE dr3
  RTS

ALLOC:
  LDA RTAIL
  STA CT
  CLC
  ADC #1
  STA CB
  ADC #1
  CMP RMAX
  BCC al0
  LDA RMIN
al0:
  STA RTAIL
  LDA RFREE
  SEC
  SBC #2
  STA RFREE
  LDX ROW
  LDA MUL14,X
  CLC
  ADC CC
  TAX
  LDA CT
  STA MAP,X
  LDA CC
  CLC
  ADC #9
  STA TMP
  LDA ROW
  ASL A
  CLC
  ADC #9
  PHA
  JSR NTADDR
  LDA CT
  STA $2F
  JSR QPUT
  PLA
  CLC
  ADC #1
  JSR NTADDR
  LDA CB
  STA $2F
  JSR QPUT
  LDA ROW
  CMP MAXR
  BCC al1
  STA MAXR
al1:
  LDA #1
  STA DIRTY
  RTS

UPLOAD:
  LDA CT
  LDX #0
  JSR UPTILE
  LDA CB
  LDX #8
UPTILE:
  STA TMP3
  STX TSAVX
  LSR A
  LSR A
  LSR A
  LSR A
  CLC
  ADC #$10
  STA $2E
  LDA TMP3
  ASL A
  ASL A
  ASL A
  ASL A
  STA $2D
; tiles a portrait borrowed still hold its plane 0: rewrite it once (FF)
  LDA TMP3
  SEC
  SBC #$40
  CMP #$40
  BCC ut_a
  SBC #$20
ut_a:
  PHA
  AND #7
  TAX
  LDA BITTAB,X
  STA TBIT
  PLA
  LSR A
  LSR A
  LSR A
  TAX
  LDA TMAP,X
  AND TBIT
  BEQ ut_n
  EOR TMAP,X
  STA TMAP,X
  LDA #$FF
  STA $2F
  LDX #8
ut_f:
  JSR QPUT
  INC $2D
  DEX
  BNE ut_f
  BEQ ut_p
ut_n:
  LDA $2D
  ORA #8
  STA $2D
ut_p:
  LDX TSAVX
  LDA #8
  STA TMP
ut1:
  LDA COLBUF,X
  STA $2F
  JSR QPUT
  INC $2D
  INX
  DEC TMP
  BNE ut1
  RTS

PUTGLYPH:
  STA GL
  STX GH
  STY SAVY
; 簡中: same codes, simplified glyphs stored 0x600 ids later (font banks +3)
  LDA LANG
  BEQ pgl
  LDA GH
  CLC
  ADC #6
  STA GH
pgl:
  LDA $2A
  BEQ pm0
  LDA #$41
  BNE pm1
pm0:
  LDA #$A1
pm1:
  CMP RMIN
  BEQ pm2
  JSR RESETVARS
pm2:
  LDA #0
  STA SKIPW
  LDA #12
  STA GW
  CPX #0
  BNE w12
  LDA GL
  CMP #$30
  BCC w12
  CMP #$3A
  BCS w12
  LDA #8
  STA GW
w12:
  LDA TX
  CLC
  ADC GW
  CMP #113
  BCC pg1
  JSR NEWLINE
pg1:
  JSR ENSUREROW
pg3:
  LDX #4
  LDA TX
  AND #7
  BEQ pgn
  LDA TX
  LSR A
  LSR A
  LSR A
  CMP LASTC
  BNE pgn
  LDX #2
pgn:
  STX TMP3
  LDA RFREE
  CMP TMP3
  BCS pg4
  LDA ROW
  BEQ pg4
  JSR SCROLL
  JMP pg3
pg4:
  LDA ROW
  CMP SEEN
  BCS pg5
  STA SEEN
pg5:
  JSR FETCH
  LDA TX
  LSR A
  LSR A
  LSR A
  STA CC
  LDA TX
  AND #7
  BNE shift4
  JSR ALLOC
  LDX #15
a1:
  LDA GBL,X
  STA COLBUF,X
  DEX
  BPL a1
  JSR UPLOAD
  LDA GW
  CMP #9
  BCC g_end
  INC CC
  JSR ALLOC
  LDX #15
a2:
  LDA GBR,X
  STA COLBUF,X
  DEX
  BPL a2
  JSR UPLOAD
  JMP g_end
shift4:
  LDA CC
  CMP LASTC
  BEQ s_have
  JSR ALLOC
  LDX #15
  LDA #0
s0:
  STA LASTBUF,X
  DEX
  BPL s0
  JMP s_merge
s_have:
  LDA LASTT
  STA CT
  LDA LASTB
  STA CB
s_merge:
  LDX #15
s1:
  LDA GBL,X
  LSR A
  LSR A
  LSR A
  LSR A
  ORA LASTBUF,X
  STA COLBUF,X
  DEX
  BPL s1
  JSR UPLOAD
  INC CC
  JSR ALLOC
  LDX #15
s2:
  LDA GBL,X
  ASL A
  ASL A
  ASL A
  ASL A
  STA TMP
  LDA GBR,X
  LSR A
  LSR A
  LSR A
  LSR A
  ORA TMP
  STA COLBUF,X
  DEX
  BPL s2
  JSR UPLOAD
g_end:
  LDA CC
  STA LASTC
  LDA CT
  STA LASTT
  LDA CB
  STA LASTB
  LDX #15
g1:
  LDA COLBUF,X
  STA LASTBUF,X
  DEX
  BPL g1
  LDA TX
  CLC
  ADC GW
  STA TX
  LDX SPEED
d1:
  JSR WAITFR
  DEX
  BNE d1
  LDY SAVY
  RTS
; ---------- default name: どうし -> 林道長 ----------
NAMECHK:
  STA $3B
; first text after a menu choice starts in a clean window
  LDA FRESH
  BEQ nc0
  JSR RESETTXT
nc0:
  LDA $03
  CMP #$05
  BNE nc9
  LDA $02
  CMP #$80
  BNE nc9
  LDY #3
nc1:
  LDA $0580,Y
  CMP DEFNM,Y
  BNE nc5
  DEY
  BPL nc1
  LDA #<LINSTR
  STA $02
  LDA #>LINSTR
  STA $03
  BNE nc9
nc5:
  LDY #3
nc6:
  LDA $0580,Y
  CMP SPNM,Y
  BNE nc9
  DEY
  BPL nc6
  LDA #<LINSTR2
  STA $02
  LDA #>LINSTR2
  STA $03
nc9:
  LDY #0
  RTS
DEFNM:
  .db $6F,$B3,$BC,$20
LINSTR:
  .db $24,$24,$24,$24,$24,$24,$24,$24
SPNM:
  .db @SPNM@
LINSTR2:
  .db $24,$24,$24,$24,$24,$24,$24,$24
; player name byte -> glyph (A=lo, X=hi): kana kept, the second kana set
; ($E0-$FC, can come from passwords) mapped to normal kana, anything else shown as ？
NAMEMAP:
  LDX #0
  CMP #$61
  BCC nmq
  CMP #$7A
  BCC nm9
  CMP #$A6
  BCC nmq
  CMP #$E0
  BCC nm9
  CMP #$FD
  BCS nmq
  SBC #$DF
  TAX
  LDA NMTAB,X
  LDX #0
nm9:
  RTS
nmq:
  LDA #@QLO@
  LDX #@QHI@
  RTS
NMTAB:
  .db @NMTAB@
BITTAB:
  .db 1,2,4,8,16,32,64,128

; ================= portraits (banked part) =================
; set geometry: A=cols X=rows Y=tilecount
SETGEO:
  STA PW
  STX PH
  STY PCNT
  LDA #0
  STA $04
  RTS

; upload PCNT tiles from bank FONTBANK+2 at ($04) to tiles PT0..
UPTILES:
; upload PCNT tiles from bank FONTBANK+2 at ($04) to the tile numbers listed in PLIST
  LDA #FONTBANK+2
  STA TMP2
  LDA #0
  STA PTILE
ul1:
  JSR FETCHBLK
  LDY #0
ul2:
  LDX PTILE
  LDA PLIST,X
  PHA
  LSR A
  LSR A
  LSR A
  LSR A
  CLC
  ADC #$10
  STA $2E
  PLA
  ASL A
  ASL A
  ASL A
  ASL A
  STA $2D
  LDX #16
ul3:
  LDA FBUF,Y
  STA $2F
  JSR QPUT
  INC $2D
  INY
  DEX
  BNE ul3
  INC PTILE
  CPY #32
  BNE ul2
  LDA $04
  CLC
  ADC #32
  STA $04
  BCC ul4
  INC $05
ul4:
  JSR WAITFR
  LDA PTILE
  CMP PCNT
  BCC ul1
  RTS

; PLIST[k] = PT0 + k (consecutive tiles)
FILLSEQ:
  LDX #0
  LDA PT0
fs1:
  STA PLIST,X
  CLC
  ADC #1
  INX
  CPX PCNT
  BCC fs1
  RTS

; nametable address of row A, column PCC -> $2E/$2D
PNTADR:
  STA PTMP
  LSR A
  LSR A
  LSR A
  STA $2E
  LDA PCC
  AND #$20
  LSR A
  LSR A
  LSR A
  ORA $2E
  ORA #$20
  STA $2E
  LDA PTMP
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  STA $2D
  LDA PCC
  AND #$1F
  ORA $2D
  STA $2D
  RTS

PORTDRAW:
  JSR UPTILES
  LDA PR0
  STA PR
pd1:
  LDA PC0
  STA PCC
  LDA PW
  LSR A
  STA PCNTC
pd2:
  LDA PR
  JSR PNTADR
  LDA $2D
  STA $02
  LDA $2E
  STA $03
  JSR $E093
  LDA #$FC
  CPY #0
  BEQ pd4
pd3:
  SEC
  ROL A
  DEY
  BNE pd3
pd4:
  AND ($3A),Y
  STA ($3A),Y
  STA $2F
  JSR QPUT
  INC PCC
  INC PCC
  DEC PCNTC
  BNE pd2
  INC PR
  INC PR
  LDA PR
  SEC
  SBC PR0
  CMP PH
  BCC pd1
  JSR WAITFR
  LDA #0
  STA PTILE
  LDA PR0
  STA PR
pd5:
  LDA PC0
  STA PCC
  LDA PW
  STA PCNTC
pd6:
  LDA PR
  JSR PNTADR
  LDX PTILE
  LDA PLIST,X
  STA $2F
  JSR QPUT
  INC PTILE
  INC PCC
  DEC PCNTC
  BNE pd6
  INC PR
  LDA PR
  SEC
  SBC PR0
  CMP PH
  BCC pd5
  JMP WAITFR

; indoor "leave the room" menu: disciple portrait 32x32 left of the window
SHOWIN:
  STY PSVY
  LDA PORTON
  BNE si1
  JSR SAVEZP
  LDA #4
  STA PC0
  LDA #8
  STA PR0
  LDA #4
  LDX #4
  LDY #16
  JSR SETGEO
  LDA RMAX
  SEC
  SBC #16
  STA PT0
  STA RMAX
  LDA RFREE
  SEC
  SBC #16
  STA RFREE
  JSR FILLSEQ
  LDA #$9B
  STA $05
  JSR PORTDRAW
  LDA #2
  STA PORTON
  JSR RESTZP
si1:
  LDY PSVY
  RTS
PFILLDOOR:
; tiles this village never shows: 48-byte list per village in bank 18 at $BA00 + v*64
  LDA $4A
  AND #7
  PHA
  LSR A
  LSR A
  CLC
  ADC #$BA
  STA $05
  PLA
  AND #3
  LSR A
  ROR A
  ROR A
  STA $04
  LDA #FONTBANK+2
  STA TMP2
  JSR FETCHBLK
  LDY #31
pdl1:
  LDA FBUF,Y
  STA PLIST,Y
  DEY
  BPL pdl1
  LDA $04
  CLC
  ADC #32
  STA $04
  JSR FETCHBLK
  LDY #15
pdl2:
  LDA FBUF,Y
  STA PLIST+32,Y
  DEY
  BPL pdl2
  LDA #0
  STA $04
  RTS
; door-box glyph page: $80+n (繁中) or $A0+n (簡中) in bank 18
BOXHI:
  LDA BOXN
  CLC
  ADC #$80
  LDX LANG
  BEQ bh1
  ADC #$20
bh1:
  RTS
BANKEND:

; ================= bank 7 only: door / idle message boxes =================
.org $B600
; X/A = $B3E9+n (call-site pointer); byte there = layout variant
HOOKBOX:
  STX $00
  STA $01
  LDA $04
  PHA
  LDA $05
  PHA
  TXA
  SEC
  SBC #$E9
  STA BOXN
  LDY #0
  LDA ($00),Y
  TAY
  LDA VLO,Y
  STA $00
  LDA VHI,Y
  STA $01
  JSR BOXHI
  STA $05
  LDA #0
  STA $04
  LDA #FONTBANK+2
  STA TMP2
  LDX #$E0
hb3:
  JSR FETCHBLK
  LDY #0
hb4:
  TXA
  LSR A
  LSR A
  LSR A
  LSR A
  CLC
  ADC #$10
  STA $2E
  TXA
  ASL A
  ASL A
  ASL A
  ASL A
  STA $2D
  LDA #$FF
  STA $2F
  LDA #8
  STA TMP
hb5:
  JSR QPUT
  INC $2D
  DEC TMP
  BNE hb5
  LDA #8
  STA TMP
hb6:
  LDA FBUF,Y
  STA $2F
  JSR QPUT
  INC $2D
  INY
  DEC TMP
  BNE hb6
  INX
  CPY #32
  BNE hb4
  JSR WAITFR
  LDA $04
  CLC
  ADC #32
  STA $04
  CPX #0
  BNE hb3
  LDA BOXN
  CMP #8
  BCS hb7
  JSR SHOWDOOR
hb7:
  PLA
  STA $05
  PLA
  STA $04
  LDA $01
  RTS
SHOWDOOR:
  JSR SAVEZP
  LDA $4F
  STA PTMP
  LDA $50
  LSR A
  ROR PTMP
  LSR A
  ROR PTMP
  LSR A
  ROR PTMP
  LDA PTMP
  CLC
  ADC #4
  AND #$FE
  STA PC0
  LDA #6
  STA PR0
  LDA #6
  LDX #8
  LDY #48
  JSR SETGEO
  JSR PFILLDOOR
  LDA #$98
  STA $05
  JSR PORTDRAW
  LDA #1
  STA PORTON
  JMP RESTZP
VLO:
  .db 0,0,0,0,0,0,0,0
VHI:
  .db 0,0,0,0,0,0,0,0
BOX7END:

; ================= portrait variables =================
PORTON = $6070
PC0    = $6071
PR0    = $6072
PW     = $6073
PH     = $6074
PT0    = $6075
PCNT   = $6076
PTMP   = $6078
PSV    = $6090
PSVY   = $6081
PR     = $6082
PCC    = $6083
PTILE  = $6084
BOXN   = $6085
PCNTC  = $6086
SKIPW  = $6087
TBIT   = $6088
TSAVX  = $6089
TMAP   = $60A0
PLIST  = $6200
LANG   = $60F7
FRESH  = $608A
CSRC   = $608B
CBANK  = $608D
CVALID = $608E
LTMP   = $60E0


.org $FF95
ZPL:
  .db $00,$01,$02,$03,$3A,$3B,$5E,$04,$05,$35
SAVEZP:
  LDY #9
sz1:
  LDX ZPL,Y
  LDA $00,X
  STA PSV,Y
  DEY
  BPL sz1
  RTS
REGC_END:

.org $FD23
RESTZP:
  LDY #8
rz1:
  LDX ZPL,Y
  LDA PSV,Y
  STA $00,X
  DEY
  BPL rz1
  LDA PSV+9
  JMP $C9D1

PRESTORE:
  LDA #0
  STA PCNTC
  LDA PC0
  STA PCC
  LDA PW
  STA PTMP
pr1:
  LDA PCC
  JSR COLW
  INC PCC
  DEC PTMP
  BNE pr1
  JMP WAITFR

; redraw one background column A (full height); wait a frame every 2nd call
COLW:
  STA $5E
  JSR $DF82
  JSR $DF9D
  JSR $E023
  LDA PCNTC
  EOR #1
  STA PCNTC
  BNE cw9
  JSR WAITFR
cw9:
  RTS

; door box close: box and portrait columns restored together
BOXCLOSE:
  LDA PORTON
  BNE bc1
  JMP $F801
bc1:
  LDX #$B4
bc2:
  JSR WAITFR
  DEX
  BEQ bc3
  JSR READPAD
  LDA $19
  BEQ bc2
bc3:
  LDA #0
  STA PCNTC
  LDA $5E
  STA $46
  SEC
  SBC #6
  STA PCC
  LDA $46
  CLC
  ADC #11
  STA $47
bc4:
  LDA PCC
  JSR COLW
  INC PCC
  LDA $46
  JSR COLW
  LDA $47
  JSR COLW
  INC $46
  DEC $47
  LDA $46
  CMP $47
  BCC bc4
  JSR CRESTORE
  JMP PTAINT

; put the area's own background tiles A1-D0 back (the door portrait borrowed them)
CRESTORE:
  LDA CVALID
  BEQ cr9
  LDA $35
  PHA
  LDA CBANK
  JSR $C9D1
  LDA CSRC
  STA $00
  LDA CSRC+1
  STA $01
  LDA #$10
  STA $2D
  LDA #$1A
  STA $2E
  LDX #24
crl:
  LDY #0
cr1:
  LDA ($00),Y
  STA $2F
  JSR QPUT
  INC $2D
  BNE cr2
  INC $2E
cr2:
  INY
  CPY #32
  BNE cr1
  LDA $00
  CLC
  ADC #32
  STA $00
  BCC cr3
  INC $01
cr3:
  JSR WAITFR
  DEX
  BNE crl
  PLA
  JMP $C9D1
cr9:
  RTS

; CHR block loader entry (call at $EA31): remember where tiles A1-D0 came from
LDHOOK:
  PHA
  LDA $06
  BNE lh8
  SEC
  LDA #$10
  SBC $02
  STA LTMP
  LDA #$1A
  SBC $03
  STA LTMP+1
  BCC lh8
  LDA LTMP+1
  CLC
  ADC #$03
  CMP $05
  BCC lh_ok
  BNE lh8
  LDA LTMP
  CMP $04
  BEQ lh_ok
  BCS lh8
lh_ok:
  CLC
  LDA $00
  ADC LTMP
  STA CSRC
  LDA $01
  ADC LTMP+1
  STA CSRC+1
  LDA $35
  STA CBANK
  LDA #1
  STA CVALID
  BNE lh9
lh8:
  LDA $03
  CMP #$1A
  BCC lh9
  CMP #$1D
  BCS lh9
  LDA #0
  STA CVALID
lh9:
  PLA
  JMP $C589

CHOICEEND:
  LDA #1
  STA FRESH
  LDA PORTON
  CMP #2
  BNE ce1
  JSR PORTOFF
  LDA #1
  STA SKIPW
ce1:
  JMP $EE72

PORTOFF:
  LDA PORTON
  BEQ po2
  JSR SAVEZP
  JSR PRESTORE
  JSR RESTZP
  JMP PTAINT
po2:
  RTS

; portrait gone: mark its tiles for a plane-0 rewrite, give tiles back to the ring
PTAINT:
  LDA #$FF
  LDX PORTON
  CPX #2
  BEQ pt_in
  LDX #7
pt_o:
  STA TMAP+8,X
  DEX
  BPL pt_o
  BMI pt_z
pt_in:
  STA TMAP+5
  STA TMAP+6
  STA TMAP+7
  LDA RMAX
  CMP #$6F
  BNE pt_z
  LDA #$7F
  STA RMAX
  LDA RFREE
  CLC
  ADC #16
  STA RFREE
pt_z:
  LDA #0
  STA PORTON
  RTS
; 道士之心 secret: "どうしのこころどうしのこころへ" -> preset save data (Luohuang village)
PWDEC:
  LDX #14
pw1:
  LDA $06DB,X
  CMP SPPW,X
  BNE pw9
  DEX
  BPL pw1
  LDX #8
pw2:
  LDA SPDATA,X
  STA $06F9,X
  DEX
  BPL pw2
  CLC
  RTS
pw9:
  JMP $B952
SPPW:
  .db $6F,$B3,$BC,$C9,$BA,$BA,$DB,$6F,$B3,$BC,$C9,$BA,$BA,$DB,$CD
SPDATA:
  .db @SPDATA@
PORTEND:
