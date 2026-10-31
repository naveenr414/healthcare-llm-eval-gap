# BenchmarkCards: Assumption Mismatches and Missing Evidence

**Status:** Descriptive analysis following the review of assumption-to-evidence coding and benchmark archetypes (October 16, 2026).  
**Corpus:** 18 healthcare benchmarks; five assumption assessments per benchmark (90 assessments).  
**Purpose:** Identify which evaluation-to-deployment assumptions fail or only partially hold, what evidence is missing, and how evidence requirements vary by benchmark design.

## 1. Analytical approach

Each BenchmarkCard is assessed relative to its **specified deployment scenario**, along five dimensions:

1. **Example sourcing (task):** Are the evaluation examples representative of the intended setting?
2. **Information sufficiency (task):** Does the benchmark reflect the information available at deployment?
3. **Interaction structure (task):** Does it reflect how the model interacts with users or the environment?
4. **Actor/decision-maker (outcome):** Does it reflect who acts on the model's output and how?
5. **Outcome measure (outcome):** Is the scored outcome aligned with the deployment-relevant outcome?

Each assessment is **Yes**, **Partial**, **No**, or **Unknown**. The existing free-text fields describing *additional data necessary* were coded into a nonexclusive taxonomy of evidence needs. Each benchmark was also classified by its primary evaluation format. All counts below are descriptive of these 18 annotated benchmarks, **not** estimates for the population of medical AI evaluations.

### Final evidence taxonomy

| Code | Missing evidence category | Operational meaning |
|---|---|---|
| **E1** | Representative inputs | More realistic queries, workflows, or error distributions rather than selected, synthetic, or otherwise unrepresentative examples. Former E6 (workflow/error realism) is included here. |
| **E2** | Incomplete information and context | Incomplete/ambiguous histories, missing tests, or additional context that needs to be elicited or retrieved. |
| **E3** | Realistic sequential interactions | Multi-turn interaction, sequential choices, real rather than simulated user responses, and comparable interaction evidence. |
| **E4** | Human behavior | How clinicians or patients understand, interpret, accept, reject, follow, or use model outputs. |
| **E5** | Downstream outcomes | Patient health, clinical safety, deployment utility, and whether the evaluated task reflects the intended deployment task. |

**Coding rules:** Codes are multi-label and may co-occur. **E5** combines downstream consequences with target-task alignment. A missing outcome can be important even if the original card does not explicitly recommend collecting E5 evidence; therefore, coded frequency is not the prevalence of all plausible gaps.

### Coding decisions confirmed in review

- DentalQA outcome: **E4, E5**.
- MedDG actor: **E4, E5**; MedDG outcome: **E5**.
- MVME example sourcing: **Unknown** (do not reclassify as a demonstrated mismatch); information: **E1, E2**; outcome: **E5**.
- EBMQA outcome: **E4, E5**.
- MEDEC outcome: **E4, E5**.

## 2. How often are assumptions unmet?

| Assumption | Yes | Partial | No | Unknown | Partial + No |
|---|---:|---:|---:|---:|---:|
| Example sourcing | 5 | 11 | 1 | 1 | **12/18** |
| Information sufficiency | 6 | 5 | 7 | 0 | **12/18** |
| Interaction structure | 5 | 4 | 9 | 0 | **13/18** |
| Actor / decision-maker | 3 | 4 | 11 | 0 | **15/18** |
| Outcome measure | 1 | 14 | 3 | 0 | **17/18** |

**Interpretation:** Unresolved outcome alignment is widespread: 17 of 18 assessments of outcome measurement are Partial or No, and 15 of 18 actor/decision-maker assessments are Partial or No. This should **not** be reduced to “17 benchmarks measure the wrong outcome”: most of those 17 are **Partial**, not **No**. Task assumptions vary more by evaluation format. One sourcing assessment (MVME) remains **Unknown** because construction details were insufficient.

## 3. Which assumptions call for which additional evidence?

Cells count **assumption assessments** assigned each code (not distinct benchmarks). An assessment may contribute to multiple columns.

