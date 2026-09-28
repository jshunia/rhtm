"""Rebuild the 120-state machine and verify its finite certificates."""
from pathlib import Path
import argparse,json,hashlib
from rh120_source import RHBuilder
from rh_source import RHBuilder as Previous
from builder import save,count
from minimize import minimize
from tables import canonical,read,write
from window_certificate import generate,verify_projection
from compatible_merge import optimize,quot
from verify_control import generate as control_generate,check as control_check
from godel import encode,decode
from published_reference import PUBLISHED_120_SHA256
ROOT=Path(__file__).resolve().parent

def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def compile_named(b):
    raw=b.build(False);sm,mp,rounds=minimize(raw)
    for (q,s),(w,d,n) in raw.items():
        assert sm[mp[q],s]==(w,d,mp.get(n,'halt'))
    tab,ids,missing=canonical(sm);unmerged,rawids,_=canonical(raw)
    mapping=[ids[mp[q]] for q,i in sorted(rawids.items(),key=lambda x:x[1])]
    for (q,s),(w,d,n) in unmerged.items():
        assert tab[mapping[q],s]==(w,d,-1 if n<0 else mapping[n])
    return raw,tab,{q:ids[mp[q]] for q in mp},unmerged,mapping,rounds,missing

def build():
    for folder in ('machines','reports'):(ROOT/folder).mkdir(exist_ok=True)
    previous=Previous();oldraw,oldtab,*_=compile_named(previous)
    oldcert=generate(oldtab,2)
    from window_certificate import verify
    oldedges=verify(oldtab,oldcert)['reachable_read_overapproximation']
    oldgroups,_=optimize(oldtab,oldedges);oldfinal,oldmap=quot(oldtab,oldedges,oldgroups)
    verify_projection(oldtab,oldfinal,oldcert,oldmap)
    # Packaging adaptation: the historical archived table is not in the
    # manuscript. Regenerate this predecessor without claiming archive equality.
    assert len(oldfinal)==242
    b=RHBuilder();raw,tab,names,unmerged,bmap,rounds,missing=compile_named(b)
    cert=generate(tab,2);info=verify(tab,cert)
    groups,trace=optimize(tab,info['reachable_read_overapproximation'])
    final,projection=quot(tab,info['reachable_read_overapproximation'],groups)
    verify_projection(tab,final,cert,projection)
    assert len(tab)==242 and len(final)==240
    expected=ROOT/'machines/RH_120.tm'
    if expected.exists():assert read(expected)==final
    save(raw,ROOT/'machines/RH_121_raw_named.tm')
    for name,t in [('RH_121_predecessor',tab),('RH_122_unmerged',unmerged),('RH_120',final)]:
        write(t,ROOT/'machines'/f'{name}.tm')
    # Independent reference: fingerprint of the literal Appendix I listing,
    # extracted before running any generator. No generated table is distributed.
    assert hashlib.sha256((ROOT/'machines/RH_120.tm').read_bytes()).hexdigest()==PUBLISHED_120_SHA256
    dump(ROOT/'machines/bisimulation.json',bmap)
    dump(ROOT/'machines/window_certificate.json',cert)
    dump(ROOT/'machines/RH_120.projection.json',projection)
    dump(ROOT/'machines/RH_121.dispatch.json',b.dispatch_certificate)
    dump(ROOT/'machines/RH_121.names.json',names)
    dump(ROOT/'machines/RH_120.names.json',{q:projection[i] for q,i in names.items()})
    control=control_generate(oldraw,previous.root,raw,b.root)
    control_info=control_check(oldraw,previous.root,raw,b.root,control)
    dump(ROOT/'machines/control_bisimulation.json',control)
    for name,t in [('RH_121_predecessor',tab),('RH_120',final)]:
        n,g,k=encode(t);assert decode(n,g)==t
        dump(ROOT/'machines'/f'{name}.goedel.json',{'states':n,'G_bits':g.bit_length(),'G_decimal':str(g),'K_decimal':str(k)})
    # Deliberate corruptions must be rejected by the projection/control checks.
    bad=dict(final);w,d,n=bad[0,0];bad[0,0]=(1-w,d,n)
    try:verify_projection(tab,bad,cert,projection)
    except ValueError:pass
    else:raise AssertionError('Corrupted reachable write accepted')
    changed=json.loads(json.dumps(control));changed['pairs'][0]['new'][0]='halt'
    try:control_check(oldraw,previous.root,raw,b.root,changed)
    except AssertionError:pass
    else:raise AssertionError('Corrupted control pair accepted')
    info.pop('reachable_read_overapproximation')
    report={'previous_121_regenerated':True,'published_120_matches':True,
        'historical_121_archive_compared':False,'raw_counts':count(raw),'predecessor_states':len(tab)//2,
        'final_states':len(final)//2,'transitions':len(final),'minimizer_rounds':rounds,'completed_missing':missing,
        'window':info,'merge_trace':trace,'control_bisimulation':control_info,'G_bits':g.bit_length(),
        'sha256':hashlib.sha256((ROOT/'machines/RH_120.tm').read_bytes()).hexdigest(),
        'negative_controls_rejected':['reachable write mutation','control-operation mismatch']}
    dump(ROOT/'reports/build.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');args=p.parse_args()
    print(json.dumps(build(),indent=2))
    if args.test:
        from verify_math import run
        print(json.dumps(run(),indent=2))
