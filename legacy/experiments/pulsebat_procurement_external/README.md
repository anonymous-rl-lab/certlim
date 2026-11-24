# PulseBat evidence-procurement gate

This repository evaluates finite-evidence certification on real retired
lithium-ion batteries from the open PulseBat dataset.

The registered task is qualification of an incoming retired-battery population
for a high-retained-capacity second-life service.  Gold-standard SOH comes from
a full CCCV charge and CC discharge.  Evidence menus range from nameplate data
and passive OCV to controlled 5-second current-pulse responses.

The experiment directly evaluates three objects from the theory:

1. an exact permanent collision under non-diagnostic nameplate/history evidence;
2. the certification frontier opened by targeted pulse evidence;
3. physical evidence procurement cost, expressed as test time, maximum C-rate,
   and the number of independently sampled batteries—not an arbitrary monetary
   price.

Run:

```bash
python scripts/run_all.py
python scripts/audit_release.py
python -m unittest discover -s tests -v
```

The compact 151-row processed table is included.  Rebuild it from the upstream
workbooks with `scripts/prepare_data.py PATH_TO_CLONED_PULSEBAT_REPOSITORY`.

## Sources

- Dataset/code: <https://github.com/terencetaothucb/Pulse-Voltage-Response-Generation>
- Raw-data archive: <https://doi.org/10.5281/zenodo.13360631>
- Associated article: <https://www.nature.com/articles/s41467-024-54454-0>

This is a registered second-life capacity-margin qualification task.  It does
not claim that every battery below 80% SOH is intrinsically unsafe in every
possible application.

