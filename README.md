# RH in 120 states: source-only reproduction package

Joseph M. Shunia, *A 120-State Binary Turing Machine Equivalent to the
Riemann Hypothesis*, arXiv:2609.30306 (September 2026).

Paper: https://arxiv.org/abs/2609.30306

This directory contains the Python and C++ source extracted from the paper's
appendices, plus a small runner that checks the published finite results.
It starts with no machine tables, certificates, reports, or compiled binaries.
Everything needed at runtime is local; verification performs no downloads.

## Quick start

Requirements:

- Python 3.10 or newer, using only the standard library. No pip packages.
- A C++17 compiler, such as g++ or clang++, for the literal tape replays.

From this directory, run:

```sh
python3 verify.py
```

The command rebuilds the machines, runs the mathematical and finite-certificate
checks, compiles both C++ checkers, and runs the literal bootstrap and stage
replays. It exits with a nonzero status if a check fails. The final success
message is `All included finite verification checks passed` followed by timing.

To select a compiler:

```sh
python3 verify.py --cxx g++
```

For the Python checks alone:

```sh
python3 verify.py --python-only
```

The Python-only command explicitly skips literal tape replay. Use normal Python
execution: `-O`, `-OO`, and `PYTHONOPTIMIZE` disable assertions used by the
published checks, and the runner rejects them. The runner compiles C++ with
assertions enabled. The commands also work when `verify.py` is invoked by its
absolute path from another directory.

Generated files appear in `machines/`, `reports/`, and `build/`, all excluded by
`.gitignore`. In particular, `machines/RH_120.tm` is the regenerated machine.
These directories are created only when verification runs; none is distributed
in the source ZIP.

## What is checked

- Exact SHA-256 agreement between the regenerated 120-state table and the
  literal table printed in Appendix I. The expected fingerprint was extracted
  from the manuscript before running the compiler.
- Compilation to 122 named working states, all-tapes minimization to 121,
  and a reachability-restricted projection to 120 states / 240 transitions.
- The source-control certificate, including all possible conditional-decrement
  outcomes: 84 operation-boundary pairs and 125 outcome edges.
- The dispatcher certificate: 121 terminal paths, maximum control-word length
  18, and maximum zero run 3.
- The five-cell inductive window certificate: 1,621 admitted state/window pairs,
  3,218 closure obligations, and 240 projected state/read pairs.
- Rejection of deliberately corrupted transitions, certificates, and mappings.
- Reversible coding of the final transition table into a 2,140-bit integer.
- The exact host-integer checks, including 255 complete stages through n = 256,
  32,640 intermediate product identities, 100,000 scaling-clock inputs, and
  10,000 unit-conserving scaling cases.
- Literal bootstrap replay to the asserted full tape configuration after
  89,775,610 steps, followed by a separate literal stage replay checking
  completed endpoints 2, 3, and 4. The runner also checks their published step
  counts: 92,233,600; 113,387,256; and 208,951,810.

The literal replays use the generated named table, whose filename is
`RH_121_raw_named.tm` in the original source. That filename is retained even
though the raw table has 122 named working states; its minimized predecessor
has 121. The projection checks connect this construction to the final table.

These are finite implementation and certificate checks. The analytic RH
equivalence and the uniform register-backend semantics are proved in the
paper; the runner is not a proof-assistant formalization of those arguments.

## Run the individual published checks

Run the reproduction driver first so the checkers have their generated inputs:

```sh
python3 -B reproduce.py --test
python3 -B verify_certificate.py
```

To compile and run the C++ programs individually on a Unix-like system:

```sh
mkdir -p build
c++ -O3 -std=c++17 bootstrap_check.cpp -o build/bootstrap_check
./build/bootstrap_check machines/RH_121_raw_named.tm
c++ -O3 -std=c++17 stage_check.cpp -o build/stage_check
./build/stage_check machines/RH_121_raw_named.tm
```

`verify.py` additionally checks the exact published counts and replay timings.
The standalone certificate checker imports table and certificate utilities,
but does not import the machine compiler.

## Extraction and packaging changes

Extraction used the supplied published manuscript `rhtm(2).tex`, with SHA-256:

```text
d9059de4dfb96a8809cceddc35e024582581654bd68c17203d9929bda28cb179
```

The SHA-256 of the literal Appendix I transition-table listing, including its
header and final LF newline, is:

```text
b4b0f07607fc92dae6940f6e6c2d184fec3c13bbfc8cd00a0253321be6009db5
```

The following files are extracted verbatim except for the two documented
packaging adaptations below. Line numbers refer to the supplied TeX file.

| File | Manuscript source lines |
| --- | --- |
| `baseline_source.py` | 1623-1756 |
| `rh_source.py` | 1763-1782 |
| `rh120_source.py` | 1794-1806 |
| `dispatch.py` | 1814-1862 |
| `vendor/builder.py` | 1873-2127 |
| `minimize.py` | 2136-2161 |
| `tables.py` | 2167-2208 |
| `window_certificate.py` | 2217-2281 |
| `compatible_merge.py` | 2287-2350 |
| `verify_certificate.py` | 2356-2390 |
| `verify_control.py` | 2405-2477 |
| `bootstrap_check.cpp` | 2489-2549 |
| `stage_check.cpp` | 2559-2598 |
| `reproduce.py` | 2607-2686 |
| `verify_math.py` | 2692-2850 |
| `godel.py` | 2856-2878 |

1. The printed `reproduce.py` expects `baseline/RH_121.tm`, an older archived
   table absent from the manuscript's listings. This package retains the
   regeneration and certificate verification of that preceding source and
   checks its 121-state count, but does not claim an independent comparison
   with the missing historical archive. The build report states this explicitly.
   The final 120-state table is instead anchored independently to Appendix I
   by the fixed fingerprint in `published_reference.py`.
2. `tables.py` writes explicit UTF-8/LF bytes, avoiding platform-dependent
   newline translation so the published fingerprint is portable.

`verify.py`, `published_reference.py`, this README, and `.gitignore` are the
packaging additions. The compiler, arithmetic routines, minimizer, certificate
algorithms, and C++ replay code are unchanged from the printed listings.

The paper also reports a separate 601-state NQL implementation from preceding
work. Its source and compiler snapshot are not printed in these appendices;
that separate historical cross-check is outside this package. It is not a
dependency of the principal 120-state construction reproduced here.

The backend's existing provenance notice is preserved: `vendor/builder.py` is
a research adaptation of Andrew J. Wade's MIT-0 TMBuilder. The original source
URL is recorded in that file.
