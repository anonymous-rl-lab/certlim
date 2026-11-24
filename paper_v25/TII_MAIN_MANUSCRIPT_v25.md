# Finite-Evidence Limits for Causal Safety Certification in Battery Management Systems

## Abstract

When does a battery diagnostic need one more recorded field, and when is a simple decision rule already sufficient? We bound the worst-case fraction of attempts that can end in approval or rejection under separate limits on each error. A common confidence region determines which reference grades are resolved, provides a feasible rule for each candidate measurement, and bounds the decision rate of every rule using that measurement. In NASA, 276 of 1,539 stage-policy combinations were gradeable. With five independent readings per model and two 5% error budgets, the cutoff-only upper bound was 24.179%. Recording the current band gave a feasible rate of 24.367%. A calibrated likelihood-ratio rule also met an illustrative 24.30% requirement and left at most 0.002234 percentage points for further optimization. In capacity screening, a charge-trace rule met both error bounds on 1,057 complete CETL holdout records under within-grade independence. Applied unchanged to ReLiB, it rejected 5,356 of 6,907 confirmed qualified records. In two Leaf donor packs, a secondary rule using the current visit’s charge decided 65 of 88 recorded visits with zero observed errors. It met the 20% empirical target in each grade across the full schedule, where the prior-capacity rule fell short after mandatory reference visits were counted.

**Index Terms—** Battery management systems, causal safety, evidence acquisition, finite-sample certification, over-the-air updates, partial identifiability, selective decision.


## I. Introduction

A battery test bench already records whether a discharge step ended at cutoff. Should it also save the current band? That choice matters if adding the field lets the battery management system (BMS) approve or reject a proposed policy often enough while keeping both kinds of error within budget. The engineer must also choose a rule. If a simple rule already meets the requirement, how much more could the best rule on those same records deliver?

A reference experiment defines the policy-risk grade. The proposed diagnostic supplies the readings available at decision time. We compare channels on the same gradeable systems and at the same error budgets. A feasible rule tells the engineer what a channel can deliver. An upper bound over every rule using that channel tells the engineer when changing the algorithm cannot make it adequate. On the richer channel, the distance from a simple rule to the upper bound quantifies the most that further optimization could buy.

The need for a different measurement also depends on how ambiguity arises. Repeated readings from a fixed system can separate mixtures that agree on one draw. If two systems with opposite grades have the same evidence law, that ambiguity persists for every block length.

For a certification experiment \(\mathsf E\) and a block of \(n\) evidence units, the key object is

\[
\Delta_{\mathsf E}(n)
=
d_{\mathrm{TV}}\!\left(
\operatorname{co}\mathcal P_{\mathrm S}^{\mathsf E,n},
\operatorname{co}\mathcal P_{\mathrm U}^{\mathsf E,n}
\right),
\tag{1}
\]

the total-variation distance between the convex hulls of the registered safe and unsafe evidence families. Here \(n\) counts independent draws under each fixed model, as in (8). This distance bounds the optimal worst-case three-state decision rate \(\mathcal D_{\alpha,\beta}(\mathsf E,n)\), where \(\alpha\) limits unsafe approvals and \(\beta\) limits rejections of safe policies. Fig. 1 shows how an engineer uses the resulting bounds and checks a frozen rule at a new source.

![Measurement choice, rule simplification and external acceptance](figures/fig1_workflow.png)

**Fig. 1. What to measure, which rule to use, and when to keep the reference test.** On the registered NASA models, an upper bound rules out cutoff-only evidence at the example target. A feasible lookup establishes the value of current, and a separately calibrated likelihood-ratio rule also suffices. At a new source the frozen rule needs its own error check. ReLiB supplies such a check for the CETL capacity rule.

1. **Finite-evidence limits.** The geometry of the two grade families determines when repeated observations can resolve ambiguity and when a different measurement is necessary.
2. **A computable measurement choice.** One confidence region determines reference grades and admissible diagnostic laws. The resulting feasible rule and all-rule upper bound quantify both the value of an additional field and the scope for simplifying the decision rule.
3. **Decisions on recorded battery tests.** NASA evaluates field retention and rule complexity on the same task. CETL and ReLiB test a frozen capacity screen across sources. Leaf tests whether a scheduled reference discharge can be omitted when a charge measurement is already available. ALT and PulseBat examine block length and measurement conditions.

## II. Related Work and the Missing Certification Object

Battery prognostic methods estimate health, remaining life and aging trajectories [1]–[4], including from fragmentary histories and physics-informed models [39]–[41]. Lu et al. use fragment trends to initialize a remaining-life model [39]. Li et al. use auxiliary labels and selective pseudolabeling to estimate capacity when labels are scarce [49]. Learned charging policies optimize efficiency and degradation [5]–[7]. Impedance, relaxation, incremental capacity and pulses provide candidate diagnostics [21]–[24]. An average prediction error leaves open whether a diagnostic meets separate limits on unsafe approval and unnecessary rejection.

Shift detection, conformal prediction and selective classifiers relate uncertainty to coverage or predictive risk [8]–[11]. Zhou et al. use evidential uncertainty to flag potentially unknown fault classes [50]. Set-valued classifiers minimize ambiguity subject to class-conditional coverage [43]. CETL instantiates a related two-grade decision problem. The policy setting adds two requirements. A separate reference experiment determines the grade, and the same rule must meet both limits across every registered model with that grade. Source-specific validation remains important in capacity transfer [38].

Off-policy evaluation and safe improvement address identifiable intervention targets [12]–[16]. Partial identification permits a set of reference risks [17], [18]. Composite testing supplies least-favorable mixtures [19], [20], [35], and grouped-sample theory explains how repeated observations sharing a component can identify mixtures [42]. We use these results to bound the decision rate of a cheaper experiment after grading uncertainty has been propagated to its evidence laws.

Acceptance sampling specifies lot-level operating characteristics and producer and consumer risks [36], [37]. Blackwell comparison and Le Cam deficiency compare experiments over decision problems [30], [34]. Here the task and the two error limits are fixed. A feasible rule and an upper bound over all rules for each channel together identify a range of decision requirements for which an added measurement changes feasibility.

## III. Industrial Certification Problem

### A. Registered Battery Systems and Deployment Policies

Let \(\Theta\) be a registered class of structural battery-system models. A model \(\theta\in\Theta\) specifies the state transition, exogenous uncertainty, observable variables, executable actions, safety outcome, and measurement mechanisms. Let \(Z\in\mathcal Z_{\mathrm{op}}\) denote operating conditions, \(A\in\mathcal A\) a battery-management action, and \(H\in\{0,1\}\) a registered adverse endpoint. A proposed BMS or OTA policy is a Markov kernel \(\pi(a\mid z)\).

For a registered operating-envelope distribution \(\mu_{\mathrm{op}}\), define policy risk

\[
\begin{aligned}
\Psi(\theta,\pi)
&=\int_{\mathcal Z_{\mathrm{op}}}\sum_{a\in\mathcal A}\pi(a\mid z)\\
&\qquad\times\,
P_\theta\!\left(H=1\mid Z=z,\operatorname{do}(A=a)\right)
\mu_{\mathrm{op}}(\mathrm dz).
\end{aligned}
\tag{2}
\]

