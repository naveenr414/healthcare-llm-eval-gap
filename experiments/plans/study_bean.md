---

# Bean information and interaction decomposition

# Bean Information, Interaction, and Uptake Decomposition

## Question

How do the ordered performance differences between full-case LLM evaluation,
observed interaction, disclosed-information counterfactuals, and human final
decisions align with (i) information not being revealed by the user, (ii)
multi-turn interaction and presentation format, and (iii) human uptake?

The experiment should report both disposition accuracy and relevant-condition
accuracy. It should distinguish the performance of the model from the
performance of the human–LLM system.

## Motivation

The existing Bean/HELPMed analysis compares four stages, but the stages change
several things simultaneously. The full-case LLM receives a complete,
canonical case and is asked directly for an answer. In the human treatment, the
participant decides what to reveal, interacts over multiple turns, interprets
the model's replies, and makes the final decision. The proposed counterfactual
LLM evaluations hold the underlying case and model fixed while changing the
information set and presentation format.

The primary scientific target is not a causal effect of conversation in the
strict experimental sense. The new model-only conditions are counterfactual
reconstructions of the observed conversations. They identify how much model
performance changes under controlled information/presentation transformations,
while the human final-decision comparison measures the additional uptake gap.

## Existing Setup

The existing Bean files and labels are retained:

- `data/bean/direct_trials_condition.csv`: full-case direct LLM trials for
  GPT-4o, Llama 3 70B, and Command R+.
- `data/bean/clean_examples.csv`: 600 observations per treatment, containing
  the observed patient messages, LLM messages, final participant choice, and
  participant cluster.
- `data/bean/clean_prescored.csv`: red-flag and differential correctness
  labels for the observed LLM and participant text.
- `data/bean/saved_results.csv`: an existing patient-first-message
  evaluation for treatment 1 (Llama) retained for provenance; it is not a
  primary condition in this revised GPT-4o experiment.
- `data/bean/scenarios.csv`: scenario IDs, gold disposition, red flags, and
  full differential.

The Bean/HELPMed treatment coding is:

| `model_id` | Arm |
|---:|---|
| 1 | Llama 3 70B |
| 2 | GPT-4o |
| 3 | Control |
| 4 | Command R+ |

Treatment 2 is the GPT-4o arm used for the primary experiment. The other model
and control treatments are not rerun here; their existing files remain
available for context and future extensions. Every future table, figure, and
report must use these labels rather than treating `model_id = 1` as GPT.

The existing study uses ten scenarios and 600 observations per arm. The
existing bootstrap gives each scenario equal weight and resamples patient
participants as clusters for human-treatment observations. Preserve these
conventions unless a result is explicitly labeled as a raw-row sensitivity.

## Experimental Design

### Outcomes

Report two outcome families for every condition:

1. **Disposition accuracy:** whether the model's or participant's primary
   healthcare-service recommendation matches the scenario's gold category in
   `scenarios.csv`. The five categories are Ambulance, A&E, Urgent Primary
   Care, Routine GP, and Self-care. Dispositions are scored from the service
   recommendation, never from a diagnosis or explanation.
2. **Relevant-condition accuracy:** whether the response contains at least one
   condition in the scenario's `full_differential`, using the existing
   canonical scoring procedure.

Also report the stricter red-flag outcome: whether the response contains at
least one condition in the scenario's `red_flags`. Do not silently substitute
the differential outcome for disposition accuracy.

The condition-specific disposition sources and extraction rules are:

| Condition | Source | Extraction |
|---|---|---|
| A | Direct model response | Parse the answer to standardized question 1 |
| B | Observed model messages | Classify the final explicit service recommendation in the conversation |
| C | `participant next_step` | Map the participant's final choice to one category |
| D | Newly generated response | Parse the answer to standardized question 1 |
| E1 | Newly generated response | Parse the answer to standardized question 1 |
| E2 | Newly generated response | Parse the answer to standardized question 1 |

B is different because the real conversation did not necessarily use the
standardized two-question prompt. If a response gives no clear service
recommendation, gives conflicting recommendations, or gives only vague advice
such as "seek medical attention," disposition is coded as ambiguous/missing;
the response is not forced into a category. For example, "Go to A&E" maps to
A&E, "See an urgent GP today" maps to Urgent Primary Care, "Seek medical
attention" is ambiguous, and "See your GP, or go to A&E if concerned" is
ambiguous unless one current primary recommendation is clearly stated.

