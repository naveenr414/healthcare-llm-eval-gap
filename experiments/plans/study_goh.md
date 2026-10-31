# Goh Study Plan

## Question

How do two deployment assumptions change apparent clinical decision-making
performance?

1. How much does performance change when a model moves from a full-information
   benchmark to a sequential workflow in which it must request information?
2. How does performance change when GPT is used alone, by a physician with GPT,
   or by a physician without GPT?

The first question uses Hager et al. (2024)'s MIMIC-IV-Ext Clinical Decision
Making dataset. The second uses the anonymized raw score records released
with Goh et al. (2025). The studies are complementary rather than a single
pooled experiment: Hager varies information availability and workflow, whereas
Goh varies decision-maker composition.

## Motivation

The Bean study measures performance as information moves through a patient-facing
conversation. The Hager and Goh studies test related deployment assumptions that the Bean study
does not isolate. Hager provides the same clinical cases under full-information
and sequential information-gathering workflows. Goh provides score records for
physicians with GPT, physicians with conventional resources, and repeated GPT
runs. The analyses are designed to show how workflow and decision-maker
composition change measured performance; they are not intended to produce one
pooled clinical-performance number.

## Existing repository setup

The Hager data are already downloaded under `data/mimic/`, and the required
evaluator support code is vendored under `data/mimic/hager_framework/`.
The authoritative Hager pathology-to-case mapping is
`data/mimic/mimic-iv-ext-cdm/1.1/pathology_ids.json`.
The Goh source file is `data/goh/source_data_fig1.csv`. Bean analysis code
provides the repository convention for saved reports, fixed seeds, explicit
validation, and bootstrap output. No Hager API run is currently authorized by
this plan; implementation must prepare the runners and accounting before any
model calls are made.

## Case study B: Goh et al. 2025

### Data and access

The public source file is:

```text
data/goh/source_data_fig1.csv
```

It contains 400 scored case records, 97 anonymized IDs, and five cases. The
released scores include total percentage score and sub-scores for management,
factual reasoning, diagnostic reasoning, specificity, and general reasoning.
The source documentation describes 92 physician participants randomized evenly
between the two physician arms. The GPT-alone arm is different: the study team
prompted the model five times on each of the five cases, producing 25 model
observations. Thus, the five `anon_id` values in the GPT-alone rows represent
five GPT run replicates, not five human participants.
The group labels in the released data are:

- `Physicians + Conventional Resources only`;
- `Physicians+GPT-4`;
- `GPT Alone`.

