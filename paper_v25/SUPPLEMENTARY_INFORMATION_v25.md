# Supplementary Information

## Finite-Evidence Limits for Causal Safety Certification in Battery Management Systems

### Guide to the supplementary material

Sections S1–S4 give the decision problem, proofs, LPs, and numerical checks. Section S5 reconstructs the NASA policy registry, quantifies uncertainty from missing and estimated stratum rates, and gives bounds for all eleven block lengths. Sections S6–S8 give the accelerated-life, PulseBat, Zhu, Jones, and MATR analyses. Section S9 describes the fixed-current replay, whole-cell transfer, and thermal stress test. Section S10 maps the claims to their source files. Sections S11 and S12 give policy-specific comparisons, continuous uncertainty calculations, matched baselines, dependence sensitivity, procurement bounds and the frozen-rule transfer audit. Section S13 tests a frozen capacity-screening rule on a CETL holdout and on an external public archive. Section S14 gives the Leaf workflow, local analysis chronology, visit-level denominators and donor-pack results.

## S0. Registered evidence modules

**Table S1. Registered evidence modules and claim boundaries.**

| Module | Physical units | Reference target | Candidate evidence | Theory object | Permitted interpretation |
|---|---:|---|---|---|---|
| NASA randomized usage | 28 cells, 513 grouped-policy stages | Standardized cutoff risk and separate fixed-current challenge | Cutoff alone or cutoff with current band | Completion bounds, confidence-protected decisiveness, transfer | Conditional on listed grades and sampling design |
| CETL and ReLiB | 4,000 source records; 6,909 external records | Capacity at least 10.85 Ah | Completed charge trace before reference discharge | Class-conditional acceptance and external transfer of a fixed rule | Held-out capacity decisions, measured workload in replay and external error counts |
| NASA/UCF accelerated life | 16 qualified packs | Surface-temperature event \(>70\,^{\circ}\mathrm C\) | 2.520-A reference-discharge channel | Finite-order intersection and \(n_\star\) | Independent structural replication; not an identified policy-switch experiment |
| PulseBat | 151 retired batteries; registered frontier carried by 17 LFP35 batteries | Full capacity calibration; SOH qualification | Chemistry-label control, OCV, 0.5C/1C/1.5C pulses over ten SOCs | Operating-condition-aware evidence frontier; fixed-SOC cost comparison | Pairwise-separable qualification instance; not nontrivial hull geometry, arbitrary OTA-policy, or field-accident certification |
| Zhu relaxation | 118 cells | Robust EOL@90 domain grades | Early summary and relaxation features | Pairwise versus hull geometry; pipeline controls | Methodological audit only |
| Jones EIS + MATR | 48 Jones cells; 124 MATR cells | External capacity or cycle-life grades | EIS/history and early voltage curves | Prediction versus transported bilateral certification | Transport boundary; no arbitrary causal-policy claim |

---

## S1. Formal setup and assumptions

### S1.1 Registered target and evidence experiment

For a fixed candidate battery-management policy \(\pi\), the registered policy risk is

\[
\Psi(\theta,\pi)
=
\int_{\mathcal Z_{\mathrm{op}}}
\sum_{a\in\mathcal A}\pi(a\mid z)
P_\theta\{H=1\mid Z=z,\operatorname{do}(A=a)\}
\,\mu_{\mathrm{op}}(\mathrm dz).
\tag{S1}
\]

Thresholds \(\tau_{\mathrm S}<\tau_{\mathrm U}\) divide the registered model class into safe, buffer, and unsafe regions. The buffer is a protected region; none of the extreme-class guarantees licenses automatic certification inside it.

A candidate evidence experiment is the complete acquisition specification

\[
\mathsf E=(\kappa_{\mathsf E},M_{\mathsf E}),
\tag{S2}
\]

where \(\kappa_{\mathsf E}\) contains the diagnostic action, operating condition, duration, preprocessing, quantizer, and independent sampling unit, and \(M_{\mathsf E}\) is the observation mechanism. In particular, changing SOC changes \(\mathsf E\); it is not merely a sensitivity variable outside the experiment.

**Standing assumptions.** Throughout this SI the evidence alphabet \(\mathcal X_{\mathsf E}\) is finite, \(\Theta_{\mathrm S}\) and \(\Theta_{\mathrm U}\) are nonempty compact subsets of the registered parameter space, and \(\theta\mapsto P_\theta^{\mathsf E}\) is continuous. These are the hypotheses of main-text Theorem 1; Sections S2.1 and S2.3 use them without further mention. Total variation is normalized as \(d_{\mathrm{TV}}(P,Q)=\sup_A|P(A)-Q(A)|=\tfrac12\|P-Q\|_1\), which is the objective of the program in Section S3.1.

For each fixed \(\theta\), the main theorem assumes conditionally i.i.d. evidence units with one-unit law \(P_\theta^{\mathsf E}\). The finite-sample upper bound can instead be applied to directly registered joint \(n\)-unit laws. The permanent-collision equivalence uses the fixed-model product laws at all orders. Under a mixture that draws one model for a whole sequence, the resulting unconditional sequence is exchangeable. General exchangeability alone does not give the fixed-model product structure used in the proof.

### S1.2 Composite families and decision rule

For \(j\in\{\mathrm S,\mathrm U\}\), define

\[
\mathcal K_j^{\mathsf E}(n)
=
\operatorname{co}\left\{
(P_\theta^{\mathsf E})^{\otimes n}:\theta\in\Theta_j
\right\}.
\tag{S3}
\]

The certification distance and gate are

\[
\Delta_{\mathsf E}(n)
=d_{\mathrm{TV}}\!\left(\mathcal K_{\mathrm S}^{\mathsf E}(n),
\mathcal K_{\mathrm U}^{\mathsf E}(n)\right),
\qquad
G_{\mathsf E}(n)=\mathbf1\{\Delta_{\mathsf E}(n)=0\}.
\tag{S4}
\]

An \(n\)-unit randomized rule outputs `Certify`, `Alert`, or `Reject` and must satisfy

\[
\sup_{\theta\in\Theta_{\mathrm U}}
P_\theta\{\Gamma_n=\textsf{Certify}\}\le\alpha,
\qquad
\sup_{\theta\in\Theta_{\mathrm S}}
P_\theta\{\Gamma_n=\textsf{Reject}\}\le\beta.
\tag{S5}
\]

Its worst-case extreme-class decisiveness is the probability of not returning `Alert`, optimized over all rules satisfying (S5):

\[
\mathcal D_{\alpha,\beta}(\mathsf E,n)
=
\sup_{\Gamma_n\ \mathrm{satisfies}\ (\mathrm{S5})}
\ \inf_{\theta\in\Theta_{\mathrm S}\cup\Theta_{\mathrm U}}
P_\theta\{\Gamma_n\ne\textsf{Alert}\}.
\tag{S5a}
\]

This is main-text (11); every proof below refers to this quantity.

---

## S2. Proofs

### S2.1 Finite-evidence upper bound and exact collision value

Compactness gives a closest pair

\[
P_\star\in\mathcal K_{\mathrm S}^{\mathsf E}(n),
\qquad
Q_\star\in\mathcal K_{\mathrm U}^{\mathsf E}(n),
\qquad
d_{\mathrm{TV}}(P_\star,Q_\star)=\Delta_{\mathsf E}(n).
\tag{S6}
\]

Write these distributions as mixtures of fixed-model product laws under safe and unsafe mixing measures \(\nu_{\mathrm S}\) and \(\nu_{\mathrm U}\). The side-error controls are preserved under mixing:

\[
Q_\star\{\Gamma_n=\textsf{Certify}\}\le\alpha,
\qquad
P_\star\{\Gamma_n=\textsf{Reject}\}\le\beta.
\tag{S7}
\]

Total variation gives

\[
P_\star\{\Gamma_n=\textsf{Certify}\}
\le
Q_\star\{\Gamma_n=\textsf{Certify}\}
+\Delta_{\mathsf E}(n).
\tag{S8}
\]

Therefore

\[
P_\star\{\Gamma_n\ne\textsf{Alert}\}
\le \alpha+\beta+\Delta_{\mathsf E}(n).
\tag{S9}
\]

The left side is an average of safe-model decisiveness probabilities under \(\nu_{\mathrm S}\), so at least one safe model has decisiveness no larger than the right side. Taking the worst model and then the best valid rule proves

\[
\mathcal D_{\alpha,\beta}(\mathsf E,n)
\le\min\{1,\alpha+\beta+\Delta_{\mathsf E}(n)\}.
\tag{S10}
\]

If the hulls intersect, choose \(P_\star=Q_\star\). When \(\alpha+\beta\le1\), the data-independent rule that outputs `Certify`, `Reject`, and `Alert` with probabilities \(\alpha\), \(\beta\), and \(1-\alpha-\beta\) is feasible and has decisiveness \(\alpha+\beta\) for every model. When \(\alpha+\beta>1\), choose any \(p\in[1-\beta,\alpha]\), output `Certify` with probability \(p\), and otherwise output `Reject`. Hence

\[
G_{\mathsf E}(n)=1
\Longrightarrow
\mathcal D_{\alpha,\beta}(\mathsf E,n)=\min\{1,\alpha+\beta\}.
\tag{S11}
\]

If a rule never outputs `Alert` on the two extreme classes, its decisiveness equals one. Substitution into (S10) gives the operational necessary condition

\[
\Delta_{\mathsf E}(N)\ge1-\alpha-\beta.
\tag{S12}
\]

This is a necessary condition for any no-Alert rule, not merely for the constructive rule used later.

### S2.2 Monotonicity and the gate dichotomy

Let \(M_n\) marginalize an \((n+1)\)-unit law to its first \(n\) units. For any \(P\in\mathcal K_{\mathrm S}(n+1)\) and \(Q\in\mathcal K_{\mathrm U}(n+1)\), their marginals lie in the corresponding \(n\)-unit hulls. Total-variation data processing gives

\[
\Delta_{\mathsf E}(n)
\le d_{\mathrm{TV}}(PM_n,QM_n)
\le d_{\mathrm{TV}}(P,Q).
\tag{S13}
\]

Taking the infimum proves \(\Delta(n+1)\ge\Delta(n)\), hence \(G(n+1)\le G(n)\). An \(n\)-unit rule can ignore an additional observation, so \(\mathcal D(n+1)\ge\mathcal D(n)\). Consequently, either \(G(n)=1\) for all \(n\), or there is a first finite \(n_\star\) after which \(G(n)=0\) permanently.

### S2.3 Permanent obstruction if and only if an exact collision exists

If a safe model and an unsafe model have the same one-unit law, their product laws coincide at every order, so every pair of hulls intersects.

For the converse, assume \(G(n)=1\) for every \(n\). For each \(n\), select safe and unsafe mixing measures satisfying

\[
\int(P_\theta^{\mathsf E})^{\otimes n}\nu_{\mathrm S,n}(\mathrm d\theta)
=
\int(P_\theta^{\mathsf E})^{\otimes n}\nu_{\mathrm U,n}(\mathrm d\theta).
\tag{S14}
\]

