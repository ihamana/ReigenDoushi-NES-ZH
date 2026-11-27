import sys
def make_ips(orig,new):
    out=bytearray(b'PATCH'); i=0; n=len(new)
    o=orig+bytes(max(0,n-len(orig)))
    while i<n:
        if i<len(orig) and new[i]==o[i]: i+=1; continue
        j=i
        while j<n and j-i<0xFFFF and (j>=len(orig) or new[j]!=o[j] or (j+1<n and j+1<len(orig) and new[j+1]!=o[j+1])): j+=1
        if i==0x454F46: i-=1
        out+=bytes([i>>16,(i>>8)&255,i&255,(j-i)>>8,(j-i)&255])+new[i:j]; i=j
    out+=b'EOF'; return bytes(out)
def apply_ips(orig,patch):
    data=bytearray(orig); p=5
    while patch[p:p+3]!=b'EOF':
        off=int.from_bytes(patch[p:p+3],'big'); ln=int.from_bytes(patch[p+3:p+5],'big'); p+=5
        if ln==0:
            rl=int.from_bytes(patch[p:p+2],'big'); v=patch[p+2]; p+=3; chunk=bytes([v])*rl
        else: chunk=patch[p:p+ln]; p+=ln
        if off+len(chunk)>len(data): data+=bytes(off+len(chunk)-len(data))
        data[off:off+len(chunk)]=chunk
    return bytes(data)
if __name__=='__main__':
    a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read()
    p=make_ips(a,b); assert apply_ips(a,p)==b
    open(sys.argv[3],'wb').write(p); print('ips',len(p))