The raw counts are 197, 178, and 25 records, respectively. The public source
data are linked from the [Goh et al. Nature Medicine article](https://www.nature.com/articles/s41591-024-03456-y).

### Primary Goh decomposition

Let:

- (H) denote physician alone/conventional resources;
- (C) denote physician plus GPT-4;
- (M) denote GPT alone.

For each outcome, report:

\[
\Delta_{\mathrm{assistance}} = C-H,
\]

\[
\Delta_{\mathrm{collaboration}} = M-C,
\]

and the total standalone gap:

\[
M-H = (M-C) + (C-H).
\]

The primary outcome is `total_pct`. Repeat the decomposition for the released
subscores as secondary analyses. Because the released subscores are not defined
for every case, each subscore is averaged equally over the cases with observed
values; structurally undefined case-subscore cells are not scored as zero.

Interpretation:

- (C-H>0): GPT assistance improves physician performance;
- (M-C\approx 0): physician involvement produces little additional change
  relative to GPT alone;
- (M-C>0): GPT alone outperforms the physician-plus-GPT system;
- (M-C<0): physician involvement improves on GPT alone.

Use “collaboration gap” or “standalone-versus-assisted difference” rather than
claiming a formal mediation effect unless the design and released variables
support a causal mediation analysis.

### Goh weighting and dependence

Because the five cases have different maximum scores, use the released
percentage outcomes and give the five cases equal weight in the primary
analysis. For each group, define the primary estimate as the unweighted mean
of the five case-specific means. Within a bootstrap replicate, first resample
the relevant IDs with replacement, retaining all observed case records for
each sampled ID. Then calculate the mean for each of the five cases in the
expanded sample and average those five case means. Do not calculate an
ID-level average first, since that would give IDs rather than cases equal
weight. Report raw record counts separately.

Do not treat all 400 rows as independent. For the two physician arms, resample
the 92 anonymized physician IDs, retaining all observed cases for each sampled
physician. For GPT alone, treat the five anonymized IDs as five model-run
replicates, not participants; if an interval is reported, resample those five
run IDs while retaining all five cases within each run. Report the effective
number of physician participants and GPT run replicates separately. Also report
a case-level descriptive sensitivity analysis, but do not interpret 25
GPT-alone rows as 25 independent model replications. For the GPT-alone group,
the five run IDs are the resampling units; the resulting interval should be
described as uncertainty across five model runs.

Report the group means, physician-clustered and GPT-run-clustered confidence
intervals, case-balanced estimates, and the three decomposition contrasts.
Include resident/attending, specialty, years of experience, and time spent only
as descriptive heterogeneity analyses.

For every bootstrap replicate, independently resample the IDs within each
group, compute the case-balanced estimate using the procedure above, and then
compute `C-H`, `M-C`, and `M-H`. “Independently” means that the draw of
physician IDs for `C`, the draw of physician IDs for `H`, and the draw of GPT
run IDs for `M` are separate random draws; no ID is paired across groups and
no cross-group dependence is assumed. Use `goh_bootstrap_seed = 2023` and
5,000 percentile-bootstrap replicates. If an ID draw leaves a group without
an observed record for one of the five cases, discard that draw and redraw the
IDs for that group until all five case means are defined. Use the resulting
bootstrap distributions to report percentile confidence intervals for the
three contrasts. Save the seed, replicate count, resampling unit, redraw count,
and estimator definition in the output metadata.

### Goh interpretation

The raw scores permit outcome comparisons but not a mechanism analysis of the
physician–GPT interaction. The released file does not provide the full dialogue,
search behavior, or reasoning process. Therefore, the study can establish a
score-level collaboration gap but cannot explain how physicians changed their
answers. The GPT-alone observations are repeated model runs, not human
participants, so their uncertainty should be described as uncertainty across
five runs rather than across five people.



## Common statistical conventions

- Use case-balanced primary estimates when cases have unequal score ranges or
  representation.
- Preserve repeated-unit dependence through physician- or GPT-run-clustered
  bootstrap resampling, using the unit appropriate to each arm.
- Report signed changes and the equivalent percentage-point decline where useful.
- Use percentile bootstrap intervals with 5,000 replicates and a recorded seed.
- Treat subgroup analyses as descriptive.
- Do not pool Hager and Goh scores into one numerical estimate; the studies have
  different outcomes, units, and experimental objects.

## Implementation plan

1. Add a Hager inventory builder that reads only `pathology_ids.json`, validates
   the required input and reference fields, samples the 100-case main set with
   seed `2023`, and saves the complete inventory and eligibility metadata.
2. Update the Hager framework adapter to use `gpt-4o-2024-11-20`, request
   diagnosis and treatment in both conditions, save canonical case-level
   results, and record request-level token and cost usage.
3. Add a shared Hager evaluator wrapper that scores diagnosis and each
   pathology-specific treatment component for both conditions, including zero
   scores for missing outputs.
4. Add the stratified Hager bootstrap and the Goh score-level decomposition as
   analysis scripts (`analysis/study_hager.py` and
   `analysis/study_goh.py`). The Hager API adapter is kept as a private helper
   in `analysis/_hager_api.py`. Save machine-readable tables, metadata, and
   the bootstrap configuration under `outputs/study_hager/` when
   explicitly run.
5. Keep credentialed MIMIC-derived case text and prompts local; reports may
   contain IDs and aggregate results but must not publish clinical text.
6. Add focused regression tests under `tests/test_study_hager.py` and
   `tests/test_study_goh.py` for bootstrap
   weights, result pairing, missing outputs, and API usage accounting. These
   tests must pass before any Hager or Goh results are trusted.

## Verification plan

Before any API calls:

- Verify that `pathology_ids.json` contains 2,400 unique IDs partitioned into
  the four prespecified pathologies and that every selected ID has the required
  HPI, physical examination, discharge-diagnosis, and ICD-diagnosis fields.
  Check that empty laboratory, microbiology, radiology, and procedure domains
  are retained and recorded rather than silently excluded.
- Verify that the saved Hager inventory contains exactly 25 selected cases per
  pathology, no duplicate selected IDs, and identical selected IDs for both
  conditions.
- Verify the full-information and sequential canonical schemas, including
  diagnosis, treatment components, missing-output handling, and condition
  labels, using hand-checked synthetic outputs.
- Verify Goh dimensions, labels, case numbers, outcome fields, physician ID
  counts, and GPT-run ID counts against the source documentation.
- Verify that the Goh point estimator is the mean of five case-specific means,
  that each bootstrap draw is group-independent, and that every valid
  replicate contains all five case means.
- Verify the Hager and Goh bootstrap seeds, replicate counts, signs of all
  contrasts, and saved metadata before trusting any interval.

After the pilot:

- Manually inspect at least one successful and one missing-output case per
  Hager condition.
- Confirm that treatment components are parsed and scored identically across
  conditions and that API usage totals equal the sum of request-level logs.
- Confirm that the pilot projection remains within the approved cost reserve
  before starting the 100-case run.

## Scope and non-goals

The study does not add Hager model comparisons, information-order ablations,
or a 200-case extension. It does not reconstruct Goh physician–GPT dialogues,
perform causal mediation, or treat GPT-alone run replicates as human
participants. It does not publish MIMIC-derived clinical text.

## Outputs

### Hager outputs

1. Reproducible balanced case inventory by pathology, including all eligible
   `hadm_id`s, `pathology`, `inclusion_status`, required-field exclusion reason,
   empty optional clinical domains, sampling seed, and eligibility rule.
2. Full-information versus sequential results by case and pathology.
3. Canonical case-level result records preserving raw output, parsed diagnosis,
   parsed treatment, treatment components, trajectory, model ID, and usage.
4. Diagnosis accuracy and treatment-component tables with paired confidence
   intervals.
5. Number of sequential rounds and API usage/cost by condition.
6. Saved prompts, model configuration, exact API model name, seed, token counts,
   and execution
   metadata.
7. Request-level usage log and run-level cost summary, including input,
   output, and total tokens, calls, retries, failures, and dollars by case and
   condition.



### Goh outputs

1. Validated score-level analysis frame.
2. Case-balanced group means and clustered confidence intervals.
3. Assistance, collaboration, and total-gap decomposition table.
4. Subscore decomposition table.
5. Physician-clustered, GPT-run-clustered, and case-level sensitivity analyses.
6. Descriptive heterogeneity table by resident/attending status, specialty,
   years of experience, and time spent.

## Execution order

1. Validate the local Hager and Goh files without making model calls.
2. Run the Goh score decomposition, which requires no new API calls.
3. Run the Hager 16-case pilot using one API-accessible model, with four cases
   per pathology.
4. Audit pilot trajectories, scoring, and usage records manually.
5. Create and save the seeded Hager case inventory before the main run.
6. Scale the Hager comparison to the prespecified 100-case subset using the
   same inventory for both conditions.
7. Write a joint interpretation emphasizing information/workflow constraints and
   human–AI collaboration as distinct deployment assumptions.
