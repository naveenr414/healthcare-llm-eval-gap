# Study 1 Confidence Intervals, Paired Changes, and Path Dependence

## Question

What are the uncertainty intervals for the four-stage performance sequence

\[
\text{expert single-turn} \rightarrow \text{patient first message}
\rightarrow \text{full patient conversation}
\rightarrow \text{patient final decision}?
\]

Are the changes between the patient first-message, full-conversation, and
patient-decision conditions paired within the same underlying cases? Can the
data identify the missing expert-query/multi-turn cell needed to separate query
source from interaction format, and what low-cost heterogeneity analyses are
available?

## Motivation

The existing point estimates suggest a large sequence of declines, but the
current presentation does not yet report uncertainty for each estimate and
does not consistently distinguish independent from paired comparisons. The
analysis should replace the approximate table with an auditable table of
counts, estimates, 95% confidence intervals, and confidence intervals for each
adjacent change without rerunning completed model evaluations.

The analysis also tests whether the apparent decomposition is an artifact of the
order in which query source and interaction format are changed. The available
data may support only a partial answer because the expert-query/multi-turn cell
does not appear to have been collected.

## Existing Setup

For the Bean/HELPMed interaction data, the arm coding is `1 = Llama 3 70B`,
`2 = GPT-4o`, `3 = Control`, and `4 = Command R+`. Accordingly, all GPT-4o
conversation rows must use `treatment_id == 2`; `treatment_id == 1` is the Llama
arm.

The repository defines four conditions in `analysis/study_1.py`:

1. Expert-written/direct scenario, single-turn: `direct_trials_condition.csv`,
   filtered to `model == "GPT 4o"`, using `differential_correct`.
2. Patient first message, single-turn: legacy `saved_results.csv` treatment-1
   (Llama) rows, using `correct`; this is not a GPT-4o-paired condition.
3. GPT-4o response in the real patient conversation: treatment-2 rows from
   `clean_examples.csv`, joined to `clean_prescored.csv` on `id`, using
   `differential_correct_bot`.
4. Patient final answer/decision: the same treatment-2 rows, using
   `differential_correct`.

The direct, observed GPT-4o, and human conditions have 600 observations. The
legacy saved first-message sample also has 600 observations but belongs to
treatment 1 (Llama), so it must not be presented as a GPT-4o stage or paired
with treatment-2 rows. The implementation must recompute any reported counts
rather than hard-code them. The primary revised experiment uses the
GPT-4o treatment-2 rows and equal-scenario-weighted averages across the ten
scenarios.

`analysis/study_1_bootstrap.py` already implements a 5,000-replicate bootstrap
with random seed 0 and paired, participant-clustered resampling for the last
three conditions. It is a starting point, not a substitute for verifying the
joins and estimands in this plan. Do not run `analysis/study_1.py`, because it
makes new GPT-4o API calls.

## Experimental Design

### Primary estimands

For each condition \(k\), define the binary outcome \(Y_{isk}\) as the relevant
existing correctness label for observation \(i\) in scenario \(s\). The primary
estimate gives each of the ten scenarios equal weight:

\[
\hat p_k = \frac{1}{10}\sum_{s=1}^{10}
\left(\frac{1}{N_{sk}}\sum_i Y_{isk}\right).
\]

Thus, the primary comparison standardizes all four conditions to the same
uniform distribution over the ten observed scenarios. Report the raw row count
and correct count as descriptive sample information, but calculate the primary
accuracy and changes from the scenario-balanced estimates.

The adjacent changes are defined as percentage-point changes:

\[
\Delta_{1\rightarrow2}=p_2-p_1,\quad
\Delta_{2\rightarrow3}=p_3-p_2,\quad
\Delta_{3\rightarrow4}=p_4-p_3.
\]

Negative values indicate a decline. Report both the signed change and the
equivalent decline in percentage points where useful.

For paired patient-stage changes, define the primary estimand directly from
within-`id` differences and apply the same equal scenario weighting:

\[
\Delta_{a\rightarrow b}
= \frac{1}{10}\sum_{s=1}^{10}
\left(\frac{1}{N_s}\sum_{i\in s}(Y_{ib}-Y_{ia})\right).
\]

Thus, each scenario contributes equally to the paired change, regardless of
how many patient cases it contains. The bootstrap must recompute this
scenario-balanced within-`id` difference in every replicate; it must not take a
raw row-level mean of the paired differences.

### Independence and pairing

- The legacy conditions 2, 3, and 4 are not a single-model paired sequence:
  `saved_results.csv` is treatment 1, while the current GPT-4o observed
  conversation and human outcomes use treatment 2. The revised A–E experiment
  therefore does not use `saved_results.csv`.
- Conditions 1 and 2 are not paired. The expert/direct benchmark has repeated
  direct model trials over the ten scenarios, whereas condition 2 has patient
  examples with different observed counts by scenario. Compute the 1→2 change
  using independent bootstrap draws, not a row-wise paired difference.
