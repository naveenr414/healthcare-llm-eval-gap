# Model Rank Reversals Between Benchmark and Realistic Evaluation

## Question

Do model rankings change when evaluation moves from a normal, fully specified
benchmark to a more realistic evaluation in which the model receives incomplete
information and must interact before answering? In particular, does a model that
ranks higher under the normal evaluation rank lower under the realistic
evaluation?

This plan covers the existing Bean et al. data and a multi-model extension of
the Hager et al. workflow. The first objective is to determine whether the
repository already identifies a reversal; the second is to collect the missing
cells needed to test the claim directly.

## Motivation

The repository currently reports large performance changes between benchmark-like
and deployment-like conditions, but those changes are not the same as a rank
reversal. A rank reversal requires at least two models evaluated under both
conditions on comparable tasks and samples. Establishing this distinction avoids
interpreting a single-model performance drop as evidence that model rankings
reverse.

## Existing Setup

Bean et al. data and analysis:

- `data/study1/direct_trials_condition.csv` contains three models—Command R+,
  GPT-4o, and Llama 3 70B—in the expert-written, single-turn condition.
- `data/study1/clean_examples.csv` contains 600 observations for each of four
  randomized arms. The Bean study identifies these arms as GPT-4o, Llama 3,
  Command R+, and control. The authors' HELPMed analysis notebook records the
  mapping as `1 = Llama 3 70B`, `2 = GPT 4o`, `3 = Control`, and
  `4 = Command R+`. The three treatment arms are human–LLM interactions, not
  model-only evaluations.
- `data/study1/clean_prescored.csv` provides the prescored participant outcomes
  for all four arms. The existing analysis uses only the GPT-4o arm.
- `analysis/study_1.py` and `analysis/study_1_report.py` define the existing
  correctness labels and scenario-balanced estimands.

The Bean files therefore support a cross-model comparison in both the
normal/direct condition and the randomized human-assisted condition, subject to
an estimand distinction. The direct condition measures model-only performance;
the human-assisted condition measures the outcome of a participant assigned to a
model. The patient first-message API condition and the existing model-response
analysis are GPT-4o-only. Thus, the current report estimates only the GPT-4o
realistic path, although the underlying files contain the other two LLM arms.

Hager et al. data and analysis:

- `data/mimic/physionet.org/files/mimic-iv-ext-cdm/1.1/` is the local
  credentialed dataset.
- `experiments/reports/study2/hager/hager_case_inventory.csv` defines the
  balanced 100-case sample, with 25 cases per pathology.
- `experiments/reports/study2/hager/hager_main_scored_results.csv` contains
  GPT-4o results for `full_information` and `sequential` conditions.
- `analysis/study_2_hager_api.py` runs the two conditions and currently fixes
  the model to one model ID; `analysis/study_2_hager.py` performs common
  scoring and the paired stratified bootstrap.

The existing Hager results therefore compare workflows for one model. They can
show a workflow effect for GPT-4o, but cannot show a model rank reversal.

## Experimental Design

### Definitions

For model `m` and evaluation condition `c`, let `A[m,c]` be the
scenario- or pathology-balanced accuracy under a prespecified scoring rule.
The normal condition is the fully specified, benchmark-like evaluation. The
realistic condition is the matched incomplete-information or interactive
workflow:

- Bean: expert-written single-turn model performance versus the matched
  randomized human-assisted arm for each assigned model. This is a comparison
  of model-only performance with human–LLM system performance, not two
  model-only conditions;
- Hager: full information versus sequential information gathering.

For two models `a` and `b`, a rank reversal occurs when
`(A[a,N] - A[b,N]) * (A[a,R] - A[b,R]) < 0`, where `N` is normal and `R` is
realistic. A tie or an interval that spans
zero is not a confirmed reversal. The primary pairwise reversal indicator is
the sign of the paired model difference changing across conditions.

### Existing-data audit

First, produce a no-API audit using only completed files. Recompute the Bean
normal-condition accuracy by model and reverse-prompt order, and report the
ordering. Inventory every model-by-condition cell for Bean and Hager. The audit
must label each cell as observed, missing, or not comparable; it must not infer
missing realistic scores from the GPT-4o results.