The grade belongs to a system under a policy, \((\theta,\pi)\). A fixed-policy guarantee holds uniformly over the registered systems. When several policies are admitted, the designer must specify whether the lookup receives their identity. Supplying it permits a separate lookup for each policy; withholding it requires a common lookup.

Given \(0\le\tau_{\mathrm S}<\tau_{\mathrm U}\le1\), define

\[
\begin{aligned}
\Theta_{\mathrm S}(\pi)&=\{\theta:\Psi(\theta,\pi)\le\tau_{\mathrm S}\},\\
\Theta_{\mathrm U}(\pi)&=\{\theta:\Psi(\theta,\pi)\ge\tau_{\mathrm U}\},
\end{aligned}
\tag{3}
\]

with a buffer class \(\Theta_{\mathrm A}(\pi)\) between the thresholds. Equation (7) controls decisions on the two extreme classes. A separate operating rule can assign `Alert` to a known buffer grade.

### B. Reference Identification Versus Certification Evidence

The two experiments have different jobs.

- \(\mathsf R\) identifies \(\Psi\) or its grade through randomized loading, complete capacity calibration, a controlled thermal protocol, or a justified physical reference.
- \(\mathsf E\) is the evidence that can be purchased at certification time, such as history, OCV, EIS, relaxation, a reference segment, or a diagnostic pulse.

For reference distribution \(r\), let

\[
\mathcal J_{\Psi}^{\mathsf R}(r;\pi)
=
\{\Psi(\vartheta,\pi):P_{\vartheta}^{\mathsf R}=r,\ \vartheta\in\Theta\}.
\tag{4}
\]

An empirical unit is eligible to populate an extreme class only if its reference identified set lies entirely below \(\tau_{\mathrm S}\) or entirely above \(\tau_{\mathrm U}\). If the set crosses the thresholds, the unit cannot serve as known safe or unsafe truth. This prevents a certification experiment from manufacturing its own labels.

When \(\mathsf R\) randomizes actions with known propensity \(e(a\mid z)>0\), the interventional response is identified on the common support:

\[
P_\theta(H=1\mid z,\operatorname{do}(a))
=P_\theta(H=1\mid z,a),
\tag{5}
\]

and (2) follows by standardization. If actions are assigned only once per cell, pack, or domain, a freely chosen policy dimension is generally not identifiable from that dataset alone.

### C. Evidence Menus and Physical Costs

A certification experiment is executable, \(\mathsf E=(\kappa_{\mathsf E},M_{\mathsf E})\), where \(\kappa_{\mathsf E}\) specifies the diagnostic action, operating condition, duration, and sampling unit, and \(M_{\mathsf E}\) specifies the measurement map. Two tests using the same voltage sensor under different current pulses are different experiments; a feature computed only from existing telemetry is not.

For \(n\) independent physical evidence units, record a cost vector

\[
\mathbf C_{\mathsf E}(n)
=
\bigl(n,T_{\mathsf E}(n),Q_{\mathsf E}(n),S_{\mathsf E}(n),B_{\mathsf E}(n)\bigr),
\tag{6}
\]

representing independent units, test time, energy throughput, maximum stress, and hardware burden. These quantities remain separate rather than being collapsed into a single price. A ledger may compare only on components it registers; the battery ledgers register \(n\), \(T_{\mathsf E}\), and \(S_{\mathsf E}\), which confines the Pareto comparison of Section VI-D to one operating point.

### D. Three-State Certification

An \(n\)-sample rule is
 \(\Gamma_n: \mathcal X_{\mathsf E}^{n} \rightsquigarrow \{\textsf{Certify},\textsf{Alert},\textsf{Reject}\}\).

For tolerances \(\alpha,\beta\in(0,1)\), require

\[
\begin{aligned}
\sup_{\theta\in\Theta_{\mathrm U}}
P_\theta\{\Gamma_n=\textsf{Certify}\}&\le\alpha,\\
\sup_{\theta\in\Theta_{\mathrm S}}
P_\theta\{\Gamma_n=\textsf{Reject}\}&\le\beta.
\end{aligned}
\tag{7}
\]

Both probabilities use all attempts for a given true model. For example, at one admissible law for the unsafe NASA model RW10, stage 53, low-current policy, the five-reading rule approves 5.00%, rejects 19.58% and defers 75.42%. Among decisions at that law, 20.34% are mistaken approvals. The unsafe fraction among approvals across a fleet also depends on the fleet’s grade mix (Supplementary Section S12.4).


## IV. Causal Certification Frontier

### A. Composite Geometry

Let \(P_\theta^{\mathsf E}\) be the single-unit evidence distribution, with repeated units i.i.d. conditional on a fixed \(\theta\). Define the safe and unsafe \(n\)-unit families

\[
\mathcal P_j^{\mathsf E,n}
=
\{(P_\theta^{\mathsf E})^{\otimes n}:\theta\in\Theta_j\},
\qquad j\in\{\mathrm S,\mathrm U\},
\tag{8}
\]

and their convex hulls \(\mathcal K_j^{\mathsf E}(n)=\operatorname{co}(\mathcal P_j^{\mathsf E,n})\). Convexification is a least-favorable prior drawn once for the whole block, not redrawn per observation.

The certification distance is (1), and the gate is

\[
G_{\mathsf E}(n)
=
\mathbf 1\{\mathcal K_{\mathrm S}^{\mathsf E}(n)
\cap\mathcal K_{\mathrm U}^{\mathsf E}(n)\neq\varnothing\}.
\tag{9}
\]

For comparison, define the minimum pairwise distance

\[
d_{\mathrm{pair},\mathsf E}(n)
=
\inf_{\theta_{\mathrm S},\theta_{\mathrm U}}
d_{\mathrm{TV}}\!\left(
(P_{\theta_{\mathrm S}}^{\mathsf E})^{\otimes n},
(P_{\theta_{\mathrm U}}^{\mathsf E})^{\otimes n}
\right).
\tag{10}
\]

Because each original distribution is contained in its hull,
 \(0\le\Delta_{\mathsf E}(n) \le d_{\mathrm{pair},\mathsf E}(n)\), so a positive pairwise distance does not by itself establish composite certification.

Define the optimal extreme-class decisiveness

\[
\mathcal D_{\alpha,\beta}(\mathsf E,n)
=
\sup_{\Gamma_n\ \mathrm{satisfies}\ (7)}
\inf_{\theta\in\Theta_{\mathrm S}\cup\Theta_{\mathrm U}}
P_\theta\{\Gamma_n\neq\textsf{Alert}\}.
\tag{11}
\]

### B. Main Theorem

**Theorem 1 (Finite-evidence safety-certification limit).** Assume that \(\Theta\) is compact, \(\Theta_{\mathrm S}\) and \(\Theta_{\mathrm U}\) are nonempty, the evidence alphabet is finite, and \(\theta\mapsto P_\theta^{\mathsf E}\) and \(\theta\mapsto\Psi(\theta,\pi)\) are continuous. Then:

