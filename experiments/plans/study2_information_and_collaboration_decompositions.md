# Study 2: Information and Human–AI Collaboration Decompositions

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

Study 1 measures performance as information moves through a patient-facing
conversation. Study 2 tests two related deployment assumptions that Study 1
does not isolate. Hager provides the same clinical cases under full-information
and sequential information-gathering workflows. Goh provides score records for
physicians with GPT, physicians with conventional resources, and repeated GPT
runs. The analyses are designed to show how workflow and decision-maker
composition change measured performance; they are not intended to produce one
pooled clinical-performance number.

## Existing repository setup

The Hager data are already downloaded under `data/mimic/`, and the authors'
dataset, framework, and analysis repositories are cloned under `external/`.
The authoritative Hager pathology-to-case mapping is
`data/mimic/physionet.org/files/mimic-iv-ext-cdm/1.1/pathology_ids.json`.
The Goh source file is `data/goh/source_data_fig1.csv`. Study 1 analysis code
provides the repository convention for saved reports, fixed seeds, explicit
validation, and bootstrap output. No Hager API run is currently authorized by
this plan; implementation must prepare the runners and accounting before any
model calls are made.

## Case study A: Hager et al. 2024

### Data and access

The downloaded Hager dataset is the MIMIC-IV-Ext Clinical Decision Making
dataset, version 1.1. It contains 2,400 MIMIC-derived cases across four
pathologies: appendicitis, cholecystitis, diverticulitis, and pancreatitis. The
released files include the history of present illness, physical examination,
laboratory tests, microbiology, radiology reports, ICD diagnoses and
procedures, discharge diagnosis, and discharge procedures.

Use `pathology_ids.json` as the authoritative Hager eligibility source. Do not
silently substitute converted `*_hadm_info_first_diag.pkl` files or a new
discharge-diagnosis rule. Require HPI, physical examination, discharge
diagnosis, and ICD diagnosis fields for eligibility. Treat laboratory,
microbiology, radiology, ICD-procedure, and discharge-procedure domains as
legitimately empty when no row is recorded; preserve those cases and record the
empty domains in the case inventory. Any exclusion for a missing required
field must be recorded in the case inventory with its reason.

Local data:

```text
data/mimic/physionet.org/files/mimic-iv-ext-cdm/1.1/
```

