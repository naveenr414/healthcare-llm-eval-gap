# Goh Study Report

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