| Assumption | Representative inputs | Incomplete information | Sequential interactions | Human behavior | Downstream outcomes |
|---|---:|---:|---:|---:|---:|
| Example sourcing | 12 | 0 | 0 | 0 | 0 |
| Information sufficiency | 3 | 12 | 0 | 0 | 0 |
| Interaction structure | 2 | 0 | 13 | 0 | 0 |
| Actor / decision-maker | 0 | 0 | 0 | 15 | 1 |
| Outcome measure | 0 | 0 | 1 | 13 | 7 |
| **Total** | **17** | **12** | **14** | **28** | **8** |

**Reading the table:** The leading *explicitly coded* evidence requirement is **E4 (human behavior)**, with 28 assessment-level assignments. Sourcing gaps tend to imply E1; incomplete-information gaps imply E2; interaction gaps imply E3. Outcome assumptions often call for E4 and can also require E5. The E5 total is low because coding tracked evidence **explicitly identified in the current cards**, not every eventual outcome that might matter.

## 4. Benchmark archetypes

These are **descriptive format groupings**, not statistically learned clusters. AfriMed-QA is assigned a distinct mixed-source category following author review.

| Primary evaluation archetype | n | Benchmarks |
|---|---:|---|
| **Static QA / knowledge questions** | 7 | TCMBench, CMExam, DentalQA (DentalBench), MedXpertQA, MedExQA, EBMQA, MedQA |
| **Curated clinical cases** | 3 | DiagnosisArena, MENTAT, JAMA Clinical Challenge |
| **Authentic user questions / conversations** | 2 | MedicationQA, MedDG |
| **Simulated interactive care** | 3 | InfoGatherQA (MedQA-CS), MVME, HealthBench |
| **Clinical workflow tasks** | 2 | MedAgentBench, MEDEC |
| **Mixed-source QA** | 1 | AfriMed-QA |

These are primary labels: a benchmark may have additional characteristics. In particular, group size is small and unbalanced.

## 5. Benchmark format × missing evidence

Each cell counts **distinct benchmarks** in that group that require the indicated evidence type (at least one coded assumption). Unlike the previous table, a benchmark is counted **only once per evidence type**.

| Format | n | Representative inputs | Incomplete information | Sequential interactions | Human behavior | Downstream outcomes |
|---|---:|---:|---:|---:|---:|---:|
| Static QA / knowledge questions | 7 | 7 | 7 | 7 | 7 | 3 |
| Curated clinical cases | 3 | 2 | 2 | 3 | 3 | 0 |
| Authentic user questions / conversations | 2 | 0 | 0 | 1 | 2 | 1 |
| Simulated interactive care | 3 | 3 | 1 | 2 | 1 | 2 |
| Clinical workflow tasks | 2 | 1 | 1 | 0 | 1 | 1 |
| Mixed-source QA | 1 | 0 | 1 | 1 | 1 | 0 |

**Denominators matter:** For instance, 7/7 static QA benchmarks are coded E1–E4, compared with 2/2 authentic-input benchmarks coded E4. Given 1–3 benchmarks in most other groups, avoid comparing raw counts without referencing n.

## 6. Main findings and implications for FAccT

### Finding 1 — Static QA has a recurring set of evidence requirements

All **seven** static QA/knowledge benchmarks were coded as needing more representative inputs (E1), incomplete-information evidence (E2), realistic interactions (E3), and human-decision evidence (E4). This suggests a recurring **evaluation pathway**: from exam or knowledge questions toward realistic clinical inputs, sequential information gathering, and testing how clinicians use model outputs. This does **not** establish that all static QA benchmarks are unsuitable or that these steps alone guarantee clinical validity.

### Finding 2 — More realistic inputs do not remove outcome-related uncertainty

The two benchmarks built from authentic user questions/conversations, **MedicationQA** and **MedDG**, have no coded E1 or E2 requirements, yet **both require E4**. MedDG also requires E5: extracting entities from conversations is not itself a direct test of a patient-facing assistant's guidance quality. Thus **task realism and downstream-outcome evidence are separable**. A benchmark may capture real language or dialogue without determining what users do as a result or whether the intended assistant task is performed.

### Finding 3 — Simulated interaction changes the evidence question, rather than ending it

The three simulated interactive care benchmarks (**InfoGatherQA, MVME, HealthBench**) all have E1 requirements, two have E3 requirements, and two have E5 requirements. They address some limits of one-shot QA but leave open questions about the transfer from synthetic or simulated users and encounters to real deployment. The appropriate next evaluation can involve real patient queries, real continuation turns, or downstream outcome evidence.