- Conditions 2→3 and 3→4 must use within-`id` changes. Also report the paired
  2→4 change as a useful secondary contrast, although it is not an adjacent
  transition in the main table.

### Confidence intervals

Use a nonparametric percentile bootstrap with 5,000 replicates and random seed
0, preserving the conventions in `analysis/study_1_bootstrap.py`:

- For condition 1, resample rows independently within each scenario and
  calculate the mean accuracy within each scenario before averaging the ten
  scenario means equally.
- For conditions 2–4, resample the 343 patient participants with replacement,
  include all rows contributed by each sampled participant, keep all three
  outcomes from each `id` together, and calculate the mean within each scenario
  before averaging the ten scenario means equally.
- For the 1→2 change, subtract independently resampled estimates.
- For the 2→3, 3→4, and 2→4 changes, calculate the within-`id` difference,
  average those differences within each scenario, and average the ten scenario
  means equally in every bootstrap replicate.
- Use the 2.5th and 97.5th percentiles for two-sided 95% intervals.

The primary target is accuracy under a uniform distribution over the ten
observed scenarios. Participant-clustered intervals account for dependence
among cases from the same participant while preserving this scenario-balanced
estimand. Raw-row-weighted estimates may be reported as a sensitivity analysis
for the observed case distribution, but they should not replace the balanced
primary estimates.

Report interval sensitivity for the same scenario-balanced estimands using two
additional resampling schemes. First, use a row-level bootstrap that resamples
patient rows independently within scenario while retaining the three outcomes
from each `id` together; this preserves within-case pairing but ignores
dependence across cases from the same participant. Second, use a
scenario-clustered bootstrap that resamples the ten scenario-level means with
replacement and averages the sampled scenario means equally; for conditions
2–4, calculate the sampled scenario-level paired differences from the same
scenario draw. Report the three methods side by side, including interval
endpoints and widths, and state whether the differences are material for the
main estimates and changes.

## Data and Sample

Required inputs:

- `data/study1/direct_trials_condition.csv`
- `data/study1/saved_results.csv`
- `data/study1/clean_examples.csv`
- `data/study1/clean_prescored.csv`
- `data/study1/scenarios.csv` for scenario labels and urgency/condition
  metadata in the heterogeneity analysis

Inclusion rules:

- Condition 1: rows with `model == "GPT 4o"`.
- GPT-4o observed conditions: rows with `treatment_id == 2` in
  `clean_examples.csv`, with successful one-to-one joins on `id` to
  `clean_prescored.csv`.
- Exclude no observations silently. Any missing, duplicate, or unmatched IDs
  should fail a required check and be reported.

For condition 2, use `saved_results.csv` as the authoritative result file. This
is the file written by `analysis/study_1.py` and consumed by the existing
bootstrap workflow. 

The patient sample currently has 600 rows, but scenario counts are unequal.
The direct GPT-4o sample has 600 rows and 60 rows per scenario.

## Procedure

### 1. Reconstruct and validate the four conditions

Create a canonical analysis frame with one row per patient `id` for conditions
2–4 and a separate direct-condition frame for condition 1. Use explicit binary
conversion for `True`/`False` values; do not rely on accidental pandas coercion.

Compute the point estimate and correct count for each condition. The output
table should have:

```text
Evaluation condition | N | Correct | Estimate | 95% CI | Δ from previous | 95% CI of Δ
```

For condition 1, show `—` for the adjacent change. For the remaining rows,
report changes in percentage points, not proportions.

### 2. Paired analysis

For each paired transition, calculate the per-case difference:

\[
D_i^{2\rightarrow3}=Y_{i3}-Y_{i2},\qquad
D_i^{3\rightarrow4}=Y_{i4}-Y_{i3}.
\]

Report the counts of transitions in each direction (`0→1`, `1→0`, `0→0`,
`1→1`) and the mean within-case difference. The primary inferential interval is
the paired bootstrap interval for the mean difference.

The prose result should be phrased in the requested form, for example:

> Performance changed by [estimate] percentage points [95% CI X–Y] when moving
> from the patient’s initial query to the complete conversation.

Use “changed” rather than “caused” because this is an observational comparison
of stages in the same interaction, not a randomized intervention between the
two stages.

### 3. Path-dependence / 2×2 assessment

Inventory the four conceptual cells:

| Query source | Single-turn | Multi-turn |
|---|---:|---:|
| Expert | available: condition 1 | unavailable in current files |
| Patient | available: condition 2 | available: condition 3 |

Do not fabricate or impute the expert/multi-turn cell. Check whether
`direct_trials_condition.csv` contains any conversation history or sequential
turns that could validly supply it; based on the current schema it contains
direct model text only, so it should be treated as absent unless inspection
finds otherwise.

The result should explicitly state that the existing data identify the path

\[
(\text{expert},\text{single})
\rightarrow(\text{patient},\text{single})
\rightarrow(\text{patient},\text{multi}),
\]

