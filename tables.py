from collections import deque
from pathlib import Path
import hashlib
def canonical(table,start='0a.boot1.A'):
    states={q for q,s in table}
    assert {n for w,d,n in table.values()}-states <= {'halt'}
    labels={start:0};queue=deque([start]);out={};missing=[]
    while queue:
        q=queue.popleft()
        for s in (0,1):
            if (q,s) not in table:
                assert (q,s)==('1b.reg.prep_1',1)
                w,d,n=1,'R','halt';missing.append((q,s))
            else:w,d,n=table[q,s]
            assert w in (0,1) and d in ('L','R')
            if n=='halt':dest=-1
            else:
                if n not in labels:labels[n]=len(labels);queue.append(n)
                dest=labels[n]
            out[labels[q],s]=(w,1 if d=='R' else -1,dest)
    assert len(labels)==len(states)
    return out,labels,missing

def write(table,path):
    text='# start 0; blank 0; halt H; one tape; two symbols; L/R only\n'
    for (q,s),(w,d,n) in sorted(table.items()):
        text+=f'{q} {s} {w} {"R" if d==1 else "L"} {"H" if n==-1 else n}\n'
    # Preserve the paper's LF encoding on Windows as well as Unix.
    path.write_bytes(text.encode('utf-8'))
    return hashlib.sha256(text.encode()).hexdigest()


def read(path):
    t={}
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith('#'):continue
        q,s,w,d,n=line.split();key=(int(q),int(s))
        assert key not in t
        t[key]=(int(w),1 if d=='R' else -1,-1 if n=='H' else int(n))
    n=len(t)//2
    assert len(t)==2*n and set(t)=={(q,s) for q in range(n) for s in (0,1)}
    assert all(w in (0,1) and d in (-1,1) and -1<=z<n for w,d,z in t.values())
    return t