1. For every \(n\ge1\),

   \[
   \mathcal D_{\alpha,\beta}(\mathsf E,n)
   \le
   \min\{1,\alpha+\beta+\Delta_{\mathsf E}(n)\}.
   \tag{12}
   \]

   If the two hulls intersect, the frontier is exact:

   \[
   G_{\mathsf E}(n)=1
   \Longrightarrow
   \mathcal D_{\alpha,\beta}(\mathsf E,n)
   =\min\{1,\alpha+\beta\}.
   \tag{13}
   \]

   Conversely, if an \(N\)-unit rule never outputs `Alert` on \(\Theta_{\mathrm S}\cup\Theta_{\mathrm U}\) while satisfying both side-error constraints, then necessarily

   \[
   \Delta_{\mathsf E}(N)\ge 1-\alpha-\beta.
   \tag{13a}
   \]

2. \(\Delta_{\mathsf E}(n)\) and \(\mathcal D_{\alpha,\beta}(\mathsf E,n)\) are nondecreasing in \(n\), whereas \(G_{\mathsf E}(n)\) is nonincreasing. Let
 \(n_\star(\mathsf E)=\inf\{n:G_{\mathsf E}(n)=0\}\).

   Hence exactly one of two cases holds: either \(n_\star=\infty\), or \(n_\star<\infty\) and \(G_{\mathsf E}(n)=0\) for every \(n\ge n_\star\).

3. The gate remains closed to certification for every finite \(n\) if and only if there exists an exact single-unit cross-grade collision:

   \[
   G_{\mathsf E}(n)=1\ \forall n
   \Longleftrightarrow
   \exists\theta_{\mathrm S}\in\Theta_{\mathrm S},
   \theta_{\mathrm U}\in\Theta_{\mathrm U}:
   P_{\theta_{\mathrm S}}^{\mathsf E}
   =P_{\theta_{\mathrm U}}^{\mathsf E}.
   \tag{14}
   \]

4. If \(n\ge n_\star<\infty\), there exists \(f_n:\mathcal X_{\mathsf E}^n\to[0,1]\) whose uniform safe–unsafe expectation gap equals \(\Delta_{\mathsf E}(n)\). Its symmetric margin is
 \(\gamma_\star(n)=\frac{\Delta_{\mathsf E}(n)}{2}\).

   Averaging \(f_n\) over \(m\) independent blocks yields both side errors no larger than

   \[
   \exp\!\left[-\frac{m\Delta_{\mathsf E}(n)^2}{2}\right].
   \tag{15}
   \]

**Proof sketch.** For (12), take a closest safe–unsafe pair of mixtures and apply the Le Cam two-mixture argument [34] to the `Certify` and `Reject` events. At hull intersection, a data-independent rule that outputs the two extreme labels with the allowed side-error probabilities attains (13); setting \(\mathcal D=1\) in (12) gives (13a). Marginalizing an \((n+1)\)-unit experiment and applying total-variation data processing proves monotonicity. If the hulls intersect for every \(n\), compactness gives limiting safe and unsafe mixing measures whose exchangeable sequence laws agree at every order. Uniqueness of the de Finetti mixing measure on the finite alphabet [31] forces their pushforward supports to share a single-unit distribution, proving (14). When the hulls are disjoint, Sion's minimax theorem [32] gives a bounded separating statistic with gap \(\Delta_{\mathsf E}(n)\); Hoeffding concentration [33] gives (15). Full proofs are in Supplementary Section S2, on the setup of Section S1, with a synthetic companion in Section S4.

**Corollary 1 (finite registered classes are decidable).** Suppose the two extreme classes contain \(M_{\mathrm S}\) and \(M_{\mathrm U}\) distinct single-unit evidence laws. After merging duplicates within each side, let \(r\le M_{\mathrm S}+M_{\mathrm U}\) be the number of distinct laws in their union. If no exact cross-grade collision exists, then

\[
n_\star(\mathsf E)\le r-1\le M_{\mathrm S}+M_{\mathrm U}-1.
\tag{15a}
\]

The proof uses a separating scalar functional and Vandermonde nonsingularity (Supplementary Section S2). This tensor-power independence argument is related to grouped mixture identification [42]. For four distinct PulseBat laws the bound is three draws. It governs structural separation; arbitrarily close laws can still require many more measurements to achieve useful decisiveness.

### C. The Three Regions

Three operational regions follow (Fig. 2).

- **Permanent collision:** \(n_\star=\infty\); more of the same evidence cannot raise worst-case decisiveness above (13).
- **Delayed separation:** \(1<n_\star<\infty\); one-unit hulls overlap, but repeated units reveal higher-order structure.
- **Immediate separation:** \(n_\star=1\); only confidence, sampling, cost, and transport remain.

![Certification geometry and the finite/permanent divide](figures/fig2_geometry.png)

**Fig. 2. The finite/permanent divide (schematic).** (a) Delayed separation: the one-unit hulls intersect, so \(\Delta=0\), yet no safe-unsafe pair is identical and the product structure separates them at \(n_\star\). (b) Permanent obstruction: one pair induces the same evidence law, so \(\Delta(n)=0\) at every \(n\), decisiveness equals \(\min\{1,\alpha+\beta\}\), and no parameter-independent re-encoding helps.

### D. Data Processing and Evidence Change

If one unit of a derived experiment \(Y\) is generated from an \(n\)-unit block \(X^n\) through a \(\theta\)-independent Markov kernel, then any common safe–unsafe distribution of \(X^n\) remains common after the transformation. Consequently,

\[
G_{\mathsf E}(n)=1
\Longrightarrow
G_{K\circ\mathsf E}(1)=1.
\tag{16}
\]

A residual, embedding, or conformal score computed from old evidence may improve computation or estimation but cannot cross a permanent gate; a new channel must change the joint experiment on the colliding pair. This is the operational content of Blackwell ordering [30], a corollary of the geometry rather than a competing theory.


## V. Confidence-Certified Decision and Evidence Procurement

### A. Distributional Uncertainty

The theorem concerns population distributions; experiments estimate them from finite batteries. Let \(\mathcal C_{\theta,\eta}\) be simultaneous confidence sets satisfying

\[
P\!\left(
P_\theta^{\mathsf E}\in\mathcal C_{\theta,\eta}
\text{ for every registered }\theta
\right)\ge1-\eta.
\tag{17}
\]

Define a conservative separation certificate

\[
\underline\Delta_{\mathsf E,\eta}(n)
=
\inf_{\widetilde P_\theta\in\mathcal C_{\theta,\eta}}
\Delta_{\mathsf E}\!\left(n;\{\widetilde P_\theta\}\right).
\tag{18}
\]

On the simultaneous-coverage event \(\Delta_{\mathsf E}(n)\ge\underline\Delta_{\mathsf E,\eta}(n)\). A positive plug-in distance estimates geometry and a significant permutation rejects a label-exchangeability null; neither equals (18), which alone establishes separation with the stated coverage.

Certificate (18) protects the *geometry*; procurement needs one rule admissible for every law the confidence sets allow. Write the expanded block families

\[
\widetilde{\mathcal P}_{\mathrm S}^{\mathsf E,n}(\eta)
=\{\widetilde P_\theta^{\otimes n}:
\widetilde P_\theta\in\mathcal C_{\theta,\eta},\ \theta\in\Theta_{\mathrm S}\},
\tag{19}
\]

