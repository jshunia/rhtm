"""Proof-producing local-window reachability for deterministic binary TMs.

A window contains 2*r+1 consecutive cells, with its most-significant bit leftmost.
The unknown newly exposed cell is ALWAYS allowed to be either symbol. This is an
inductive overapproximation, not a finite execution sample or a nonhalting test.
"""
from collections import deque

def successors(table,q,w,r):
    symbol=(w>>r)&1
    write,move,target=table[q,symbol]
    if target<0:return ()
    changed=(w&~(1<<r))|(write<<r)
    mask=(1<<(2*r+1))-1
    if move==1:return ((target,((changed<<1)&mask)|b) for b in (0,1))
    return ((target,(changed>>1)|(b<<(2*r))) for b in (0,1))

def generate(table,radius=2):
    if not isinstance(radius,int) or not 1<=radius<=8:raise ValueError('radius')
    n=len(table)//2;mask=[0]*n;mask[0]=1;todo=deque([(0,0)])
    while todo:
        q,w=todo.popleft()
        for a,v in successors(table,q,w,radius):
            if not(mask[a]>>v)&1:
                mask[a]|=1<<v;todo.append((a,v))
    return {'radius':radius,'window_width':2*radius+1,'masks':mask,
        'interpretation':'bit w of masks[q] permits the state/window pair (q,w); left cell is highest bit',
        'initial_state':0,'initial_tape':'all zero',
        'unknown_exterior':'both symbols, independently at every abstract step'}

def verify(table,cert):
    """Standalone finite invariant check, independent of the fixed-point finder."""
    r=cert['radius'];W=2*r+1;n=len(table)//2;m=cert['masks']
    if not isinstance(r,int) or not 1<=r<=8 or cert['window_width']!=W:raise ValueError('bad radius')
    if len(m)!=n or any(not isinstance(x,int) or x<0 or x>=(1<<(1<<W)) for x in m):raise ValueError('bad masks')
    if not m[0]&1:raise ValueError('blank initial configuration omitted')
    total=0;edges=set();obligations=0
    for q,bits in enumerate(m):
        for w in range(1<<W):
            if not (bits>>w)&1:continue
            total+=1;s=(w>>r)&1;edges.add((q,s))
            write,move,target=table[q,s]
            if target<0:continue
            # Spell out the successor calculation rather than call successors().
            cells=[(w>>i)&1 for i in reversed(range(W))]
            cells[r]=write
            for exterior in (0,1):
                shifted=cells[1:]+[exterior] if move==1 else [exterior]+cells[:-1]
                v=0
                for cell in shifted:v=2*v+cell
                if not (m[target]>>v)&1:raise ValueError(('invariant not closed',q,w,target,v))
                obligations+=1
    return {'state_window_pairs':total,'reachable_read_overapproximation':sorted(edges),
            'closure_obligations':obligations,
            'excluded_reads':sorted(set(table)-edges)}

def verify_projection(old,new,cert,mapping):
    evidence=verify(old,cert)
    if len(mapping)!=len(old)//2 or mapping[0]!=0:raise ValueError('bad mapping')
    if any(not isinstance(q,int) or not 0<=q<len(new)//2 for q in mapping):raise ValueError('bad state target')
    for q,s in evidence['reachable_read_overapproximation']:
        w,d,n=old[q,s]
        expected=(w,d,-1 if n<0 else mapping[n])
        if new[mapping[q],s]!=expected:raise ValueError(('projection action mismatch',q,s))
    return evidence
