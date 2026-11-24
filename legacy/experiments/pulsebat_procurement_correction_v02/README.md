# PulseBat correction overlay v01

This directory corrects the interpretation of the frozen PulseBat experiment
without changing `repo_v5` or its provenance hashes.

Run the full corrective audit from this directory:

```bash
python scripts/audit_pulsebat.py \
  --permutations 999 --bootstraps 2000 --tag full
python -m unittest discover -s tests -v
```

Primary conclusions:

- the frozen SOC=5%, 0.5C numerical result is reproduced;
- released PulseBat hull geometry degenerates to chemistry-specific pairwise
  separation and is carried by 17 LFP35 batteries;
- the “nameplate/history” arm is actually a chemistry-label-only constructive
  control;
- SOC=10% OCV has a certified positive frontier, so active-pulse superiority is
  not global;
- the paired superiority of SOC=10% OCV over the registered pulse is not
  established;
- cross-SOC physical Pareto dominance is not auditable from the released
  non-SOC-indexed conditioning-cost ledger.

See `AUDIT_REPORT.md` and `docs/CLAIM_CORRECTIONS.md` for the paper-level scope.
