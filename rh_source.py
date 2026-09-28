"""RH source with an unrecombined split divisor at the digit-phase entrance.

The mathematical criterion and order of endpoints are unchanged from RH_123.
The inherited source/backend and dispatcher are in baseline_source.py and vendor/.
"""
from baseline_source import RHBuilder as Baseline, subroutine

class RHBuilder(Baseline):
    @subroutine
    def seed_deficit(self):
        """For f=v=0: (j,f,v)=(J,0,0) -> (0,J,J).

        The divisor j+v+1 is unchanged. The next divide accepts this split form.
        """
        return [self.while_decnz(self.j,[self.v.inc,self.f.inc])]

    def stage_code(self):
        prod=self.label('product',[self.product_step(),[self.f.decnz,'continue_product']])
        return [self.move(self.m,self.f),prod,self.seed_deficit(),
                self.digits(),self.width()]
