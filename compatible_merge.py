"""Greedy compatible state merging using a supplied proven reachable-read set.
Selection is heuristic. Correctness of the selected mapping is checked separately.
"""
from collections import deque
def unionmerge(tab,edges,groups,pairs):
    n=len(tab)//2;p=list(range(n));dd=[{} for _ in range(n)]
    for q,s in edges:dd[q][s]=tab[q,s]
    def find(q):
        while p[q]!=q:p[q]=p[p[q]];q=p[q]
        return q
    todo=list(pairs)+[(q,r) for q,r in enumerate(groups) if q!=r]
    while todo:
        a,b=todo.pop()
        if a<0 or b<0:
            if a!=b:return None
            continue
        a,b=find(a),find(b)
        if a==b:continue
        if a>b:a,b=b,a
        for s,t in dd[b].items():
            if s in dd[a]:
                z=dd[a][s]
                if z[:2]!=t[:2]:return None
                todo.append((z[2],t[2]))
            else:dd[a][s]=t
        p[b]=a;dd[b]={}
    return [find(q) for q in range(n)]

def optimize(tab,edges):
    n=len(tab)//2;g=list(range(n));record=[]
    while True:
        roots=sorted(set(g));best=None
        for i,a in enumerate(roots):
            for b in roots[i+1:]:
                new=unionmerge(tab,edges,g,[(a,b)])
                if new is not None and (best is None or len(set(new))<len(set(best[0]))):best=(new,a,b)
        if best is None:break
        g,a,b=best
        record.append({'a':a,'b':b,'states':len(set(g))})
        print(record[-1],flush=True)
    return g,record

def quot(tab,edges,g):
    small={}
    for q,s in edges:
        w,d,n=tab[q,s];a=(w,d,g[n] if n>=0 else -1)
        key=(g[q],s)
        assert key not in small or small[key]==a
        small[key]=a
    # Arbitrary unreachable reads are completed, never used on actual runs.
    for old in range(len(g)):
        for s in (0,1):
            w,d,n=tab[old,s]
            small.setdefault((g[old],s),(w,d,g[n] if n>=0 else -1))
    start=g[0];ren={start:0};todo=deque([start]);out={}
    while todo:
        q=todo.popleft()
        for s in (0,1):
            w,d,n=small[q,s]
            if n>=0 and n not in ren:ren[n]=len(ren);todo.append(n)
            out[ren[q],s]=(w,d,ren[n] if n>=0 else -1)
    assert len(ren)==len(set(g))
    return out,[ren[r] for r in g]

