# PulseBat claim corrections

This table supersedes PulseBat wording in `repo_v5/docs/CLAIM_STATUS.md`.  The
frozen `repo_v5` files remain unchanged for provenance.

| Earlier claim | Corrected status | Audited evidence |
|---|---:|---|
| PulseBat tests nontrivial composite convex-hull geometry | **Rejected** | For every released menu and every registered block length, convex-hull distance equals the minimum chemistry-specific pairwise TV within numerical tolerance (maximum LP residual (5.40\times10^{-9})). |
| All 151 batteries equally support the registered Δ(1)=0.5273 result | **Rejected** | The minimum is carried by LFP35: 9 qualified and 8 unqualified batteries. Deleting any of 45 decisive LMO10 batteries leaves Δ unchanged; LFP35 leave-one-out values span 0.5000–0.6162. |
| More measured nameplate/history samples cannot replace a diagnostic pulse | **Not tested as written** | The released data contain chemistry and nominal capacity, but no format or historical-use fields. The implementation hard-codes a one-symbol law within chemistry. The valid result is an exact collision for a **chemistry-label-only constructive negative control**. |
| A 0.5C pulse opens a positive frontier at the registered SOC=5% | **Supported locally** | Δ(1)=0.5273, chemistry-stratified permutation (p=0.001), whole-battery bootstrap 95% CI [0.3455, 0.7227]. |
| The registered 0.5C pulse is the globally preferred PulseBat acquisition | **Rejected** | SOC is part of the experiment. Across 40 SOC×menu points, passive OCV at SOC=10% has Δ(1)=0.6273, (p=0.001), CI [0.4455, 0.7980]. The registered SOC=5% is the weakest OCV point. |
| SOC=10% OCV is statistically proven to have larger Δ than SOC=5% 0.5C pulse | **Not established** | Paired whole-battery bootstrap for the difference gives point estimate +0.1000 but 95% CI [−0.1864, 0.3773]; (P_\mathrm{boot}(\text{difference}>0)=0.692). |
| SOC=10% OCV physically Pareto-dominates SOC=5% 0.5C pulse | **Not auditable from the released cost ledger** | The ledger assigns menu-level time/stress independent of SOC. Its prose includes 1C conditioning time, while its OCV maximum C-rate is recorded as zero. Cross-SOC conditioning time, energy, and peak stress must be normalized before a physical dominance claim. |
| Greater pulse stress necessarily buys more certification information | **Rejected at fixed SOC=5%** | 0.5C, 1C, and 1.5C have the same registered Δ curve; 0.5C uses less incremental pulse time and amplitude. |
| Evidence acquisition should optimize only the sensor/menu | **Rejected** | The empirical Δ surface changes materially with SOC; the procurement object must be menu×operating condition, consistent with κ in the theory. |

The corrected positive conclusion is therefore narrower and stronger:
**PulseBat supports operating-condition-aware evidence design.  A positive
certification frontier can be opened by either active or passive voltage
evidence, depending on SOC; test stress is not monotonically related to
certification information.**  The dataset does not establish a global physical
Pareto optimum until conditioning costs are registered consistently.
