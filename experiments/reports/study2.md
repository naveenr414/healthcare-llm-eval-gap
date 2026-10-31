# Study 2 report: Hager and Goh decompositions

## Summary

This run completed the no-API Goh analysis, the 16-case Hager pilot, and the
planned 100-case Hager main analysis. The main Hager run used
`gpt-4o-2024-11-20` on the same 25 cases per pathology under
full-information and sequential-information conditions.

Across the pilot and main run, Hager made 561 successful API requests. The
100-case main run made 100 full-information calls and 379 sequential workflow
calls. Its recorded API cost was **$1.67305**: $0.60356 for full information
and $1.06949 for sequential information. There were no failed requests or
retries in the main run. The pilot cost was an additional $0.2912375, for a
combined Hager API cost of **$1.9642875**.

## Experiment

Hager cases were selected from the authoritative `pathology_ids.json` source
with the prespecified seed 2023, selecting four cases per pathology. All 2,400
authoritative IDs were eligible. Empty microbiology or procedure domains were
retained as valid cases and recorded in the inventory rather than treated as
exclusions. Both Hager conditions used the same 16 selected IDs.

The Hager pilot summaries were descriptive only because no confidence intervals
were computed for the pilot. Diagnosis accuracy was 0.8125 in both conditions.
The main analysis below is the prespecified 100-case result. Pilot component-
level treatment scores were:

| Component | Full information | Sequential |
|---|---:|---:|
| Antibiotics | 0.667 | 1.000 |
| Appendectomy | 1.000 | 1.000 |
| Cholecystectomy | 0.375 | 0.500 |
| Colectomy | 0.250 | 0.000 |
| Colonoscopy | 0.250 | 0.000 |
| Drainage | 0.250 | 0.250 |
| ERCP | 0.250 | 0.500 |
| Support | 0.438 | 0.750 |

### Hager main analysis

Intervals are 95% percentile intervals from 5,000 stratified bootstrap
replicates, resampling 25 cases within each pathology and preserving the paired
conditions.

| Outcome | Full information | Sequential | Sequential − full |
|---|---:|---:|---:|
| Diagnosis | 0.860 [0.790, 0.920] | 0.810 [0.740, 0.880] | −0.050 [−0.120, 0.010] |
| Antibiotics | 0.787 [0.693, 0.880] | 0.893 [0.827, 0.960] | 0.107 [0.013, 0.200] |
| Appendectomy | 0.960 [0.880, 1.000] | 0.960 [0.880, 1.000] | 0.000 [0.000, 0.000] |
| Cholecystectomy | 0. [0.360, 0.520] | 0.540 [0.500, 0.600] | 0.100 [0.020, 0.180] |
| Colectomy | 0.160 [0.040, 0.320] | 0.120 [0.000, 0.240] | −0.040 [−0.200, 0.120] |
| Colonoscopy | 0.160 [0.040, 0.320] | 0.120 [0.000, 0.240] | −0.040 [−0.160, 0.080] |
| Drainage | 0.100 [0.020, 0.180] | 0.060 [0.000, 0.120] | −0.040 [−0.140, 0.060] |
| ERCP | 0.200 [0.080, 0.360] | 0.280 [0.120, 0.480] | 0.080 [−0.120, 0.320] |
| Support | 0.580 [0.490, 0.670] | 0.750 [0.660, 0.830] | 0.170 [0.060, 0.280] |

The Goh analysis used the released 400-row file, with five cases equally
weighted in the primary `total_pct` estimator. Confidence intervals used 5,000
independent ID-clustered bootstrap replicates with seed 2023. The three groups
were 46 physician IDs for physicians plus conventional resources, 46 physician
IDs for physicians plus GPT, and five GPT-alone run IDs.

## Results

### Goh primary decomposition

Values are percentage points. Intervals are percentile-bootstrap 95% intervals.

| Group or contrast | Estimate | 95% interval |
|---|---:|---:|
| Physicians + conventional resources | 35.75 | [33.46, 38.01] |
| Physicians + GPT | 42.68 | [39.77, 45.93] |
| GPT alone | 43.67 | [39.19, 46.76] |
| Physicians + GPT minus conventional resources | 6.94 | [3.31, 10.90] |
| GPT alone minus physicians + GPT | 0.98 | [-4.08, 5.55] |
| GPT alone minus conventional resources | 7.92 | [3.10, 12.01] |