The dataset is credentialed PhysioNet data and must remain local and excluded
from public outputs. The official dataset page is
[PhysioNet MIMIC-IV-Ext CDM](https://physionet.org/content/mimic-iv-ext-cdm/1.1/).

The authors' public code is available locally under `external/`:

- `MIMIC-Clinical-Decision-Making-Dataset`: dataset conversion code;
- `MIMIC-Clinical-Decision-Making-Framework`: interactive and full-information
  evaluation framework;
- `MIMIC-Clinical-Decision-Making-Analysis`: aggregation and paper analyses.

### Primary comparison

Use the same model and the same cases under two conditions:

| Condition | Model input | Decision task |
|---|---|---|
| Full information | All relevant information supplied upfront | Diagnosis and treatment |
| Sequential workflow | HPI supplied first; model requests additional information iteratively | Diagnosis and treatment after information gathering |

The primary estimand is the within-case workflow change:

\[
\Delta_{\mathrm{workflow}}
= A_{\mathrm{sequential}} - A_{\mathrm{full\ information}}.
\]

Negative values indicate that performance falls under the sequential workflow.
The same cases and model must be used in both conditions. Both conditions must
produce and save a `Final Diagnosis` and a `Treatment` field. Revise the
full-information prompt from diagnosis-only to an explicit diagnosis-and-
treatment format, and update its result writer and evaluator so that treatment
is parsed and scored rather than dropped. The sequential workflow must use the
same two-field final-output format. Report diagnosis and treatment separately;
do not combine them into one score.

Treatment performance is component-level. For each case, use the Hager
evaluator's `Treatment Required` and `Treatment Requested` indicators and
report the fraction of cases in which each pathology-specific component was
requested. Components include the relevant procedures and supportive or
medical treatments defined by each pathology evaluator (for example,
appendectomy, cholecystectomy, drainage, ERCP, antibiotics, and support). Do
not collapse these indicators into an all-or-nothing treatment score or an
exact treatment-set score. Report component estimates overall and by
pathology, with missing treatment output coded as zero for every applicable
component.

### Hager result normalization and evaluation

The two runners must be converted into one canonical case-level result schema
before scoring. Each saved result must contain `hadm_id`, pathology, condition,
the raw model output, parsed `final_diagnosis`, parsed `treatment`, the parsed
treatment-component indicators, the full trajectory when available, and the
number of sequential rounds. For the
sequential runner, use the final answer and intermediate steps returned by the
agent. For the full-information runner, parse the two labeled fields from its
raw answer and store an empty trajectory with rounds marked as not applicable.

Both conditions must then be passed to the same pathology evaluator with the
same reference fields: discharge diagnosis, ICD diagnoses, procedures, and
discharge procedures. The evaluator must parse and score diagnosis and each
treatment component for both conditions. Treatment scoring must not be conditional on a
nonempty trajectory; the full-information condition receives a treatment score
from its saved `Treatment` field. Tool-use scores and sequential-round counts
are workflow-specific diagnostics and are not used as substitutes for the
common diagnosis or treatment outcomes.

Before the main run, test this transformation on hand-checked outputs from
both conditions and verify that missing or unparsable diagnosis/treatment
fields are recorded explicitly. A missing or unparsable diagnosis receives a
diagnosis score of 0. A missing or unparsable treatment receives a score of 0
for every applicable treatment component. If the entire model output is
missing, diagnosis and all applicable treatment components receive 0.

For Hager confidence intervals, use a stratified case-level bootstrap. In each
replicate, resample with replacement separately within each of the four
pathology strata, drawing exactly 25 cases within each pathology. This preserves
the 25-per-pathology design in every replicate; do not resample the four
pathologies themselves or pool all 100 cases before resampling. Recompute the
full-information diagnosis estimate, sequential diagnosis estimate,
each full-information and sequential treatment-component estimate, and each
sequential-minus-full difference, applying the same sampled case IDs to both
conditions. Use 5,000 percentile-bootstrap replicates with a fixed
`hager_bootstrap_seed` of `2023`.

No information-order, ablation, model-comparison, or secondary workflow
decomposition is planned for this study. The Hager analysis is intentionally
limited to the primary full-information versus sequential-workflow contrast.

### Hager model and execution scope

Use `gpt-4o-2024-11-20` for both conditions. Record the exact model ID in every
run. This fixed GPT-4o snapshot is selected for reproducibility and for
continuity with the GPT-4o-based analyses elsewhere in the project. The
existing Hager framework uses an older OpenAI client interface and a legacy
`gpt-4` configuration, so the API adapter and model configuration must be
updated before running the study.

Begin with a 16-case pilot, with exactly four cases per pathology, using the
same model and prompts intended for the main analysis. Verify prompt
construction, tool/request parsing, stopping behavior, diagnosis and treatment
parsing, treatment scoring in the full-information evaluator, and saved
trajectories before scaling.

The main analysis is one model on a prespecified balanced subset of 100 cases:
25 cases per pathology. Construct the inventory from the validated IDs in
`pathology_ids.json` by sorting eligible `hadm_id`s
within each pathology, setting the sampling seed to `2023`, and sampling 25
IDs without replacement within each pathology. Save the complete inventory,
including sampled and unsampled cases, with at least these columns:
`hadm_id`, `pathology`, and `inclusion_status`. Save the seed and the
eligibility rule alongside the inventory. The same saved inventory must feed
both the full-information and sequential conditions; neither condition may
resample or drop cases independently. The pilot and this 100-case analysis are
the complete Hager scope. A larger extension and a full replication across
many local 70B models are out of scope.

### Hager API cost

The current GPT-4o price is $2.50 per million input tokens and $10.00 per
million output tokens under standard pricing. See the [official GPT-4o model
page](https://developers.openai.com/api/docs/models/gpt-4o) and [official API
pricing](https://developers.openai.com/api/docs/pricing).

The cost estimate must be based on API usage recorded during the pilot rather
than a guessed number of calls, because the sequential condition can make
multiple requests per case and sends an expanding conversation context. A
pre-pilot estimate is nevertheless useful for deciding whether to proceed. In
the released files, the median case contains about 5,500 characters of HPI,
examination, laboratory, microbiology, and imaging text (about 1,400 tokens
using a conservative character-to-token proxy); the 90th-percentile case is
about 9,900 characters (about 2,500 tokens) before framework instructions and
conversation history are added. The framework also permits up to 10 sequential
agent iterations.

The budget calculation is:

\[
\mathrm{cost}
= \frac{2.50}{10^6} \times \mathrm{input\ tokens}
+ \frac{10.00}{10^6} \times \mathrm{output\ tokens}.
\]

Run the 16-case pilot first and save usage for every API request. At
minimum, the request log must contain the condition, `hadm_id`, call index,
model ID, timestamp, input-token count, output-token count, total-token count,
request status, and request cost. Save a run-level summary with total calls,
tokens, cost, retries, and failures by condition and for the full run. Use the
measured per-case cost to set the main-run budget. Before the pilot, use the
following planning ranges:

| Run | Expected API cost | Reserve before execution |
|---|---:|---:|
| 16-case pilot | $2–$6 | $10 |
| 100-case main analysis | $10–$25 | $40 |

These ranges assume one full-information call per case and roughly 4–6
sequential calls per case, with the sequential calls repeatedly carrying the
case context. The reserve allows for longer cases, framework summarization
calls, retries, and occasional outputs longer than expected; it is not a
claim about realized usage. Stop and reassess if the pilot's measured
per-case projection exceeds the $40 main-analysis reserve. The realized amount
must be reported from the API usage records.

### Hager interpretation

The full-information versus sequential comparison is a controlled workflow
contrast on the same cases, not a randomized clinical intervention. It should be
described as evidence that information availability and interaction format can
change measured model performance. It does not establish that a particular
workflow effect would hold in clinical practice without additional validation.

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
   analysis scripts (`analysis/study_2_hager.py` and
   `analysis/study_2_goh.py`). Add the explicit Hager API adapter in
   `analysis/study_2_hager_api.py`. Save machine-readable tables, metadata, and
   the bootstrap configuration under `experiments/reports/study2/` when
   explicitly run.
5. Keep credentialed MIMIC-derived case text and prompts local; reports may
   contain IDs and aggregate results but must not publish clinical text.
6. Add focused regression tests under `tests/test_study_2.py` for bootstrap
   weights, result pairing, missing outputs, and API usage accounting. These
   tests must pass before any Study 2 results are trusted.

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
