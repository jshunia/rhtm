"""Independent exact host-integer checks; these are NOT binary-tape executions."""
from pathlib import Path
from fractions import Fraction
from itertools import product
import json,math
ROOT=Path(__file__).resolve().parent

def ell(B,b):
    assert B>=0 and b>=2
    d=0
    while B: B//=b; d+=1
    return d

def beta(B,b):
    assert B>=0 and b>=2
    d=0
    while B: B=(B-1)//b; d+=1
    return d

def fold_unit(x,j,v):
    while j:j-=1;v+=1;x+=1
    while v:v-=1;j+=1
    return x,j,v

def transform_unit(x,j,v):
    m=x;x=0
    while True:
        x,j,v=fold_unit(x,j,v)
        if not m:break
        m-=1;x+=1
    return x,j,v,m

def divide_unit(x,j,v):
    m=x;x=0;v+=j;j=0
    while m:
        m-=1
        if v:v-=1;j+=1
        else:v+=j;j=0;x+=1
    return x,j,v,m

def prime_flags(N):
    s=bytearray(b'\1')*(N+1);s[0:2]=b'\0\0'
    for p in range(2,math.isqrt(N)+1):
        if s[p]:s[p*p:N+1:p]=b'\0'*((N-p*p)//p+1)
    return s

def scaling(j,f):
    m=q=0
    while j:
        j-=1;m+=1
        for _ in range(2):m+=(j+1)//2;j//=2
        f//=2;q+=1
    return m,f,q

def scanner_checks():
    from rh120_source import RHBuilder
    total=0;reports={}
    for cls,name in [(RHBuilder,'RH_121')]:
        b=cls(True);tab=b.build(False);cert=b.dispatch_certificate;k=cert['scanner_states']
        assert k==4
        stored=json.loads((ROOT/'machines'/f'{name}.dispatch.json').read_text())
        assert stored==json.loads(json.dumps(cert))
        words={r['bits'] for r in cert['control_words']}
        # Also cover every synthetic length <=10 word beginning in 1 and
        # satisfying the stated forbidden-run premise.
        for length in range(1,11):
            for suffix in product('01',repeat=length-1):
                w='1'+''.join(suffix)
                if '0'*k not in w:words.add(w)
        cases=0
        for word in words:
            assert '0'*k not in word and word[0]=='1'
            tape={i:int(s) for i,s in enumerate(word)}
            for start,bit in enumerate(word):
                if bit!='1':continue
                h=start-1;q='4.run.0';steps=0;copy=dict(tape)
                while q!='5.root.1':
                    assert steps<10*(len(word)+k)+10
                    read=copy.get(h,0);w,d,q=tab[q,read]
                    assert w==read # scanner is read-only
                    h+=1 if d=='R' else -1;steps+=1
                assert h==1 and copy==tape
                cases+=1
        total+=cases;reports[name]={'scanner_states':k,'maximum_zero_run':cert['maximum_consecutive_zeros'],
                'certified_leaf_paths':cert['terminal_paths'],'test_words':len(words),'read_only_scan_executions':cases}
    return {'cases':total,'machines':reports,'scope':'Finite language certificates and synthetic operation-entry scanner runs; inherited tape-layout invariant is an additional semantic premise.'}

def run():
    counts={};c=0
    for x,j,v in product(range(7),repeat=3):
        assert fold_unit(x,j,v)==(x+j,j+v,0)
        assert transform_unit(x,j,v)==(x*(j+v+1)+j,j+v,0,0);c+=1
    counts['fold_unit_cases']=counts['transform_unit_cases']=c;c=0
    for B in range(40):
        for j,v in product(range(7),repeat=2):
            J=j+v+1;q,r=divmod(B,J)
            got=divide_unit(B,j,v);assert got==(q,r,J-1-r,0)
            assert transform_unit(*got[:3])==(B,J-1,0,0);c+=1
    counts['split_divider_and_reconstruction_cases']=c;c=0
    for b in range(2,18):
        for B in list(range(257))+[b**d-1 for d in range(1,20)]+[b**d for d in range(1,20)]+[sum(b**i for i in range(1,d+1)) for d in range(1,15)]:
            e=ell(B,b);d=beta(B,b)
            assert max(e-1,0)<=d<=e
            if B:assert sum(b**i for i in range(1,d))<B<=sum(b**i for i in range(1,d+1))
            if e:assert b**(e-1)<=B<b**e
            c+=1
    counts['offset_digit_witnesses']=c
    for n in range(1,100001):
        j=n-1;q=0
        while j:j=(j-1)//4;q+=1
        assert q==((3*n).bit_length()-1)//2
    counts['scaling_clock_cases']=100000;c=0
    for j in range(1000):
        q=((3*(j+1)).bit_length()-1)//2
        W=(q+1)*2**q
        for f in (0,1,2,3,7,15,W-1,W,W+1,2*W):
            assert scaling(j,f)==(j,f//2**q,q);c+=1
    counts['unit_conserving_scaling_cases']=c
    small=[(1,5,Fraction(4,3)),(2,21,Fraction(8,3)),(3,85,Fraction(4)),(4,341,Fraction(16,3)),
           (5,1365,10*Fraction(56,81)+Fraction(682,2389)),(6,2656,Fraction(22,3))]
    assert all(Fraction(N)/L<(q+1)*2**q for q,N,L in small)
    counts['small_range_rational_inequalities']=len(small)
    sieve=prime_flags(4096);A=F=P=1
    for j in range(2,4097):
        assert (A%j!=0)==bool(sieve[j]);A*=j*(j if A%j else 1)
        F*=j
        if sieve[j]:P*=j
        assert A==F*P
    counts['self_sieve_identities']=4095
    rows=[];steps=0;flags=prime_flags(256)
    for n in range(2,257):
        # Execute the source-level product control through exact unit-kernel
        # contracts, with an independent sieve/factorial oracle at EVERY step.
        x=j=0;f=n-2;F=P=1
        while True:
            j+=1;J=j+1;q,r=divmod(x,J);v=J-1-r;x=q;j=r
            if v:x,j,v=x*(j+v+1)+j,j+v,0
            for _ in range(2):x,j,v=x*(j+v+1)+j,j+v,0
            F*=J
            if flags[J]:P*=J
            assert x==F*P-1 and j==J-1 and v==0;steps+=1
            if not f:break
            f-=1
        f=j;v=j;j=0;old=x;division_steps=0
        while x:
            x-=1;J=j+v+1;x,j=divmod(x,J);v=J-1-j
            f=max(f-1,0);division_steps+=1
        j+=v;v=0
        assert division_steps==beta(old,n)
        assert j==n-1 and f==max(n-1-beta(F*P-1,n),0)
        delta=f;m,f,q=scaling(j,f);final=max(f-q,0)
        assert m==n-1 and final==0 # finite validation, not an RH proof
        rows.append({'n':n,'ordinary_digits':ell(old,n),'offset_digits':division_steps,'deficit':delta,'clock':q,'threshold':(q+1)*2**q,'post_compare_deficit':final})
    counts['complete_host_integer_stages']=len(rows);counts['intermediate_product_invariants']=steps
    report={'counts':counts,'scanner':scanner_checks(),'stages':rows,
            'scope':'Exact host-integer and isolated scanner checks. Full arithmetic stages use mathematically specified kernel contracts, not binary-tape execution or AST formal verification.'}
    (ROOT/'reports/math_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    return {k:v for k,v in report.items() if k!='stages'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
