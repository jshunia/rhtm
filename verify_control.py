"""Finite bisimulation of the two source-control transducers.

The generated dispatch/DAG/jump transitions are interpreted literally.
At register leaves, the existing register primitive contract supplies the
success/failure outcome. Every possible decrement outcome is explored;
increment always succeeds. No concrete counter range is assumed.
"""
from collections import deque
import json
from pathlib import Path

def encode(q,h,ones):return (q,h,tuple(sorted(ones)))
def seek(tab,c):
    q,h,positions=c;ones=set(positions);seen=set()
    while not q.startswith('3.') and q!='halt':
        key=encode(q,h,ones)
        if key in seen:raise ValueError('Control-only infinite loop')
        seen.add(key)
        if q=='2e.reg.cleanup_1':
            h-=1;q='6.continue.0'
        else:
            s=int(h in ones);w,d,q=tab[q,s]
            if w:ones.add(h)
            else:ones.discard(h)
            h+=1 if d=='R' else -1
        if not -5<=h<=100:raise ValueError('Control extent exceeded')
    return encode(q,h,ones)

def successor(tab,c,success):
    q,h,ones=c
    if not q.startswith('3.'):raise ValueError('Not an operation')
    if q.endswith('.inc') and not success:raise ValueError('Increment cannot fail')
    return seek(tab,('6.break.0' if success else '6.break.1',h-1,ones))

def generate(old,oldroot,new,newroot):
    start=(seek(old,('N'+str(oldroot),3,(0,1))),seek(new,('N'+str(newroot),3,(0,1))))
    ids={start:0};todo=deque([start]);rows=[]
    while todo:
        a,b=todo.popleft()
        if a[0]!=b[0]:raise ValueError(('Different operations',a,b))
        outputs=[]
        if a[0]!='halt':
            for s in ((1,) if a[0].endswith('.inc') else (0,1)):
                pair=successor(old,a,s),successor(new,b,s)
                if pair not in ids:ids[pair]=len(ids);todo.append(pair)
                outputs.append([s,ids[pair]])
        rows.append({'old':a,'new':b,'successors':outputs})
    return {'initial_pair':0,'pairs':rows,'semantics':'Register primitive outcomes; all possible decrement outcomes, increments always succeed.'}

def check(old,oldroot,new,newroot,cert):
    def c(v):return (v[0],v[1],tuple(v[2]))
    rows=cert['pairs'];assert cert['initial_pair']==0
    assert c(rows[0]['old'])==seek(old,('N'+str(oldroot),3,(0,1)))
    assert c(rows[0]['new'])==seek(new,('N'+str(newroot),3,(0,1)))
    edges=0
    for row in rows:
        a,b=c(row['old']),c(row['new']);assert a[0]==b[0]
        expected=[] if a[0]=='halt' else [1] if a[0].endswith('.inc') else [0,1]
        assert [s for s,_ in row['successors']]==expected
        for s,k in row['successors']:
            assert 0<=k<len(rows)
            assert successor(old,a,s)==c(rows[k]['old'])
            assert successor(new,b,s)==c(rows[k]['new']);edges+=1
    return {'operation_boundary_pairs':len(rows),'outcome_edges':edges,'halting_pairs':sum(r['old'][0]=='halt' for r in rows),'all_decrement_outcomes_checked':True}

if __name__=='__main__':
    from rh_source import RHBuilder as Old
    from rh120_source import RHBuilder as New
    a,b=Old(),New();old,new=a.build(False),b.build(False)
    cert=generate(old,a.root,new,b.root);info=check(old,a.root,new,b.root,cert)
    (Path(__file__).resolve().parent/'machines/control_bisimulation.json').write_text(json.dumps(cert,indent=2))
    (Path(__file__).resolve().parent/'reports/control_verification.json').write_text(json.dumps(info,indent=2))
    print(json.dumps(info,indent=2))
