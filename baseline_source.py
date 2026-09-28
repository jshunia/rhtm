"""Five-register RH counterexample search with an offset-division digit count.

No uncounted arithmetic operations, tape input or infinite background are used.
At main entry m=M and all other registers are zero. A passing stage tests n=M+2
and returns with m=n-1, all other registers zero. The inherited root restarts main.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent/'vendor'))
from builder import Builder, subroutine
from dispatch import specialize_dispatch

class RHBuilder(Builder):
    def __init__(self, fast=True):
        super().__init__()
        self.fast = fast
        self.dispatch_certificate = None
        for name in ('m','j','x','f','v'):
            setattr(self,name,self.reg(name))

    def label(self,name,seq,zeros=0,ones=0):
        while isinstance(seq,(tuple,list)) and len(seq)==1:
            seq=seq[0]
        if isinstance(seq,int):
            if name not in self.seqs[seq].unresolved:
                return seq
            seq=self.seqs[seq].seq
        return super().label(name,seq,zeros,ones)

    @subroutine
    def move(self,a,b):
        """b += a, a = 0, for distinct registers."""
        return [self.while_decnz(a,b.inc)]

    @subroutine
    def addval(self,a,b,tmp):
        """b += a, preserving a; distinct registers; tmp starts/ends zero."""
        return [self.while_decnz(a,[b.inc,tmp.inc]),self.move(tmp,a)]

    @subroutine
    def fold(self):
        """(x,j,v) <- (x+j,j+v,0). The two increments commute."""
        loop=self.label('fold',[self.j.decnz,
            [self.v.inc,[self.x.inc,'continue_fold']]])
        return [loop,self.move(self.v,self.j)]

    @subroutine
    def transform(self):
        """(x,j,v) <- (x*(j+v+1)+j,j+v,0); m starts/ends zero.

        Fold first, then repeat 'x += 1; fold' once for each saved input unit.
        The post-tested loop is algebraically the earlier prelude-plus-loop.
        """
        loop=self.label('transform',[self.fold(),
            [self.m.decnz,[self.x.inc,'continue_transform']]])
        return [self.move(self.x,self.m),loop]

    @subroutine
    def twice(self):
        return [self.transform(),self.transform()]

    @subroutine
    def divide(self):
        """For m=0, divide B=x by J=j+v+1, even when v is initially nonzero.

        Output (x,j,v)=(B//J,B%J,J-1-B%J); m is again zero.
        """
        tick=self.label('tick',[[self.v.decnz,[self.j.inc,'break_tick']],
            [self.move(self.j,self.v),self.x.inc]])
        return [self.move(self.j,self.v),self.move(self.x,self.m),
                self.while_decnz(self.m,tick)]

    @subroutine
    def if_nonzero(self,a,body):
        return [self.if_decnz(a,[a.inc,body])]

    @subroutine
    def product_step(self):
        """Advance J and compute A_J-1, where A_J=J! product_{p<=J}p."""
        return [self.j.inc,self.divide(),
                self.if_nonzero(self.v,self.transform()),self.twice()]

    @subroutine
    def dec_f(self):
        """Saturating decrement, returning normally on either result."""
        return [self.label('sat',[self.f.decnz,'break_sat'])]

    @subroutine
    def digits(self):
        """Subtract b_j+1(x) from f, saturating, where b is defined by
        x <- (x-1)//(j+1) while x>0. Consume x and restore the divisor.

        Unlike ordinary digit counting, the loop condition's decrement is
        intentional. Remainder and complement remain split between divisions.
        """
        loop=self.label('digits',[self.x.decnz,
            [self.divide(),[self.dec_f(),'continue_digits']]])
        return [loop,self.move(self.v,self.j)]

    @subroutine
    def halve(self,a):
        """a=j or f: a <- floor(a/2), v=0 scratch. For j, collect removed
        units in m. Register x is untouched and can count scaling iterations.
        """
        prefix=[self.m.inc] if a==self.j else []
        return [self.while_decnz(a,[prefix,self.if_decnz(a,self.v.inc)]),
                self.move(self.v,a)]

    @subroutine
    def compare(self):
        return [self.while_decnz(self.x,self.dec_f()),self.if_decnz(self.f,'halt')]

    @subroutine
    def width(self):
        """At entry j=n-1, f=delta, other registers zero. Test
        delta//2**q <= q, q=floor(log_4(3n)), and recover n-1 in m.
        """
        return [self.while_decnz(self.j,[self.m.inc,self.halve(self.j),
            self.halve(self.j),self.halve(self.f),self.x.inc]),self.compare()]

    def stage_code(self):
        prod=self.label('product',[self.product_step(),[self.f.decnz,'continue_product']])
        return [self.move(self.m,self.f),prod,
                self.addval(self.j,self.f,self.v),self.digits(),self.width()]

    @subroutine
    def main(self):
        return self.stage_code()

    def generate(self):
        table=super().generate()
        if self.fast:
            table,self.dispatch_certificate=specialize_dispatch(self,table)
        return table