The audit should explicitly report:

1. whether at least two models have valid outcomes in both normal and realistic
   conditions;
2. whether any pair changes ordering using point estimates;
3. whether uncertainty intervals for the pairwise differences support a
   reversal;
4. whether the observed design supports only a within-model workflow change.

Expected design conclusion from the current repository: Bean has the required
cross-model cells in the raw study files, but the current report does not yet
estimate the three human-assisted model arms jointly. Hager still lacks the
required cross-model-by-condition cells. Any Bean reversal should therefore be
described as a change in the ranking of model-assigned human–LLM systems
relative to model-only direct performance, not as a pure model-only reversal.

### Hager multi-model extension

Use the existing Hager inventory unchanged: the same 100 cases, 25 per
pathology, in both conditions and for every model. Evaluate at least three
models, including the existing GPT-4o snapshot and two additional models that
can be run under the same API or local inference interface. The exact model IDs,
versions, and access mode must be fixed before execution and recorded in every
canonical result.

For each model, run:

1. `full_information`: all released clinical domains supplied upfront;
2. `sequential`: history supplied first, followed by the model's permitted
   information requests and final diagnosis/treatment output.

Keep prompts, tool/request schemas, stopping rules, temperature, seed, case
inventory, evaluator, and treatment component definitions identical across
models except where a model-specific adapter is technically required. Any
adapter difference must be recorded and assessed as a comparability risk.

Use diagnosis accuracy as the primary cross-model outcome because it is defined
for every Hager case. Report treatment-component accuracy as a secondary,
component-specific outcome; do not collapse heterogeneous treatment components
into a single score for the rank claim.

The primary estimand for each model and condition is the mean over the four
pathology-specific accuracies, giving each pathology equal weight. Within each
pathology, give each of the 25 cases equal weight. The primary workflow change
is `A[m,R] - A[m,N]`. The primary rank comparison is the pairwise model
difference `A[a,c] - A[b,c]` in each condition.

## Data and Sample

Bean inputs:

- `data/study1/direct_trials_condition.csv`
- `data/study1/clean_examples.csv`
- `data/study1/clean_prescored.csv`
- `data/study1/scenarios.csv`

Hager inputs:

- the local MIMIC-IV-Ext CDM files;
- `data/mimic/physionet.org/files/mimic-iv-ext-cdm/1.1/pathology_ids.json`;
- `experiments/reports/study2/hager/hager_case_inventory.csv`.

Do not change the Hager case sample between models or conditions. Require one
scored result per `(model_id, hadm_id, condition)`. Missing, duplicate, failed,
or unparsable outputs must be recorded and must fail the primary complete-case
analysis rather than being silently dropped. A prespecified sensitivity analysis
may report the available-case result with its exact missingness pattern.

## Procedure

1. Build a canonical model-condition table with model ID, condition, sample
   counts, balanced accuracy, and uncertainty intervals.
2. For Bean, use the existing correctness labels and scenario-balanced
   estimand for all three LLM arms. Treat the direct condition as model-only
   performance and the randomized treatment-arm outcomes as human–LLM system
   performance. Keep the control arm separate from model rankings.
3. For Hager, score every result with the existing common evaluator. Preserve
   raw output, parsed diagnosis, treatment components, trajectory, rounds, and
   usage metadata.
4. For each model pair and condition, calculate the paired case-level accuracy
   difference using the same cases. Define a point-estimate reversal when the
   signs differ across conditions.
5. Use 5,000 stratified bootstrap replicates with seed 2023. Resample the 25
   Hager cases within each pathology and carry all models and both conditions
   together within each sampled case. Recompute each model-condition accuracy,
   each pairwise model difference, each workflow change, and the change in the
   pairwise difference across conditions.
6. Treat the cross-condition rank-change contrast

   `R[a,b] = (A[a,R] - A[b,R]) - (A[a,N] - A[b,N])`

   as the primary reversal contrast. A negative-to-positive or
   positive-to-negative change in the pairwise difference is the substantive
   reversal pattern.