The released secondary subscores were also analyzed, but their case support is
not uniform: factual is defined for cases 1–2, diagnostic for cases 2 and 4,
and general for cases 1 and 3. These estimates therefore use equal weighting
over the cases where each subscore is defined; undefined cells are not scored
as zero.

## Verification

- Hager inventory: 2,400 rows, 2,400 eligible, and 16 pilot cases selected as
  4 per pathology.
- Hager API main run: 100/100 full-information cases and 100/100 sequential
  cases completed; all 479 main-run requests were successful.
- Hager pilot: 16/16 cases completed in each condition; all 82 pilot requests
  were successful.
- Hager condition pairing and pathology labels were validated before scoring.
- Hager canonical outputs preserve raw output, parsed diagnosis and treatment,
  trajectories, model ID, usage, diagnosis score, and treatment components.
- Goh source dimensions and group counts matched the documented source: 400
  records, 97 IDs, 197/178/25 records, and 46/46/5 IDs.
- Goh bootstrap completed with 5,000 replicates per outcome and zero redraws.

## Diagnostics and robustness

The Goh intervals are clustered by the released ID units rather than by raw
rows. The five GPT-alone IDs are treated as model-run replicates, not human
participants. Hager pilot scores are reported by treatment component rather
than collapsed into a single treatment score.

The Hager scoring environment did not contain the upstream evaluator's
optional `en_core_sci_lg` spaCy model or `exllamav2` package. To score the
already completed pilot without making additional API calls, the evaluator was
run with a local compatibility shim using a blank spaCy pipeline and text-based
fallback behavior. The Hager scores should therefore be treated as pilot
diagnostics pending rerun in the fully specified evaluator environment.

## Interpretation

The Goh results are consistent with a positive descriptive difference between
physicians plus GPT and physicians with conventional resources. The GPT-alone
versus physicians-plus-GPT contrast is small relative to its interval, so this
analysis does not establish a clear difference between those two groups. These
are descriptive decompositions of released scores, not a causal mediation
estimate.

The Hager main analysis shows a small negative point estimate for diagnosis in
the sequential condition, with an interval that includes zero. Treatment
effects are component-specific: sequential information is higher for
antibiotics, cholecystectomy, and support, while the other components are
uncertain or unchanged. This does not establish that one workflow is generally
better; it shows that the workflow comparison depends on the scored decision
component.

## Caveats and deviations from plan

- The Hager pilot was run before the main analysis and remains in the output
  directory as a diagnostic; it was not pooled with the main analysis.
- Hager pilot scoring used the compatibility fallback described above. This is
  a runtime/environment deviation, not a change to the API outputs or the
  prespecified outcome definitions.
- The Goh analysis uses the released scores and cannot reconstruct the original
  physician–GPT dialogue or establish a formal causal mediation mechanism.

## Outputs

- [Hager case inventory](study2/hager/hager_case_inventory.csv)
- [Hager pilot point estimates](study2/hager/hager_pilot_point_estimates.csv)
- [Hager canonical pilot results](study2/hager/hager_pilot_canonical_results.jsonl)
- [Hager main point estimates](study2/hager/hager_main_point_estimates.csv)
- [Hager main bootstrap intervals](study2/hager/hager_bootstrap_intervals.csv)
- [Hager main canonical results](study2/hager/hager_main_canonical_results.jsonl)
- [Hager main full-information usage and cost summary](study2/hager/main/full_information_usage.jsonl.summary.json)
- [Hager main sequential usage and cost summary](study2/hager/main/sequential_usage.jsonl.summary.json)
- [Full-information usage and cost summary](study2/hager/pilot/full_information_usage.jsonl.summary.json)
- [Sequential usage and cost summary](study2/hager/pilot/sequential_usage.jsonl.summary.json)
- [Goh decomposition](study2/goh/goh_decomposition.csv)
- [Goh heterogeneity table](study2/goh/goh_heterogeneity.csv)
- [Goh analysis metadata](study2/goh/goh_analysis_metadata.json)

