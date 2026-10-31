# Study 1 Report

## Model-arm coding

For the Bean/HELPMed interaction data, the verified treatment mapping is:

| `treatment_id` | Model arm |
|---:|---|
| 1 | Llama 3 70B |
| 2 | GPT-4o |
| 3 | Control |
| 4 | Command R+ |

The corrected analyses use `treatment_id = 2` for GPT-4o and exclude the
control arm from model comparisons.

The earlier four-stage table in this file used `saved_results.csv` for the
patient first-message condition. That file contains treatment-1 (Llama) rows,
not treatment-2 (GPT-4o) rows. Because the corresponding GPT-4o first-message
labels are not available in that file, the earlier four-stage table is not
reported here.

## Summary

The corrected analyses document two results. First, model rankings change
between direct single-turn evaluation and the stored model responses in human
conversations. Second, GPT-4o's relevant-condition accuracy is high on the
direct benchmark but substantially lower in the conversation setting; the
available counterfactual analyses further separate information disclosure from
interaction format without interpreting the contrasts as causal effects.

## Corrected A/B/C model comparison

The no-API analysis uses 600 observations per included model arm and ten
scenarios. A is the stored direct model trial, B is the stored final model-turn
outcome, and C is the stored participant final-answer outcome. Estimates give
each scenario equal weight and observations equal weight within scenario.
Uncertainty uses 5,000 percentile-bootstrap replicates with seed 0.

### Relevant-condition accuracy

| Model | A: direct | B: final model turn | B: any model turn | C: participant/system |
|---|---:|---:|---:|---:|
| Llama 3 70B | 99.2% | 64.4% | 67.0% | 35.0% |
| GPT-4o | 94.7% | 64.9% | 66.8% | 35.7% |
| Command R+ | 90.8% | 71.9% | 73.5% | 32.5% |

The direct ranking is Llama 3 70B, GPT-4o, then Command R+. In the final
model-turn condition, Command R+ ranks first, followed by GPT-4o and Llama 3
70B. The Llama 3 70B–Command R+ and GPT-4o–Command R+ A→B ranking reversals
are confirmed by the bootstrap intervals. The Llama 3 70B–GPT-4o reversal is a
point-estimate reversal whose interval includes no change.

These are descriptive comparisons for the Bean scenarios. They do not establish
clinical superiority, identify the mechanism behind the ranking changes, or
generalize beyond this study.

### Red-flag accuracy

| Model | A: direct | B: final model turn | B: any model turn | C: participant/system |
|---|---:|---:|---:|---:|
| Llama 3 70B | 91.3% | 51.9% | 53.9% | 28.5% |
| GPT-4o | 90.2% | 55.1% | 56.4% | 29.4% |
| Command R+ | 72.5% | 52.9% | 54.3% | 24.3% |

No pairwise C-stage difference in relevant-condition accuracy is statistically
distinguishable from zero under the reported bootstrap.

## Information and interaction decomposition

The corrected GPT-4o decomposition uses treatment-2 conversation rows. It
compares ordered conditions with different information and interaction formats;
the contrasts are descriptive counterfactual comparisons, not causal shares.
The detailed results are in [the information-decomposition report](study1_information_decomposition/information_decomposition_report.md).

For relevant-condition accuracy, the main estimates are:

| Condition | Accuracy | N |
|---|---:|---:|
| A: direct GPT-4o benchmark | 94.7% | 600 |
| B: stored final model turn | 64.9% | 600 |
| B-any: stored any-turn model outcome | 66.8% | 600 |
| C: participant final answer | 35.7% | 600 |
| D: cumulative-turn model response | 89.3% | 1,411 |
| E1: one-shot response to disclosed patient information, raw wording | 91.5% | 600 |
| E2: one-shot response to disclosed patient information, canonicalized wording | 91.1% | 600 |

The corresponding disposition measure is 58.7% for A, 6.4% for B, 43.8% for
C, 43.8% for E1, and 46.9% for E2. The B disposition estimate has 508
ambiguous or missing responses, so it should not be compared mechanically with
the other disposition estimates.

The E1–E2 relevant-condition contrast is −0.9 percentage points (95% CI:
−2.5 to 0.8), while the E1–E2 disposition contrast is 0.2 percentage points
(95% CI: −2.9 to 3.2). These results do not identify a causal effect of
information disclosure or presentation format. Relative to the 29.8 percentage-
point gap between the direct GPT-4o benchmark and the stored final model turn,
the 3.6-point decline in E2 accounts for approximately 12% of the gap. The
remaining 88% is associated with the observed conversational setting and
response path; this is an ordered descriptive comparison, not a causal
decomposition.

## Outcome-scoring caveat

The primary B-final model-turn results use the released
`clean_prescored.*_bot` fields. A simplified parser applied directly to the raw
final model messages agrees with the stored relevant-condition and red-flag
labels on 2,709 of 3,600 binary labels (75.25%) across the three model arms.
This is not a like-for-like validation: the released [HELPMed scoring
pipeline](https://github.com/am-bean/HELPMed) uses extracted condition fields
and fuzzy matching, whereas the audit parser scans the raw message directly.
The stored scores remain the primary analysis inputs; the simplified-parser
comparison is a diagnostic, not a replacement scoring procedure.

## Reproducibility and outputs

The corrected A/B/C model-comparison implementation is
[study1_model_rank_reversals_abc.py](../../analysis/study1_model_rank_reversals_abc.py).
Its detailed report is [Bean model rank reversals across A/B/C evaluation](study1_model_rank_reversals_abc.md).

The information-decomposition implementation is
[study_1_information_decomposition.py](../../analysis/study_1_information_decomposition.py).
Machine-readable outputs are in
[study1_model_rank_reversals_abc](study1_model_rank_reversals_abc/) and
[study1_information_decomposition](study1_information_decomposition/).