Use all responses for the primary result: ambiguous, missing, blank, and
unparsable dispositions count as incorrect in primary disposition accuracy.
Report the ambiguity/missingness rate separately. Valid-only accuracy may be
reported as a sensitivity analysis. Existing direct-trial responses do not
already contain a validated disposition score; raw responses must be newly
parsed and validated.

### Conditions

For the GPT-4o arm, estimate the following model-only conditions on the same
observed case IDs wherever possible:

**A. Full-case canonical single-turn (existing benchmark).**

Provide the complete original scenario, including Specific Case Details,
General Life Details, and Additional Medical History, followed by the standard
two questions. Reuse the existing direct trials and stored raw responses; do
not rerun A for outcomes already computed. Parse the stored raw responses for
the newly specified disposition outcome. Only a documented missing direct trial
may be rerun, using the original model ID and prompt settings.

For disposition, distinguish two quantities. Bean et al.'s original GPT-4o
direct benchmark is 64.7%; the paper reports this from a disposition-only direct
prompt. The current implementation also reports a parser-based disposition
score from the stored raw direct responses, but this is a sensitivity estimate
under the repository's stored response format and must not be described as the
original Bean score.

**B. Observed multi-turn model performance (existing human conversation).**

Use the stored LLM response from the actual conversation and score it using the
existing `differential_correct_bot`, `red_flag_correct_bot`, and disposition
labels where available. This is descriptive observed multi-turn performance,
not a newly generated counterfactual. Report two B outcomes:

- **Primary B:** the final model turn, for comparability with one-shot
  conditions and the participant's final decision.
- **Secondary B:** any-turn recognition, equal to 1 if any model message in the
  conversation contains a relevant condition or red flag.

The any-turn outcome applies to relevant-condition and red-flag recognition;
disposition remains a final-recommendation outcome and is not credited from an
earlier model message.

**C. Human final decision (existing human conversation).**

Use the participant's final disposition and named conditions after the
conversation. This is the human–LLM system outcome, not another model-only
condition.

**E1. Stitched patient-information single-turn, raw wording.**

Concatenate all user messages from the observed conversation, in chronological
order, into one prompt. Do not include any previous LLM responses. Ask the
assigned model the standard two questions once. This estimates the effect of
having all patient-disclosed information available simultaneously while
removing turn-taking and response-path dependence.

The stitched prompt should preserve the user's original wording and order, with
only explicit turn separators.

**E2. Stitched patient-information single-turn, canonicalized facts.**

Use a one-time, offline GPT-assisted extraction pass to rewrite the participant's
user messages into structured propositions. The extractor receives only the raw
user messages—not the original hidden scenario or any LLM response—and must
return JSON containing every proposition, an exact source quote and turn,
faithful canonical wording, a proposition type, and a case-format section.
Preserve every proposition, including uncertainty, negation, and user-supplied
diagnostic beliefs or causal interpretations. Label beliefs as patient-reported
rather than objective facts. Validate exact source coverage; any invalid,
unmatched, or uncovered sentence is retained verbatim as labeled
patient-reported text.

Render E2 deterministically from the saved extraction JSON in the original
case-format sections. E2 therefore contains only information from E1 while
changing wording and organization. The extraction JSON and validation status
are versioned outputs; the evaluated GPT-4o call never performs its own
canonicalization.

**D. Raw-wording information-release curve.**

For each observed GPT-4o interaction and each cumulative turn \(t\), make a
fresh independent GPT-4o call containing the user's raw messages from turns 1
through \(t\), in their original order, with explicit turn separators. Do not
include any previous LLM response, hidden original-case information, or future
user turns. Ask the standard two questions. This produces a turn-level curve
of what GPT-4o says when given exactly the information disclosed up to that
point, using raw wording. It is a newly generated counterfactual condition,
not the stored model response from the natural conversation (B). The primary
turn-by-turn analysis compares turns \(t\) and \(t+1\) only among interactions
that reached turn \(t+1\): evaluate both cumulative prompts for that same set
of IDs and report the within-ID change. This is conditional on reaching turn
\(t+1\), not a population-wide causal effect. The available-panel level curve,
which averages each turn over all interactions with at least that many turns,
is retained as a descriptive secondary result and must be labeled as such.
The full-case A estimate is a separate reference point, not an additional D
call.

### Disposition-only prompt sensitivity check

