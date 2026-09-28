"""Check only delivered tables/certificates, without importing the machine compiler."""
from pathlib import Path
from copy import deepcopy
import json,hashlib
from tables import read
from window_certificate import verify_projection
ROOT=Path(__file__).resolve().parent

def run():
    old=read(ROOT/'machines/RH_121_predecessor.tm');new=read(ROOT/'machines/RH_120.tm')
    cert=json.loads((ROOT/'machines/window_certificate.json').read_text())
    mp=json.loads((ROOT/'machines/RH_120.projection.json').read_text())
    info=verify_projection(old,new,cert,mp);rejected=[]
    def must_fail(label,changed_new,changed_cert,changed_map):
        try:verify_projection(old,changed_new,changed_cert,changed_map)
        except (ValueError,KeyError,IndexError):rejected.append(label);return
        raise RuntimeError('Invalid certificate accepted: '+label)
    c=deepcopy(cert);c['masks'][0]&=~1
    must_fail('remove blank initial window',new,c,mp)
    q=next(i for i,m in enumerate(cert['masks']) if i!=0 and m)
    c=deepcopy(cert);c['masks'][q]=0
    must_fail('remove reachable successor state windows',new,c,mp)
    bad=dict(new);w,d,n=bad[0,0];bad[0,0]=(1-w,d,n)
    must_fail('flip a reachable write',bad,cert,mp)
    q,s=info['excluded_reads'][-1];c=deepcopy(cert);c['masks'][q]|=1<<(s<<cert['radius'])
    must_fail('admit a formerly impossible local window',new,c,mp)
    badmap=list(mp);badmap[0]=1
    must_fail('wrong start-state projection',new,cert,badmap)
    out={'old_states':len(old)//2,'new_states':len(new)//2,'state_window_pairs':info['state_window_pairs'],
         'closure_obligations':info['closure_obligations'],'projected_reachable_reads':len(info['reachable_read_overapproximation']),
         'excluded_reads':info['excluded_reads'],'negative_controls_rejected':rejected,
         'scope':'Inductive finite certificate; unknown neighboring cells always include both 0 and 1. Does not assume RH, source-loop invariants, or nonhalting.'}
    (ROOT/'reports/certificate_checks.json').write_text(json.dumps(out,indent=2)+'\n')
    return out
if __name__=='__main__':print(json.dumps(run(),indent=2))
