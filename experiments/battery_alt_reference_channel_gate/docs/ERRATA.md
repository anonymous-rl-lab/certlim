# ERRATA — battery ALT gate package

Every entry here is a deviation from, or a correction to, a file that had already been
hashed. Nothing below is a threshold retune to make a gate pass; where a gate failed it
is reported as failed.

---

## A. v01 → v02: the registered design was not estimable (G0 FAILED)

**What v01 registered.** `config/registered.json` (sha256 `ee138dbc…`) defined a unit
θ = (pack, life stage), an action A = the discharge current binned into five levels,
three deployment policies π, and a policy risk
Ψ(θ,π) = Σ_a π(a) · P(hazard | θ, a). Grades came from tertiles of Ψ.

**What the data actually contain.** `scripts/03_g0_feasibility.py` →
`results/G0_feasibility.json`:

| quantity | value |
|---|---|
| θ units | 104 |
| action bins per θ (median / max) | 1 / 2 |
| θ units with exactly one action bin | 83.7 % |
| action bins with ≥5 missions per θ (median) | 1 |
| within-θ current spread, A (median / max) | 0.167 / 9.44 |
| action bins per **pack over its whole life** (median / max) | 1 / 2 |
| packs covering ≥3 action bins | 0 % |
| within-mission current variation `I_max/I_med` (median) | 1.029 |

The dataset README says so directly: *regular* packs are cycled at one load level for
life, *second life* packs at constant current, and *recommissioned* packs change load
**between life stages**. The load is assigned per pack, or at most per pack × life
stage. It is never assigned per mission.

**Consequence.** With one covered action bin per θ, Ψ(θ,π) reduces to that bin's hazard
rate and is constant in π by construction. The v01 run showed exactly this signature —
three deliberately different policies gave mean Ψ of 0.478 / 0.460 / 0.446 and a
degenerate tertile pair τ = (0.00, 0.99).

**Decision.** G0 is recorded as FAILED. The π axis is dropped for this dataset, and with
it **G5 (policy switch)**, which has no estimable target here. G7 was always to be run on
NASA Randomised-Walk and is unaffected. The v01 config and its degenerate output are kept
in the package; they are not deleted and not repaired.

v02 (`config/registered_v02.json`) is a **different experiment on the same data**, not a
retune of v01: the unit is the pack, the grade comes from the pack's hazard rate under
its own operational load, and the evidence channel is the pack's *reference discharge* —
a standardised 2.52 A probe (measured 2.520 ± 0.001 A across all 481 reference blocks
and all 26 packs). That is the paper's own setting: certify from a cheap standardised
bench measurement, while the hazard occurs under field load.

---

## B. Four errors in the v02 gate text (`config/errata_corrections.json`)

Found after the first v02 run. The as-registered verdicts are kept in
`results/gates_v02_asregistered.json`.

| id | registered | correct | source |
|---|---|---|---|
| **E1** | Δ_E(n) non-increasing in n | Δ_E(n) **non-decreasing**; hence G_E(n) non-increasing | Thm 1(2), eq (22b) |
| **E2** | n⋆ = min{n : Δ_E(n) ≤ 0.05} | n⋆ = inf{n : G_E(n) = 0} = inf{n : Δ_E(n) > 0} | eq (19), (20), (23) |
| **E3** | Sion tolerance 1e−8 | 1e−6 | HiGHS feasibility tolerance is 1e−7, so 1e−8 was unachievable by construction on the largest LPs |
| **E4** | "permanent obstruction ⟺ hulls collide at n = 1" | ⟺ an **exact pairwise** collision P_{θS} = P_{θU} | eq (24) |

E1 and E2 are the same mistake written twice: Δ_E(n) is the separation *available* from n
samples, so it grows with n. I had it backwards. Under the registered wording G3 and G4
both fail; under the correct wording both pass.

