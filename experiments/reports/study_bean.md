---

# Bean study summary

# Bean Study Report

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
The detailed results are in the information-decomposition outputs under `outputs/study_bean/information_decomposition/`.

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
[study_bean.py](../../analysis/study_bean.py).
Its detailed outputs are under `outputs/study_bean/model_rank_reversals/`.

The information-decomposition implementation is
[study_bean.py](../../analysis/study_bean.py).
Machine-readable outputs are in
`model_rank_reversals/` and `information_decomposition/`.


---

# Bean information and interaction decomposition

# Bean Information and Interaction Decomposition

This report was generated from the saved records and counterfactual JSONL outputs.
The comparisons are ordered descriptive counterfactual contrasts, not causal shares.
A's disposition row is the newly parsed raw-response outcome; Bean et al.'s original GPT-4o direct disposition benchmark is 64.7% and is reported separately below.
E1 is a one-shot GPT-4o response to the concatenated patient messages in their original wording. E2 is a one-shot GPT-4o response to the same disclosed patient information after a GPT-assisted, source-validated rewrite into vignette-style propositions; E2 is not the hidden complete case.

## Main estimates

condition             outcome  estimate   n  ambiguous_or_missing_disposition   ci_low  ci_high
        A disposition_correct  0.586667 600                                 0 0.576667 0.595000
        A    relevant_correct  0.946667 600                                 0 0.933333 0.960000
        A    red_flag_correct  0.901667 600                                 0 0.896667 0.906667
        B disposition_correct  0.063684 600                               508 0.046013 0.082755
        B    relevant_correct  0.648712 600                               508 0.606741 0.689150
        B    red_flag_correct  0.550652 600                               508 0.510066 0.592670
    B_any disposition_correct  0.063684 600                               508 0.046013 0.082755
    B_any    relevant_correct  0.668202 600                               508 0.626403 0.708011
    B_any    red_flag_correct  0.563797 600                               508 0.523022 0.604561
        C disposition_correct  0.438158 600                                 0 0.398287 0.479150
        C    relevant_correct  0.356731 600                                 0 0.312906 0.400715
        C    red_flag_correct  0.293679 600                                 0 0.252677 0.334627

## Stored-score validation

Stored B-final parser agreement is reported below.
B final-turn parser agrees with stored differential/red-flag labels for 426/600 rows.

## Contrasts

contrast             outcome  estimate  n_paired
     B-C disposition_correct -0.374474       600
     B-C    relevant_correct  0.291980       600
     B-C    red_flag_correct  0.256973       600

## Information-release curve

D has not been generated.

## Disposition-only prompt sensitivity check

This is a secondary prompt-format check. It reruns E1 on the same 600 raw patient-information inputs with a disposition-only question; it does not replace the primary combined-prompt E1 condition.

Bean et al. original GPT-4o direct disposition benchmark: **64.7%**.
New disposition-only E1: **36.3%** (95% CI 32.5%–40.1%).
Existing combined-prompt E1: **43.8%** (95% CI 39.9%–47.7%).
Disposition-only minus combined-prompt E1: **-7.5%** (95% CI -10.8%–-4.3%).
The two E1 outcomes agree for 498/600 interactions; the new condition has 149/600 ambiguous or missing dispositions.
The check used 600 calls and cost $1.02. The original 64.7% result and the new 36.3% result should not be treated as identical estimands: the former is Bean et al.'s original direct benchmark, while the latter is a raw-disclosed-information prompt sensitivity condition.


---

# Bean model rank reversals

# Bean Model Rank Reversals Across A/B/C Evaluation

## Summary

The corrected no-API analysis finds model-ranking changes between direct model
evaluation (A) and observed model responses in human conversations (B). For
relevant-condition accuracy, Llama 3 70B versus Command R+ and GPT-4o versus
Command R+ are uncertainty-confirmed A→B reversals; their Holm-adjusted
p-values are 0.0000 and 0.0016. The Llama 3 70B versus GPT-4o comparison is a
point-estimate reversal, but its interval includes no change. These results use the stored `clean_prescored`
model-turn labels for B-final and the corrected bootstrap that gives every
within-scenario observation equal weight while resampling participant
clusters.

## Experiment

The analysis used the existing Bean/HELPMed data without API calls:

- A: stored direct model trials;
- B: stored final model-turn outcomes from the randomized conversation arms;
- B-any: stored any-turn model outcomes, reported as a secondary diagnostic;
- C: stored participant final-answer outcomes for the assigned model arm.

Disposition accuracy was not included because a common validated disposition
score is not available for all three stages.

The treatment mapping was `1 = Llama 3 70B`, `2 = GPT-4o`, `3 = Control`, and
`4 = Command R+`. The control arm was excluded from model pairwise tests.
There were 600 observations per included model arm and ten scenarios. Estimates
give each scenario equal weight and weight observations equally within each
scenario. The analysis used 5,000 percentile-bootstrap replicates with seed 0.

## Results

### Relevant-condition accuracy

| Model | A direct | B final | B any-turn | C participant/system |
|---|---:|---:|---:|---:|
| Llama 3 70B | 0.9917 | 0.6437 | 0.6701 | 0.3500 |
| GPT-4o | 0.9467 | 0.6487 | 0.6682 | 0.3567 |
| Command R+ | 0.9083 | 0.7190 | 0.7351 | 0.3245 |

### Red-flag accuracy

| Model | A direct | B final | B any-turn | C participant/system |
|---|---:|---:|---:|---:|
| Llama 3 70B | 0.9133 | 0.5187 | 0.5386 | 0.2846 |
| GPT-4o | 0.9017 | 0.5507 | 0.5638 | 0.2937 |
| Command R+ | 0.7250 | 0.5286 | 0.5431 | 0.2428 |