## Retrospective Case Studies: Mapping Assumptions to Evidence Requirements

### Overview

We examine three retrospective case studies—Bean et al., Hager et al., and Goh et al.—to illustrate how explicitly documenting evaluation assumptions can inform subsequent evaluation choices. For each study, we distinguish (1) the assumptions that would have been identified from the initial evaluation, (2) the additional evidence available or collected, (3) what this evidence reveals about the evaluation-to-deployment gap, and (4) which questions remain unresolved.

These case studies are not intended to demonstrate that BenchmarkCards identify an optimal evaluation strategy or predict the results of subsequent experiments. Rather, they illustrate how researchers could use explicit assumptions to select informative next evaluations and update their understanding as evidence accumulates.

### Summary of the Three Case Studies

| Study | Initial unresolved assumption | Additional evidence | Main finding | Recommended next evaluation | Remaining uncertainty |
|---|---|---|---|---|---|
| Bean et al. | Real patient queries may contain incomplete information and require multi-turn interaction | Direct benchmark versus patient conversations; comparisons using disclosed and complete information | Large performance gaps persist, with differences across outcomes and evaluation conditions | Improve baseline performance and evaluate robustness to incomplete information and conversational interaction | Mechanisms behind performance gaps, disposition scoring, downstream patient decisions |
| Hager et al. | Static, full-information evaluations may not capture sequential clinical decision-making | Paired full-information versus sequential evaluations on 100 cases | Small aggregate diagnosis difference, but heterogeneous results across treatment components | Improve weaker clinical decision components and test robustness across static and sequential settings | Real clinical workflows, clinician behavior, downstream patient outcomes |
| Goh et al. | Standalone LLM evaluation may not reflect performance when physicians mediate recommendations | Comparison of GPT alone, physicians with GPT, and physicians with conventional resources | No clearly distinguishable difference between GPT alone and physicians with GPT on the measured score | Deprioritize repeating the same average mediation comparison in similar settings; examine other unresolved deployment assumptions | Generalizability, formal equivalence, actual physician–LLM interactions, downstream outcomes |

### Case Study 1: Bean et al. — Incomplete Information and Conversational Interaction

**Initial evaluation and assumptions.** The initial benchmark evaluates LLM performance on medical scenarios where relevant information is provided directly to the model. However, real patients may present incomplete or ambiguous information, and models may need to interact with patients over multiple turns to obtain clinically relevant details. A BenchmarkCard constructed from the initial evaluation would therefore identify two important task assumptions: (1) whether the available information reflects what patients provide in practice, and (2) whether single-turn performance transfers to multi-turn patient conversations. A natural next evaluation would involve realistic patient queries, incomplete information, and multi-turn interaction.

**Additional evidence.** The retrospective analysis compares direct benchmark performance with model responses during patient conversations and participant-level outcomes. For GPT-4o, relevant-condition accuracy decreases from 94.7% in direct evaluation to 64.9% on the stored final model turn, while participant/system accuracy is 35.7%. In a controlled one-shot setting using the information disclosed by patients, accuracy is 91.5% when the original patient wording is preserved and 91.1% after the same information is rewritten into vignette-style propositions. The latter condition is not the hidden complete case. Relative to the 29.8 percentage-point gap between the direct benchmark and the stored final model turn, the 3.6-point decline in the canonicalized disclosed-information condition accounts for approximately 12% of the gap. The remaining difference is associated with the observed conversational setting and response path. These are ordered descriptive comparisons, not causal shares.

Disposition performance provides a complementary result. Direct benchmark accuracy is 58.7%, while one-shot performance using disclosed patient information is 43.8% with raw wording and 46.9% after canonicalization. Participant final-answer accuracy is 43.8%. The stored final-turn disposition estimates contain extensive missing or ambiguous scoring and should not be directly compared with the other conditions. These contrasts are descriptive and do not establish a causal decomposition of the performance gap.