The original Bean et al. direct-model disposition benchmark used a
disposition-only prompt, whereas the primary D/E1/E2 implementation asks the
model for both disposition and relevant conditions in one response. To assess
whether this prompt-format difference contributes to the disposition gap, run a
secondary check on the same 600 GPT-4o E1 inputs:

- preserve the complete raw user-message sequence and the GPT-4o model settings;
- ask only the disposition question using the five NHS categories;
- parse the response with the same disposition parser and primary denominator;
- compare the new outcome to the existing combined-prompt E1 outcome at the
  interaction level and with scenario-balanced, participant-clustered bootstrap
  intervals.

This check is not a replacement for A or E1. Bean et al.'s original GPT-4o
disposition benchmark is 64.7%; the new check estimates disposition accuracy
under raw participant-disclosed information with a disposition-only prompt.
The contrast between this check and combined-prompt E1 is a prompt-format
sensitivity result, not an information or human-uptake effect.

### Human–LLM system condition

For the GPT-4o arm, the real participant's final disposition and named
conditions are retained as the system-level outcome. The model-only outcomes
are not substituted for the participant's decision. Report:

- model performance under A, B, D, E1, and E2;
- observed LLM performance in B;
- participant final-decision performance after the conversation;
- paired changes from observed LLM output to participant final decision.

## Data and Sample

Use treatment 2 observations with a successful one-to-one join on `id` across
`clean_examples.csv` and `clean_prescored.csv`. Preserve the observed 600
records and the ten scenario IDs. The primary unit is an observed
patient–scenario interaction; `participant_id` is the bootstrap cluster.

For model-only counterfactuals, use the same observed IDs and GPT-4o model as
the conversation. Do not pool other models into the primary experiment.

The E2 extraction JSONL must be version-controlled as a derived input artifact
before the evaluated E2 calls are run. Each row must contain the interaction ID,
source turn, exact source quote, canonical proposition, proposition type,
case-format section, validation status, model ID, prompt hash, and token usage.
The extractor receives no original-case text, so it cannot import undisclosed
facts. The original HELPMed scenario text may be retained separately for audit,
but it is not supplied to the E2 extractor or evaluated E2 prompt.

For the GPT-4o arm, the planned new-call counts are 1,411 for D (one call per
observed user turn), 600 for E1, 600 for E2, and 600 for the one-time E2
preprocessing pass: 3,211
calls total before retries. A and C require no new calls, and B uses stored
model messages.

At current standard GPT-4o pricing, use approximately $9--12 as the expected
API cost and reserve $15 for retries and prompt-length variation. Record actual
request-level usage and cost in the metadata output.

The completed disposition-only prompt sensitivity check adds 600 optional
GPT-4o calls. It used $1.02 in API cost, so the realized total for the primary
run plus this check is approximately $10.86. The check is stored separately
from the primary E1/D/E2 records and should not be folded into the primary
condition estimates.

The realized primary run used 3,211 GPT-4o calls and cost $9.84: 1,411 D
calls, 600 E1 calls, 600 E2 calls, and 600 E2 extraction calls. The primary
report's combined-prompt E1 disposition estimate is 43.8%; the optional
disposition-only E1 check is 36.3%. The latter is a prompt-format sensitivity
condition, not a replacement for E1.

## Procedure

### Prompting

Use the same model, temperature, token limit, and standard two-question output
format for all newly generated model-only conditions. Record model ID, prompt
variant, prompt text, source user IDs, token usage, retries, and raw response.
Do not use conversation history or previous model responses in D, E1, or E2.

For A, preserve the original direct-evaluation prompt. For E1, concatenate all
user turns without adding facts. For E2, use the saved GPT-assisted extraction
and render all validated propositions in a fixed canonical template. Do not
endorse a patient-reported belief as an objective fact; retain its proposition
and label its source and uncertainty. For D, render cumulative user turns in
raw wording. The E2 preprocessing pass uses temperature 0 and a structured JSON
response; its model, prompt, usage, retries, and validation status are logged
separately from the evaluated GPT-4o calls.

### Estimands

For outcome (Y), condition (c), and scenario (s), report the
scenario-balanced estimate

\[
\hat p_{c,Y} = \frac{1}{10}\sum_{s=1}^{10}
\left(\frac{1}{N_{c,s}}\sum_i Y_{i,c,s}\right).
\]

For paired model-only contrasts on the same observed IDs, report the mean
within-ID change, averaged equally across scenarios. The primary contrasts are:

- E1 vs. E2: raw wording/order vs. canonical case framing with the same
  disclosed information;
