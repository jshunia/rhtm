"""A checked, program-specific replacement of the read-only dispatcher scan.

This is not an all-tapes bisimulation: its premise is the live control-word
language of the compiled source. See README for the invariant and bootstrap check.
"""
def control_words(builder):
    rows=[]
    def visit(node,prefix,active):
        if isinstance(node,int):
            if node in active:
                raise ValueError('This certificate requires an acyclic control DAG')
            seq=builder.seqs[node].seq
            if len(seq)!=2:raise ValueError('Source has not been binarized')
            for bit,child in enumerate(seq):
                visit(child,prefix+str(bit),active|{node})
        else:
            rows.append((prefix,node))
    visit(builder.root,'110',frozenset())
    return rows

def specialize_dispatch(builder,table):
    words=control_words(builder)
    longest=max(max(map(len,w.split('1'))) for w,_ in words)
    # Boot2 is alternating control with a two-one suffix. Normal operation
    # adds a phase marker 1 and at most one intervening zero before the sentinel.
    k=max(longest,2)+1
    out=dict(table)
    for i in range(k):
        out[f'4.run.{i}',1]=(1,'L','4.run.0')
        out[f'4.run.{i}',0]=(0,'L',f'4.run.{i+1}') if i+1<k else (0,'R','4.dispatch.scan')
    old_entry=out['6.continue.0',1]
    out['6.continue.0',1]=(1,'L','4.run.0')
    reached=set();todo=['0a.boot1.A']
    while todo:
        q=todo.pop()
        if q in reached:continue
        reached.add(q)
        for bit in (0,1):
            if (q,bit) in out:todo.append(out[q,bit][2])
    out={key:v for key,v in out.items() if key[0] in reached}
    old_states={q for q,_ in table};new_states={q for q,_ in out}
    cert={'live_control_prefix':'110','terminal_paths':len(words),
        'maximum_word_length':max(len(w) for w,_ in words),
        'maximum_consecutive_zeros':longest,'scanner_states':k,
        'old_entry_transition':old_entry,'new_entry_transition':out['6.continue.0',1],
        'removed_states':sorted(old_states-new_states),'added_states':sorted(new_states-old_states),
        'control_words':[{'bits':w,'terminal':v} for w,v in words],
        'scope':'Language/invariant-based scanner replacement, not an all-tapes state merge.'}
    return out,cert