**Implications for subsequent evaluation.** The initial BenchmarkCard would have recommended moving beyond complete-information, single-turn evaluation. The additional evidence confirms the importance of assessing models under realistic patient interactions, but also reveals that improving information availability alone may be insufficient. Two complementary next steps emerge: (1) improving baseline model capability, particularly disposition accuracy, even under controlled information conditions, and (2) evaluating robustness to incomplete information and conversational interaction. Additional work is also needed to distinguish failures of information acquisition from failures of information integration or response generation.

**Remaining uncertainty.** The mechanisms driving the differences between direct and conversational performance remain unresolved. The analysis also reveals model-ranking reversals between direct evaluation and final model-turn performance, demonstrating that evaluation conditions can affect comparative model assessments. Further work would need to investigate these mechanisms, validate disposition scoring, and determine how model outputs affect downstream patient decisions.

### Case Study 2: Hager et al. — Static Versus Sequential Clinical Decision-Making

**Initial evaluation and assumptions.** Static medical evaluations often provide a complete clinical case and ask the model to produce a diagnosis or treatment recommendation. In practice, clinical decision-making is sequential: clinicians gather information, order tests, update diagnoses, and make treatment decisions as information becomes available. A BenchmarkCard would therefore identify the assumption that full-information, single-turn performance is informative about performance during sequential clinical workflows. A natural next evaluation would compare performance on the same cases under complete-information and sequential-information conditions.

**Additional evidence.** We conducted a paired comparison of full-information and sequential evaluation on 100 clinical cases using GPT-4o. Diagnosis accuracy was 86% under full information and 81% under sequential information, a difference of -5 percentage points, with a 95% confidence interval of [-12, 1] percentage points. Thus, the aggregate diagnosis difference was relatively small and not statistically distinguishable from zero under the reported interval.

However, the effect of sequential information varied across treatment components. Sequential evaluation produced higher scores for antibiotics (78.7% versus 89.3%), cholecystectomy (44.0% versus 54.0%), and supportive care (58.0% versus 75.0%). Other components showed smaller, uncertain, or unchanged differences. Therefore, the implications of sequential evaluation depended on which clinical decision was being measured. The reported heterogeneity is across decision components; establishing heterogeneity across individual conversations would require a separate case-level analysis.

**Implications for subsequent evaluation.** The initial BenchmarkCard would have identified sequential decision-making as a potentially important mismatch. The subsequent analysis indicates that sequential evaluation does not necessarily produce a large aggregate decrease in diagnosis accuracy, but its effects vary across clinical decisions. Accordingly, the next evaluation should not simply seek to eliminate the difference between static and sequential accuracy. Instead, researchers could first identify clinical decision components with weak baseline performance, improve model capability on those components, and then test whether these improvements generalize to sequential settings.

A complementary direction would be to investigate which types of cases or clinical decisions benefit from sequential information gathering and which deteriorate. Such analyses could help identify whether failures arise from incomplete observations, information-gathering decisions, or difficulties integrating information over time.

**Remaining uncertainty.** These results do not establish that sequential interaction is unimportant. The aggregate diagnosis comparison may obscure meaningful differences across tasks or individual cases. Moreover, both evaluation conditions remain approximations of clinical practice. Additional evidence would be needed to establish performance in real clinician workflows and determine how model assistance changes clinician decisions or patient outcomes.

### Case Study 3: Goh et al. — Physician Mediation and Human–AI Performance

**Initial evaluation and assumptions.** Standalone LLM evaluations implicitly assume that model performance is informative about performance when the model is used by clinicians. However, physicians may interpret, reject, modify, or selectively incorporate model recommendations. Consequently, an LLM's standalone accuracy need not correspond to the performance of a human–AI team. A BenchmarkCard would identify the role of the human decision-maker as an unresolved outcome assumption and recommend comparing model-only performance with performance when physicians use model assistance.

**Additional evidence.** The retrospective analysis compares three conditions: physicians using conventional resources, physicians using GPT, and GPT alone. The respective scores are 35.75%, 42.68%, and 43.67%. Physicians using GPT outperform physicians using conventional resources by approximately 6.94 percentage points in the reported comparison. However, GPT alone exceeds physicians using GPT by only 0.98 percentage points, with a 95% confidence interval of [-4.08, 5.55] percentage points.

