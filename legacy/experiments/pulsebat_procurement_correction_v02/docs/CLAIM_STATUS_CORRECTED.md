# Claims versus evidence

| Claim | Status | Evidence boundary |
|---|---:|---|
| Exact old-evidence collision can force Alert | Supported | Registered finite SCM witness |
| Re-encoding old evidence cannot remove an exact collision | Supported | XOR/data-processing negative control |
| A registered proxy can break the collision | Supported | Registered paired SCM only |
| \(\Delta(n)\) controls both obstruction and bounded separation | Supported | Exact LP/Sion computation through registered range |
| Minimal separable block is the optimal procurement block | Rejected | \(n_\star=2\), but Hoeffding optimum is 14 |
| Jones EIS adds cross-temperature capacity information | Supported diagnostically | Same-seed real-versus-permuted cell-bootstrap RMSE gains: 0.0094 and 0.0136; already-inspected external cohort |
| More old Jones history fully substitutes for EIS | Rejected for registered capacity forecasting | Paired real-versus-permuted RMSE gains remain positive, but are much smaller than the uncontrolled 51.2%/40.7% comparisons |
| EIS always outperforms old history for every task | Rejected | Old history is stronger on the registered binary ranking task |
| Jones EIS yields transported three-decision error control | Rejected | After conservative nondegenerate threshold repair, Unsafe→Certify median error remains 52.1% for old-history+EIS |
| Jones EIS improves prediction and certification in the same direction | Rejected | RMSE improves while AUC drops by 0.117 and Unsafe→Certify rises by 0.509 versus old history |
| MATR Curve-100 contains information absent from Scalar-100 summaries | Supported as external prediction evidence | MAPE 25.8% vs 42.9%; paired-curve permutation diagnostic p=0.005 |
| Five-cycle MATR curve evidence reliably replaces 100-cycle scalar telemetry | Not established | Point MAPE improves, but registered paired-permutation gate fails: p=0.373 |
| MATR source-calibrated 80% intervals transport to batch 3 | Rejected | Best external coverage 57.5%; Curve-100 coverage 37.5% |
| MATR demonstrates usable positive safety certification | Rejected | All registered menus produce zero external `Certify` decisions |
| Balanced-average decisiveness is sufficient for bilateral certification | Rejected as an empirical gate design | MATR G3 passes from Reject-side decisions despite zero Certify; future gates must constrain each side separately |
| Pairwise domain separation is sufficient for composite certification | Rejected empirically at the registered Zhu resolution | K=4 min pairwise TV=0.25 while convex-hull Delta=0; post-hoc gap randomization p=0.0075 |
| Zhu K=8 establishes a positive absolute composite margin | Not established | Hull Delta=0.1786, but absolute-Delta permutation p=0.2234; K=8 is a sensitivity resolution |
| Zhu relaxation adds separation beyond a dimension-matched pipeline control | Not established | K=8 gain=0.0714 versus redundancy floor=0.1481; within-domain pairing p=0.398 |
| Zhu relaxation is an independent causal proxy | Not established | It is a non-derived measurement channel; conditional-independence/completeness assumptions were not tested |
| Zhu composite geometry is insensitive to low-support domains | Rejected as a finite-sample diagnostic | Removing one n=2 safe domain changes K=8 Delta from 0.1786 to 0.5178 |
| More chemistry-label-only samples can replace a measured diagnostic channel | Rejected for the registered constructive control | The implementation assigns one point mass per chemistry on both grades, so Delta=0 and optimal D=0.10 for every n; format/history fields were not observed |
| A low-stress active pulse opens a positive empirical certification frontier | Supported **only at registered SOC=5%** | 0.5C pulse Delta(1)=0.5273, D(1)=0.2517; stratified permutation p=0.001 and whole-battery bootstrap 95% CI [0.3455, 0.7227] |
| The SOC=5% 0.5C pulse is the globally preferred PulseBat experiment | Rejected | SOC=10% OCV has Delta(1)=0.6273, p=0.001 and CI [0.4455, 0.7980]; however its paired Delta advantage over the SOC=5% pulse is not established (difference CI [-0.1864, 0.3773]) |
| Greater diagnostic stress necessarily buys more certification information | Rejected at fixed SOC=5% | 0.5C, 1C and 1.5C pulses have the same worst-case frontier; 0.5C has lower incremental pulse time/amplitude |
| PulseBat validates nontrivial convex-hull geometry | Rejected | At every released menu and n, hull Delta equals the minimum chemistry-specific pairwise TV within 5.40e-9; Battery ALT and Zhu carry the nontrivial hull evidence |
| All 151 PulseBat batteries equally support the registered frontier | Rejected | The registered minimum is carried by 9 safe and 8 unsafe LFP35 batteries; deleting any decisive LMO10 battery leaves Delta unchanged |
| PulseBat establishes transported field-accident or arbitrary-policy causal certification | Not established | The endpoint is a registered capacity-margin qualification label, not accident truth or a randomized OTA-policy effect |
| Jones, MATR or Zhu validates arbitrary causal-policy certification | Not established | No arbitrary-policy ground truth or randomized causal identification in these external datasets |
| Physical procurement cost is measurable | Partially supported at fixed SOC | PulseBat registers incremental menu time/amplitude and independent batteries, but its cost ledger is not SOC-indexed and inconsistently treats conditioning stress; a cross-SOC physical Pareto claim is not established |
| The finite-sample bound holds when policy risk is identified by randomized load assignment | Supported on the registered NASA RW class | 11/11 n values; Delta rises 0.1494→0.5558 and the maximum Sion residual is 4.32e-8 |
| The collision bound can be attained by an engineering-plausible policy | Supported on the registered NASA RW class | Adversarial thermal derating gives Delta=0 and D=0.10=alpha+beta |
| Any unobserved confounding automatically creates a collision | Rejected on NASA RW | The preregistered naive confounding construction increases Delta from 0.0869 to 0.0953 |
| First-order convex-hull intersection is a permanent obstruction | Rejected empirically on Battery ALT | K=2 has Delta(1)=Delta(2)=0, no exact pairwise collision (min TV 0.00397), and n_star=3 |
| A theorem-valid evidence channel is necessarily empirically useful | Rejected | Battery ALT satisfies the structural gates, but reference-channel Delta(20) has permutation p=0.206 |
| Battery ALT identifies policy-switch risk | Not estimable | G0 fails: 83.7% of theta units cover one action bin, so the policy axis has no registered estimand |
| NASA RW protection intervention equals accident incidence | Rejected as a semantic interpretation | H records the 3.2 V protection cutoff (implemented as Vend<=3.25 V), not a field accident |
