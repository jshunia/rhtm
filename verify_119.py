"""Check the 120-to-119 projection in RH_120_to_119_reduction.tex.

The return-state restriction is checked from the published transition table.
The preparation-state restriction, that canonical state 6 scans zero, is the
note's inherited premise from the 120-state bootstrap and register backend.
"""
from pathlib import Path
import hashlib, json
from tables import read
from published_reference import PUBLISHED_120_SHA256, PUBLISHED_119_SHA256

ROOT = Path(__file__).resolve().parent
A = {39, 48, 74, 80, 90, 93, 94, 113, 117}
B = {72, 75, 102, 112}
# Unique predecessor of each state in A ∪ B, from the return-state proof.
PREDECESSOR = {
    39: 33, 48: 40, 74: 60, 80: 65, 90: 76, 93: 81, 94: 82, 113: 109, 117: 114,
    72: 59, 75: 61, 102: 95, 112: 108,
}


def project_state(q):
    if q < 0:
        return -1
    if q <= 36:
        return q
    if q == 37:
        return 6
    return q - 1


def incoming(table, dest):
    return sorted((q, s, w, d) for (q, s), (w, d, n) in table.items() if n == dest)


def require_incoming(table, dest, expected):
    got = incoming(table, dest)
    if got != expected:
        raise AssertionError(f"incoming transitions to {dest}: {got}")


def return_state_restriction(table):
    """Direct transition-table argument that a run from state 0 never reads (37, 0)."""
    left_one = set()
    for q, p in sorted(PREDECESSOR.items()):
        require_incoming(table, q, [(p, 1, 1, 1)])
        if p == 0 or q == 0:
            raise AssertionError("return-state predecessor is the initial state")
        left_one.add(q)
    if left_one != A | B:
        raise AssertionError("return-state sets A and B do not match the note")

    require_incoming(table, 86, [(72, 1, 1, 1)])
    require_incoming(table, 89, [(75, 1, 1, 1), (102, 1, 1, 1), (112, 1, 1, 1)])
    two_left = {86, 89}
    marked_sources = {q for dest in two_left for q, s, w, d in incoming(table, dest)}
    if not marked_sources <= B <= left_one:
        raise AssertionError("states 86 and 89 are not entered only from B")

    require_incoming(table, 32, [
        (29, 1, 1, 1), (86, 1, 0, -1), (89, 1, 0, -1), (115, 1, 1, 1),
    ])
    left_sources = {q for q, s, w, d in incoming(table, 32) if d < 0}
    if left_sources != two_left:
        raise AssertionError("left-moving entries to state 32 lack the two-cell mark")
    left_one.add(32)

    entries = [(p, 1, 0, -1) for p in sorted(A | {32})]
    require_incoming(table, 37, sorted(entries + [(37, 0, 0, -1)]))
    external = [q for q, s, w, d in incoming(table, 37) if q != 37]
    if set(external) != A | {32} or not set(external) <= left_one:
        raise AssertionError("entries to state 37 do not land on the proved one")
    # Every outside entry scans one. The only zero-scanning predecessor is the
    # (37, 0) self-loop, so a first visit that scans zero cannot occur.
    return {"state_37_read_zero_unreachable_from_state_0": True}


def project_table(table):
    out = {}

    def assign(key, value):
        if key in out:
            raise AssertionError(f"projection collision at {key}")
        out[key] = value

    for q in range(120):
        if q in (6, 37):
            continue
        for s in (0, 1):
            w, d, n = table[q, s]
            assign((project_state(q), s), (w, d, project_state(n)))
    w, d, n = table[6, 0]
    assign((6, 0), (w, d, project_state(n)))
    w, d, n = table[37, 1]
    assign((6, 1), (w, d, project_state(n)))
    return out


def projection_equations(old, reduced):
    checked = 0
    for q in range(120):
        for s in (0, 1):
            if (q, s) in ((6, 1), (37, 0)):
                continue
            w, d, n = old[q, s]
            if reduced[project_state(q), s] != (w, d, project_state(n)):
                raise AssertionError(f"projection equation failed at {(q, s)}")
            checked += 1
    if checked != 238:
        raise AssertionError(f"expected 238 projection equations, checked {checked}")
    return checked


def run():
    source_path = ROOT / "RH_120.tm"
    reduced_path = ROOT / "RH_119.tm"
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    reduced_sha = hashlib.sha256(reduced_path.read_bytes()).hexdigest()
    if source_sha != PUBLISHED_120_SHA256:
        raise AssertionError("RH_120.tm differs from the Appendix I table")
    if reduced_sha != PUBLISHED_119_SHA256:
        raise AssertionError("RH_119.tm differs from the recorded 119-state table")
    old = read(source_path)
    archived = read(reduced_path)
    restriction = return_state_restriction(old)
    reduced = project_table(old)
    equations = projection_equations(old, reduced)
    if reduced != archived:
        raise AssertionError("projected table differs from RH_119.tm")
    if {project_state(q) for q in range(120)} != set(range(119)):
        raise AssertionError("projected working states are not {0,...,118}")
    old_halts = sorted((q, s) for (q, s), (_, _, n) in old.items() if n < 0)
    new_halts = sorted((q, s) for (q, s), (_, _, n) in reduced.items() if n < 0)
    if old_halts != [(6, 1), (77, 1)] or new_halts != [(76, 1)] or project_state(77) != 76:
        raise AssertionError("halting transitions do not match the reduction corollary")
    wrong = dict(reduced)
    wrong[6, 1] = old[6, 1]
    if wrong == archived:
        raise AssertionError("keeping the original (6,1) halt was accepted")
    report = {
        "source_states": 120,
        "reduced_states": len(reduced) // 2,
        "transitions": len(reduced),
        "projection_equations": equations,
        "excluded_reads": [[6, 1], [37, 0]],
        "return_state_restriction": restriction,
        "preparation_state_restriction": "inherited from the 120-state bootstrap and register-backend argument",
        "original_halting_transitions": old_halts,
        "halting_transition": new_halts[0],
        "matches_RH_119": True,
        "sha256": reduced_sha,
        "negative_controls_rejected": ["keeping the original (6,1) halt at the merged state"],
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "reduction_119.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