and \(\widetilde{\mathcal P}_{\mathrm U}^{\mathsf E,n}(\eta)\) likewise. Let \(\mathfrak G_{\alpha,\beta,\eta}\) collect the randomized `Certify`/`Alert`/`Reject` rules \(\Gamma\) on \(\mathcal X_{\mathsf E}^n\) whose two side errors hold *uniformly* over those families, and define the confidence-protected decisiveness

\[
\underline{\mathcal D}_{\alpha,\beta,\eta}(\mathsf E,n)
=
\sup_{\Gamma\in\mathfrak G_{\alpha,\beta,\eta}}
\ \inf_{P\in\widetilde{\mathcal P}_{\mathrm S}^{\mathsf E,n}\cup\widetilde{\mathcal P}_{\mathrm U}^{\mathsf E,n}}
P\{\Gamma\neq\texttt{Alert}\}.
\tag{20}
\]

The operator order is the content. Certificate (18) says every admissible configuration is separated; (20) says one fixed rule is admissible and decisive across all of them. The first does not imply the second, because the configuration attaining \(\underline\Delta\) and the rule attaining \(\mathcal D\) need not correspond. On the coverage event, \(\underline{\mathcal D}_{\alpha,\beta,\eta}\le\mathcal D_{\alpha,\beta}\) for the same extreme-class registry. With confidence-based grading, both quantities here refer to the retained models; the fraction left ungraded is reported separately.

For implementation the simultaneous region includes reference risks as well as evidence probabilities. A model enters the safe or unsafe family only when its entire risk interval meets the corresponding threshold. Grades and channels use the same target population and weights. Algorithm 1 evaluates (20) on this retained class and reports its denominator.

### B. Computing a Rule and Its Optimality Bound

For finite registered classes \(\Delta_{\mathsf E}(n)\) comes from a linear program over safe and unsafe mixture weights. With mass functions \(p_i^{(n)}\) and \(q_j^{(n)}\), solve

\[
\min_{\lambda,\mu,t}
\frac12\sum_x t_x
\tag{21}
\]

subject to

\[
\begin{aligned}
-t_x\le
\sum_i\lambda_i p_i^{(n)}(x)
-\sum_j\mu_j q_j^{(n)}(x)
&\le t_x,\\
\lambda,\mu&\in\text{simplices}.
\end{aligned}
\tag{22}
\]

The dual of (21) returns a bounded separator. Decisiveness requires a second optimization over the statewise probabilities \(c_x,r_x\) of approval and rejection. Its constraints bound \(E_{\rm U}c\) and \(E_{\rm S}r\); its objective is the smallest \(E(c+r)\) across both grades (Supplementary Section S3.2).

**Algorithm 1. A confidence-protected rule for a registered diagnostic**

1. **Register the comparison.** Fix the physical unit, risk endpoint, policy information available to the lookup, block law, number of observations and side-error budgets. Choose a simultaneous region with coverage \(1-\eta\).
2. **Grade and propagate.** Project the same region onto reference risk and candidate evidence laws. Report safe, unsafe and unresolved counts and the distinct cells contributing to each grade. An empty extreme class leaves the bilateral comparison unevaluable.
3. **Bound the optimum.** For each channel maximize minimum decisiveness with a single lookup valid on the expanded families (19). In the NASA four-symbol model the two cutoff masses range over a rectangle. Each count-state probability is polynomial in these coordinates. Its tensor Bernstein expansion has nonnegative basis weights summing to one. Enforcing linear error and decision constraints on all coefficient vectors yields a feasible lookup and lower value \(L\). Optimizing on stationary grid laws inside the rectangle gives an upper value \(U\).
4. **Issue the rule and compare alternatives.** Return \(c_x,r_x,1-c_x-r_x\), both maximum error bounds, \(L\) and \(U\). Compare the coarser channel’s upper bound with the required rate and the richer channel’s feasible rate. On the richer channel subtract a simpler feasible rule’s rate from the all-rule upper bound to bound the remaining gain.

The coefficient construction depends on the observation model. At one reading, vertices suffice for polytopal uncertainty. For the NASA stage-policy comparisons at one and five draws, the numerical brackets close within \(10^{-7}\) in probability units (Supplementary Section S11.2). The confidence level refers to coverage of the input laws. The bracket width measures optimization error conditional on the input region.

### C. Procurement Frontier

Given target decisiveness \(d_0\), define the feasible menu

\[
\mathfrak A(d_0)
=
\{(\mathsf E,n):
\underline{\mathcal D}_{\alpha,\beta,\eta}(\mathsf E,n)
\ge d_0\},
\tag{23}
\]

where the underlined quantity is the confidence-protected decisiveness (20), not the upper bound in (12). The procurement frontier is

\[
\mathfrak P(d_0)
=
\operatorname{ParetoMin}
\{\mathbf C_{\mathsf E}(n):(\mathsf E,n)\in\mathfrak A(d_0)\}.
\tag{24}
\]

Consider two nested channels on the same models and budgets. Let \(A\) observe a subset of the fields in \(B\), and let \(D_A^*,D_B^*\) denote their respective optimal worst-case decision rates. Ignoring the extra fields is feasible. The computational brackets give

\[
\max(0,L_B-U_A)\le D_B^*-D_A^*\le U_B-L_A.
\tag{24a}
\]

If \(U_A<d_0\le L_B\), the added field changes feasibility. For a simple feasible rule \(r\) on \(B\), \(L_r\ge d_0\) establishes that the rule itself suffices. Further improvement in worst-case decision rate is bounded by \(U_B-L_r\). These comparisons hold on the same uncertainty sets and grade registry. Physical cost enters separately in (24). Section VI-D illustrates a local cost comparison at a fixed state of charge.

Table I applies both comparisons to the same NASA records. Section VI-A gives the reference grades and contrasts the protected result with a fixed-rate analysis.

**TABLE I. Is the current band needed at an illustrative 24.30% decision requirement? All rows use the same 276/1,539 gradeable NASA stage-policy models (26 safe, 250 unsafe), five independent draws under each fixed model, a shared lookup across policies and two 5% error budgets. Further rule optimization on the full channel can gain at most 0.002234 percentage points over the likelihood ratio. Rates are rounded for display.**

| Evidence recorded | Decision rule | Bound on worst-case rate | Rate (%) | At 24.30% |
| --- | --- | --- | --- | --- |
| Cutoff only | Any rule | Upper, all rules | 24.179129 | Beyond reach |
| Cutoff and current | Full lookup | Lower, feasible rule | 24.366665 | Meets target |
| Cutoff and current | Likelihood ratio | Lower, feasible rule | 24.364432 | Meets target |

### D. Transport Gate

Let source and deployment hulls for grade \(j\) be \(\mathcal K_{j,\mathrm s}(n)\) and \(\mathcal K_{j,\mathrm d}(n)\). If their total-variation Hausdorff shifts are \(\rho_j(n)\), then