but do not identify the reverse-order interaction-format contrast

\[
(\text{expert},\text{single})
\rightarrow(\text{expert},\text{multi}).
\]

Therefore the data cannot fully separate query-source and interaction-format
effects or establish path-independent additive effects. The plan may report the
observed sequential decomposition, but should label it as path-specific.

### 4. Low-cost heterogeneity

Run only descriptive, pre-specified subgroup analyses that require no new model
calls:

- Direct-trial model comparison for GPT-4o, Llama 3 70B, and Command R+ using
  `differential_correct`.
- Direct-trial reverse-order comparison using `reverse`.
- Scenario/condition-level estimates for the four main conditions, joining
  `scenario_id` to `scenarios.csv` and reporting the primary condition and
  urgency category.

For each subgroup, report `N`, correct count, and estimate. Treat these as
descriptive heterogeneity, not confirmatory hypothesis tests. Do not introduce
patient demographic subgroups unless they are represented as structured fields;
free-text extraction from `chat_history` is outside this plan.

The intended questions for the two direct-trial analyses are: (i) holding the
expert-written, single-turn task fixed, do GPT-4o, Llama 3 70B, and Command R+
differ in `differential_correct` accuracy? and (ii) holding the model and task
fixed, does reversing the order of the service recommendation and differential
questions change `differential_correct` accuracy? These are descriptive questions
about static direct trials. They do not compare real-patient interactions across
models or identify a causal effect in the RCT.

## Outputs

Produce:

1. A machine-readable result table containing counts, estimates, confidence
   intervals, adjacent changes, and change intervals.
2. A concise human-readable report containing the main table, paired transition
   counts, the paired 2→3 and 3→4 interpretations, and the missing 2×2 cell.
3. A diagnostic table of scenario-level estimates and the descriptive model and
   reversal comparisons.
4. Saved bootstrap configuration: seed, number of replicates, resampling unit,
   and input-file paths.

No GPT API outputs or new model calls are required. Estimated additional API
   cost: **$0**. The implementation must not call `analysis/study_1.py` or any
   OpenAI endpoint.

## Verification

### Required correctness checks

- Confirm the four point counts are 568, 497, 385, and 204 unless the source
  files have changed; if they differ, report the discrepancy rather than
  silently proceeding.
- Confirm `N == 600` for every main condition.
- Confirm condition-1 direct GPT-4o rows have 60 observations for each of the
  ten scenarios.
- Confirm the GPT-4o observed conditions have exactly 600 unique patient IDs
  and one row per ID after the joins.
- Confirm `saved_results.csv` is labeled as treatment 1 and is not joined to
  the GPT-4o treatment-2 frame.
- Confirm all binary outcomes are in `{0, 1}` after conversion and contain no
  missing values.
- Confirm every paired difference equals the corresponding endpoint
  subtraction for the same ID.
- Confirm the bootstrap implementation reproduces the existing point estimates
  and the point differences before calculating intervals.
- Confirm no code path makes an API call.

### Diagnostics

- Compare the new point estimates and intervals with the existing output of
  `analysis/study_1_bootstrap.py`.
- Report whether row-level and scenario-clustered intervals materially differ.
- Report the number of discordant pairs for 2→3 and 3→4.
- Confirm that the primary analysis uses only `saved_results.csv` for condition
  2
- Check the distribution of patient rows across scenarios before interpreting
  raw versus scenario-balanced estimates.

## Interpretation

A confidence interval for an estimate describes uncertainty under the chosen
resampling target; it does not correct for the non-random construction of the
benchmark or for possible dependence induced by repeated scenarios.

A paired 2→3 interval excluding zero would support a within-case change between
the patient’s first message and the full conversation. A paired 3→4 interval
excluding zero would support a within-case difference between the model’s
conversation response and the patient’s final answer. These comparisons do not
establish that adding turns caused the change, because the full conversation
also contains additional patient information and the observed interaction is
not randomized at that stage.

The missing expert/multi-turn cell prevents a complete 2×2 decomposition and
prevents a claim that the query-source and interaction-format effects are
path-independent. Heterogeneity results should be framed as descriptive checks
of whether the headline ordering is stable across models, scenarios, and
prompt reversal—not as independently powered subgroup conclusions.

## Implementation Notes

Implement this as a new analysis/reporting script rather than modifying the
existing API-calling workflow. Reuse the loading conventions and bootstrap
seed from `analysis/study_1_bootstrap.py`, but add explicit validation, the
main table, paired transition counts, and the 2×2 data-availability audit.

Use a distinct output directory under `experiments/` or another clearly named
non-source-data location. Preserve all existing user changes in
`analysis/study_1.py` and `analysis/study_1_bootstrap.py`.

## Open Questions

None for the primary analysis. The only substantive limitation is structural:
the current repository does not contain a valid expert-written multi-turn
condition, so that cell should remain missing rather than be generated by a
new GPT call under this plan.