Compactness of the two parameter sets implies compactness of their probability-measure spaces. Along a common subsequence \(n_k\to\infty\), let the two mixing measures converge weakly to \(\nu_{\mathrm S}\) and \(\nu_{\mathrm U}\). For any fixed \(m\), marginalize (S14) to \(m\) coordinates and take the limit. Continuity gives equality of the two mixtures at every finite order.

Let \(T(\theta)=P_\theta^{\mathsf E}\) and let \(\mu_j=T_\#\nu_j\) be the pushforward measures on the simplex of one-unit laws. Equality at every order means that \(\mu_{\mathrm S}\) and \(\mu_{\mathrm U}\) generate the same exchangeable sequence law. Uniqueness of the de Finetti mixing measure on a finite alphabet implies

\[
\mu_{\mathrm S}=\mu_{\mathrm U}.
\tag{S15}
\]

This conclusion concerns pushforward measures; it does not require \(\nu_{\mathrm S}=\nu_{\mathrm U}\), because the parameterization need not be identifiable. The common pushforward is supported with probability one on both compact images \(T(\Theta_{\mathrm S})\) and \(T(\Theta_{\mathrm U})\). Their intersection is therefore nonempty, yielding a safe and unsafe parameter pair with the same one-unit evidence law.

### S2.4 Sion identity and constructive confidence rate

For fixed separable \(n\), let \(\mathcal F_n=[0,1]^{\mathcal X^n}\) and define \(\phi(f;P,Q)=E_Pf-E_Qf\). The function is bilinear and continuous on finite-dimensional compact convex sets. Sion's theorem gives

\[
\begin{aligned}
&\sup_{0\le f\le1}
\left[
\inf_{P\in\mathcal K_{\mathrm S}(n)}E_Pf
-\sup_{Q\in\mathcal K_{\mathrm U}(n)}E_Qf
\right]\\
&\quad=\inf_{P,Q}\sup_{0\le f\le1}(E_Pf-E_Qf)
=\inf_{P,Q}d_{\mathrm{TV}}(P,Q)
=\Delta_{\mathsf E}(n).
\end{aligned}
\tag{S16}
\]

Thus an optimal bounded separator \(f_n\) exists. If \(a_n\) is its smallest safe expectation and \(b_n\) its largest unsafe expectation, then \(a_n-b_n=\Delta(n)\). Thresholding the average of \(m\) independent block statistics at \((a_n+b_n)/2\) yields the symmetric margin

\[
\gamma_\star(n)=\frac{\Delta_{\mathsf E}(n)}2
\tag{S17}
\]

and both side errors are bounded by

\[
\exp\left[-\frac{m\Delta_{\mathsf E}(n)^2}{2}\right].
\tag{S18}
\]

The \(m\) blocks are independent under a fixed \(\theta\), which is exactly where the side-error constraints (S5) are imposed; under a composite mixture the blocks are exchangeable rather than independent, and (S18) is not claimed there.

For target side error \(\delta\), the constructive block count satisfies \(m\ge2\log(1/\delta)/\Delta(n)^2\), and the corresponding total physical units are

\[
N(n)=n\left\lceil\frac{2\log(1/\delta)}{\Delta_{\mathsf E}(n)^2}\right\rceil.
\tag{S19}
\]

The first separable block \(n_\star\) need not minimize (S19).

### S2.5 Finite-class stopping bound

Suppose the union of the two extreme classes contains \(r\) distinct one-unit laws \(R_1,\ldots,R_r\), with no cross-grade duplicate. If the \((r-1)\)-unit hulls intersect, there are nonzero signed coefficients \(c_1,\ldots,c_r\), positive on one side and negative on the other, satisfying

\[
\sum_{\ell=1}^r c_\ell R_\ell^{\otimes(r-1)}=0.
\tag{S20}
\]

Marginalization gives the same equality for orders \(k=0,\ldots,r-1\). Because the alphabet is finite and the laws are distinct, choose a bounded function \(h\) such that \(t_\ell=E_{R_\ell}h\) are pairwise distinct; this requires avoiding only finitely many hyperplanes. Integrating the product function \(\prod_{u=1}^kh(x_u)\) gives

\[
\sum_{\ell=1}^r c_\ell t_\ell^k=0,
\qquad k=0,\ldots,r-1.
\tag{S21}
\]

The associated Vandermonde matrix is invertible, so all \(c_\ell=0\), a contradiction. Therefore

\[
n_\star\le r-1\le M_{\mathrm S}+M_{\mathrm U}-1.
\tag{S22}
\]

This makes the structural dichotomy decidable for a finite registered class. It does not upper-bound the number of physical units needed for a confidence certificate.

### S2.6 Parameter-independent data processing

Let one unit of a derived experiment be generated from an original \(n\)-unit block by a \(\theta\)-independent Markov kernel \(K_n\). If \(R\) belongs to both original hulls, then \(RK_n\) belongs to both derived hulls because mixing commutes with the common kernel. Thus

\[
G_{\mathsf E}(n)=1\Longrightarrow G_{K_n\circ\mathsf E}(1)=1.
\tag{S23}
\]

The change from subscript \(n\) to 1 records consumption: one derived unit consumes an original \(n\)-unit block. Deterministic residuals, representations, uncertainty scores, and conformal scores computed solely from old evidence are covered. They may improve finite-sample estimation or implementation, but cannot repair a permanent cross-grade collision.

This is a population statement between nested experiments. Independently fitted PCA maps, separately optimized quantizers, or two unrelated feature pipelines do not automatically define a Blackwell chain. Empirical data-processing checks must use a strict coarsening of the same registered partition and a dimension-matched redundant control.

### S2.7 Buffer-zone protection

The decisiveness objective is defined only on \(\Theta_{\mathrm S}\cup\Theta_{\mathrm U}\). A rule that is decisive on both extreme classes has no automatic guarantee on \(\Theta_{\mathrm A}\). Production deployment must therefore distinguish evidence-driven `Alert` from buffer-protection `Alert`; closing the structural gate on the extremes does not justify eliminating the buffer.

---

## S3. Computation and uncertainty

### S3.1 Hull-distance linear program

For finite safe and unsafe collections with \(n\)-unit mass functions \(p_i^{(n)}(x)\) and \(q_j^{(n)}(x)\), introduce mixture weights \(\lambda\), \(\mu\) and nonnegative residual variables \(t_x\). Solve

\[
\min_{\lambda,\mu,t}\frac12\sum_x t_x
\tag{S24}
\]

subject to

\[
-t_x\le\sum_i\lambda_i p_i^{(n)}(x)-\sum_j\mu_jq_j^{(n)}(x)\le t_x,
\quad
\lambda,\mu\text{ in probability simplices}.
\tag{S25}
\]

The objective is \(\Delta_{\mathsf E}(n)\); the dual provides the bounded separator in (S16). Direct enumeration grows as \(|\mathcal X|^n\). Whenever the evidence law is multinomial, the released code uses count vectors as sufficient statistics; the reduction is cross-checked against full sequence enumeration at small \(n\) in Section S3.5.

### S3.2 Exact three-state decisiveness program

For each evidence state \(x\), let \(c_x\) and \(r_x\) be the probabilities of `Certify` and `Reject`, with \(0\le c_x,r_x\) and \(c_x+r_x\le1\). Add the two side-error constraints for every registered extreme model and maximize \(t\) subject to

\[
\sum_xP_\theta(x)(c_x+r_x)\ge t
\quad\text{for every }\theta\in\Theta_{\mathrm S}\cup\Theta_{\mathrm U}.
\tag{S26}
\]

The optimum is \(\mathcal D_{\alpha,\beta}(\mathsf E,n)\). The hull-distance and decisiveness LPs are distinct implementations; agreement with the theorem is therefore not a same-code identity.

### S3.3 Finite-battery uncertainty

Let \(\mathcal C_{\theta,\eta}\) be simultaneous confidence sets for all registered evidence laws. A conservative certificate is

\[
\underline\Delta_{\mathsf E,\eta}(n)
=
\inf_{\widetilde P_\theta\in\mathcal C_{\theta,\eta}}
\Delta_{\mathsf E}\!\left(n;\{\widetilde P_\theta\}\right).
\tag{S27}
\]

On the simultaneous-coverage event the true distance is at least the value in (S27). Sections S5 and S9 evaluate both geometric separation and decision rules on uncertainty-expanded families. Permutation tests assess association under their respective label-exchangeability nulls.

**Why a robust distance is not yet a robust rule.** (S27) is a statement about geometry: every admissible configuration of the registered laws has composite separation at least \(\underline\Delta_{\mathsf E,\eta}(n)\). Procurement feasibility, main-text (23), instead requires one deployable rule that stays admissible whatever the truth is. These are different quantifier orders, and the first does not imply the second: the configuration attaining the infimum in (S27) and the rule attaining \(\mathcal D_{\alpha,\beta}\) at that configuration need not be admissible at any other configuration. Main-text (19)-(20) therefore define the confidence-protected decisiveness \(\underline{\mathcal D}_{\alpha,\beta,\eta}\) directly, as a \(\sup_\Gamma\inf_P\) over rules whose two side errors hold uniformly on the uncertainty-expanded families. The definition has three properties.

*Ordering.* Every \(\Gamma\in\mathfrak G_{\alpha,\beta,\eta}\) is in particular admissible at the true configuration, and the infimum in main-text (20) runs over a superset of the true block laws, so on the simultaneous-coverage event

\[
\underline{\mathcal D}_{\alpha,\beta,\eta}(\mathsf E,n)
\le
\mathcal D_{\alpha,\beta}(\mathsf E,n)
\le
\min\{1,\alpha+\beta+\Delta_{\mathsf E}(n)\}.
\tag{S28}
\]

The left quantity is what procurement may promise; the right is what the population theorem permits. Reporting the second where the first is required is the error main-text (20) exists to prevent.

*Finiteness at one unit.* For \(n=1\) the maps \(P\mapsto P\{\Gamma=\texttt{Certify}\}\) and \(P\mapsto P\{\Gamma=\texttt{Reject}\}\) are linear. If each \(\mathcal C_{\theta,\eta}\) is a polytope—as for the \(\ell_1\) and simultaneous-multinomial sets this formulation admits—every uniform side constraint is attained at a vertex, so main-text (20) is a finite linear program in the \(2|\mathcal X_{\mathsf E}|\) rule variables, with one constraint per vertex per registered model.

*Conservative relaxation above one unit.* At \(n>1\), the convex hull of product laws at confidence-polytope vertices can omit product laws at interior points. Using only those vertices relaxes the rule constraints. An outer approximation follows from \(d_{\rm TV}(P^{\otimes n},Q^{\otimes n})\le n\,d_{\rm TV}(P,Q)\). Section S5 uses tighter, channel-specific outer and inner problems to establish the reported bounds.

The point-law kernel implements Sections S3.1–S3.2. The NASA supplement implements the expanded-family programs and the separate chronological replay.

### S3.4 Numerical tolerances

All primary LPs use the released SciPy/HiGHS configuration. Gate decisions use the tolerances frozen in the corresponding configuration or documented correction ledger. Sion residuals are reported as numerical identities, not statistical tests. The top-level repository manifest protects released artifacts byte-for-byte; subexperiment manifests preserve their own frozen scopes.

### S3.5 Kernel implementation, cost, and validation

The point-law separation and decision kernel used within the main-text workflow is released as the MIT-licensed package named in Data and Code Availability. Its inputs are the registered point laws and block length. It screens for an identical cross-grade pair, enumerates count states, lifts each law to the block level and then solves the separation and decision programs. To find the first separating order, it increments the block length up to the finite-class ceiling when computationally feasible. The package supplement implements the rectangle step of Algorithm 1. This section records what it costs to run, which constants govern its verdicts, and what has been checked. All timings below come from one commodity core of a containerized cloud host and are reported to fix orders of magnitude, not as a hardware benchmark.

**Sufficient-statistic reduction.** For a multinomial evidence law the count vector is sufficient, so the kernel enumerates \(\binom{n+K-1}{K-1}\) states rather than \(K^n\) sequences. At \(K=8,n=10\) this is 19,448 states instead of \(1.07\times10^{9}\) sequences. The reduction is exact rather than an approximation, and was checked against the definition it optimizes: on 40 randomized instances with \(K\le3,n\le5\), the hull distance computed on count states and on brute-force enumeration of all \(K^n\) sequences agreed to within \(10^{-9}\) on every instance. States are enumerated so that \(n=1\) reproduces the symbol order, checked for \(K=2,\dots,8\); every other block length carries its own ordering, so block-space vectors must be indexed through the returned state array rather than assumed to align with symbols. Indexing block-space vectors positionally instead silently transposes separator verdicts at \(n=1\).

**Cost and the dual fast path.** \(\Delta_{\mathsf E}(n)\) is obtained from the bounded separation game, whose value equals the primal hull distance by the Sion identity (S16)-(S17). The two are not interchangeable numerically. One measurement per row, on one instance, on one host:

**Table S2. Single-solve cost of the primal and dual programs.** One measurement per row, one instance, one host.

| \(K\) | \(n\) | states | primal (s) | dual (s) | speedup |
|---|---|---|---|---|---|
| 3 | 60 | 1,891 | 0.058 | 0.010 | 6x |
| 4 | 30 | 5,456 | 0.607 | 0.031 | 20x |
| 6 | 15 | 15,504 | 6.455 | 0.115 | 56x |
| 8 | 10 | 19,448 | 36.436 | 0.211 | 172x |

These ratios indicate scale, not a guarantee. Solve time is strongly instance-dependent: repeating the \(K=4,n=30\) row on three further random law sets of the same size gave primal times of 0.50, 0.74 and 1.08 s, and an independent re-run of the whole table on a differently loaded host reproduced the ordering but not the ratios. What is structural is the direction and its growth: the primal (S24)-(S25) carries one residual variable and two inequalities per state, so both its variable and its constraint count grow with \(|\mathcal X|\), whereas the dual carries \(|\mathcal X|+2\) variables against only one inequality per registered model, and it was faster on every instance measured.

Agreement between the two was measured on 57 randomized instances: median discrepancy \(2.6\times10^{-9}\), worst \(3.1\times10^{-7}\). No monotone relation to state count was observed — the worst case occurred at 1,891 states while several instances above 15,000 states agreed to \(10^{-8}\) — so the discrepancy is not predictable from problem size, and any dual value below \(\tau_{\mathrm{d}}=10^{-5}\) is discarded and re-solved with the primal program. That floor is roughly thirty times the worst observed discrepancy and applies exactly where the gate verdict \(G_{\mathsf E}(n)=\mathbf 1\{\Delta\le\tau_0\}\) is decided; away from zero the dual value is used directly. Forcing the primal everywhere is available and is what the released frontier scripts use for the final tabulated points.

Vectorizing the constraint assembly gives a speedup of 1.0x: the cost is in the solve, not in building the matrices, which is why the dual formulation rather than a faster encoding of the primal is what buys the margin.

**Constants.** Values at or below \(\tau_0=10^{-9}\) are treated as exactly zero throughout; a single tolerance governs every gate decision. The enumeration ceiling \(\Sigma_{\max}=20{,}000\) is a **time** budget, not a memory one: the table above reaches 36 s of primal solve just below it, on a program whose memory footprint is unremarkable. No measurement above the ceiling is reported here, and the instance dependence above means that no ceiling expressed in states can be a reliable time guarantee; the constant is set where an overrun costs minutes rather than the hours that larger state spaces have been observed to take. A ceiling chosen from memory alone would admit jobs that run far longer than any interactive use allows.

**Stopping and the four regions.** For a finite registered class with \(r\) distinct one-unit laws and no exact cross-grade collision, Corollary 1 gives \(n_\star\le r-1\), which the kernel uses as an exhaustive search ceiling. This bounds the *structural* search only. It is not a sample-size formula: the number of physical units needed for the confidence statement (S27) is a separate and generally much larger quantity, and the two must not be reported together as though one implied the other.

The search returns one of four labels. `immediate` and `delayed` correspond to \(n_\star=1\) and \(1<n_\star\le r-1\). `permanent` is returned only from the step-1 exact-collision screen, which is the condition Theorem 1(3) actually requires; hull intersection at some \(n\) is not sufficient and does not license it. `undetermined` is returned when the enumeration exhausts \(\Sigma_{\max}\) before the gate opens. The distinction between the last two is not cosmetic: `permanent` instructs a program to abandon a measurement channel, `undetermined` instructs it to coarsen the alphabet or spend more computation, and collapsing the second into the first converts a solvable budget problem into a false claim about the physics.

**Registered classes of individual units.** The exact-collision screen is a statement about registered laws. If each registered model is one physical unit rather than a cohort, two units can produce identical histograms by chance on a small alphabet with few draws, which is an exact collision by definition and would be reported as a permanent obstruction. The kernel therefore reports which models collide, and — when the experiment was registered from raw counts rather than from laws, and every colliding pair has bitwise identical counts — flags the collision as a possible finite-sample coincidence rather than a structural finding. A mixed case, in which only some colliding pairs are raw-count ties, does not raise the flag. Resolving it is a registration decision — cohorts rather than units, or a finer alphabet — and is not decidable from the geometry.

**Validation.** The hull-distance and three-state programs are separate implementations, so their agreement with main-text (12) is a genuine check. On 600 randomized instances spanning \(K\in\{2,3,4\}\), \(n\in\{1,\dots,4\}\) and \(\alpha,\beta\in(0.01,0.2)\), the certification bound was never violated; the largest excess of \(\mathcal D_{\alpha,\beta}\) over \(\min\{1,\alpha+\beta+\Delta\}\) was \(1.4\times10^{-16}\), at floating-point noise. The released package carries 68 regression tests, of which 29 lock the failure modes identified in an adversarial audit of the kernel, so that a repaired failure mode reappears as a test failure rather than as a wrong number.

---

## S4. Synthetic proof companion

### S4.1 Exact causal collision and policy reversal

Let \(q\in(0,1/2)\) and \(r=(1-\sqrt{1-2q})/2\), so \(2r(1-r)=q\). In the direct-effect world,

\[
A\sim\mathrm{Bernoulli}(1/2),\qquad H=A\oplus E,\quad E\sim\mathrm{Bernoulli}(q).
\tag{S29}
\]

In the hidden-common-cause world,

\[
U\sim\mathrm{Bernoulli}(1/2),\quad
A=U\oplus E_A,\quad H=U\oplus E_H,
\quad E_A,E_H\stackrel{\mathrm{iid}}{\sim}\mathrm{Bernoulli}(r).
\tag{S30}
\]

Both worlds have

\[
P(A=a,H=h)=
\begin{cases}
(1-q)/2,&a=h,\\
q/2,&a\ne h,
\end{cases}
\tag{S31}
\]

but their interventional risks differ:

\[
P_{\mathrm D}(H=1\mid\operatorname{do}(A=a))=q+(1-2q)a,
\qquad
P_{\mathrm H}(H=1\mid\operatorname{do}(A=a))=1/2.
\tag{S32}
\]

The constant policy \(A=1\) makes the direct-effect world more hazardous, while \(A=0\) reverses the grade ordering. Hence collision is policy-specific; it is not equivalent to the presence or direction of confounding.

### S4.2 Synthetic numerical gates

The released synthetic package verifies exact observational collision, policy reversal, data processing, independent-proxy breakage, LP primal–dual agreement, and Monte Carlo calibration. For its finite composite example:

- \(\Delta(1)=0\), \(\Delta(2)=0.125\), and \(n_\star=2\);
- the no-Alert necessary threshold at \(\alpha=\beta=0.05\) is first met at \(N=47\), while the exact three-state LP first reaches decisiveness one at \(N=48\);
- the first Hoeffding-optimal block is \(n=14\), tied in total cost with \(n=19\), at \(N=266\);
- count-space and full \(2^n\)-sequence LPs agree through \(n=8\) to floating-point tolerance.

These values separate three concepts: the structural gate \(n_\star\), the unrestricted necessary/sufficient no-Alert sample threshold, and the conservative constructive sample size.

---

## S5. NASA grouped policies and uncertainty in the certification frontier

### S5.1 Sampling, weights and grade assignment

The released step table contains 389,307 rows from 28 cells in seven bench arms. The grouped-policy reconstruction retains 366,464 rows after the original eligibility filters. A stage between reference discharges of a cell requires at least 150 eligible steps. The first recorded step voltage is divided at 3.55, 3.70 and 3.85 V, with an upper inclusion limit of 4.0 V. The median discharge current is rounded to the nearest integer (ties to even), clipped to 1–5 and restricted to groups 1–4. This coarsening can put different physical settings in the same group. The exact intervention interpretation requires the starting-voltage state to precede the action and the distribution of physical settings within each group to be specified. Section S9 uses prior-step voltage and two specified load settings.

The target weights are \(w_{za}=\mu_z\pi_a\), with \(\mu\) the empirical voltage-bin frequencies in the uniform arms. The policy vectors, in ascending current-group order, are (0.25, 0.25, 0.25, 0.25), (0.05, 0.20, 0.15, 0.60), and (0.25, 0.60, 0.10, 0.05). The endpoint is \(H=1\) when terminal voltage is at most 3.25 V. Let \(C\) be the strata with at least five recorded steps, \(r_{za}\) their empirical event frequencies, and \(m\) the total target weight outside \(C\). Holding observed rates fixed gives

\[
L=\sum_{(z,a)\in C}w_{za}r_{za},\qquad
m=\sum_{(z,a)\notin C}w_{za},\qquad
\Psi\in[L,L+m].
\tag{S33}
\]

A model is safe if \(L+m\le0.15\), unsafe if \(L\ge0.35\), and otherwise unresolved. The 1,539 combinations of cell, stage and policy yield 443 safe and 528 unsafe models. Of 738 models graded safe by the observed-risk sum alone, 295 can exceed the safe threshold, including 16 that can reach the unsafe threshold. For example, RW17, stage 19, uniform policy gives \(L=0.1426\), \(m=0.3494\), and upper risk 0.4920. These are ranges over completions conditional on empirical rates; statistical uncertainty is addressed in S5.3.

### S5.2 Matched-channel comparison and numerical bounds

Both channels observe \(H\). Each uses a common lookup across the three policies, without the policy index as an input. The richer one also records whether the current belongs to group 3 or 4. Let \(q\) be the policy mass on these groups and \(t_0,t_1\) the joint probabilities of cutoff at low and high current. The single-draw probability vector, in the order low/no cutoff, low/cutoff, high/no cutoff, high/cutoff, is

\[
p=(1-q-t_0,\ t_0,\ q-t_1,\ t_1).
\tag{S34}
\]

The weighted mass of missing strata in each band gives an interval for each \(t_j\). These two intervals form a rectangle; \(t_0+t_1\) is the same risk used in grading. The safe and unsafe reference thresholds imply a one-draw TV distance of at least 0.20 for every pair of opposite-grade mixtures. The expanded-hull LP gives 0.201005.

For a count-only block, all admissible laws are binomial with rates in the corresponding risk intervals. Evaluating just the interval endpoints gives an upper bound on optimal decisiveness. For an outer bound on the family of block laws, enclose each grade by its smallest and largest rate, \(l,u\). For \(p=(1-x)l+xu\), the binomial law at \(p\) is a Bernstein-weighted mixture of \(n+1\) laws. Its \(k\)th component is the convolution of binomials with parameters \((k,u)\) and \((n-k,l)\). A rule admissible for all these components supplies a lower bound on attainable decisiveness. Upper and lower optima agree numerically at all eleven block lengths.

For four symbols the one-draw rectangle vertices suffice. At higher orders a subset of admissible stationary product laws gives upper bounds. At \(n=2,5\) a grid of five positions per coordinate is used for each registered rectangle. For a lookup valued in \([0,1]\), the pure second derivative of its \(n\)-draw expectation along either coordinate is bounded by \(2n(n-1)\). Bilinear interpolation on a rectangle of side lengths \(h_0,h_1\) then incurs error at most \(n(n-1)(h_0^2+h_1^2)/4\). Adding this slack to side errors and subtracting it from decisiveness gives a feasible lower-bound rule. A second feasible rule ignores the current band. The stronger lower bound is reported. For other block lengths a subset of boundary laws suffices for a valid upper bound. The reported widths describe optimization envelopes, not sampling intervals. At five draws the tensor calculation in S11 matches the stationary-grid upper bound. Values are rounded; the five-draw increment is 0.080840 percentage points to six decimals.

**Table S3. Worst-case decisiveness and incremental value of the current band. Sufficiently sampled rates are fixed; missing strata can take any admissible event rate.**

| Draws | Count D (%) | Full D, lower (%) | Full D, upper (%) | Gain ceiling (pp) |
| --- | --- | --- | --- | --- |
| 1 | 11.547 | 11.548 | 11.548 | 0.0017 |
| 2 | 13.571 | 13.571 | 13.578 | 0.0065 |
| 3 | 16.223 | 16.223 | 16.253 | 0.0308 |
| 4 | 19.694 | 19.694 | 19.749 | 0.0553 |
| 5 | 24.238 | 24.319 | 24.319 | 0.0808 |
| 6 | 30.189 | 30.189 | 30.471 | 0.2820 |
| 8 | 37.461 | 37.461 | 38.738 | 1.2767 |
| 10 | 42.437 | 42.437 | 45.637 | 3.1995 |
| 12 | 51.541 | 51.541 | 53.240 | 1.6985 |
| 15 | 58.757 | 58.757 | 63.001 | 4.2439 |
| 20 | 71.361 | 71.361 | 74.726 | 3.3651 |

For the association check, retain common stage numbers within each arm and temperature pair (1,008 model rows). Permute the four entire cell profiles within each group, keeping each cell's stages and policies together. The observed one-draw hull distance under midpoint completion is 0.214045; none of 500 random permutations reaches it (one-sided \(p=1/501\)). The grades and the evidence share the cutoff indicator. The separate-record association check appears in S9.1.

### S5.3 Simultaneous grading and one admissible rule

For a stratum with \(y\) events in \(N\) visits, invert the beta-mixture likelihood ratio with mixing distribution Beta(1/2,1/2). At a candidate rate \(p\) the ratio is

\[
M_N(p)=\frac{B(y+1/2,N-y+1/2)}
 {B(1/2,1/2)\,p^y(1-p)^{N-y}} .
\tag{S35}
\]

The error allocated to stratum \(j\) in stage \(s\ge0\) of a cell is \(0.05/[28K(s+1)(s+2)]\), where \(K=16\) counts voltage-current strata here. Retain rates satisfying \(M_N(p)\le1/\eta_{sj}\), where \(\eta_{sj}\) is that allocation. A stratum with fewer than five observations retains the full interval. Ville's inequality and the summable stage allocation give simultaneous coverage under a fixed conditional event rate within each stratum, with visit membership determined before its outcome. Risk intervals and evidence rectangles use the same component intervals. The coverage statement pertains to the measured protocol, including the realized target weights.

This construction retains 26 safe models from eight cells and 250 unsafe models from four cells; 1,263 combinations are withheld. At one draw the protected distance is 0.201053 and one admissible lookup attains 0.115549 decisiveness. Table S9 gives the full confidence-protected grid, with the five-draw optimum tightened in S11. As a sensitivity calculation, fixed-design weighted Hoeffding margins retain 127 safe and 368 unsafe models; these counts use different sampling assumptions.

## S6. Main experiment 2: NASA/UCF accelerated life

### S6.1 Scope

Sixteen packs with at least 15 valid reference segments were retained. The reference channel is a constant-current discharge measured at \(2.520\pm0.001\) A. The endpoint is a physical surface-temperature event above 70 °C. This dataset supplies independent structural replication, not an identified policy-switch experiment: load is assigned at pack or pack-stage level, and 83.7% of the resulting units cover only one action level.

### S6.2 Gate closure and channel refinement

**Table S4. Structural gate by quantizer resolution.**

| Resolution | \(\Delta(1)\) | \(\Delta(2)\) | \(\Delta(3)\) | Minimum pairwise TV at \(n=1\) | \(n_\star\) |
|---:|---:|---:|---:|---:|---:|
| \(K=2\) | 0 | 0 | 0.0000355 | 0.003968 | 3 |
| \(K=4\) | 0 | 0.065370 | 0.120908 | 0.113636 | 2 |
| \(K=8\) | 0.045406 | 0.108597 | 0.156044 | 0.121377 | 1 |

Across 30 evaluated \((K,n)\) points, the theorem bound is never exceeded; the maximum apparent excess is \(-1.4\times10^{-17}\), and the maximum Sion residual is \(5.02\times10^{-8}\). Strictly nested coarsening satisfies \(\Delta_{K=2}\le\Delta_{K=4}\le\Delta_{K=8}\) wherever the common grid is evaluated.

The coarsest channel gives the empirical nontrivial branch: two low-order hull intersections occur despite positive minimum pairwise TV, and the gate closes at \(n=3\). The separate pack-block grade-association calibration yields \(p=0.206\). Therefore the channel is valid as a structural example but is not claimed to be a useful deployment diagnostic.

### S6.3 Protocol corrections

The registered text incorrectly described the monotonic direction of \(\Delta\) and \(\mathcal D\), and its numerical Sion tolerance was tighter than solver feasibility. Both defects are preserved in the errata ledger; corrected analyses do not overwrite the registered artifact. The policy-switch feasibility gate remains failed rather than being repaired retrospectively.

---

## S7. Main experiment 3: PulseBat operating-condition-aware procurement

### S7.1 Registered and corrected scopes

PulseBat contains 151 retired batteries measured at ten SOCs. Full capacity calibration defines qualification: SOH \(\ge0.90\) is qualified, SOH \(\le0.80\) is unqualified, and the middle range is buffered. The original SOC=5% analysis was locked after a feasibility probe, not preregistered. It selected LMO10 and LFP35, the SOH thresholds, quantizer correction, and the numerical gates \(\Delta(1)\ge0.40\) and bootstrap lower bound above 0.25. NMC21 was excluded using grade composition because it supplied only one unqualified battery.

The released observations contain chemistry and nominal capacity but no physical-format or historical-use fields. The implemented baseline is therefore a chemistry-label-only point mass. It is retained as a constructive collision control, not described as measured nameplate/history evidence.

### S7.2 SOC by evidence-menu grid

The correction evaluates all 40 combinations using 999 chemistry-stratified permutations and 2000 whole-battery bootstrap replicates at each point.

**Table S5. Point estimates \(\Delta(1)\) over the complete acquisition grid.** Asterisks denote permutation \(p\le0.05\).

| SOC (%) | OCV | 0.5C pulse | 1C pulse | 1.5C pulse |
|---:|---:|---:|---:|---:|
| 5 | 0.1455 | 0.5273* | 0.5273* | 0.5273* |
| 10 | 0.6273* | 0.6273* | 0.6273* | 0.6196* |
| 15 | 0.4136* | 0.5809* | 0.5496* | 0.4522* |
| 20 | 0.4455* | 0.5093* | 0.4559* | 0.3346* |
| 25 | 0.2682 | 0.3033* | 0.3024* | 0.2996 |
| 30 | 0.5273* | 0.2721 | 0.2096 | 0.2132 |
| 35 | 0.5273* | 0.1820 | 0.2445 | 0.3061* |
| 40 | 0.2364 | 0.2445 | 0.2757* | 0.3695* |
| 45 | 0.5182* | 0.4596* | 0.4908* | 0.5563* |
| 50 | 0.6045* | 0.4908* | 0.5221* | 0.5733* |

**Table S6. Uncertainty at the two emphasized acquisition points.**

| Point | \(\Delta(1)\) | Permutation \(p\) | Whole-battery bootstrap 95% interval |
|---|---:|---:|---:|
| Registered SOC=5%, 0.5C pulse | 0.5273 | 0.001 | [0.3455, 0.7227] |
| Diagnostic SOC=10%, passive OCV | 0.6273 | 0.001 | [0.4455, 0.7980] |

The paired whole-battery contrast, SOC10 OCV minus SOC5 0.5C pulse, has observed difference 0.1000 and bootstrap interval \([-0.1864,0.3773]\). Thus both points have positive evidence frontiers, but superiority of the passive point over the pulse is not established.

### S7.3 Pairwise degeneration and load-bearing cohort

For every released PulseBat menu and registered \(n\), convex-hull distance equals the smaller chemistry-specific pairwise TV to within \(5.40\times10^{-9}\). The disjoint chemistry encoding prevents nontrivial cross-chemistry mixing; PulseBat is therefore a pairwise-separable procurement instance, not an instantiation of composite-hull effects.

The grade counts for the two retained chemistries are:

**Table S7. PulseBat grade counts for the two retained chemistries.**

| Chemistry | Qualified | Unqualified |
|---|---:|---:|
| LMO10 | 15 | 30 |
| LFP35 | 9 | 8 |

At the registered point, the smaller separation is carried by the 17 LFP35 batteries. Deleting any of the 45 decisive LMO10 units leaves \(\Delta(1)\) unchanged; LFP35 leave-one-out values range from 0.5000 to 0.6162. The number 151 describes the measured cohort, not the effective worst-case support.

### S7.4 Cost-ledger restriction

The frozen ledger is comparable among menus at SOC=5%, where 0.5C, 1C, and 1.5C have the same registered distance and the smallest pulse has lower incremental excitation. It is not auditable across SOC: elapsed time includes conditioning, whereas peak C-rate is indexed only by diagnostic menu and records OCV as zero stress. Conditioning energy, conditioning peak stress, labor, and site cost are not registered per SOC. Therefore no cross-SOC physical-Pareto dominance is claimed.

---

## S8. Boundary calibration experiments

### S8.1 Zhu voltage relaxation: composite geometry and pipeline controls

The Zhu data are used as a diagnostic geometry audit. At the frozen \(K=4\) resolution,

\[
d_{\mathrm{pair}}=0.2500,
\qquad
\Delta=0.
\tag{S36}
\]

At \(K=8\), the minimum pairwise TV is 0.4286 and hull distance is 0.1786; the latter does not exceed its label-permutation null (\(p=0.2234\)). Removing one low-support safe domain changes \(\Delta\) from 0.1786 to 0.5178, demonstrating sensitivity of a composite minimum to registration support.

Adding relaxation to the baseline increases the plug-in distance by 0.0714, while a dimension-matched redundant menu produces a 0.1481 floor with null standard deviation 0.0596. The relaxation increment is therefore not established beyond pipeline dimension. Independently fitted quantizers also produce an apparent data-processing reversal; the reversal disappears when the coarse partition is a strict merge of the fine partition. None of these results supports a useful relaxation-channel claim.

### S8.2 Jones EIS: corrected diagnostic transport audit

All Jones quantities reported here come from the method-corrected diagnostic rerun, not a new preregistered confirmation. Adding EIS to action features reduces cross-temperature capacity RMSE from 0.212 to 0.103. The same-seed paired improvement over permuted EIS is 0.00938 with 95% interval \([0.00186,0.01628]\). However, adding EIS to long history reduces external AUC by 0.117 and raises unsafe-to-`Certify` error from 0.509 to 0.521.

The corrected analysis uses paired split differences, not a difference between separately selected medians. A former narrow AUC pass becomes a fail under the paired definition. The source baseline's collapsed thresholds are not treated as a valid three-state decisiveness comparison. These corrections are preserved as diagnostic history.

### S8.3 Severson/MATR: corrected diagnostic transport audit

The registered Curve-5 permutation gate fails with \(p=0.373\); the registered transport-calibration gate also fails, and the overall registered verdict is `FAIL`. A later Curve-100 diagnostic gives external MAPE 25.8% compared with 42.9% for a scalar summary and beats its paired curve-permutation control with \(p=0.005\). However, Curve-100 external interval coverage is 37.5%, the best menu coverage is 57.5%, and all registered menus issue zero positive `Certify` decisions on the locked external batch.

This experiment therefore supports only the boundary statement that prediction gain and bilateral transported certification are different objects.

### S8.4 Claims prohibited by the boundary audits

**Table S8. Claims prohibited by the boundary audits.**

| Observation | Supported boundary | Prohibited interpretation |
|---|---|---|
| Zhu \(d_{\mathrm{pair}}>0\), \(\Delta=0\) | Pairwise separation can overstate composite certifiability | Relaxation is an established causal proxy |
| Redundant floor exceeds relaxation increment | Finite-sample pipelines require matched redundancy controls | Added dimensions create population information |
| Jones RMSE improves while unsafe certification rises | Prediction and bilateral certification can move oppositely | EIS is generally harmful or useless |
| MATR Curve-100 predicts better but does not certify | Source predictive uncertainty does not automatically transport | Voltage curves lack lifetime information |

---

## S9. Decision under confidence, physical replay, and transport

**Table S9. Decisiveness on the 276 confidence-graded models in S5.3. Both side-error budgets are 0.05; values are percentages.**

| Draws | Count D (%) | Full D, lower (%) | Full D, upper (%) |
| --- | --- | --- | --- |
| 1 | 11.542 | 11.555 | 11.555 |
| 2 | 13.561 | 13.561 | 13.594 |
| 3 | 16.202 | 16.202 | 16.267 |
| 4 | 19.657 | 19.657 | 19.771 |
| 5 | 24.179 | 24.367 | 24.367 |
| 6 | 30.096 | 30.096 | 30.392 |
| 8 | 37.408 | 37.408 | 40.683 |
| 10 | 42.323 | 42.323 | 45.528 |
| 12 | 51.477 | 51.477 | 54.153 |
| 15 | 58.569 | 58.569 | 61.618 |
| 20 | 71.282 | 71.282 | 74.224 |

### S9.1 Disjoint reference and replay measurements

The physical challenge uses nominal 1.5-A and 3.0-A settings, accepting measured median currents within 0.06 A. Context is the preceding recorded discharge's terminal voltage in the same cell and aging stage, split at 3.55 V. Each of the four context-current combinations has target weight one quarter. For stages of at least 150 original steps, consecutive 25-record chunks are allocated alternately to reference and replay. Each chunk's first observation is excluded so its context cannot cross the split. The reference and replay halves are interleaved in time and can share a latent degradation state. The endpoint is the cutoff termination defined in S5.1.

Reference grades follow (S33) with four equally weighted strata. Among 529 eligible stages, 210 are safe, 133 unsafe and 186 unresolved at fixed observed rates. The stage-level simultaneous procedure in S5.3 with \(K=4\) leaves all 529 unresolved. A less conservative fixed-design sensitivity retains 10 safe and 34 unsafe. The replay comparisons below use grades protected against missing strata only. For the separate association check, 246 stages in 27 cells have at least five records per stratum in each half. Equal-stage cell summaries of reference and replay cutoff rates, centered within bench arm and temperature, have correlation 0.927. Permuting the cell summaries within arm yields one-sided \(p=0.0007\) in 9,999 draws.

The two lowest-numbered cells in each of seven arms train one lookup; the other 14 cells test it. In training, the action-stratified lookup uses the pair of low-current and high-current cutoff counts. The comparator uses their sum. Conditional stratum frequencies define product laws on training stages with adequate replay support. In testing, one or two distinct readings per stratum produce blocks of four or eight. Readings are matched by chronological rank within stratum, excluding leftovers; block sizes reuse the inputs in separate analyses. Each method sees identical blocks. Reported probabilities average the randomized lookup entries, first across blocks within a stage, then across stages and contributing cells with equal weights. Safe rejection and unsafe approval are unconditional on issuing a decision.

**Table S10. Four-measurement held-out replay. Entries are percentages; 13 cells provide 102 safe stages (1,828 blocks) and two cells provide 62 unsafe stages (277 blocks). Cell memberships can overlap.**

| Rule | Safe decisive | Unsafe decisive | Safe reject | Unsafe approve |
| --- | --- | --- | --- | --- |
| Cutoff count | 18.43 | 29.60 | 0.530 | 3.610 |
| Current + cutoff | 18.48 | 14.63 | 0.526 | 0.325 |
| Current + cutoff, tie-break | 19.10 | 62.06 | 0.985 | 0.294 |
| Mean-only | 11.54 | 11.54 | 4.286 | 2.840 |

The mean-only rule assumes only that the mean cutoff fraction is bounded by the reference grade thresholds on the challenge; it interpolates a two-outcome rule linearly in the observed fraction. It allows arbitrary dependence inside a block. Across all 28 leave-one-cell-out folds the standard action-stratified rule has 11.02% unsafe-stage decisiveness and 4.75% unsafe approval. These folds test transfer of the fitting procedure. Only the 14-cell holdout applies one common fitted lookup to every test cell. Whole-cell stratified bootstrap intervals and grade-specific numbers of contributing cells are supplied in the artifact. Two unsafe test cells provide little information about variability across new cells.

### S9.2 Multiple optimal rules

The primary LP maximizes the minimum training decisiveness. Distinct lookup tables can attain its optimum \(d^*\). An exploratory second solve holds both error constraints fixed, requires training decisiveness at least \(d^*-10^{-9}\), and maximizes the mean probability of correct action with equal grade weights. A separate ablation constrains approval to be nonincreasing and rejection to be nondecreasing in each current-specific cutoff count. These comparisons were devised after inspecting the first replay.

**Table S11. Unsafe-stage decisiveness and unsafe approval (%) by optimization and validation design. The 28 leave-one-out folds include six cells with eligible unsafe stages.**

| Objective | Holdout decisive | Holdout approve | Leave-one-out decisive | Leave-one-out approve |
| --- | --- | --- | --- | --- |
| Primary LP | 14.63 | 0.33 | 11.02 | 4.75 |
| Monotone | 16.43 | 0.22 | 10.14 | 4.96 |
| Tie-break | 62.06 | 0.29 | 42.62 | 3.31 |
| Monotone + tie-break | 62.06 | 0.29 | 17.15 | 4.81 |

Tie-breaking increases unsafe-stage decisions in both designs. The maximum observed stage-level errors of the plain tie-broken rule on the 14-cell holdout are 16.67% safe rejection and 5.625% unsafe approval. The latter averages randomized lookup probabilities over physical blocks in the worst held-out unsafe stage. Table S12 evaluates a different one-reading rule and maximizes over whole-cell confidence sets. When all cell stages must meet both 5% budgets, the empirical check therefore fails. An exact random re-pairing of the same retained stratum-level records, preserving their margins, changes the primary action-stratified rule's unsafe-stage decisiveness from 14.63% to 14.69%. With a 60-s endpoint the analogous leave-one-out comparison gives 10.02% versus 10.39% for the standard and tie-broken rules.

### S9.3 Whole-cell registration and recording horizon

This secondary analysis includes every recorded stage, independent of its eventual length. Each cell is one model. Within each reference or replay stratum the target is the historical average of visit-specific conditional event probabilities \(p_i\). For a predictable stratum, Bernoulli conditional moment generating functions give a nonnegative martingale proportional to \(\exp(\lambda\sum_i H_i)/\prod_i[1+p_i(e^\lambda-1)]\) with starting value one. Jensen's inequality bounds its logarithm below by \(\lambda\sum_i H_i-N\log[1+\bar p_N(e^\lambda-1)]\). Invert this bound at levels allocated equally over 28 cells, four strata, two record halves, and the positive and negative grid \(\lambda=\pm2^{j/2},\ j=-12,\ldots,4\). The total error budget per endpoint is 0.05. The construction permits drift in conditional event rates; applicability requires the recorded current to identify the assigned setting and the recorded steps to represent the stated historical target. A prospective lifetime exposure would need its own sampling design.

**Table S12. One-measurement whole-cell rules evaluated over confidence sets. Errors are worst-case probabilities (%). Certified decisiveness is reported only when both error budgets hold.**

| Registry | Safe/unsafe/unresolved | Unsafe approve | Safe reject | Certified decisive (%) |
| --- | --- | --- | --- | --- |
| 28 cells, fitted | 16/4/8 | 5.00 | 5.00 | 18.86 |
| 14 training, fitted | 8/2/4 | 5.00 | 5.00 | 20.61 |
| 14 test, frozen rule | 8/2/4 | 5.6297 | 4.1807 | — |

On the held-out cells the frozen lookup has minimum decisiveness 20.61% over the confidence sets, but its unsafe approval bound exceeds 5%. In the full 28-cell class the maximum guaranteed decision rate for cutoff alone is 13.46%; with current it is 18.86%. Sixteen cells are safe, four unsafe and eight unresolved. All four unsafe cells belong to the uniform charge/discharge arm. Memorizing each pure-grade training arm's label classifies all eight safe and two unsafe gradeable test cells correctly. This control accounts for the observed whole-cell labels using information known before any measurement.

The skewed arms typically end event-free steps at 60 s and the uniform arms at 300 s. Imposing a common horizon defines a different endpoint: recorded cutoff termination by 60 s. No event-free step in the released table terminated before 60 s. With the same whole-cell inference 23 cells are safe, none is unsafe and five are unresolved. Consequently the bilateral comparison has no unsafe denominator. This test changes the observation horizon while other protocol differences persist.

### S9.4 Timing of the derating signal

A diagnostic reanalysis uses the preceding recorded step's maximum temperature and compares it with the past-only median through two steps earlier. At least five past records are required. The previously fitted cool/hot action probabilities are reused without another search, with thermal-state prevalence estimated by voltage bin. Of the corrected uniform-policy models, 98 safe and 155 unsafe models are evaluable. At one draw, midpoint completion gives hull distances 0.1717 for uniform loading and 0.1364 for derating. With unrestricted missing strata, the corresponding guaranteed distances are both numerically zero and decisiveness is 0.10. These calculations establish neither an executable cross-grade collision for the true laws nor its persistence across block lengths. The original construction used current-step peak temperature, observed after the loading decision.

## S10. Reproduction and claim provenance

The NASA analysis is a retrospective correction on previously inspected public records. The initial correction settings precede the new replay outputs. Tie-breaking, whole-cell registration and the 60-s duration comparison are exploratory extensions. The first record of every 25-record chunk was excluded on revision to prevent context crossing the split. The time-uniform whole-cell analysis includes short stages to avoid conditioning eligibility on future stage length. The protocol notes and fixed inputs are included with the code.

**Table S13. Primary sources for the results. NASA filenames are relative to the NASA results directory. Paths beginning with evidence are relative to this package. Other paths refer to the companion archive cited in the main paper.**

| Claim | Analysis status | Source |
|---|---|---|
| NASA classes and channel-value bounds | Retrospective correction | `legacy_grades.csv`, `corrected_frontier.csv` |
| Five-draw sharpened bounds, policy comparisons, matched rules and dependence | Retrospective extension, Section S11 | `evidence/review_v21/results/` |
| Acquisition bounds, transfer and high-current sensitivity | Retrospective analysis, Section S12 | `evidence/decision_v22/results/` |
| Capacity screening and external replay | Locally locked primary samples; external census added after primary analysis | `evidence/CETL/results/`, `evidence/ReLiB/public_results/`, `evidence/ReLiB/public_census/` |
| Leaf scheduled retests | Locally fixed primary and secondary workflows, with a descriptive full-archive secondary comparison | `evidence/Leaf/PROTOCOL.md`, `evidence/Leaf/READOUT.md`, `evidence/Leaf/results/` |
| NASA within-arm profile permutation | Corrected diagnostic | `legacy_block_test.csv` |
| Simultaneous classes and protected rules | Retrospective correction | `confidence_summary.csv`, `confidence_frontier.csv` |
| Matched replay and empirical errors | Retrospective held-out comparison | `physical_summary.csv`, `physical_cell_association.csv` |
| Tie-break and order restriction | Exploratory ablation | `ordered_summary.csv` |
| Whole-cell transfer, protocol and horizon | Exploratory diagnostics | `whole_cell_certificate.csv`, `arm_only_summary.csv`, `fixed60/whole_cell_certificate.csv` |
| Prior-temperature stress test | Corrected diagnostic | `thermal_summary.csv`, `thermal_missing_robust.csv` |
| ALT finite-order closure | Corrected registered analysis | `experiments/battery_alt_reference_channel_gate/results/frontier_v02.csv`; `gates_v02.json` |
| ALT channel null \(p=0.206\) | Corrected diagnostic | `experiments/battery_alt_reference_channel_gate/results/null_calibration_v02.json` |
| PulseBat registered SOC=5% point | Locked after feasibility probe | `experiments/pulsebat_procurement_external/results/frontier.csv`; `uncertainty.json` |
| PulseBat 40-point grid and corrected scope | Corrected diagnostic | `experiments/pulsebat_procurement_correction_v02/results/full/soc_menu_uncertainty.csv`; `audit_summary.json` |
| Zhu boundary calibration | Frozen plus corrected diagnostic | `experiments/zhu_relaxation_external/results/pairwise_vs_hull.csv`; `geometry_permutation_summary.csv` |
| Jones transport boundary | Corrected diagnostic | `experiments/jones_eis_external/results/cross_temperature_audit_rerun/paired_summary.csv` |
| MATR transport boundary | Frozen failure plus diagnostic | `experiments/severson_matr_external/results/full/menu_metrics.csv`; `results/full/summary.json` |

Section S12 reports retrospective derivations and sensitivity analyses from the same registered input. The corrected NASA experiment starts from the released 389,307-step table. A clean rebuild reproduced all 57 result CSVs byte-for-byte. The evidence directory provides the source checksum, software versions, row-level grades, fitted lookups, and the command to reproduce them. The three main figures can be regenerated from the paper package. PulseBat's local menu and criteria were locked after feasibility inspection; the full SOC grid is diagnostic. The Zhu and Jones corrections and the unsuccessful MATR external certification retain their original status.


## S11. Policy identity, matched decision rules and dependence

### S11.1 What is held fixed when two channels are compared?

The physical cell is the unit for splitting training and test data and for resampling. The grouped-law benchmark has 513 eligible stages distributed over 28 cells. Each stage appears under three target policies. A probability of decision in Tables I and S3 describes a block from a fixed stage-policy model. The denominator in a worst-case comparison is the set of gradeable models; it assigns no fleet prevalence to them. All comparisons below are retrospective extensions using the same step table and thresholds. They involve no additional physical measurements.

A pooled lookup observes the block alone. A policy-specific lookup receives the policy label at no measurement cost and observes the same block. Each row below compares channels on identical systems. With known policy, both errors must still hold within every gradeable policy. If all policies have both grades, the best achievable minimum over the union is the minimum of the three separately optimized decision rates, because the lookups can be selected independently. When a grade is absent, the corresponding bilateral comparison is recorded as unavailable.

**Table S14. Policy-specific five-draw certification. S/U/? denote safe, unsafe and unresolved stage-policy models. Count and full are decision rates (%); gain is in percentage points. Full retains current alongside cutoff.**

| Uncertainty | Policy | S/U/? | Count | Full | Gain |
| --- | --- | --- | --- | --- | --- |
| Missing | Shared | 443/528/568 | 24.238 | 24.319 | 0.081 |
| Missing | Uniform | 98/155/260 | 24.362 | 26.347 | 1.985 |
| Missing | High | 120/243/150 | 24.266 | 31.601 | 7.335 |
| Missing | Low | 225/130/158 | 24.287 | 24.647 | 0.360 |
| 95% | Shared | 26/250/1263 | 24.179 | 24.367 | 0.188 |
| 95% | Uniform | 0/76/437 | — | — | — |
| 95% | High | 0/137/376 | — | — | — |
| 95% | Low | 26/37/450 | 24.278 | 24.367 | 0.089 |

For example, with missing-stratum uncertainty the known high-current-weighted policy gains 7.335 points. This conditional increment compares the same 120 safe and 243 unsafe models in both channels. In contrast, supplying policy identity to the full channel changes the common worst-case decision rate by 0.328 points (24.319% to 24.647%). With simultaneous component uncertainty the safe class disappears under two policies, and only the low-current policy admits a within-policy bilateral comparison. The 26 safe and 250 unsafe pooled combinations are drawn from eight and four cells, respectively.

### S11.2 Protecting the full five-observation rule

The two joint cutoff masses in (S34) vary over a rectangle. Map each nondegenerate coordinate to \([0,1]\); a zero-width coordinate gives a constant polynomial. For any multinomial count state the block probability is a polynomial of degree at most \(n\) in each coordinate. Expand the vector of probabilities in the tensor Bernstein basis of degrees \((n,n)\). The basis weights are nonnegative and sum to one. Enforcing each linear side-error and minimum-decision constraint at every coefficient vector therefore protects the entire rectangle. Conversely, enforcing the constraints only at stationary grid laws relaxes the problem. Solving on both sets brackets the optimal value for each rule family.

The solver computes the coefficients by interpolation on the grid \(\{0,1/n,\ldots,1\}^2\), checks reconstruction off the grid and scans every rectangle for violated constraints. A small inward scaling of the delivered lookup removes solver overshoot at the 5% boundary. For the stage-policy comparisons at \(n=1,5\), upper and lower values agree within \(10^{-7}\) in probability units. The lower bound is an attainable rule. These are numerical optimization enclosures conditional on the input regions. An independent verifier obtains the same coefficients by conditioning on the number of low-current readings and counting high-endpoint slots with a hypergeometric law. It reproduces both side errors and the minimum decision rate for all 720 released state rows across 24 fits.

### S11.3 Which conventional rules meet the same budget?

All four competitors receive the same four-symbol counts and use the same gradeable models, confidence rectangles, abstention action, randomization and 5% side-error limits. The common objective is to maximize the minimum probability of issuing a decision. For the score methods, midpoint completions induce a class-mixture mass \(m_j(x)\) over count states by averaging models equally within grade. The midpoint is used only to order or rank the states; the error constraints use every admissible completion.

The likelihood-ratio score is \(\log m_{\rm U}(x)-\log m_{\rm S}(x)\). The out-of-distribution score is the total-variation distance from a point at \(x\) to the safe class mixture, \(1-m_{\rm S}(x)\). For either score, approval is nonincreasing and rejection nondecreasing with the score. Tied states share the same probabilities. The class-mass-rank comparator uses \(p_j(x)=\sum_{y:m_j(y)\le m_j(x)}m_j(y)\). At each common threshold it acts on a singleton retained label and otherwise requests more evidence. We optimize over randomized mixtures of all distinct threshold rules, including data-independent decisions. This is a model-based conformal-style comparator. Its worst-case guarantees here are supplied by the same robust constraints as for the other methods.

**Table S15. Matched five-reading rules on the confidence-graded stage models. Entries are worst-case probabilities in percent. Maxima on admissible grid laws match the protected side-error limits at the displayed precision.**

| Policy | Rule | Unsafe approve | Safe reject | Decisive |
| --- | --- | --- | --- | --- |
| Shared | Full lookup | 5.00 | 5.00 | 24.367 |
| Shared | Likelihood ratio | 5.00 | 5.00 | 24.364 |
| Shared | OOD distance | 5.00 | 5.00 | 24.286 |
| Shared | Class-mass rank | 5.00 | 5.00 | 24.362 |
| Low | Full lookup | 5.00 | 5.00 | 24.367 |
| Low | Likelihood ratio | 5.00 | 5.00 | 24.278 |
| Low | OOD distance | 5.00 | 5.00 | 24.286 |
| Low | Class-mass rank | 5.00 | 5.00 | 24.301 |

A distribution-free, nonrandomized class-conditional split-conformal check has a separate limitation on the physical whole-cell split in Table S12. There are at most eight safe and two unsafe training cells available for calibration. The usual finite-sample conformal p-values [11] are bounded below by \(1/9\) and \(1/3\), even before reserving cells for model fitting. At classwise level 0.05 both labels are retained for every test state, so the singleton decision rate is zero. This counting argument uses one calibration score per cell and applies for any chosen nonconformity score. It does not require treating stages as independent replicates.

### S11.4 Sensitivity to dependence between readings

For each admissible one-draw law \(P\), let \(R_5(P)\) repeat one sampled symbol five times. Replace the product law by \((1-\rho)P^{\otimes5}+\rho R_5(P)\) and require one rule to satisfy both errors for all \(\rho\in[0,\bar\rho]\). Each symbol keeps its marginal probability. For the indicator of any nonconstant event, the within-block pairwise correlation is \(\rho\). The two endpoints suffice at fixed \(P\), by linearity. Applying the same Bernstein expansion to both endpoints protects the whole family.

**Table S16. Common-symbol dependence sensitivity at five readings on the pooled confidence-graded class. The dependence cap is a sensitivity parameter. Error and decision rates are percentages.**

| Dependence cap | Unsafe approve | Safe reject | Decisive |
| --- | --- | --- | --- |
| 0.00 | 5.00 | 5.00 | 24.367 |
| 0.10 | 5.00 | 5.00 | 22.730 |
| 0.25 | 5.00 | 5.00 | 20.872 |
| 0.50 | 5.00 | 5.00 | 17.776 |
| 1.00 | 5.00 | 5.00 | 11.555 |

At the unrestricted endpoint, the one-draw decision rate is attainable by using one position in the block. Conversely, an adversary may repeat one symbol throughout the block, so a five-draw rule cannot exceed the one-draw optimum. The same equality holds if all couplings with the registered marginal are permitted. Intermediate values in Table S16 pertain to the stated common-symbol model. The experiment estimates no telemetry correlation parameter.

### S11.5 Changing the physical aggregation unit

As a sensitivity analysis, give each eligible stage of a cell equal weight and average the endpoints of its joint-mass rectangles within each policy. The risk and evidence use the same weights. This defines \(28\times3=84\) distinct cell-policy models. The product experiment for this table samples a new stage uniformly for each draw from a fixed cell and policy. Fixing one latent stage for the entire block would give a mixture of products and a different estimand. The independent physical replay and the fixed-current whole-cell experiment in S9 have their own sampling protocols.

**Table S17. Equal-stage cell-policy aggregation. The final column brackets five-draw full-channel decisiveness (%) on the gradeable part of the class.**

| Uncertainty | Policy | Models | S/U/? | Decisive |
| --- | --- | --- | --- | --- |
| Missing | Shared | 84 | 24/16/44 | 32.080 to 32.086 |
| Missing | Uniform | 28 | 4/4/20 | 61.566 to 61.566 |
| Missing | High | 28 | 5/8/15 | 37.271 to 37.271 |
| Missing | Low | 28 | 15/4/9 | 40.937 to 40.937 |
| 95% | Shared | 84 | 0/5/79 | — |
| 95% | Uniform | 28 | 0/1/27 | — |
| 95% | High | 28 | 0/4/24 | — |
| 95% | Low | 28 | 0/0/28 | — |

Of the 84 equal-stage models, the simultaneous intervals grade five unsafe and leave 79 unresolved. This inference inherits the stage-level simultaneous intervals. The whole-cell procedure in S9 uses a different reference target, assignment and evidence protocol, which accounts for its different grade counts.


## S12. From numerical bounds to a measurement and transfer decision

### S12.1 Procurement and rule complexity on the same class

Let \(A\) be cutoff only, \(B\) current plus cutoff and \(r\) a feasible likelihood-ratio lookup for \(B\). All three are evaluated on the same retained classes, within the same uncertainty region, at the same budgets and block length. If \(L_B>U_A\), a conservative lower bound on the fraction of the available additional decisiveness recovered by \(r\), when \(L_r\ge U_A\), is

\[
\frac{L_r-U_A}{U_B-L_A}.
\tag{S37}
\]

The numerator lower-bounds the increment of this specific feasible rule over the optimal cutoff rule. The denominator upper-bounds the full-channel increment. For the 276 pooled confidence-graded combinations the cutoff upper value is 24.179129%, the full-channel interval is 24.366665% at both ends to six decimals, and the calibrated likelihood-ratio lower value is 24.364432% (rounded). Subtracting the feasible likelihood-ratio lower bound from the full optimum's upper bound gives at most 0.002234 percentage points of headroom. Equation (S37), evaluated before rounding, gives at least 98.80%. The reference quantity for this fraction is the 0.187537-point field increment. For the low-current-only registry, the likelihood-ratio and cutoff bounds coincide to the reported precision, even though the unrestricted rule gains 0.089 points. These are differences between minimax decision values. A statement about improvement for each individual true law would require a separate law-specific comparison.

Table I uses the same retained registry and the unrounded endpoints in Table S18. Its first row upper-bounds every cutoff-only rule. Its next two rows give achievable rates for the full lookup and the likelihood-ratio rule. The upper endpoint for the unrestricted full channel bounds possible improvements over either rule.

**Table S18. Five-draw acquisition thresholds. Each row gives the cutoff upper endpoint and a feasible full-channel lower endpoint (%). Only the full channel can meet a target strictly above the first and at or below the second; comparisons use unrounded output.**

| Region and policy | Cutoff upper | Full lower | Grades (S/U/?) |
| --- | --- | --- | --- |
| Simultaneous, shared | 24.179129 | 24.366665 | 26/250/1263 |
| Simultaneous, low | 24.277892 | 24.366665 | 26/37/450 |
| Fixed rates, high | 24.265592 | 31.600804 | 120/243/150 |

### S12.2 Geometry and frozen-rule transport

For a statewise randomized approval function \(c\in[0,1]\), choose a source unsafe law within the Hausdorff distance of any target unsafe law. The difference in expected approval is bounded by total variation. Take the supremum over target laws and repeat for rejection over safe laws to obtain (26a). A nonpositive value of (26) leaves the geometric criterion inconclusive. A positive value establishes separation of the target hulls. Whether a particular source lookup meets the target budgets can be evaluated with (26a) or directly on the target sets.

For the one-reading whole-cell experiment both current bands have probability one half. A law is determined by its two joint cutoff masses \(t_0,t_1\) in (S34). The TV distance between two such laws is the sum of the absolute coordinate differences. We form each grade hull from the vertices of every cell rectangle, compute the largest vertex-to-hull distance in each direction by linear programming, and take the larger direction. On the training and held-out confidence hulls the respective symmetric shifts are 0.025912 (safe) and 0.034524 (unsafe). Using unrounded values gives the geometric margin 0.315590 and target hull distance 0.380618. The training lookup has 5% error bounds on each source side. Direct maximization over the held-out sets gives the sharper target bounds reported in Table S12. Its 5.6297% unsafe approval bound is a statement about permissible whole-cell laws. The 5.625% empirical worst-stage value in S9.2 comes from a separate four-reading replay.

### S12.3 Stability of the high-current design comparison

For the 28 leave-one-cell-deletion analyses we fix target weights, remove the cell and all its stages, recompute both five-draw decision optima, and keep the original grade definitions. The within-policy gain spans 6.800 to 8.114 percentage points, with the endpoints after removing RW26 and RW24, respectively. This measures sensitivity of the registered optimum to individual cells.

To check timing, we run a paired regrading calculation on records where both the recorded first-step voltage and the previous discharge step's terminal voltage qualify. The previous record must be within the same cell and stage. Both analyses retain the original target voltage weights, four measured-current groups, stage eligibility, event threshold and five-draw comparison. On the common record set, 510 stages meet eligibility. Using the first recorded step voltage gives 118 safe and 242 unsafe stages, and a gain of 7.561 points. Replacing the voltage proxy gives 99 safe and 278 unsafe stages and a gain of 6.779 points. Regrading is part of this sensitivity. Both versions have zero safe stages under simultaneous uncertainty, with 137 and 132 unsafe stages, respectively.

Among all original high-current stages the smallest simultaneous upper risk is 0.188713, in RW17 stage 2. Its fixed-rate lower and upper endpoints are both 0.031511. Thus even this stage fails the 0.15 safe criterion after incorporating rate uncertainty. The resulting lack of a safe class is displayed explicitly in Fig. 3a. The raw step table, 28 deletion outputs, timing results and acquisition/transfer tables accompany S12. These checks reuse the existing bench cohort; validation on a separately acquired batch remains open.


### S12.4 The denominator of each error budget

For RW10, stage 53, under the low-current-weighted policy, take the lower endpoints of the two joint cutoff masses in the NASA confidence rectangle. The four probabilities in low/no cutoff, low/cutoff, high/no cutoff, high/cutoff order are (0.57126559788, 0.27873440212, 0.077750475286, 0.072249524714). For each of the 56 count states, multiply its five-draw multinomial probability by each action probability in the pooled full lookup. Summing gives 5.0000% approve, 19.5779% reject and 75.4221% defer. Approval divided by the sum of approval and rejection is 20.34%. Both calculations condition on the same unsafe law. A fleet-level calculation of risk among released policies also requires grade prevalences and the approval rates across those grades. The check script reconstructs the law and recomputes all three action probabilities.

## S13. Capacity screening after a diagnostic charge

### S13.1 Endpoint, sampling design and frozen rules

A reusable cell passes the capacity specification when a reference discharge delivers at least 10,850 mAh. This imports the 70%-of-nameplate criterion from [45] into the 15.5-Ah use case. It defines a capacity grade for the bench test. NASA policy risks, thresholds and evidence units retain their definitions in S5. No customer-specified minimum decision rate or test price was available. The charge-to-discharge comparison shares the cost of a completed charge in both arms.

CETL [44] contains 4,000 retired IFR32135 records with voltage, current and accumulated charge at a nominal 3-s cadence. Reference labels agree with the final discharge counter in all 4,000 records. We locked the CETL analysis locally after an earlier screening study and before reading the CETL capacity outcomes. Contiguous blocks of 20 records were hash-ranked and allocated to training, calibration and test in proportions 40%, 25% and 35%. Within blocks, cell traces stay together. The full-trace analysis retained 2,890 complete records, comprising 1,110 training, 723 calibration and 1,057 test records. Out of 1,110 exclusions, 1,099 had zero voltage only at the first charge sample, ten had other charge zeros and one had a discharge-voltage zero. File order correlated with capacity (Spearman correlation \(-0.739\)), and only eight test blocks contained complete below-specification records. Original pack IDs were unavailable. Block resampling therefore addresses file-order sensitivity only.

Each arm fits a 200-tree Extra Trees regressor to normalized discharge capacity on the training split. A uses the first charging voltage. B uses 40 features from the completed charge, including current and voltage at fixed trace fractions, throughput, threshold-crossing times and sample count. On calibration records, class-specific score order statistics set two thresholds using one-sided 97.5% binomial limits. For B, scores strictly above 0.8875340919192738 pass, scores strictly below 0.692783304648114 reject and intermediate values or ties defer. At application B reads only charge-side signals. This is a feasible score-based rule; the continuous-rectangle optimality calculation of Section V concerns the separate NASA task. Frozen B reproduces every released action on the 2,890 complete CETL records and the charge-only routing of all 1,400 originally allocated test records.

### S13.2 Source holdout, errors and channel time

**Table S19. CETL operated at two 5% class-conditional budgets. Limits are one-sided 97.5% exact binomial upper bounds. Decision rates and their minimum are empirical.**

| Test scope and rule | False pass (upper %) | False reject (upper %) | Decisions below spec. | Decisions qualified | Min. (%) |
| --- | --- | --- | --- | --- | --- |
| Complete A | 0/142 (2.5643) | 36/915 (5.4055) | 16/142 | 36/915 | 3.93 |
| Complete B | 2/142 (4.9951) | 20/915 (3.3557) | 100/142 | 384/915 | 41.97 |
| All A | 0/152 (2.3977) | 36/1,248 (3.9713) | 16/152 | 36/1,248 | 2.88 |
| All B | 2/152 (4.6721) | 20/1,248 (2.4642) | 101/152 | 384/1,248 | 30.77 |

For an individual frozen rule the two upper limits have joint coverage of at least 95% under independent target sampling within grade. The false-pass limit for complete-case B is 4.9951%, close to the specified budget. The complete-case paired counts of decisions gained/lost with B are 85/1 below specification and 383/35 among qualified cells. Both meet their one-sided paired tests at 0.025. When all 1,400 test records are routed, 342 invalid charging traces defer. One additional record has a valid charge and a discharge-voltage anomaly; its recorded capacity provides the reference in this sensitivity analysis.

Complete-case A decided on 52 cells associated with 49.01 hours of recorded reference discharge. B decided on 484 cells associated with 625.19 hours. Subtraction gives 432 net additional decisions and 576.19 discharge-channel hours. Per complete test record, the difference is 32.71 channel-minutes; over all 1,400 test records, it is 24.72. Channel time sums across test channels. Both rules incurred 1,404.35 hours of charging on the complete cohort, and every archived cell received a discharge. These figures describe the gross workload attached to alternative actions. Realized savings also depend on whether the actions are acceptable, their errors, and the cost of handling richer traces. The paired block-bootstrap interval for the increase in the minimum decision rate was 25.43 to 49.77 percentage points; that for the difference in discharge workload was 381.92 to 777.62 channel-hours.

An additional post hoc engineering control used only the initial voltage and final accumulated charge, with the same model, source split and calibration procedure. It made 152 passes, 95 rejections and 810 deferrals on the 1,057 complete held-out records. Errors were 1/142 false passes (upper limit 3.8611%) and 21/915 false rejections (3.4870%); decisive counts were 75/142 and 172/915. Its 247 decisions corresponded to 287.43 recorded discharge hours. B made 237 additional decisions, corresponding to 337.76 gross hours. Pointwise checks for each rule do not provide a joint confidence statement across the three alternatives. The reproducible reviewer comparison is provided in the CETL evidence folder.

A stronger claim would compare B to every rule on a prespecified coarsening of A. For a four-bin voltage channel the computed robust optimum was 10.44%. In the simultaneous comparison across both channels and across B’s error and decision rates, the B false-pass upper limit rises to 6.18%. Thus these data do not establish a strict procurement certificate over all four-bin lookups. Table S19 assesses the two fitted rules directly.

### S13.3 External transfer and checks on the reference discharge

We applied the unchanged B weights, feature order, input units and thresholds to the public 15.5-Ah ReLiB archive [46]. The source contains 6,909 CSV records. Before examining target capacity outcomes, a local protocol selected the first 1,024 members by SHA-256 rank of the full archive path. One pass through the records calculated actions from the first constant-current/constant-voltage charge in original sample order; a sealed prediction list preceded a second pass reading reference capacity. A reference was confirmed when the constant-current discharge at step 3 had at least two readings, a positive final counter and a subsequent recorded step. After the primary analysis produced no confirmed below-specification record, we evaluated the full archive with the same rule and criteria. This census includes all 1,024 primary records. Both protocols were recorded locally in retrospective public data; neither had an external prospective registration.

**Table S20. External archive evaluated at the 10.85-Ah specification. All records had a discharge step. Two census files ended during that step and lack the prespecified completion marker.**

| Scope | Records | Qualified / below / unconfirmed | Pass / reject / defer | Qualified rejected (%) |
| --- | --- | --- | --- | --- |
| Locked primary | 1,024 | 1,024 / 0 / 0 | 0 / 791 / 233 | 77.25 |
| Follow-up census | 6,909 | 6,907 / 0 / 2 | 0 / 5,358 / 1,551 | 77.54 |

The two unconfirmed records both received a rejection. Using the authors’ final recorded discharge counter directly would add two qualified records (15.019 and 15.133 Ah), giving 5,358/6,909 false rejects (77.55%). The prespecified analysis already identifies 5,356 errors, or at least 77.52% of the entire file archive, regardless of the missing grades. With zero confirmed below-specification cells the conditional false-pass frequency is undefined. These finite-archive counts do not require sampling independence. In the primary set an independent CSV reader reproduced all 1,024 capacities and all frozen actions. Integrating measured discharge current at the nominal 3-s cadence also assigned all 1,024 references to the same grade. The median absolute difference between the integral and the capacity counter was 34.2 mAh.

No exact charge trace or prespecified rounded signature matched any of the 4,000 CETL records. The target archive identifies nominal capacity but supplies no verified per-record model number, physical cell serial, original pack, or arrival-lot mapping. Six dates encoded in filenames permit descriptive summaries only. The median within-trace charging current shifted from 10.0 A in CETL training to 6.0 A in the ReLiB primary sample; the median trace length shifted from 1,603 to 2,561 samples. These are observable changes in the model inputs. Their individual causal contributions cannot be estimated from the two archives. Within the published records the number skipping the discharge step was zero. Plant-wide savings from deploying a rule would require information on units absent from the archive and on executed work orders.

## S14. A scheduled repeat-capacity decision on Nissan Leaf units

### S14.1 Units, chronology and local protocol

The published Stanford–Relyion data [47] contain eight electrical test units from two original Nissan Leaf packs. Each unit connects two parallel pouch cells at the test terminals [48]. Seven units came from a first-generation pack and unit 2.1 from a second-generation pack. The 88 recorded visits span January 27, 2022 to July 6, 2023. All reported capacities retain the source measurement scale. The 22.75-Ah scenario uses the 32.5-Ah nominal scale from [47] and applies to the 4.0–3.0 V window. These measurements describe usable capacity under the stated protocol. Pack generation, calendar time and state of health were not independently varied.

Both packs were reserved in their entirety. During source selection, the published first-visit charge values were visible. The primary protocol was sealed locally before reviewing later reference outcomes. A second local document identifies the steps and defines the secondary same-visit rule after inspection of one odd anchor visit, before even-visit adjudication. Neither seal has a third-party timestamp. The package includes both documents and the sealed paired actions. No thresholds were estimated on these packs. Archival visit order determines nonoverlapping odd–even pairs. Visits that never entered the archive cannot be counted.

### S14.2 Which measurements each decision requires

The primary rule takes the previous odd visit's reference capacity and makes its decision before the following even visit. Odd visits always require reference measurement, including the final unpaired odd visit on a unit. No omitted even-visit measurement is needed as a later input. The secondary design takes charge throughput after initial conditioning to 3.0 V and the standardized charge to 4.0 V at the current visit. Both rules request reference discharge for scores from 21.125 through 24.375 Ah inclusive. The 1.625-Ah margin is 5% of the nominal capacity. The separate 5% error budgets specify a fraction of visits within each reference grade. The 20% minimum decision rate in each grade is a study-defined requirement.

The subsequent nominal C/20 discharge supplied the common reference. Its endpoint had to be within 0.03 V of 3.0 V, its start at or above 3.95 V, and its median current magnitude within 5% of 1.55 A. The original counter and independent current integration differed by at most 0.00730 Ah over the 88 visits. Only the standardized reference discharge contributes channel time. Conditioning, standardized charge, recharging and other diagnostics remain separate. If a downstream step needs a fresh capacity label or the same terminal condition, its own requirements determine whether a discharge can be omitted.

### S14.3 Error denominators, coverage and workload

On the 41 optional retests the primary rule recorded zero false passes in 27 below-specification visits and zero false rejects in 14 qualified visits. It passed five, rejected 26 and deferred ten. The same-visit rule made the same action on every paired visit. The primary rule's 31 decisive visits accounted for 406.92 hours of reference discharge. Counting all 47 mandatory anchors leaves 31 decisions among 88 recorded visits, including 5/32 qualified and 26/56 below specification. Counting the mandatory visits makes the qualified side fall below the 20% requirement.

For the secondary full-archive description, 10 passes, 55 rejections and 23 deferrals correspond to 10/32 and 55/56 decisive visits within grade. The false-pass and false-reject counts were 0/56 and 0/32. The 34 additional decisions over the full primary schedule came from the 47 mandatory anchor visits. The selected segments occupied 850.98 of 1,200.39 recorded discharge-channel hours. All were actually performed. The hours for the alternative schedules overlap. Future calendar time and the effect of omitting a discharge on subsequent aging were not observed.

Within the first-generation pack the same-visit rule decided 2/22 qualified visits and 55/56 below-specification visits. All ten second-generation visits were qualified and eight were decisive. At the first visit to each unit the seven below-specification units were rejected and the one qualified unit was referred. The two packs do not support an independent-lot error bound. The same-visit charge and subsequent discharge capacities differed by 0.054 Ah at the median and by at most 0.334 Ah. A post hoc forced decision at the specification gave 88/88 correct on this schedule. This explains why a simple recorded measurement carried useful information. It does not establish a gain from more elaborate prediction.