The C-stage pairwise bootstrap intervals all include zero for relevant-condition
accuracy:

| Pairwise difference at C | Estimate | 95% bootstrap interval |
|---|---:|---:|
| Llama 3 70B − GPT-4o | −0.0067 | [−0.0658, 0.0538] |
| Llama 3 70B − Command R+ | 0.0255 | [−0.0311, 0.0816] |
| GPT-4o − Command R+ | 0.0322 | [−0.0274, 0.0907] |

Thus the point ranking at C is GPT-4o, Llama 3 70B, then Command R+, but no
pairwise C difference is statistically distinguishable from zero in this
bootstrap.

### Primary A→B reversal tests

Differences are left-model minus right-model. `R` is the change in the pairwise
difference from A to B. The interval is the 95% bootstrap percentile interval
for `R`; Holm adjustment applies only to the three relevant-condition A→B
tests.

| Pair | A difference | B difference | R | 95% interval for R | Raw p | Holm p | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| Llama 3 70B − GPT-4o | 0.0450 | −0.0050 | −0.0500 | [−0.1078, 0.0101] | 0.1040 | 0.1040 | Point-estimate reversal |
| Llama 3 70B − Command R+ | 0.0833 | −0.0754 | −0.1587 | [−0.2151, −0.1021] | 0.0000 | 0.0000 | Confirmed reversal |
| GPT-4o − Command R+ | 0.0383 | −0.0703 | −0.1087 | [−0.1685, −0.0502] | 0.0008 | 0.0016 | Confirmed reversal |

The analogous A→C and B→C comparisons are included in
`bean_abc_pairwise_rank_changes.csv`. They are secondary system-level
comparisons because C includes participant behavior and uptake.

## Verification

- The full 5,000-replicate run completed successfully.
- The three included arms each contain 600 observations.
- Each included arm contains all ten scenarios.
- The examples and prescored files have unique IDs and the example IDs are
  present in the prescored file.
- Among the 1,800 included conversation rows, there are no missing values in
  `scenario_id`, `participant_id`, `chat_history`, `likely_cause`, or
  `next_step`.
- Direct relevant-condition totals reproduce the expected values: Llama 3
  70B 595/600, GPT-4o 568/600, and Command R+ 545/600.
- Treatment 3 is absent from the pairwise model tables.
- Manual assertions for Holm adjustment and reversal classification passed;
  the analysis and test files also compile successfully. `pytest` was not
  installed in the environment, so the test file was not executed through
  pytest.

## Diagnostics / Robustness

The included arms have duplicate participant–scenario records: 21 for Llama 3
70B, 26 for GPT-4o, and 19 for Command R+. The corrected bootstrap retains all
rows from each sampled participant and computes scenario means using the raw
observation counts. This now matches the point-estimate estimand.

The raw final-message parser agrees with the stored B-final labels on 2,709 of
3,600 binary labels (75.25%). This is not a direct validation of the stored
labels: the audit parser scans the raw final message, whereas the released
[HELPMed scoring pipeline](https://github.com/am-bean/HELPMed) uses extracted
condition fields and fuzzy matching. The primary analysis therefore uses
`clean_prescored.differential_correct_bot` and
`clean_prescored.red_flag_correct_bot` as the authoritative stored B-final
outcomes, while treating the simplified-parser comparison as a diagnostic.

## Interpretation

The direct ranking for relevant-condition accuracy is Llama 3 70B, GPT-4o,
then Command R+. In observed conversations, Command R+ has the highest stored
B-final accuracy, followed by GPT-4o and Llama 3 70B. The two
uncertainty-confirmed reversals show that relative model ordering can depend
on whether models are evaluated directly or through the observed
human-interaction condition.

This is a descriptive result about the Bean scenarios and randomized treatment
arms. It does not establish clinical superiority, identify a causal mechanism
for the ranking change, or establish generalization beyond this study.

## Caveats

The B-final outcome is inherited from the repository's stored scoring fields,
not reconstructed from raw final messages. The 24.75% disagreement is between
those fields and a simplified raw-message parser, not between two equivalent
implementations of the released scorer. The released scoring procedure should
be reproduced separately before claiming an independent audit of the B-final
labels; this uncertainty does not by itself show that the stored labels are
incorrect.

## Deviations from Plan

The corrected bootstrap now matches the planned row-weighted within-scenario
estimand. The current implementation writes the model-condition and pairwise
summary CSVs but does not export all 5,000 bootstrap draws as a separate CSV
or produce scenario-level sensitivity tables. Disposition accuracy is also not
included. The parser comparison is reported diagnostically rather than used as
a hard failure because the stored B-final fields are the analysis inputs.

## Outputs

- `bean_abc_model_condition_estimates.csv`
- `bean_abc_pairwise_rank_changes.csv`
- `bean_abc_model_condition_inventory.csv`
- Analysis implementation: `analysis/_bean_model_comparison.py` (public entry point: `analysis/study_bean.py`)


---

# Bean disposition prompt sensitivity check

# Disposition-only prompt check

This check reruns E1 on the same 600 GPT-4o conversations, using raw cumulative patient messages but a disposition-only prompt. It does not replace the primary decomposition.

- New disposition-only E1, scenario-balanced: **36.3%** (95% CI 32.5%–40.1%)
- Existing combined-prompt E1, scenario-balanced: **43.8%** (95% CI 39.9%–47.7%)
- New minus existing E1: **-7.5%** (95% CI -10.8%–-4.3%)
- Exact outcome agreement: **498/600**
- New ambiguous/missing dispositions: **149/600**
- API cost recorded by this check: **$1.02**

The Bean et al. GPT-4o direct disposition benchmark is 64.7%. That original benchmark is not replaced by this check; the check identifies how much the combined versus disposition-only prompt changes the raw-information counterfactual.