- B vs. E1: observed multi-turn model vs. raw stitched single-turn model;
- B vs. C: observed model advice vs. human uptake;
- A--E2: the scenario-balanced performance difference between the complete
  canonical case and the information disclosed in observed participant
  interactions.

For the A--E2 comparison, define the scenario-paired estimand for outcome \(Y\)
as

\[
\Delta_s(Y) = \bar Y_{A,s} - \bar Y_{E2,s},
\qquad
\Delta(Y) = \frac{1}{10}\sum_{s=1}^{10}\Delta_s(Y).
\]

A and E2 are paired at the scenario level but not at the interaction-ID level.
Both conditions are evaluated on the same ten scenarios; E2 additionally
varies according to the information disclosed by each observed participant.

For the information-release curve, report the estimate at each cumulative turn
and the change from the previous turn, followed by the already-estimated A
full-case reference. The primary D contrast at each adjacent pair uses the
fixed panel that reached the later turn; report the available-panel curve as a
secondary descriptive result. Report both disposition and relevant-condition
outcomes.

Overall, present A, B, C, D, E1, and E2 as an ordered descriptive
decomposition. The component differences are path-dependent counterfactual
contrasts, not unique causal effects or fractions of the total gap explained.
Where compatible estimands permit, verify the arithmetic identity of the
sequence, but do not interpret individual components as causal shares.

### Confidence intervals

Use 5,000 percentile-bootstrap replicates with seed 0 for all estimates and
contrasts. Keep the ten scenarios fixed and give them equal weight in every
replicate. For each replicate:

1. Sample `participant_id` clusters with replacement and retain every row from
   each sampled participant, including all scenarios, E1/E2 pairs, B/C
   outcomes, and all D turns.
2. For each patient-derived condition, compute the mean within each scenario
   and then average the ten scenario means equally.
3. For A, independently resample direct-trial rows within each scenario and
   compute its scenario-balanced estimate.
4. For A--E2, subtract the independently bootstrapped scenario-balanced A and
   E2 estimates.
5. For E1--E2, B--E1, and D adjacent-turn comparisons, preserve the paired
   outcomes from the same interaction or participant within the replicate.

For the primary D comparison between turns \(t\) and \(t+1\), restrict both
cumulative-prompt outcomes to IDs that reached \(t+1\), then compute the
within-ID change before scenario balancing. This preserves participant
clustering while removing mechanical composition changes between adjacent
turns. Report 95% intervals as the 2.5th and 97.5th percentiles. The release
curve's pointwise intervals are descriptive; use a simultaneous band or
false-discovery-adjusted secondary display if many turn-level comparisons are
emphasized.

## Outputs

Required artifacts:

- `information_decomposition_main.csv`: point estimates and 95% intervals for
  both outcome families, by model and condition, including disposition
  ambiguity/missingness counts.
- `information_decomposition_contrasts.csv`: paired contrasts and intervals.
- `information_release_curve.csv`: turn-level cumulative estimates and
  intervals, with fixed-panel adjacent-turn contrasts as primary and the
  available-panel curve labeled secondary.
- `e2_extractions.jsonl`: saved GPT-assisted proposition extractions,
  source quotes, canonical rewrites, and validation status.
- `counterfactual_prompt_metadata.jsonl`: source IDs, retained facts, prompt
  variant, model, usage, and execution status.
- `information_decomposition_report.md`: concise factual report with separate
  disposition, red-flag, and differential results.
- A figure showing the condition sequence A, B, C, D, E1, and E2 and a second figure showing the
  information-release curve, if the curve is sufficiently interpretable.

## Verification

### Required correctness checks

- Treatment-to-model mapping is verified from the raw histories and documented.
- Every included counterfactual has exactly one source interaction ID, scenario,
  assigned model, and prompt variant.
- No user fact appears in D, E1, or E2 unless it occurs in the
  corresponding observed user messages.
- No observed conversation LLM response text appears in D, E1, or E2.
- E2's saved extraction contains no hidden original-case input and the rendered
  prompt agrees exactly with the saved extraction.
- Exact source coverage and fallback checks confirm that every E1 proposition
  is represented in E2, including diagnostic beliefs and unmatched text.
- A manual audit of sampled E1/E2 pairs confirms semantic equivalence with no
  added or dropped user information; differences are limited to wording,
  organization, and explicit patient-reported labeling.
- Prompt hashes, model IDs, and generation settings are stored.
- Existing Bean point estimates for the observed conditions are reproduced
  before adding new conditions.
