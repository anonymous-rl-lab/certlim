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

- Cells: 16
- Expected cycle triplets: 1688
- Complete parsed cycles: 1597
- Explicit errors: 91
- Completeness: 94.609%
- Chronology pass rate: 100.000%
- Cycles/cell: {'minimum': 83, 'median': 100.5, 'maximum': 114}

## Evaluability audit (not a result)

- SOH range: 0.0451 to 1.0039
- SOH ≤ 0.95: 1592
- SOH ≤ 0.90: 1565
- This section only determines whether a registered endpoint is supportable; it is not inferential evidence.
