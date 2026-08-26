# Jones nested-geometry audit rerun

**Status: COMPLETE**

> Nested dominance is a structural invariant of evidence refinement, not an empirical PASS.

## Real-versus-permuted exploratory contrast

| block length | median real - permuted | min | max | positive seeds |
|---:|---:|---:|---:|---:|
| 1 | -0.0098 | -0.0139 | 0.0127 | 1/5 |
| 2 | 0.0427 | 0.0293 | 0.0692 | 5/5 |
| 3 | 0.0587 | 0.0422 | 0.0939 | 5/5 |

## Structural invariants

| invariant | result |
|---|---:|
| nested_eis_dominates_old | PASS |
| nested_permuted_dominates_old | PASS |
| block_monotonicity | PASS |
