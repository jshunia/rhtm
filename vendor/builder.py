"""Research adaptation of Andrew J. Wade's MIT-0 TMBuilder.
Source: https://raw.githubusercontent.com/LegionMammal978/turing_machine_explorer/main/TMBuilder.py
The naming/debugger layer is replaced; operational framework and IR follow Wade.
"""
from functools import lru_cache
from dataclasses import dataclass

class Reg(str):
    @property
    def inc(self): return '3.'+self+'.inc'
    @property
    def decnz(self): return '3.'+self+'.decnz'

@dataclass
class Seq:
    seq: tuple
    name: str | None = None
    unresolved: frozenset = frozenset()

def subroutine(f):
    def g(self,*args):
        args=tuple(self.add(v) for v in args)
        key=(f.__name__,*args)
        if key in self.memo: return self.memo[key]
        rv=tuple(v for v in (self.add(v2) for v2 in f(self,*args)) if v!=())
        self.memo[key]=rv
        if rv:
            k=self.add(rv)
            if isinstance(k,int): self.seqs[k].name=f.__name__
        return rv
    return g

class Builder:
    def __init__(self):
        self.regs={};self.seqs=[];self.lookup={};self.memo={};self.root=None
    def reg(self,name):
        if name not in self.regs: self.regs[name]=Reg(name)
        return self.regs[name]
    def add(self,tree):
        while isinstance(tree,(tuple,list)) and len(tree)==1: tree=tree[0]
        if not isinstance(tree,(tuple,list)): return tree
        if not tree: return ()
        key=tuple(v for v in (self.add(x) for x in tree) if v!=())
        if not key: return ()
        if len(key)==1: return key[0]
        if key not in self.lookup:
            unresolved=set()
            for v in key:
                if isinstance(v,int): unresolved.update(self.seqs[v].unresolved)
                elif v.startswith(('break_','continue_')): unresolved.add(v.split('_',1)[1])
            self.lookup[key]=len(self.seqs)
            self.seqs.append(Seq(key,None,frozenset(unresolved)))
        return self.lookup[key]
    def label(self,name,seq,zeros=0,ones=0):
        cf=('break_'+name,'continue_'+name)
        def contains(s):
            for e in s:
                if e in cf: return True
                if isinstance(e,int) and name in self.seqs[e].unresolved: return True
                if isinstance(e,(tuple,list)) and contains(e): return True
            return False
        def resolve(z,o,v):
            if v in cf: return '_break.'+str(z) if v==cf[0] else '_continue.'+str(o)
            if isinstance(v,int) and name in self.seqs[v].unresolved:
                return self.add(self.label(name,self.seqs[v].seq,z,o))
            if isinstance(v,(tuple,list)): return self.label(name,v,z,o)
            return v
        if not contains(seq): return seq
        assert len(seq)==2,(name,seq)
        return (resolve(zeros+1,ones,seq[0]),resolve(zeros,ones+1,seq[1]))
    def reachable(self):
        grey={self.root};black=set()
        while grey:
            i=grey.pop()
            if i not in black:
                yield i;black.add(i)
                grey.update(v for v in self.seqs[i].seq if isinstance(v,int))
    def breakout(self):
        length=max(len(s.seq) for s in self.seqs)
        while length>1:
            seen=set();match=None;reach=list(self.reachable())
            for i in reach:
                s=self.seqs[i].seq
                for off in range(len(s)+1-length):
                    p=s[off:off+length]
                    if p in seen: match=p;break
                    seen.add(p)
                if match: break
            if match:
                mi=self.add(match)
                for i in reach:
                    while True:
                        s=self.seqs[i].seq
                        if len(s)<=length: break
                        for off in range(len(s)+1-length):
                            if s[off:off+length]==match:
                                self.seqs[i].seq=s[:off]+(mi,)+s[off+length:];break
                        else: break
            else: length-=1
    def binary(self):
        i=0
        while i<len(self.seqs):
            s=self.seqs[i].seq
            if len(s)>2: self.seqs[i].seq=(s[0],self.add(s[1:]))
            i+=1
    @subroutine
    def while_decnz(self,var,body):
        return [self.label('loop',[var.decnz,'continue_loop' if body==() else [body,'continue_loop']])]
    @subroutine
    def if_decnz(self,var,body): return [[var.decnz,body]]
    @subroutine
    def if_not_decnz(self,var,body): return [self.label('fn',[[var.decnz,'break_fn'],body])]
    @subroutine
    def pair(self,out,a,b):
        return [self.label('loop',[self.while_decnz(a,[b.inc,out.inc]),[b.decnz,[[out.inc,self.while_decnz(b,a.inc)],'continue_loop']]])]
    @subroutine
    def unpair(self,a,b,n):
        return [self.label('loop',[n.decnz,[a.inc,[[b.decnz,'continue_loop'],[self.while_decnz(a,b.inc),'continue_loop']]]])]
    @subroutine
    def if_eq(self,a,b,body):
        return [self.label('fn',[[self.label('loop',[a.decnz,[[b.decnz,'continue_loop'],[self.while_decnz(a,()),'break_fn']]]),[b.decnz,[self.while_decnz(b,()),'break_fn']]],body])]
    def debug_assert_eq_val(self,*args): return ()
    def build(self,optimize=True):
        self.root=self.add(self.main())
        if optimize: self.breakout()
        self.binary()
        return self.generate()
    def generate(self):
        table={}
        def emit(q,s,w,d,n): table[q,int(s)]=(int(w),d,n)
        # Compact transcription of the operational framework, same labels as source.
        rows='''
0a.boot1.A 0 1 R 0a.boot1.B
0a.boot1.A 1 1 L 0a.boot1.C
0a.boot1.B 0 0 L 0a.boot1.A
0a.boot1.B 1 0 L 0a.boot1.D
0a.boot1.C 0 1 L 0a.boot1.A
0a.boot1.D 0 1 L 0a.boot1.B
0a.boot1.D 1 1 R 0a.boot1.E
0a.boot1.E 0 0 R 0a.boot1.D
0a.boot1.E 1 0 R 0a.boot1.B
0b.boot2.0 0 1 L 6.continue.0
0b.boot2.0 1 1 R 0b.boot2.1
0b.boot2.1 0 0 R 0b.boot2.0
0b.boot2.1 1 1 R 0b.boot2.2
1b.reg.prep_1 0 0 R 1b.reg.prep_2
1b.reg.prep_2 0 1 R 1b.reg.prep_2
1b.reg.prep_2 1 1 L 6.continue.0
2b.reg.-1.dec 0 0 R 2b.reg.-2.dec
2b.reg.-1.dec 1 1 R 2b.reg.-1.dec
2b.reg.-1.inc 0 0 R 2b.reg.-2.inc
2b.reg.-1.inc 1 1 R 2b.reg.-1.inc
2b.reg.-2.dec 0 1 L 2c.reg.return_1_1
2b.reg.-2.dec 1 0 R 2b.reg.dec.check
2b.reg.-2.inc 0 1 R 2b.reg.inc.shift_1
2b.reg.-2.inc 1 1 R 2b.reg.-2.inc
2b.reg.dec.check 0 0 L 2b.reg.-2.dec
2b.reg.dec.check 1 1 R 2b.reg.dec.scan_1
2b.reg.dec.scan_1 0 0 R 2b.reg.dec.scan_2
2b.reg.dec.scan_1 1 1 R 2b.reg.dec.scan_1
2b.reg.dec.scan_2 0 0 L 2b.reg.dec.shift_1
2b.reg.dec.scan_2 1 1 R 2b.reg.dec.scan_1
2b.reg.dec.shift_1 0 1 L 2b.reg.dec.shift_2
2b.reg.dec.shift_1 1 1 L 2b.reg.dec.shift_1
2b.reg.dec.shift_2 0 0 L 2c.reg.return_0_1
2b.reg.dec.shift_2 1 0 L 2b.reg.dec.shift_1
2b.reg.inc.shift_1 0 0 L 2c.reg.return_0_1
2b.reg.inc.shift_1 1 0 R 2b.reg.inc.shift_2
2b.reg.inc.shift_2 0 1 R 2b.reg.inc.shift_1
2b.reg.inc.shift_2 1 1 R 2b.reg.inc.shift_2
2c.reg.return_0_1 0 0 L 2c.reg.return_0_2
2c.reg.return_0_1 1 1 L 2c.reg.return_0_1
2c.reg.return_0_2 0 0 L 6.break.0
2c.reg.return_0_2 1 1 L 2c.reg.return_0_1
2c.reg.return_1_1 0 0 L 2c.reg.return_1_2
2c.reg.return_1_1 1 1 L 2c.reg.return_1_1
2c.reg.return_1_2 0 0 L 6.break.1
2c.reg.return_1_2 1 1 L 2c.reg.return_1_1
2e.reg.cleanup_1 0 0 R 2e.reg.cleanup_1
2e.reg.cleanup_1 1 0 R 2e.reg.cleanup_2
2e.reg.cleanup_2 0 0 L 0b.boot2.0
2e.reg.cleanup_2 1 0 R 2e.reg.cleanup_2
4.dispatch.0 0 0 L 4.dispatch.scan
4.dispatch.0 1 1 L 4.dispatch.0
4.dispatch.scan 0 0 R 4.dispatch.scan
4.dispatch.scan 1 1 R 5.root.1
5.root.1 0 0 R 0b.boot2.0
5.root.1 1 1 R 5.root.2
6.break.0 0 1 R 2e.reg.cleanup_1
6.break.0 1 0 L 6.break.0
6.break.1 0 0 L 6.break.0
6.break.1 1 0 L 6.break.1
6.continue.0 0 0 L 6.continue.0
'''
        for line in rows.strip().splitlines(): emit(*line.split())
        for j,r in enumerate(self.regs.values()):
            for op in ('inc','dec'):
                emit(f'2b.reg.{j}.{op}',0,0,'R',f'2b.reg.{j-1}.{op}')
                emit(f'2b.reg.{j}.{op}',1,1,'R',f'2b.reg.{j}.{op}')
            for state,op in ((r.inc,'inc'),(r.decnz,'dec')):
                emit(state,0,1,'R','1b.reg.prep_1')
                emit(state,1,0,'R',f'2b.reg.{j}.{op}')
        r=next(iter(self.regs.values()))
        emit('0a.boot1.C',1,1,'R',r.inc)
        emit('0b.boot2.2',0,0,'R',r.inc)
        emit('0b.boot2.2',1,1,'R',r.decnz)
        @lru_cache(None)
        def zeros(v):
            if not isinstance(v,int): return 0
            a,b=self.seqs[v].seq
            return max(1+zeros(a),zeros(b))
        mz=max(2+zeros(self.root),2)
        for j in range(1,mz+1):
            emit(f'4.dispatch.{j}',0,0,'L',f'4.dispatch.{j-1}')
            emit(f'4.dispatch.{j}',1,1,'L',f'4.dispatch.{j}')
        emit('6.continue.0',1,1,'L',f'4.dispatch.{mz}')
        for s in (0,1): emit('5.root.2',s,0,'R',f'N{self.root}')
        def jump(kind,j):
            for k in range(1,j+1):
                if kind=='break':
                    emit(f'6.break.{k}',0,0,'L',f'6.break.{k-1}')
                    emit(f'6.break.{k}',1,0,'L',f'6.break.{k}')
                else:
                    emit(f'6.continue.{k}',0,0,'L',f'6.continue.{k}')
                    emit(f'6.continue.{k}',1,0,'L',f'6.continue.{k-1}')
        for i in self.reachable():
            for s,v in enumerate(self.seqs[i].seq):
                q=f'N{i}'
                if isinstance(v,int): emit(q,s,s,'R',f'N{v}')
                elif v.startswith('_break.'):
                    level=int(v.split('.')[1])
                    if s==0 and level==0: emit(q,s,1,'L','6.continue.0')
                    else:
                        j=level-(1-s); assert j>=0
                        jump('break',j);emit(q,s,0,'L',f'6.break.{j}')
                elif v.startswith('_continue.'):
                    j=int(v.split('.')[1])-s;assert j>=0
                    jump('continue',j);emit(q,s,0,'L',f'6.continue.{j}')
                else: emit(q,s,s,'R',v)
        reach=set();stack=['0a.boot1.A']
        while stack:
            q=stack.pop()
            if q in reach: continue
            reach.add(q)
            stack += [table[q,s][2] for s in (0,1) if (q,s) in table]
        return {k:v for k,v in table.items() if k[0] in reach}

def count(table):
    states={q for q,s in table}
    return {'framework':sum(q[0].isdigit() for q in states),'decision_DAG':sum(q[0]=='N' for q in states),'total':len(states)}

def save(table,path):
    with open(path,'w') as f:
        f.write('#! start 0a.boot1.A\n')
        for (q,s),(w,d,n) in sorted(table.items()): f.write(f'{q} {s} {w} {d} {n}\n')