Thus, the analysis does not identify a clear difference between GPT-alone and physician-plus-GPT performance on the measured task. Although this finding does not establish statistical equivalence or the absence of physician mediation effects, it suggests that a large average difference is not evident in these evaluated cases.

**Implications for subsequent evaluation.** Unlike Bean et al., where additional evidence reveals substantial performance discrepancies, the Goh analysis suggests that one hypothesized gap may be less consequential for the measured outcome in the evaluated setting. Having directly compared model-only and physician-mediated performance, researchers could reasonably deprioritize repeating the same average comparison under closely similar conditions.

Instead, subsequent evaluations could focus on assumptions that remain unresolved, including generalization to different patients, clinical environments, and deployment contexts. Importantly, the BenchmarkCard need not recommend an additional experiment solely for the sake of collecting more evidence: some assumptions can be provisionally supported or assigned lower priority after empirical testing.

**Remaining uncertainty.** The small observed difference does not establish that standalone model performance is representative of deployment in general. The available data do not reconstruct the physician–GPT interactions or identify how physicians incorporate model recommendations. Moreover, the study does not establish equivalence across clinical settings or demonstrate improvements in downstream patient health. These remain possible targets for further evaluation, depending on the intended deployment scenario.

### Cross-Case Synthesis

The three studies illustrate different ways that additional evidence can update the assessment of evaluation-to-deployment assumptions.

**First, unresolved assumptions can correspond to substantial performance gaps.** Bean et al. demonstrates that evaluations using complete, directly presented clinical scenarios may differ substantially from performance during patient interactions. However, the additional analyses also demonstrate why it is important to distinguish identifying a gap from explaining its mechanism: differences in information availability alone do not explain all observed performance changes.

**Second, an assumption may matter differently across tasks and outcomes.** Hager et al. shows that moving from full-information to sequential evaluation has a relatively small aggregate effect on diagnosis accuracy while producing heterogeneous changes across treatment components. Consequently, evaluating a single aggregate outcome may conceal important differences in how particular clinical decisions respond to changes in the evaluation setting.

**Third, testing an assumption need not reveal a substantial mismatch.** Goh et al. provides an example where standalone model performance and physician-mediated model performance are not clearly distinguishable on the measured score. This illustrates that assumption-driven evaluation can also reduce the priority of specific concerns, rather than necessarily recommending increasingly realistic or expensive evaluations.

Together, these cases suggest a sequential process for using BenchmarkCards:

1. **Identify unresolved assumptions:** Document which aspects of the evaluation differ from or remain unverified in the intended deployment scenario.
2. **Select additional evidence:** Identify a feasible evaluation that directly probes an unresolved assumption.
3. **Update the assessment:** Determine whether the new evidence reveals a substantial discrepancy, a heterogeneous effect, or limited observed differences.
4. **Reconsider the next evaluation:** Prioritize remaining uncertainties based on the observed evidence and intended deployment requirements.

Importantly, this process does not imply that BenchmarkCards discover optimal evaluation policies or that every identified mismatch requires a new experiment. Instead, they provide an explicit framework for reasoning about which evaluation questions remain unanswered, what evidence could address them, and how priorities might change as evidence becomes available.

### Methodological Limitations

These analyses are retrospective demonstrations rather than prospective validations of evaluation selection. The recommended evaluations are reconstructed from the original benchmark designs and intended deployment scenarios, with knowledge of the broader literature and subsequent study results. We therefore cannot claim that the framework independently predicted the observed performance gaps or would have selected these particular experiments without hindsight.

Additionally, the reported comparisons are generally descriptive and do not identify causal mechanisms for the observed differences. In particular, Bean's information comparisons should not be interpreted as causal decompositions, Hager's sequential comparisons do not establish general superiority of either evaluation format, and Goh's small measured contrast does not establish equivalence between standalone and physician-mediated performance.

The contribution of these cases is therefore illustrative: they demonstrate how explicit assumptions can structure retrospective reasoning about evaluation choices, rather than establishing that BenchmarkCards uniquely identify or optimize the next evaluation.
