# Bean Model Rank Reversals Across A/B/C Evaluation

## Question

Do the rankings of GPT-4o, Llama 3 70B, and Command R+ change across the
three existing Bean evaluation stages from Plan 1?

- **A:** direct, full-case model evaluation;
- **B:** the assigned model's observed response in the participant conversation;
- **C:** the participant's final answer after using the assigned model.

The primary rank-reversal question compares A with B, because both are
model-output outcomes. A-to-C and B-to-C comparisons are secondary system-level
comparisons: C is the outcome of a human–LLM system, not model-only performance.

## Motivation

Bean et al. evaluate three models both in isolation and in randomized human
treatment arms. The current repository analyzes the GPT-4o arm as the primary
case and does not produce a common A/B/C ranking table for all three models.
This plan uses the existing data to test whether the direct model ranking is
preserved when the model operates in an observed human interaction and whether
the ranking of assigned human–LLM systems differs again after participant
uptake.

The primary analysis is a no-API extension. It reuses stored outputs and
existing correctness labels; it does not rerun the models or reconstruct the
conversations.

## Existing Setup

Use the existing Study 1 files and Plan 1 scoring conventions:

- `data/study1/direct_trials_condition.csv`: 600 direct trials per model for
  GPT-4o, Llama 3 70B, and Command R+.
- `data/study1/clean_examples.csv`: 600 observations per randomized arm,
  including observed user and model messages, final participant choice, and
  participant cluster.
- `data/study1/clean_prescored.csv`: existing red-flag and differential
  correctness fields for model and participant responses.
- `data/study1/scenarios.csv`: ten scenarios and the gold differential,
  red-flag, and disposition labels.
- `experiments/plans/study1_information_and_interaction_decomposition.md`:
  definitions of A, B, and C and the existing outcome conventions.

The verified Bean/HELPMed treatment mapping is:

| `treatment_id` | Assigned arm |
|---:|---|
| 1 | Llama 3 70B |
| 2 | GPT-4o |
| 3 | Control |
| 4 | Command R+ |

Use only treatment IDs 1, 2, and 4 for model rankings. Treatment 3 remains a
separate control reference and is not included in pairwise model reversals.

The existing scripts that filter `treatment_id == 1` as GPT-4o are not
authoritative for this analysis and must not be reused without correcting the
mapping.

## Experimental Design

### Outcomes

The primary outcome is relevant-condition accuracy: whether the response
contains at least one condition in the scenario's `full_differential`, using
the existing canonical labels.

Report one prespecified secondary outcome:

1. red-flag recognition, using the scenario's `red_flags`.

Disposition accuracy is not included in this completed implementation because
the same validated five-category score is not available for A, B, and C.
Condition-identification and red-flag analyses are reported independently.

### Conditions

For model `m` and stage `c`, let `A[m,c]` denote the
scenario-balanced mean accuracy.

**A. Direct model performance.** Use the stored direct trials. Compute the
existing differential and red-flag outcomes by model and scenario. Do not
rerun direct trials.

**B. Observed model performance.** Use the model messages in the observed
human conversations for treatment IDs 1, 2, and 4. The primary B outcome is
the final model-turn score, matching Plan 1. The secondary B outcome is
any-turn recognition, equal to one if any model message in the conversation
contains a relevant condition or red flag. Use final-turn performance for the
primary rank comparison; do not credit an earlier model message for final-turn
disposition.

**C. Human–LLM system performance.** Use the participant's final answer from
the same randomized treatment arms. This is an assigned-arm system outcome.
Do not describe C as model-only performance or substitute B for C.

### Rank and reversal estimands

For each model pair `a,b` and stage `c`, define the pairwise difference

`D[a,b,c] = A[a,c] - A[b,c]`.

A point-estimate reversal between stages (c) and (d) occurs when

`D[a,b,c] * D[a,b,d] < 0`.

The primary reversal contrast is the change in the pairwise difference:

`R[a,b,A→B] = D[a,b,B] - D[a,b,A]`.

Report analogous (A\rightarrow C) and (B\rightarrow C) contrasts as
secondary system-level comparisons. A tie is not a reversal. A reversal is
uncertainty-supported only if the bootstrap intervals for the two relevant
pairwise differences lie on opposite sides of zero. Otherwise classify it as
point-estimate reversal, stable ranking, or indeterminate.

The primary claim is pair-specific. A global statement that “the ranking
reverses” requires at least one model pair to satisfy the prespecified
uncertainty-aware criterion.

## Data and Sample

Use all 600 observations per model arm and the same ten scenarios. Require:

- 600 direct observations per model in A;
- 600 observed conversation rows per model arm in B/C;
- one-to-one joins between `clean_examples.csv` and
  `clean_prescored.csv` by `id`;
- correct treatment mapping before any aggregation;
- no silent dropping of missing or unparsable outcomes.

Duplicate participant–scenario rows are retained. They receive equal weight as
observations within the scenario; participant ID is used only as the bootstrap
cluster.

The primary estimand gives each scenario equal weight. Within each scenario,
give each available observation equal weight. For B and C, participant ID is
the resampling cluster because participants can contribute multiple scenarios.
For A, resample direct-trial rows within model and scenario.