### Finding 4 — Workflow benchmarks require more task-specific validation

**MedAgentBench** and **MEDEC** emphasize clinical workflow tasks rather than exam-style answers. In this pair, the coded gaps concern realistic task/error distributions, necessary chart context, clinician review, and whether a scored proxy matches the intended clinical task. For instance, **MEDEC** asks about naturally occurring note errors and clinician acceptance of corrections. These are not addressed merely by converting an exam question into a multi-turn conversation.

### Synthesis

The stronger conclusion is **not** that one benchmark format is intrinsically superior. Rather, different evaluation designs leave **different types of evidence missing**. Making assumptions explicit can guide the **next evaluation or data collection effort**. Closing a task gap does not, by itself, establish human-decision validity or downstream benefit.

## 7. Suggested manuscript-ready results text

> Across 18 healthcare benchmarks, we conducted a descriptive analysis of five evaluation-to-deployment assumptions per benchmark and coded the additional evidence identified in each BenchmarkCard. We observed recurring associations between benchmark format and evidence requirements. All seven static question-answering and knowledge benchmarks were coded as requiring evidence on representative inputs, incomplete information, sequential interaction, and human decision-making. In contrast, benchmarks sourced from authentic patient questions or conversations addressed some task-representativeness concerns but still left the effects of model outputs on human decisions unresolved. Simulated interactive benchmarks captured aspects of dialogue and sequential care while leaving questions about the representativeness of simulated users and the transferability of measured outcomes to real-world settings. Clinical workflow benchmarks raised more specialized questions about actual error distributions, task context, and clinician review. Together, these patterns illustrate how explicit evaluation assumptions can identify what evidence should be gathered next, rather than treating a single benchmark score as sufficient evidence of deployment relevance.

## 8. Methods and limitations to report

- **Method:** Structured qualitative content analysis: five *deductively specified* assumption dimensions; an evidence taxonomy developed from the free-text cards; descriptive multi-label coding and frequency cross-tabs; and manually reviewed benchmark-format groupings.
- **Unit of analysis:** The assessment-by-assumption table has **90 rows**, but rows from the same benchmark are not independent. The format cross-tab has **18 benchmark units**.
- **Review status:** Archetypes and flagged coding decisions were reviewed; this is **not** a claim of independently double-coded annotations or measured inter-annotator reliability. If desired, a second coder can independently label a subset before camera-ready reporting.
- **Interpretive scope:** The deployment scenarios are author-specified; changing a deployment scenario can change the match judgments. The 18 benchmark sample includes purposively selected cases; results should not be generalized as prevalence estimates for all healthcare benchmarks.
- **Coding scope:** Missing evidence was coded from what the cards **requested explicitly**; absence of an E5 code should not be interpreted as proof that patient outcomes are sufficiently evaluated.
- **Unknown is distinct from No:** MVME example sourcing was retained as **Unknown**, reflecting a need for documentation rather than a demonstrated failure.
- **Evidence needs are hypotheses about the next study:** Cross-tabs characterize proposed follow-up evidence, not experimental proof that collecting it closes the deployment gap. The separate case studies can provide empirical illustrations of consequential gaps.

## 9. Recommended displays

1. **Table:** Five assumption dimensions × Yes / Partial / No / Unknown (Section 2).
2. **Main figure:** Assumption dimension × missing evidence type heatmap (Section 3).
3. **Main or appendix table:** Benchmark archetype × missing evidence type, **showing denominator n** (Section 5).
4. **Appendix:** Complete benchmark classifications, evidence-code decisions, and representative annotations.

## 10. Accompanying data files

- `benchmark_assumptions_coded_90_rows_final.csv` — annotation-level coded data.
- `assumption_prevalence_final.csv` — match judgment frequencies.
- `assumption_by_evidence_final.csv` — assessment-level missing-evidence cross-tab.
- `benchmark_by_evidence_final.csv` — one row per benchmark, binary evidence labels.
- `benchmark_format_final.csv` — reviewed benchmark archetypes and evidence labels.
- `benchmark_format_evidence_crosstab_final.csv` — archetype-level frequencies and within-group proportions.
- `reviewed_evidence_taxonomy.csv` — revised five-category codebook (E5 combines downstream outcomes and target-task alignment).

