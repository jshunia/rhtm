"""Exact reversible coding of a complete binary transition table."""
import sys
if hasattr(sys, "set_int_max_str_digits"): sys.set_int_max_str_digits(20000)

def encode(table):
    n=len(table)//2;b=4*(n+1)
    G=0
    for q in reversed(range(n)):
        for s in (1,0):
            w,move,target=table[q,s]
            digit=w+2*(move==1)+4*(n if target==-1 else target)
            G=G*b+digit
    return n,G,(1<<n)*(2*G+1)

def decode(n,G):
    b=4*(n+1);table={}
    for q in range(n):
        for s in (0,1):
            G,v=divmod(G,b);target=v//4
            table[q,s]=(v%2,1 if (v//2)%2 else -1,-1 if target==n else target)
    assert G==0
    return table