E4 matters more than a wording fix. Hull intersection at n = 1 is *necessary* but not
sufficient for permanent obstruction — the theory chapter says so explicitly (§ "这一区分
修正了一个过度绝对化的口号"). The corrected test measures the minimum **pairwise** TV as
well as the hull TV, and the two come apart in this data (see `results/gates_v02.json`,
`permanent_obstruction`). That is the finding, not a bug.

---

## C. `max_min_decisiveness` rewritten with a sparse LP

The dense constraint matrix used in the NASA RW package needs
(|S|+|U|+2·n_states) × (2·n_states+1) float64 entries. At K = 8, n = 10 that is 19 448
count states and ≈ 6 GB; the first v02 run was killed by the OOM killer.

`src/alt_gate/core.py` now builds the same LP as a `scipy.sparse` COO matrix. This is a
performance change only. `tests/test_core.py::test_sparse_matches_dense` keeps the old
dense implementation and asserts agreement to 1e−9 on 25 random problems.

---

## D. Two wrong assertions in my own test file, corrected before use

1. `test_multinomial_zero_probability_symbol` compared an `exp(gammaln(...))` result to
   `0.125` with `==`. Replaced by a 1e−12 tolerance.
2. `test_two_point_attainment` asserted 𝒟 = min{1, α+β+TV} for *every* two-point
   experiment. **That is false** and the test caught it (𝒟 = 0.1428 against a bound of
   0.2105). The bound of Theorem 1(1) is an inequality that is generally strict; it is
   tight exactly at two boundaries — Δ = 0 forces 𝒟 = α+β (eq 22), and α+β+Δ ≥ 1 forces
   𝒟 = 1. The file now has `test_bound_holds_and_is_not_generally_tight`,
   `test_attainment_at_collision` and `test_attainment_at_saturation` instead, and the
   G2 gate was rewritten to test the collision case rather than an arbitrary pair.

---

## E. G7 on NASA RW: registered criteria not met, and the reason is not policy transport

`results/G7_rw_holdout.json`. G7a (the registered cross-arm test) gives median |bias|
0.224 against a criterion of ≤ 0.05 — **FAILED** — while passing the Spearman criterion
(ρ = 0.783 ≥ 0.7).

Two controls were added to interpret that, both reported as supplementary and neither
substituted for the registered test:

- **G7b**, the same functional with source and target being two disjoint halves of the
  *same* cell's log: median |bias| 0.016, ρ = 0.990. So the reweighting identity and its
  estimation are sound when the unit is held fixed; the G7a bias is not noise.
- **G7c**, the same cross-arm bias evaluated at each of the three policies in turn:
  0.172 (skew_high) / 0.160 (uniform) / 0.092 (skew_low). The bias is about as large when
  evaluated at a policy the target arm **never ran** as at the one it did.

In NASA RW an arm is assigned per cell, so arm and unit are perfectly confounded. The
honest reading is that the gap is a unit/arm level shift, and this dataset cannot
separate it from policy-transport failure. What the number does supply is a measured
drift for cross-unit transport — 0.224 as the registered G7a statistic, 0.092–0.172
across the three policies in G7c — against α + β = 0.10, i.e. a negative margin, so
cross-unit transport is *not* certified here.

---

## F. The v02 freeze has no wall-clock timestamp

The NASA RW package stamped `frozen_utc` into `results/freeze.json` before anything was
computed. The v02 pipeline here did not: `scripts/04_build_reference_experiment.py` fixes
the grades and the quantiser cut points and computes no Δ or 𝒟, but it never wrote a
timestamp, and `results/freeze_v02.json` was rewritten afterwards to add the protocol
hashes — so its mtime is **not** the freeze time and is not presented as one. The field
reads `not recorded`.

What is auditable is the pair of digests: `config/registered_v02.json`
(`b5efc1e4…`) and `docs/PROTOCOL_v02.md` (`efc52c0e…`) were fixed before script 04 ran,
and script 05 — the one that computes Δ and 𝒟 — reads them and never writes them. A
rerun of `scripts/run_all.sh` reproduces every result file byte-for-byte against
`MANIFEST.sha256`, which is the stronger check anyway. Future packages should stamp the
time as RW did.