**Bottom line:** The descriptive analysis for the TODO **“Analyze assumptions versus missing evidence”** is complete. The manuscript work remaining is choosing the main displays, integrating the claims with the BenchmarkCard validation and case studies, and (if sought) performing independent annotation reliability checks.

## Results: Mismatch Frequency by Benchmark Format

Each cell gives the count of benchmarks rated **No or Partial**, divided by the number of benchmarks in the archetype (percentage in parentheses).

| Benchmark archetype | n | Example sourcing | Information sufficiency | Interaction structure | Actor / decision-maker | Outcome measure |
|---|---|---|---|---|---|---|
| Static QA / knowledge questions | 7 | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) |
| Curated clinical cases | 3 | 2/3 (67%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| Authentic user questions/conversations | 2 | 0/2 (0%) | 0/2 (0%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) |
| Simulated interactive care | 3 | 2/3 (67%) | 1/3 (33%) | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) |
| Clinical workflow tasks | 2 | 1/2 (50%) | 1/2 (50%) | 0/2 (0%) | 1/2 (50%) | 1/2 (50%) |
| Mixed-source QA | 1 | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |

**Qualification.** The sourcing assumption for MVME (in *Simulated interactive care*) is **Unknown**. Thus the reported 2/3 sourcing mismatch does not mean that the third benchmark was judged to match deployment; it was not assessed as Yes or No. The underlying four-level cross-tabulation should be retained in the appendix.

## Main Descriptive Findings

### 1. Static QA and Curated Cases Exhibit Recurring Task and Outcome Gaps

All seven static QA / knowledge-question benchmarks have at least a partial mismatch in each of the five assumption dimensions. For the three curated clinical-case benchmarks, all have at least partial mismatches in interaction structure, decision-maker, and outcome measure, although sourcing and information availability are more mixed. These patterns are consistent with the concern that single-turn question answering does not necessarily reproduce sequential clinical practice or how humans use model recommendations.

The distinction between **Partial** and **No** matters: for static QA, outcome measurement is **Partial** in five benchmarks and **No** in two. We therefore describe a pervasive *unresolved match* rather than claiming that all outcome measures are completely inappropriate.

### 2. Authentic User Questions and Conversations Narrow Some Task Gaps but Leave Outcome Gaps

For both benchmarks in the authentic-question/conversation archetype, example sourcing and information sufficiency are assessed as **Yes**. However, the decision-maker and outcome-measure assumptions are **Partial** or **No** in both. Having realistic inputs therefore does not, by itself, establish whether the output influences patients' or clinicians' actions or produces desirable downstream results.

### 3. Simulated Interactive Evaluations Capture More of the Interaction Structure but Still Leave Outcome-Measure Uncertainty

Two of three simulated interactive-care benchmarks are assessed as **Yes** on interaction structure, while **all three** have at least a partial mismatch in outcome measurement. Such simulations can test sequential behaviors that static QA omits, but their observed results do not automatically establish validity for actual patients, clinicians, or clinical outcomes. Example sourcing in this archetype also includes one **Unknown**, underscoring the need to separate insufficient documentation from a verified mismatch.

### 4. Clinical Workflow Tasks Have More Heterogeneous, Task-Specific Gaps

Neither of the two clinical-workflow benchmarks has an interaction-structure mismatch, but other assumptions vary. The relevant follow-up evaluation may involve real-world error distributions, missing patient context, clinician review, or whether a model performs the actual intended workflow. With only two benchmarks, this finding should be presented as illustrative rather than as a stable category-level pattern.

## Interpretation for the BenchmarkCards Argument

The comparison reinforces a distinction between **task validity** and **outcome validity**. Benchmarks designed around real queries or interactive simulations can address important task mismatches without resolving questions about what humans do with outputs or whether the measured endpoint captures deployment success. Conversely, workflow-specific benchmarks can have relatively faithful interaction structures while still requiring different types of external validation.

Together with the assumption-by-missing-evidence analysis, this shows how explicit assumptions can guide **which additional evidence to collect next**, rather than simply judging some benchmark formats as universally better than others.