- B's primary final-turn and secondary any-turn recognition outcomes are
  reproduced from the stored model messages by hand-checked examples.
- The stitched condition is invariant to CSV row order and preserves user-turn
  order.
- A toy extraction with known source sentences produces the expected canonical
  prompt and fallback text, and excludes hidden facts.
- Paired joins are one-to-one, and participant-cluster resampling preserves all
  outcomes for an interaction.
- For every D adjacent-turn comparison, the IDs contributing at turns \(t\) and
  \(t+1\) are identical and all sampled participant clusters carry their full
  set of rows together.
- Validate the disposition parser on hand-labeled responses from each model
  condition.
- Report valid, ambiguous, missing, and conflicting disposition counts by
  condition.
- Confirm that `next_step` mappings for the human outcome use the same
  five-category ontology.
- Confirm that existing direct-trial responses do not already contain a
  validated disposition score; raw responses must be newly parsed.

### Diagnostics

- Counts and estimates by scenario, model, and prompt variant.
- Blank-response, timeout, retry, and parse-failure rates.
- Number and proportion of propositions canonically extracted versus retained as
  fallback patient-reported text, by turn.
- Whether the model's answer changes after each newly disclosed fact.
- Separate results for conversations where the original dangerous/red-flag slot
  was disclosed versus hidden.
- Error categories: benign framing, missing-information failure,
  misinterpretation of disclosed information, failure to act on a recognized
  red flag, and blank/incomplete response.
- Compare raw-row and scenario-balanced estimates as a sensitivity analysis.

## Interpretation

A and E2 are paired at the scenario level but not at the interaction-ID level.
The A--E2 contrast estimates the gap between complete canonical information
and the information actually disclosed by participants; it does not estimate
the causal effect of missing information independent of interaction behavior.
A large E1-to-E2 gap is consistent with sensitivity to wording/order or
presentation even when the information set—including patient-reported
diagnostic beliefs—is held fixed. A large B-to-E1 gap indicates that the
observed multi-turn response path differs from a stitched single-turn
evaluation beyond the information revealed by the user. A large
observed-model-to-human gap describes the additional difference after human
uptake and decision-making.

If the fixed-panel release curve rises sharply when a small number of red-flag
facts are revealed, those facts are plausible bottlenecks. If it remains low
despite canonical disclosure, the problem is more consistent with model
reasoning or triage failure. These are descriptive patterns, not identified
causal effects.

None of these observational/counterfactual comparisons alone identifies a
causal effect of multi-turn interaction or human behavior. The design also
cannot recover the unavailable expert-query/multi-turn human cell without new
data collection.

## Implementation Notes

Extend the existing Bean analysis rather than modifying the original raw
files. Reuse the existing correctness functions and bootstrap conventions where
they apply. Run E2 preprocessing first, inspect its validation/fallback rates,
then run the evaluated D/E1/E2 calls. New API calls must be isolated from
reporting code and must never be made by tests or by the no-API reproduction
script.

The implementation should initially run a small dry-run on one scenario and a
few IDs, then run the full experiment after prompt rendering and outcome
parsing pass the required checks. The full experiment should be resumable and
write canonical JSONL outputs before aggregation.

## Open Questions

None.


---

# Bean confidence intervals, paired changes, and path dependence

# Bean Confidence Intervals, Paired Changes, and Path Dependence

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

The repository defines four conditions in `analysis/study_bean.py`:

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

The Bean implementation includes a 5,000-replicate bootstrap
with random seed 0 and paired, participant-clustered resampling for the last
three conditions. It is a starting point, not a substitute for verifying the
joins and estimands in this plan. Do not run the API path in `analysis/study_bean.py`, because it
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
0, preserving the conventions in the Bean implementation:

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

- `data/bean/direct_trials_condition.csv`
- `data/bean/saved_results.csv`
- `data/bean/clean_examples.csv`
- `data/bean/clean_prescored.csv`
- `data/bean/scenarios.csv` for scenario labels and urgency/condition
  metadata in the heterogeneity analysis

Inclusion rules:

- Condition 1: rows with `model == "GPT 4o"`.
- GPT-4o observed conditions: rows with `treatment_id == 2` in
  `clean_examples.csv`, with successful one-to-one joins on `id` to
  `clean_prescored.csv`.
- Exclude no observations silently. Any missing, duplicate, or unmatched IDs
  should fail a required check and be reported.

