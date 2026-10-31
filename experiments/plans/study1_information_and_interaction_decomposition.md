# Study 1 Information, Interaction, and Uptake Decomposition

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

The existing Study 1 files and labels are retained:

- `data/study1/direct_trials_condition.csv`: full-case direct LLM trials for
  GPT-4o, Llama 3 70B, and Command R+.
- `data/study1/clean_examples.csv`: 600 observations per treatment, containing
  the observed patient messages, LLM messages, final participant choice, and
  participant cluster.
- `data/study1/clean_prescored.csv`: red-flag and differential correctness
  labels for the observed LLM and participant text.
- `data/study1/saved_results.csv`: an existing patient-first-message
  evaluation for treatment 1 (Llama) retained for provenance; it is not a
  primary condition in this revised GPT-4o experiment.
- `data/study1/scenarios.csv`: scenario IDs, gold disposition, red flags, and
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
- Existing Study 1 point estimates for the observed conditions are reproduced
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

Extend the existing Study 1 analysis rather than modifying the original raw
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
