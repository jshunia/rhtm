"""120-state RH source: share the scaling loop's increment/continue tail.

All counter operations and the tested RH criterion are unchanged from RH_121.
Only the binary grouping is changed before the local jump is resolved.
"""
from rh_source import RHBuilder as Previous, subroutine

class RHBuilder(Previous):
    @subroutine
    def width(self):
        prefix=[self.m.inc,self.halve(self.j),self.halve(self.j),self.halve(self.f)]
        loop=self.label('width',[self.j.decnz,[prefix,[self.x.inc,'continue_width']]])
        return [loop,self.compare()]
