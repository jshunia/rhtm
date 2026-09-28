"""Strong bisimulation minimization: preserves every tape trajectory, up to states.
No transition deletion, heuristic halting assumptions, or finite-run equivalence.
"""
def minimize(t,start='0a.boot1.A'):
    states=sorted({q for q,s in t})
    # All names without outgoing instructions are halts.
    parts={q:0 for q in states}
    rounds=0
    while True:
        keys={};nparts={}
        for q in states:
            key=tuple(None if (q,s) not in t else (t[q,s][0],t[q,s][1],parts.get(t[q,s][2],-1)) for s in (0,1))
            nparts[q]=keys.setdefault(key,len(keys))
        rounds+=1
        if nparts==parts:break
        parts=nparts
    reps={}
    for q in states:reps.setdefault(parts[q],q)
    reps[parts[start]]=start
    mapping={q:reps[parts[q]] for q in states}
    out={}
    for (q,s),(w,d,n) in t.items():
        k=mapping[q],s;value=(w,d,mapping.get(n,'halt'))
        assert k not in out or out[k]==value
        out[k]=value
    return out,mapping,rounds