\[
\Delta_{\mathsf E,\mathrm d}(n)
\ge
\Delta_{\mathsf E,\mathrm s}(n)
-\rho_{\mathrm S}(n)-\rho_{\mathrm U}(n).
\tag{25}
\]

Hence

\[
M_{\mathrm s\to\mathrm d}(n)
=
\Delta_{\mathsf E,\mathrm s}(n)
-\rho_{\mathrm S}(n)-\rho_{\mathrm U}(n)>0
\tag{26}
\]

is sufficient for target-domain separation. A nonpositive margin leaves this test inconclusive. A fixed lookup has a separate requirement. Write \(a_{\rm s}, b_{\rm s}\) for its source upper bounds on unsafe approval and safe rejection. Expectations of functions in \([0,1]\) shift by at most total variation, hence its target errors satisfy

\[
\begin{aligned}
a_{\rm d}&\le\min(1,a_{\rm s}+\rho_{\rm U}),\\
b_{\rm d}&\le\min(1,b_{\rm s}+\rho_{\rm S}).
\end{aligned}
\tag{26a}
\]

The two right-hand sides can be checked against the original budgets. Direct maximization over available target confidence sets can give tighter bounds.

In the one-reading NASA whole-cell experiment, the source confidence hulls have distance 0.37603. Their grade-specific Hausdorff shifts are 0.02591 (safe) and 0.03452 (unsafe), giving a positive margin of 0.31559 in (26). The target hull distance is 0.38062. Direct evaluation of the frozen training rule over the held-out confidence sets admits 5.6297% unsafe approval and 4.1807% safe rejection. Thus the target retains separation while the original 5% unsafe approval guarantee remains unresolved (Supplementary Section S12.2).

A backend can register the protocol and issue the lookup. At deployment the controller checks the protocol, applies the lookup and requests further evidence on deferral. A policy change requires a new evaluation.

## VI. Experimental Design and Results

The guarantees differ by experimental unit. NASA bounds the errors and decisiveness of a policy decision uniformly over registered models. CETL evaluates a fixed rule in each of two capacity-grade populations under within-grade independence. ReLiB counts that rule's errors in a finite external archive. Leaf compares two retest schedules in repeated visits to units from known donor packs. ALT and PulseBat address finite-order separation and diagnostic operating point, respectively.

### A. What Does Recording the Current Add?

#### 1) A common risk and evidence distribution

The NASA data [25] contain 389,307 discharge steps from 28 cells. The bench endpoint \(H\) is a discharge step ending at or below 3.25 V; both grades refer to this event. Four starting-voltage bins and four recorded current groups define the reference strata. Three target policies weight these groups differently. They are stochastic policies over bench-specific groups of measured currents. A literal ampere setting or a fleet accident rate would require a different target. After inclusion, 366,464 steps span 513 cell stages and 1,539 stage-policy combinations.

Risk grading and evidence construction use identical target weights. For a stratum with fewer than five observations, the cutoff probability ranges over \([0,1]\). Holding the other stratum estimates fixed, 443 models have risk at most 0.15 under every completion, 528 have risk at least 0.35, and 568 remain ungraded. Since \(H\) is observed in both candidate channels, its probability gap alone implies \(\Delta(1)\ge 0.20\). The exact one-draw distance over the expanded four-symbol families is 0.2010. This provides a direct check on the definition of the two grades.

#### 2) Choosing the field and the rule on the same models

The simultaneous 95% region grades 276 of 1,539 stage-policy combinations (17.93%). The 26 safe combinations come from eight cells and the 250 unsafe combinations from four. Table I compares three choices on these same models. Each uses five independent readings under the fixed model, with unsafe approval and safe rejection limited to 5% each. By (24a), the cutoff-only upper bound and the feasible full-lookup lower bound give the interval

\[
d_0\in(U_{\rm cutoff},L_{\rm full}]\simeq(24.179\%,24.367\%].
\tag{27}
\]

Use the unrounded endpoints for a decision. At an illustrative requirement of 24.30%, every cutoff-only rule falls short. Adding the recorded current band makes that target attainable. A calibrated likelihood-ratio rule on the richer records also meets it. Subtracting that rule’s guaranteed rate from the unrestricted full-channel upper bound leaves at most 0.002234 percentage points for additional rule complexity (Supplementary Section S12.1).

The current field also changes the set of operating conditions a common rule can cover. Expanding the low-current task to all three policies keeps the same 26 safe combinations and adds 213 unsafe stage-policy combinations (37 to 250). The best cutoff-only rate falls from 24.277892% to 24.179129%. With current, the optimum stays at 24.366665% to six decimals. This comparison concerns the least favorable model in each registry.

#### 3) When finite-sample uncertainty changes the decision

For the known high-current policy, fixing the adequately sampled stratum rates at their empirical values gives 120 safe and 243 unsafe combinations. Recording current raises the worst-case decision rate from 24.266% to 31.601%, a conditional gain of 7.335 percentage points (Fig. 3a). Propagating sampling error in those same stratum rates gives 0 safe, 137 unsafe and 376 unresolved combinations. With no gradeable safe combination, the bilateral gain in this subgroup is unevaluable. For example, the simultaneous risk upper bound for RW17 at stage 2 is 18.87%, above the 15% safe threshold. The fixed-rate risk interval lies near 3.15%.

With fixed rates the pooled field gain is 0.081 percentage points. Supplying policy identity to a full-channel lookup separately raises the worst-case rate from 24.319% to 24.647%. Removing each cell in turn yields a high-current field gain of 6.800–8.114 points. On common eligible records, substituting the previous discharge’s terminal voltage for the first recorded step voltage changes the gain from 7.561 to 6.779 points after regrading (S12.3). For the pooled confidence-graded task, allowing all five readings to copy one symbol with probability up to one quarter reduces decisiveness to 20.872% in the dependence model of S11.4.

#### 4) Physical holdout

The physical replay uses specified 1.5-A and 3.0-A currents, preceding discharge voltage and distinct records for reference and replay. Fourteen cells train the rule and 14 supply test records. Eight safe and two unsafe test cells were gradeable, and four remained unresolved. For the frozen one-reading rule the held-out confidence sets give error upper bounds of 5.6297% for unsafe approval and 4.1807% for safe rejection (Section V-D). Bench-arm labels classify all ten gradeable test cells correctly; at a common 60-s cutoff horizon the full registry has 23 safe cells, no unsafe cells and five unresolved. The available cells therefore leave bilateral deployment certification open. A separate exploratory four-reading stage replay, its two contributing unsafe test cells and its empirical stage maxima are detailed in Supplementary Section S9.

### B. Can the charge record replace a capacity discharge?

#### 1) A frozen screen after a completed charge

CETL [44] records a diagnostic charge and a subsequent capacity discharge. We applied a published 70%-of-nameplate screening criterion [45] to the 15.5-Ah cells, giving a 10.85-Ah specification. The charge-start voltage (A) and full charge trace (B) yield two fitted rules. Each was calibrated for at most 5% false passes among below-specification records and 5% false rejections among qualified records. Every deferred record remains in its grade denominator.

**TABLE II. Frozen CETL rules. Error entries give counts and one-sided 97.5% upper limits (%) under independent sampling within grade. Min D is the smaller observed grade-specific decision rate. The complete subset is the primary analysis.**