7. Report an uncertainty-aware reversal classification: confirmed reversal only
   when the bootstrap interval for the normal pairwise difference lies on one
   side of zero and the interval for the realistic pairwise difference lies on
   the other side. Otherwise classify the result as point-estimate reversal,
   rank stability, or indeterminate.
8. Correctly distinguish pairwise ranking from absolute performance decline.
   A model can lose accuracy under the realistic evaluation without any rank
   reversal.

## Outputs

- `model_condition_inventory.csv`: observed/missing model-by-condition cells,
  sample sizes, and comparability notes.
- `bean_model_rankings.csv`: direct model-only estimates and randomized
  human-assisted estimates for GPT-4o, Llama 3, and Command R+, with the
  different estimands recorded explicitly.
- `hager_model_condition_estimates.csv`: model-by-condition diagnosis and
  secondary treatment estimates with intervals.
- `hager_pairwise_rank_changes.csv`: pairwise differences, workflow changes,
  reversal contrast `R[a,b]`, and reversal classification.
- `hager_rank_reversal_bootstrap.csv`: bootstrap estimates needed to reproduce
  the intervals and classifications.
- A short report stating whether the current data identify a reversal and,
  after the extension, which reversal claims are supported.

## Verification

### Required correctness checks

- Verify that every primary Hager cell has exactly the same 100 case IDs and
  25 cases per pathology.
- Verify one-to-one uniqueness of `(model_id, hadm_id, condition)`.
- Verify that model IDs, prompt condition, evaluator, and scoring version are
  recorded and consistent with the declared design.
- Reproduce the existing GPT-4o Hager estimates before adding other models.
- Use a hand-computable toy matrix where model A ranks above B in the normal
  condition and below B in the realistic condition; verify that the reversal
  classifier detects it, and verify that ties are not classified as reversals.
- Use a paired bootstrap test fixture with known case-level outcomes to verify
  that all models and both conditions are resampled on the same case draw.
- Confirm that a uniform accuracy decline for every model leaves the ranking
  unchanged.
- Confirm that missing outputs are not treated as correct and do not silently
  alter the primary sample.

### Diagnostics

- Report per-pathology rankings and reversal contrasts.
- Report the number of sequential rounds, request counts, and API cost by model;
  these are workflow diagnostics, not ranking outcomes.
- Report sensitivity to raw row weighting versus the primary balanced estimator
  only as a diagnostic.
- Inspect whether reversals are concentrated in one pathology or treatment
  component.

## Interpretation

A confirmed reversal would show that the relative ordering of at least two
models depends on whether evaluation assumes complete information or a realistic
interactive workflow. It would support the narrower claim that benchmark
rankings are not invariant to evaluation assumptions.

Stable rankings with lower realistic accuracy would show a deployment gap without
a rank reversal. A point-estimate reversal with intervals crossing zero is
suggestive but not conclusive. The existing repository result is the stronger
negative conclusion that the reversal is not currently identifiable, not evidence
that no reversal exists.

The design does not establish clinical superiority, causal effects of
interaction, or generalization beyond the selected Bean scenarios and Hager
cases. Differences in model access, decoding, adapters, or prompt compliance
can compromise cross-model comparability and must be reported.

## Implementation Notes

Extend the no-API reporting path rather than changing the completed Study 1
results. For Hager, refactor `analysis/study_2_hager_api.py` so the model ID is
an explicit run parameter and include it in output paths and usage summaries;
preserve the canonical schema consumed by `analysis/study_2_hager.py`. Add the
rank and reversal calculations to a separate analysis module so the existing
Hager scoring and bootstrap remain reproducible. Do not make API calls during
the implementation or audit phase. Run a small pilot for each added model only
after the model list, budget, prompt adapters, and acceptance checks are fixed.

## Open Questions

1. Which two additional model snapshots should be paired with GPT-4o for the
   Hager extension, given available inference/API access and a defensible
   comparison of cost and capability?
2. Should the primary Bean analysis use the existing randomized human-assisted
   arms as the realistic comparison, or should it additionally rerun all three
   models in a standardized model-only patient-facing condition?
3. If model-specific sequential tool adapters are unavoidable, what level of
   adapter difference is acceptable before the conditions should be treated as
   non-comparable?