For condition 2, use `saved_results.csv` as the authoritative result file. This
is the file written by `analysis/study_bean.py` and consumed by the existing
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
   cost: **$0**. The implementation must not call the API path in `analysis/study_bean.py` or any
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
  Bean bootstrap helper.
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
seed from the Bean implementation, but add explicit validation, the
main table, paired transition counts, and the 2×2 data-availability audit.

Use a distinct output directory under `experiments/` or another clearly named
non-source-data location. Preserve all existing user changes in
`analysis/study_bean.py`.

## Open Questions

None for the primary analysis. The only substantive limitation is structural:
the current repository does not contain a valid expert-written multi-turn
condition, so that cell should remain missing rather than be generated by a
new GPT call under this plan.


---

# Bean model rank reversals across A/B/C evaluation

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

Use the existing Bean files and Bean scoring conventions:

- `data/bean/direct_trials_condition.csv`: 600 direct trials per model for
  GPT-4o, Llama 3 70B, and Command R+.
- `data/bean/clean_examples.csv`: 600 observations per randomized arm,
  including observed user and model messages, final participant choice, and
  participant cluster.
- `data/bean/clean_prescored.csv`: existing red-flag and differential
  correctness fields for model and participant responses.
- `data/bean/scenarios.csv`: ten scenarios and the gold differential,
  red-flag, and disposition labels.
- `experiments/plans/study_bean.md` (information and interaction section):
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
- `bean_model_rank_reversals_abc.md`: concise report distinguishing model-only
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
Bean outputs. Reuse the existing scoring fields and bootstrap conventions
where they are valid, but correct the treatment mapping at the input boundary.
Preserve the raw files and prior reports. Record the mapping source and
bootstrap seed in the plan/report; input file hashes and a separate bootstrap
draw export remain future reproducibility improvements.

Do not rerun A, B, or C model calls for the primary analysis. A future extension
could generate standardized model-only patient-information conditions for all
three models, but that is a different estimand and is outside this plan.

## Open Questions

None.


---

# Bean–Hager model-rank comparison

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

- `data/bean/direct_trials_condition.csv` contains three models—Command R+,
  GPT-4o, and Llama 3 70B—in the expert-written, single-turn condition.
- `data/bean/clean_examples.csv` contains 600 observations for each of four
  randomized arms. The Bean study identifies these arms as GPT-4o, Llama 3,
  Command R+, and control. The authors' HELPMed analysis notebook records the
  mapping as `1 = Llama 3 70B`, `2 = GPT 4o`, `3 = Control`, and
  `4 = Command R+`. The three treatment arms are human–LLM interactions, not
  model-only evaluations.
- `data/bean/clean_prescored.csv` provides the prescored participant outcomes
  for all four arms. The existing analysis uses only the GPT-4o arm.
- `analysis/study_bean.py` defines the existing Bean report workflow;
  correctness labels and scenario-balanced estimands.

The Bean files therefore support a cross-model comparison in both the
normal/direct condition and the randomized human-assisted condition, subject to
an estimand distinction. The direct condition measures model-only performance;
the human-assisted condition measures the outcome of a participant assigned to a
model. The patient first-message API condition and the existing model-response
analysis are GPT-4o-only. Thus, the current report estimates only the GPT-4o
realistic path, although the underlying files contain the other two LLM arms.

Hager et al. data and analysis:

- `data/mimic/mimic-iv-ext-cdm/1.1/` is the local
  credentialed dataset.
- `outputs/study_hager/hager_case_inventory.csv` defines the
  balanced 100-case sample, with 25 cases per pathology.
- `outputs/study_hager/hager_main_scored_results.csv` contains
  GPT-4o results for `full_information` and `sequential` conditions.
- `analysis/_hager_api.py` runs the two conditions and currently fixes
  the model to one model ID; `analysis/study_hager.py` performs common
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

- `data/bean/direct_trials_condition.csv`
- `data/bean/clean_examples.csv`
- `data/bean/clean_prescored.csv`
- `data/bean/scenarios.csv`

Hager inputs:

- the local MIMIC-IV-Ext CDM files;
- `data/mimic/mimic-iv-ext-cdm/1.1/pathology_ids.json`;
- `outputs/study_hager/hager_case_inventory.csv`.

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

Extend the no-API reporting path rather than changing the completed Bean
results. For Hager, refactor `analysis/_hager_api.py` so the model ID is
an explicit run parameter and include it in output paths and usage summaries;
preserve the canonical schema consumed by `analysis/study_hager.py`. Add the
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
