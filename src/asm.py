# tiny 2-pass 6502 assembler for patching
import re, sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from dis6502 import OPS, LEN
REV={}
for c,(m,mo) in OPS.items(): REV[(m,mo)]=c
BR={'BPL','BMI','BVC','BVS','BCC','BCS','BNE','BEQ'}
class Asm:
    def __init__(s,syms=None): s.syms=dict(syms or {}); s.out=[]
    def ev(s,e,final):
        e=e.strip()
        if e.startswith('<'): return s.ev(e[1:],final)&0xFF
        if e.startswith('>'): return (s.ev(e[1:],final)>>8)&0xFF
        toks=re.findall(r"\$[0-9A-Fa-f]+|%[01]+|\d+|[A-Za-z_.][\w.]*|[-+*()&|]|<<|>>",e)
        py=''
        for t in toks:
            if t.startswith('$'): py+=str(int(t[1:],16))
            elif t.startswith('%'): py+=str(int(t[1:],2))
            elif t[0].isdigit(): py+=t
            elif re.match(r'[A-Za-z_.]',t):
                if t in s.syms: py+=str(s.syms[t])
                elif final: raise Exception('undefined '+t)
                else: py+='0x1234'
            else: py+=t
        return int(eval(py))
    def parse_operand(s,m,op,final,pc):
        op=op.strip()
        if m in BR: return 'rel',s.ev(op,final)
        if op=='' : return 'imp',None
        if op.upper()=='A': return 'acc',None
        if op.startswith('#'): return 'imm',s.ev(op[1:],final)
        mm=re.match(r'\((.*),\s*[Xx]\)$',op)
        if mm: return 'izx',s.ev(mm.group(1),final)
        mm=re.match(r'\((.*)\)\s*,\s*[Yy]$',op)
        if mm: return 'izy',s.ev(mm.group(1),final)
        mm=re.match(r'\((.*)\)$',op)
        if mm: return 'ind',s.ev(mm.group(1),final)
        mm=re.match(r'(.*),\s*([XxYy])$',op)
        if mm:
            v=s.ev(mm.group(1),final); r=mm.group(2).upper()
            zp=('zpx' if r=='X' else 'zpy'); ab=('abx' if r=='X' else 'aby')
            if self_known(s,mm.group(1)) and v<256 and (m,zp) in REV: return zp,v
            return ab,v
        v=s.ev(op,final)
        if self_known(s,op) and v<256 and (m,'zp') in REV: return 'zp',v
        return 'abs',v
    def assemble(s,src,org):
        lines=src.split('\n')
        for p in (0,1):
            final=p==1; pc=org; s.out=[]; chunks=[]; cur=None
            for ln in lines:
                ln=ln.split(';')[0].rstrip()
                if not ln.strip(): continue
                mm=re.match(r'^\s*([A-Za-z_.][\w.]*)\s*=\s*(.+)$',ln)
                if mm: s.syms[mm.group(1)]=s.ev(mm.group(2),False if not final else True); continue
                mm=re.match(r'^([A-Za-z_.][\w.]*):(.*)$',ln.strip())
                if mm:
                    s.syms[mm.group(1)]=pc; ln=mm.group(2)
                    if not ln.strip(): continue
                ln=ln.strip()
                if ln.lower().startswith('.org'):
                    pc=s.ev(ln[4:],final); cur=None; continue
                if cur is None: cur=[pc,bytearray()]; chunks.append(cur)
                if ln.lower().startswith('.db'):
                    for x in split_args(ln[3:]):
                        cur[1].append(s.ev(x,final)&0xFF); pc+=1
                    continue
                if ln.lower().startswith('.dw'):
                    for x in split_args(ln[3:]):
                        v=s.ev(x,final); cur[1]+=bytes([v&255,(v>>8)&255]); pc+=2
                    continue
                parts=ln.split(None,1); m=parts[0].upper(); op=parts[1] if len(parts)>1 else ''
                mode,v=s.parse_operand(m,op,final,pc)
                if (m,mode) not in REV:
                    if mode=='zp' and (m,'abs') in REV: mode='abs'
                    elif mode=='zpx' and (m,'abx') in REV: mode='abx'
                    elif mode=='zpy' and (m,'aby') in REV: mode='aby'
                    else: raise Exception(f'bad mode {m} {mode} :: {ln}')
                code=REV[(m,mode)]; n=LEN[mode]; b=bytearray([code])
                if mode=='rel':
                    off=v-(pc+2)
                    if final and not -128<=off<=127: raise Exception('branch range '+ln)
                    b.append(off&0xFF)
                elif n==2: b.append(v&0xFF)
                elif n==3: b+=bytes([v&0xFF,(v>>8)&0xFF])
                cur[1]+=b; pc+=n
        return chunks
def split_args(t): return [x for x in re.split(r',(?![^(]*\))',t) if x.strip()]
def self_known(s,e):
    # operand is zero-page eligible if it is a numeric literal or a symbol defined as constant <256 before use
    e=e.strip()
    if re.match(r'^\$[0-9A-Fa-f]{1,2}$',e) or re.match(r'^\d+$',e) and int(e)<256: return True
    if re.match(r'^[A-Za-z_][\w]*$',e) and e in s.syms and e.startswith('ZP_'): return True
    return False