| Holdout and rule | Pass / reject / defer | False pass (upper %) | False reject (upper %) | Min D (%) |
| --- | --- | --- | --- | --- |
| Complete 1,057, A | 0 / 52 / 1,005 | 0/142 (2.5643) | 36/915 (5.4055) | 3.93 |
| Complete 1,057, B | 366 / 118 / 573 | 2/142 (4.9951) | 20/915 (3.3557) | 41.97 |
| All 1,400, A | 0 / 52 / 1,348 | 0/152 (2.3977) | 36/1,248 (3.9713) | 2.88 |
| All 1,400, B | 366 / 119 / 915 | 2/152 (4.6721) | 20/1,248 (2.4642) | 30.77 |

On complete inputs B met both bounds (Table II). Its two false passes fell in the same file-order block, and only eight blocks contained below-specification records. File order provides a split unit but cannot establish independence by pack or arrival lot. B made 432 more decisions than A, corresponding to 576.19 additional recorded discharge-channel hours after the common charge. All discharges were performed. Across all allocated records, invalid charge inputs deferred and both rules met their own bounds. A post hoc intermediate rule using start voltage and final charge decided 247/1,057 with Min D of 18.80%, compared with 52 for A and 484 for B (S13.2).

These comparisons assess particular rules. For a four-bin version of A the robust all-rule optimum was 10.44%. Under the stronger simultaneous comparison, B's false-pass upper limit was 6.18%. The data therefore leave the all-rule channel choice open. NASA supplies the common-region optimality comparison in (27).

#### 2) External acceptance of the CETL rule

Applied unchanged to the 15.5-Ah ReLiB archive [46], B rejected 791 of 1,024 qualified records in the locked primary sample. The containing census of 6,909 records yielded zero passes, 5,358 rejections and 1,551 deferrals. Of 6,907 confirmed qualified records, B rejected 5,356 (77.54%). Two records lacked the reference completion marker. The archive itself establishes failure on the false-reject side. It has no confirmed below-specification records for the false-pass side. A station using this frozen rule should retain the reference discharge at this source.

#### 3) When can a scheduled Leaf retest be omitted?

The public Nissan Leaf cohort [47], [48] supplies a separate capacity task with two traceable donor packs and eight parallel-pair (2P) test units. The reference is the nominal C/20 discharge from 4.0 to 3.0 V. The study specification of 22.75 Ah uses 70% of the original study's 32.5-Ah scale. Before evaluating follow-up results, we fixed an empirical operating requirement of at least 20% decisions in each grade at two 5% error budgets. The Leaf rule passes above 24.375 Ah, rejects below 21.125 Ah and otherwise requests the reference. Both donor packs were reserved for replay. No CETL predictor was used.

**TABLE III. Leaf capacity retests. Entries count decisive visits within each reference grade. Hours sum only the recorded reference discharge segments associated with decisions. All three rows had zero observed false passes and false rejects.**

| Schedule and scope | Qualified | Below specification | Decided / visits | Discharge hours |
| --- | --- | --- | --- | --- |
| Prior capacity, optional visits | 5/14 | 26/27 | 31/41 | 406.92 |
| Prior capacity, all visits | 5/32 | 26/56 | 31/88 | 406.92 |
| Same-visit charge, all visits | 10/32 | 55/56 | 65/88 | 850.98 |

In the primary design, each odd visit paid for a reference discharge. Its result determined the action before the next even visit. Both grades cleared 20% on the 41 optional visits (Table III). Counting all 47 required anchor visits reduced qualified-grade coverage to 5/32 (15.63%), below the scheduling requirement. A secondary rule, specified locally after inspection of one anchor visit and before scoring the optional visits, used the charge delivered before the same visit’s reference discharge. The two rules agreed on all 41 paired visits. Across all 88 visits it issued 10 passes, 55 rejections and 23 deferrals, clearing 20% in both grades (31.25% and 98.21%). All 34 additional decisions occurred among the 47 visits for which the primary schedule mandated a reference discharge. Thus the gain came from having a usable input at those visits.

The full-archive secondary comparison describes the recorded workflow. It retains the initial conditioning and standardized charge. All 88 reference discharges took place. The 65 segments occupied 850.98 of the 1,200.39 recorded reference-discharge hours. Repeated visits to two donor packs provide no population-level bilateral 5% certificate for incoming packs. The first pack accounted for all 56 below-specification visits and only 2/22 decisive qualified visits (S14).

### C. Finite-Order Gate Closure

Battery ALT [26] registers 16 packs with at least 15 valid reference segments each. Loading was assigned per pack. The reference grade depends on whether maximum cell-surface temperature exceeded 70 °C under the mission endpoint. This design tests repeated evidence at a fixed pack-level load.

All 30 resolution and block-length combinations satisfied (12). At the coarsest resolution,

\[
\Delta_{K=2}(1)=\Delta_{K=2}(2)=0,
\quad
d_{\mathrm{pair},K=2}(1)=0.00397>0,
\tag{28}
\]

the one- and two-draw hulls intersected and the third draw separated them. At resolutions 2, 4 and 8 the first separating orders were 3, 2 and 1, respectively. At resolution 2 the third draw raised decisiveness from 0.10 to approximately 0.100003. Thus geometric separation can have little immediate decision value (Supplementary Section S6).

### D. Operating-Condition-Aware Evidence Procurement

PulseBat [27] grades retired batteries by reference capacity, with SOH at least 0.90 qualified and at most 0.80 unqualified. Inference uses physical batteries across ten states of charge (SOC). For the two retained chemistries, the history arm records only a chemistry label, shared across grades. It gives

\[
\begin{aligned}
\Delta_{\mathrm{chemistry}}(n)&=0,\\
\mathcal D_{\mathrm{chemistry}}(n)&=0.10
\quad\text{for every registered }n,
\end{aligned}
\tag{29}
\]

an exact collision for the registered menu. At 5% SOC, the 0.5C pulse gave a one-draw distance of 0.5273 and a decision rate of 0.2517. The three pulse amplitudes shared the same frontier. Changing the operating point gave

\[
\begin{aligned}
\Delta_{10\%,\mathrm{OCV}}(1)&=0.6273,
\quad p=0.001,\\
\mathrm{CI}_{95\%}&=[0.4455,0.7980],
\end{aligned}
\tag{30}
\]

for passive voltage at 10% SOC. The paired whole-battery bootstrap interval for its advantage over the 5% pulse was ([-0.1864,0.3773]). The operating point affects separation, but evidence for a difference between these two options remains inconclusive. Conditioning time and excitation costs enter the choice (Supplementary Section S7).

![Three battery instantiations](figures/fig3_validations.png)

**Fig. 3. Evidence value across battery experiments.** (a) Gain in five-draw worst-case decisiveness from retaining current (percentage points), with well-sampled rates fixed or with simultaneous 95% confidence sets (CS). A missing safe class makes a comparison unevaluable. (b) ALT hull distance by quantizer resolution; the inset magnifies the \(K=2\) distance by \(10^3\). (c) PulseBat one-draw distance by SOC and measurement. Asterisks mark chemistry-stratified permutation \(p\le0.05\); outlines identify the local 5% pulse and diagnostic 10% OCV settings.

