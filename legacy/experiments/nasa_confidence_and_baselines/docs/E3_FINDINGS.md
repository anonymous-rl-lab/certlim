# E3 findings

Protocol frozen (sha256 in config/), predictions written before the run, two errata recorded.

## Verdicts on the registered predictions

| | statement | verdict |
|---|---|---|
| P1 | the frontier rule respects both side errors on every channel | **holds** (0.0500 / 0.0500 everywhere) |
| P2 | frontier decisiveness <= alpha+beta on the adversarial channel | **fails as written** |
| P3 | a baseline looks accurate while breaching alpha | **holds** |
| P4 | all baselines notice instead | does not hold |

P2 fails for a reason worth more than the prediction: the constructed collision is
exact only at n = 1. Against the theorem's own bound min{1, alpha+beta+Delta(n)} the
rule is inside at every n (0.1000 <= 0.1000 at n=1; 0.1005 <= 0.1035 at n=5). P2 was
written assuming the collision was permanent. It is not.

## The constructed collision is a delay, not an obstruction

| n | 1 | 2 | 3 | 4 | 5 | 8 |
|---|---|---|---|---|---|---|
| Delta(n) | 0.000000 | 0.000454 | 0.001370 | 0.002283 | 0.003501 | 0.008196 |

n_star = 2, and the minimum cross-grade pairwise TV on that channel is 6.74e-3 > 0.
An adversary optimising over the whole latent-state-dependent policy family drove the
one-unit hull distance to exactly zero but could not create an exact pairwise collision,
so by Theorem 1(3) the obstruction cannot be permanent, and two units reopen the gate.

## The head-to-head

Worst case is over registered models; balanced accuracy is the baselines' own objective.
Every baseline is tuned twice and both tunings are reported.

Registered channel, n = 5 (Delta = 0.3121):

| method | tuned for | unsafe->Certify | safe->Reject | decisive | bal acc |
|---|---|---|---|---|---|
| frontier | worst case | 0.0500 | 0.0500 | 0.2007 | 0.276 |
| likelihood ratio | accuracy | **0.4572** | 0.3985 | 1.0000 | **0.932** |
| likelihood ratio | worst case | 0.0079 | **1.0000** | 1.0000 | 0.519 |
| OOD distance | accuracy | 0.3856 | 0.3023 | 1.0000 | 0.925 |
| conformal | accuracy | 0.3424 | 0.3775 | 0.6296 | 0.868 |
| conformal | worst case | 0.0000 | 0.0000 | **0.0000** | 0.000 |

Adversarial channel, n = 5 (Delta = 0.0035, so the theorem caps decisiveness at 0.1035):

| method | tuned for | unsafe->Certify | bal acc |
|---|---|---|---|
| frontier | worst case | 0.0500 | 0.179 |
| likelihood ratio | accuracy | **0.7475** | **0.943** |
| OOD distance | accuracy | 0.7172 | 0.939 |
| conformal | accuracy | 0.3466 | 0.863 |

The pattern is the same on all four channels and both block lengths: a baseline can hold
one side error down or the other, never both, and the one that can abstain buys safety
only by abstaining completely. None of this says the baselines are poor predictors. It
says a predictor tuned on its own criterion carries no bilateral guarantee, and on a
channel the theorem caps at 0.10 decisiveness a 94%-accurate rule still certifies the
worst registered unsafe model three times in four.
