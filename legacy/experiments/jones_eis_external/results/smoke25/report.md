# Jones EIS smoke report

**Overall: PASS**

## Gates

| Gate | Result |
|---|---:|
| archive_checksum | PASS |
| cell_count | PASS |
| complete_cycle_count | PASS |
| cycles_per_cell | PASS |
| pairing_and_parse_completeness | PASS |
| protocol_chronology | PASS |
| eis_support | PASS |
| action_variation | PASS |
| finite_outcomes | PASS |

## Audit counts

- Cells: 32
- Expected cycle triplets: 3578
- Complete parsed cycles: 3521
- Explicit errors: 57
- Completeness: 98.407%
- Chronology pass rate: 100.000%
- Cycles/cell: {'minimum': 94, 'median': 104.5, 'maximum': 139}

## Evaluability audit (not a result)

- SOH range: 0.0163 to 0.9053
- SOH ≤ 0.95: 3521
- SOH ≤ 0.90: 3520
- This section only determines whether a registered endpoint is supportable; it is not inferential evidence.