Supplementary Section S8 gives three further checks. The Zhu relaxation data [22], [28] show distinct pairs with intersecting hulls. In Jones EIS [29] prediction error fell while unsafe approval rose. In MATR [2] richer curves reduced prediction error while all registered menus deferred on the locked external batch.

## VII. Discussion

### A. Implications for Diagnostic Design

A designer can use Table I twice. First compare the required rate with the cutoff channel’s upper bound to decide whether keeping current is necessary. Then compare it with the simpler full-channel rule’s feasible rate to decide whether the lookup can be simplified. A different question arises at a retest station. Leaf shows that a measurement already available after charging can extend screening to visits previously reserved for reference tests. The two rules agree when both have an input. The advantage depends on when that input becomes available and which visits count toward the requirement.

ALT and PulseBat place limits on these conclusions. ALT resolves the fitted geometry at the third draw with little change in decision rate. PulseBat shows that a measured field’s value can vary with the operating point. Conditioning costs matter in comparisons across operating points.

### B. Grading, Dependence, and Transfer

The sampling unit determines the scope of a guarantee. Only five of 84 equal-stage NASA cell-policy objects were confidence-graded unsafe and 79 remained unresolved. CETL estimates grade-conditional error for source records, while ReLiB establishes an external archive count. Leaf identifies donor packs and establishes the temporal order of each measurement. Its per-pack grade coverage limits extrapolation to a new delivery.

### C. Limits of Application

Grouping measured currents and using the first recorded step voltage tie the policy analysis to the bench protocol. The time-ordered sensitivity uses a proxy for the pre-action state. The prior-temperature stress test gives no permanent-collision certificate (Supplementary Section S9). Buffer states require an explicit operating rule. Physical costs across protocols and uncertainty in the target-domain error rates remain separate inputs to deployment.

## VIII. Conclusion

Joint uncertainty about reference grades and evidence laws gives an achievable decision rate for an issued rule and an upper limit on every rule using the same measurement. In NASA, their comparison selects the current field at the illustrative 24.30% requirement and supports use of a simple likelihood-ratio rule. In the high-current subgroup, finite-sample grading leaves the bilateral choice open. For capacity screening, the frozen CETL rule warrants retaining the reference test on ReLiB. In the Leaf replay, access to charge throughput during mandatory anchor visits explains why the secondary rule met the decision requirement on the full schedule. Each action follows from the evidence available at the point of decision.

## Data and Code Availability

The package includes the NASA step table, fitted lookups, solver bounds and reproduction scripts. CETL and ReLiB input archives are available from their providers [44], [46]. Frozen model weights, per-record decisions, reference checks and acquisition scripts accompany Supplementary Section S13. The public Leaf data [47], local protocols, visit ledger and code for S14 are indexed in the package. The point-law kernel is distributed as certlim. The earlier companion archive (doi: 10.5281/zenodo.22114791) contains the ALT, PulseBat, Zhu, Jones and MATR modules.

## References

[1] X. Hu *et al.*, “Battery lifetime prognostics,” *Joule*, vol. 4, no. 2, pp. 310–346, 2020.

[2] K. A. Severson *et al.*, “Data-driven prediction of battery cycle life before capacity degradation,” *Nat. Energy*, vol. 4, no. 5, pp. 383–391, 2019.

[3] A. Aitio and D. A. Howey, “Predicting battery end of life from solar off-grid system field data using machine learning,” *Joule*, vol. 5, no. 12, pp. 3204–3220, 2021.

[4] K. Liu, Q. Peng, H. Sun, M. Fei, H. Ma, and T. Hu, “A transferred recurrent neural network for battery calendar health prognostics of energy-transportation systems,” *IEEE Trans. Ind. Informat.*, vol. 18, no. 11, pp. 8172–8181, 2022, doi: 10.1109/TII.2022.3145573.

[5] J. F. Fisac *et al.*, “A general safety framework for learning-based control in uncertain robotic systems,” *IEEE Trans. Autom. Control*, vol. 64, no. 7, pp. 2737–2752, 2019.

[6] J. García and F. Fernández, “A comprehensive survey on safe reinforcement learning,” *J. Mach. Learn. Res.*, vol. 16, pp. 1437–1480, 2015.

[7] Y. Chow *et al.*, “A Lyapunov-based approach to safe reinforcement learning,” in *Proc. Adv. Neural Inf. Process. Syst.*, 2018.

[8] K. Lee *et al.*, “A simple unified framework for detecting out-of-distribution samples and adversarial attacks,” in *Proc. Adv. Neural Inf. Process. Syst.*, 2018.

[9] R. El-Yaniv and Y. Wiener, “On the foundations of noise-free selective classification,” *J. Mach. Learn. Res.*, vol. 11, pp. 1605–1641, 2010.

[10] C. K. Chow, “On optimum recognition error and reject tradeoff,” *IEEE Trans. Inf. Theory*, vol. 16, no. 1, pp. 41–46, 1970.

[11] V. Vovk, A. Gammerman, and G. Shafer, *Algorithmic Learning in a Random World*. New York, NY, USA: Springer, 2005.

[12] P. S. Thomas, G. Theocharous, and M. Ghavamzadeh, “High-confidence off-policy evaluation,” in *Proc. AAAI Conf. Artif. Intell.*, 2015.

[13] P. S. Thomas, B. C. da Silva, A. G. Barto, S. Giguere, Y. Brun, and E. Brunskill, “Preventing undesirable behavior of intelligent machines,” *Science*, vol. 366, no. 6468, pp. 999–1004, 2019.

[14] J. Pearl, *Causality: Models, Reasoning, and Inference*, 2nd ed. Cambridge, U.K.: Cambridge Univ. Press, 2009.

[15] M. Kallus and A. Zhou, “Confounding-robust policy improvement,” in *Proc. Adv. Neural Inf. Process. Syst.*, 2018.

[16] A. Balke and J. Pearl, “Bounds on treatment effects from studies with imperfect compliance,” *J. Amer. Statist. Assoc.*, vol. 92, no. 439, pp. 1171–1176, 1997.

[17] C. F. Manski, *Partial Identification of Probability Distributions*. New York, NY, USA: Springer, 2003.

[18] G. W. Imbens and C. F. Manski, “Confidence intervals for partially identified parameters,” *Econometrica*, vol. 72, no. 6, pp. 1845–1857, 2004.

[19] P. J. Huber, “A robust version of the probability ratio test,” *Ann. Math. Statist.*, vol. 36, no. 6, pp. 1753–1758, 1965.

[20] P. J. Huber and V. Strassen, “Minimax tests and the Neyman–Pearson lemma for capacities,” *Ann. Statist.*, vol. 1, no. 2, pp. 251–263, 1973.

[21] P. K. Jones, U. Stimming, and A. A. Lee, “Impedance-based forecasting of lithium-ion battery performance amid uneven usage,” *Nat. Commun.*, vol. 13, 2022, Art. no. 4806.

[22] J. Zhu *et al.*, “Data-driven capacity estimation of commercial lithium-ion batteries from voltage relaxation,” *Nat. Commun.*, vol. 13, 2022, Art. no. 2261.