The primary analysis must report the exact missingness and completeness pattern
before computing estimates. If a required model-stage cell is incomplete, fail
the primary complete-case analysis and report any available-case result only as
a labeled sensitivity analysis.

## Procedure

1. Build a canonical long table with one row per `(model, stage, id)` where
   applicable, plus scenario, participant cluster, outcome fields, and source
   metadata.
2. Apply the verified treatment mapping and assert that treatment 3 is excluded
   from model pairwise comparisons.
3. Reproduce the existing GPT-4o A/B/C estimates using the corrected mapping
   and existing scoring fields. Do not assume that prior GPT-4o report values
   remain correctly labeled until this check passes.
4. Compute scenario-balanced `A[m,c]` for all three models and stages A, B,
   and C.
5. Compute all three model pairs—GPT-4o/Llama 3, GPT-4o/Command R+, and
   Llama 3/Command R+—for A/B, A/C, and B/C.
6. Compute `R[a,b,A→B]` as the primary reversal contrast and
   the secondary A/C and B/C contrasts.
7. Use 5,000 percentile-bootstrap replicates with seed 0. In each replicate:
   - resample participant clusters with replacement for B and C, carrying all
     rows and scenarios for each sampled participant;
   - resample A direct-trial rows within model and scenario;
   - compute each model-stage estimate, pairwise difference, and reversal
     contrast using the same scenario-balanced estimator;
   - preserve B/C pairing within each sampled human interaction.
8. For the three primary A→B relevant-condition pairwise tests, report raw
   two-sided bootstrap p-values and Holm-adjusted p-values. Apply Holm only
   across this prespecified family; leave secondary A→C, B→C, and red-flag
   comparisons labeled as exploratory.
9. Write point estimates, 95% percentile intervals, rank orderings, reversal
   classifications, and completeness diagnostics.

## Outputs

- `bean_abc_model_condition_estimates.csv`: point estimates for each model at
  A, B-final-turn, B-any-turn, and C.
- `bean_abc_pairwise_rank_changes.csv`: all pairwise differences, rank orders,
  A/B primary reversal contrasts, secondary A/C and B/C contrasts, and
  classifications.
- `bean_abc_model_condition_inventory.csv`: treatment mapping and row counts.
- `study1_model_rank_reversals_abc.md`: concise report distinguishing model-only
  A/B results from human–LLM system C results.

## Verification

### Required correctness checks

- Verify the exact mapping `1=Llama 3 70B`, `2=GPT-4o`, `3=Control`,
  `4=Command R+` before scoring.
- Verify 600 observations per model arm and ten scenarios with the expected
  scenario-by-arm counts.
- Verify one-to-one joins between examples and prescored outcomes.
- Verify that treatment 3 is absent from all model pairwise tables.
- Reproduce direct-trial model totals from the existing report: Command R+
  545/600, GPT-4o 568/600, and Llama 3 70B 595/600 for the existing
  differential outcome.
- Reproduce the GPT-4o observed model and participant outcomes after applying
  the corrected treatment mapping; document any difference from the existing
  report as a labeling correction rather than silently overwriting it.
- Verify that every primary reversal classification is based on pairwise
  differences, not on absolute accuracy changes.
- Use a toy matrix with a known A/B reversal and a uniform accuracy decline
  without a reversal; verify both classifications.
- Verify that bootstrap resampling preserves participant clusters for B/C and
  scenario strata for A.
- Verify that ties and intervals spanning zero are not classified as confirmed
  reversals.

### Diagnostics included in the completed run

- Report final-turn versus any-turn B differences.
- Compare A/B results using relevant-condition and red-flag outcomes.
- Report duplicate participant–scenario cells and the B-final parser diagnostic.
- Show the control arm only as contextual reference, not as a model ranking.

Scenario-level tables, raw-row sensitivity estimates, and separate bootstrap
draw exports are not generated by the completed implementation.

## Interpretation

A confirmed A/B reversal would show that the relative ordering of at least two
models changes between direct model evaluation and observed model output in
human interaction, using the same Bean scenarios. It would support a claim
about evaluation-condition dependence, not clinical superiority.

A confirmed A/C reversal would show that the ranking of assigned human–LLM
systems differs from the direct model ranking. It would not establish that the
model caused the difference because participant behavior and uptake are part of
C.

Stable A/B rankings with lower B accuracy indicate a deployment or interaction
gap without a model-only rank reversal. A point-estimate reversal with an
interval crossing zero is suggestive but not conclusive. Null or indeterminate
results do not show that rankings are invariant in other tasks or populations.

The analysis is descriptive and relies on the observed Bean scenarios and
randomized treatment arms. It does not identify a causal effect of conversation,
does not compare newly generated model-only patient prompts, and does not
establish generalization beyond the study design.

## Implementation Notes

Create a separate no-API analysis module rather than modifying the existing
Study 1 outputs. Reuse the existing scoring fields and bootstrap conventions
where they are valid, but correct the treatment mapping at the input boundary.
Preserve the raw files and prior reports. Record the mapping source and
bootstrap seed in the plan/report; input file hashes and a separate bootstrap
draw export remain future reproducibility improvements.

Do not rerun A, B, or C model calls for the primary analysis. A future extension
could generate standardized model-only patient-information conditions for all
three models, but that is a different estimand and is outside this plan.

## Open Questions

None.
