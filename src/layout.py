# Text layout for engine v2 (window scrolls like the original; we only wrap lines)
import re
TOK=re.compile(r'<等待>|<選項>|<換頁>|.',re.S)
CLOSE=set('，。、！？；：」』）…～ー,.!?')
LINEW=112
def cw(tk):
    if tk in '0123456789' or tk==' ': return 8
    if tk in ('<等待>','<選項>','<換頁>'): return 0
    return 12
def wrap_line(toks,start_px=0):
    w=sum(cw(t) for t in toks)
    if start_px+w<=LINEW: return [toks]
    n=-(-(start_px+w)//LINEW); target=-(-(start_px+w)//n)
    lines=[];cur=[];px=start_px;i=0
    while i<len(toks):
        tk=toks[i]; ww=cw(tk)
        if ww and (px+ww>LINEW or (px>=target and len(lines)<n-1 and tk not in CLOSE)):
            if tk in CLOSE and cur:
                if px+ww<=LINEW: cur.append(tk); px+=ww; i+=1; continue
                moved=cur.pop(); lines.append(cur); cur=[moved]; px=cw(moved); continue
            lines.append(cur); cur=[]; px=0
            if tk==' ': i+=1; continue
        cur.append(tk); px+=ww; i+=1
    if cur: lines.append(cur)
    return lines
def layout(text,name_prefix=False,yesno=False):
    toks=TOK.findall(text)
    if yesno:
        body=''.join(t for t in toks if t not in ('<選項>','\n'))
        a,b=[p for p in re.split(r'\s+',body.strip()) if p][:2]
        pad=max(1,(56-8-sum(cw(c) for c in a))//8)
        trail=len(text)-len(text.rstrip('\n'))
        return ['<選項>']+list(a)+[' ']*pad+list(b)+['\n']*trail,{}
    mm=re.match(r'^ (\S+?)[ 　]+(\d+)[ 　]*(\n*)$',text)
    if mm:
        name,cost,trail=mm.groups(); start=8+12*len(name)
        pad=max(1,(104-start-8*len(cost))//8)
        return [' ']+list(name)+[' ']*pad+list(cost)+['\n']*len(trail),{}
    hard=[];cur=[]
    for tk in toks:
        if tk in ('\n','<換頁>'): hard.append((cur,tk)); cur=[]   # a page break also starts a fresh line
        else: cur.append(tk)
    hard.append((cur,None))
    out=[]
    for k,(l,sep) in enumerate(hard):
        start=48 if (name_prefix and k==0) else 0
        for vi,v in enumerate(wrap_line(l,start)):
            if vi: out.append('\n')
            out+=v
        if sep: out.append(sep)
    return out,{}
def preview(toks,name_prefix=False):
    s=''.join({'<換頁>':'\n──(換頁)──\n','<等待>':'▼'}.get(t,t) for t in toks)
    return ('〔名字〕' if name_prefix else '')+s