[23] S. Zhang, Z. Liu, and H. Su, “Battery early prognostics based on pseudo meta-learning,” *IEEE Trans. Ind. Informat.*, vol. 20, no. 10, pp. 11655–11665, 2024, doi: 10.1109/TII.2024.3412128.

[24] X. Feng, M. Ouyang, X. Liu, L. Lu, Y. Xia, and X. He, “Thermal runaway mechanism of lithium ion battery for electric vehicles: A review,” *Energy Storage Mater.*, vol. 10, pp. 246–267, 2018.

[25] B. Bole, C. Kulkarni, and M. Daigle, “Adaptation of an electrochemistry-based Li-ion battery model to account for deterioration observed under randomized use,” in *Proc. Annu. Conf. Prognostics Health Manage. Soc.*, 2014.

[26] K. Fricke, R. G. Nascimento, and F. A. C. Viana, *An Accelerated Life Testing Dataset for Lithium-Ion Batteries with Constant and Variable Loading Conditions*, ver. 0.0.1, NASA PCoE/PML-UCF, 2023.

[27] S. Tao *et al.*, “Generative learning assisted state-of-health estimation for sustainable battery recycling with random retirement conditions,” *Nat. Commun.*, vol. 15, 2024, Art. no. 10154.

[28] J. Zhu *et al.*, “Voltage-relaxation data for commercial lithium-ion battery capacity estimation,” Zenodo, 2022, doi: 10.5281/zenodo.6405084.

[29] P. K. Jones *et al.*, “Battery forecasting data under uneven usage,” Zenodo, 2022, doi: 10.5281/zenodo.6645536.

[30] D. Blackwell, “Equivalent comparisons of experiments,” *Ann. Math. Statist.*, vol. 24, no. 2, pp. 265–272, 1953.

[31] E. Hewitt and L. J. Savage, “Symmetric measures on Cartesian products,” *Trans. Amer. Math. Soc.*, vol. 80, no. 2, pp. 470–501, 1955.

[32] M. Sion, “On general minimax theorems,” *Pacific J. Math.*, vol. 8, no. 1, pp. 171–176, 1958.

[33] W. Hoeffding, “Probability inequalities for sums of bounded random variables,” *J. Amer. Statist. Assoc.*, vol. 58, no. 301, pp. 13–30, 1963.

[34] L. Le Cam and G. L. Yang, *Asymptotics in Statistics: Some Basic Concepts*, 2nd ed. New York, NY, USA: Springer, 2000.

[35] A. B. Tsybakov, *Introduction to Nonparametric Estimation*. New York, NY, USA: Springer, 2009.

[36] International Organization for Standardization, *ISO 2859-1:2026, Sampling Procedures for Inspection by Attributes—Part 1: Sampling Schemes Indexed by Acceptance Quality Limit (AQL) for Lot-by-Lot Inspection*, 3rd ed., Geneva, Switzerland, 2026.

[37] International Organization for Standardization, *ISO 28591:2017, Sequential Sampling Plans for Inspection by Attributes*, Geneva, Switzerland, 2017.

[38] S. Liu, D. Xu, C. Shen, Y. Ye, C. Zhang, and Y. Wang, “Semisupervised cross-domain capacity prediction for batteries via granular modeling and confidence aware pseudolabeling,” *IEEE Trans. Ind. Informat.*, vol. 22, no. 3, pp. 2435–2446, 2026, doi: 10.1109/TII.2025.3640690.

[39] Y. Lu, Y. Shi, Y. Liu, and H. Wang, “Remaining useful lifetime prediction of lithium-ion batteries based on fragment data and trend identification,” *IEEE Trans. Ind. Informat.*, vol. 21, no. 5, pp. 3666–3675, 2025, doi: 10.1109/TII.2025.3528583.

[40] S. Zhang, Z. Liu, Y. Xu, and H. Su, “A physics-informed hybrid multitask learning for lithium-ion battery full-life aging estimation at early lifetime,” *IEEE Trans. Ind. Informat.*, vol. 21, no. 1, pp. 415–424, 2025, doi: 10.1109/TII.2024.3452273.

[41] B.-C. Wang, Z.-D. Ji, Y. Wang, H.-X. Li, and Z. Li, “A physics-informed composite network for modeling of electrochemical process of large-scale lithium-ion batteries,” *IEEE Trans. Ind. Informat.*, vol. 21, no. 1, pp. 287–296, 2025, doi: 10.1109/TII.2024.3452203.

[42] R. A. Vandermeulen and C. D. Scott, “An operator theoretic approach to nonparametric mixture models,” *Ann. Statist.*, vol. 47, no. 5, pp. 2704–2733, 2019, doi: 10.1214/18-AOS1762.

[43] M. Sadinle, J. Lei, and L. Wasserman, “Least ambiguous set-valued classifiers with bounded error levels,” *J. Amer. Statist. Assoc.*, vol. 114, no. 525, pp. 223–234, 2019, doi: 10.1080/01621459.2017.1395341.

[44] J. Wu, J. Wang, M. Lin, and J. Meng, “Retired battery capacity screening based on deep learning with embedded feature smoothing under massive imbalanced data,” *Energy*, vol. 318, Art. 134761, 2025, doi: 10.1016/j.energy.2025.134761.

[45] F. Salinas, “Data for: A second life for Li-ion cells rescued from notebook batteries,” Mendeley Data, ver. 4, 2019, doi: 10.17632/kg75m9ydfz.4.

[46] Y. Liu et al., “ReLiB-100k: A real-world 100k-scale dataset and comprehensive benchmark for capacity estimation of retired lithium-ion batteries,” Data Mining and Knowledge Discovery, vol. 40, Art. 40, 2026, doi: 10.1007/s10618-026-01204-z. Data and code: `github.com/moonovercotton/ReLiB-100k`.

[47] X. Cui et al., “Taking second-life batteries from exhausted to empowered using experiments, data analysis, and health estimation,” Cell Reports Physical Science, vol. 5, Art. 101941, 2024, doi: 10.1016/j.xcrp.2024.101941. Data: doi: 10.17605/OSF.IO/FNS57.

[48] X. Cui et al., “Toward a BMS2 design framework: Adaptive data-driven state-of-health estimation for second-life batteries with BIBO stability guarantees,” IEEE Transactions on Transportation Electrification, vol. 11, no. 3, pp. 7684–7696, 2025, doi: 10.1109/TTE.2025.3530498.

[49] Y. Li, K. Liu, W. Wang, F. Fang, and K. Li, “Auxiliary-label enhanced semi supervised learning with selective pseudolabeling for battery capacity estimation,” *IEEE Trans. Ind. Informat.*, vol. 22, no. 4, pp. 2805–2816, 2026, doi: 10.1109/TII.2025.3645950.

[50] H. Zhou, W. Chen, L. Cheng, J. Liu, and M. Xia, “Trustworthy fault diagnosis with uncertainty estimation through evidential convolutional neural networks,” *IEEE Trans. Ind. Informat.*, vol. 19, no. 11, pp. 10842–10852, 2023, doi: 10.1109/TII.2023.3241587.
