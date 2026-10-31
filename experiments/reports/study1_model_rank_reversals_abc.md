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
- Analysis implementation: `analysis/study1_model_rank_reversals_abc.py`
