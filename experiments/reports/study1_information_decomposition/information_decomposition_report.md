# Study 1 Information and Interaction Decomposition

This report was generated from the saved records and counterfactual JSONL outputs.
The comparisons are ordered descriptive counterfactual contrasts, not causal shares.
A's disposition row is the newly parsed raw-response outcome; Bean et al.'s original GPT-4o direct disposition benchmark is 64.7% and is reported separately below.
E1 is a one-shot GPT-4o response to the concatenated patient messages in their original wording. E2 is a one-shot GPT-4o response to the same disclosed patient information after a GPT-assisted, source-validated rewrite into vignette-style propositions; E2 is not the hidden complete case.

## Main estimates

condition             outcome  estimate   n  ambiguous_or_missing_disposition   ci_low  ci_high
        A disposition_correct  0.586667 600                                 0 0.576667 0.595000
        A    relevant_correct  0.946667 600                                 0 0.933333 0.960000
        A    red_flag_correct  0.901667 600                                 0 0.896667 0.906667
        B disposition_correct  0.063684 600                               508 0.046013 0.082755
        B    relevant_correct  0.648712 600                               508 0.606741 0.689150
        B    red_flag_correct  0.550652 600                               508 0.510066 0.592670
    B_any disposition_correct  0.063684 600                               508 0.046013 0.082755
    B_any    relevant_correct  0.668202 600                               508 0.626403 0.708011
    B_any    red_flag_correct  0.563797 600                               508 0.523022 0.604561
        C disposition_correct  0.438158 600                                 0 0.398287 0.479150
        C    relevant_correct  0.356731 600                                 0 0.312906 0.400715
        C    red_flag_correct  0.293679 600                                 0 0.252677 0.334627

## Stored-score validation

Stored B-final parser agreement is reported below.
B final-turn parser agrees with stored differential/red-flag labels for 426/600 rows.

## Contrasts

contrast             outcome  estimate  n_paired
     B-C disposition_correct -0.374474       600
     B-C    relevant_correct  0.291980       600
     B-C    red_flag_correct  0.256973       600

## Information-release curve

D has not been generated.

## Disposition-only prompt sensitivity check

This is a secondary prompt-format check. It reruns E1 on the same 600 raw patient-information inputs with a disposition-only question; it does not replace the primary combined-prompt E1 condition.

Bean et al. original GPT-4o direct disposition benchmark: **64.7%**.
New disposition-only E1: **36.3%** (95% CI 32.5%–40.1%).
Existing combined-prompt E1: **43.8%** (95% CI 39.9%–47.7%).
Disposition-only minus combined-prompt E1: **-7.5%** (95% CI -10.8%–-4.3%).
The two E1 outcomes agree for 498/600 interactions; the new condition has 149/600 ambiguous or missing dispositions.
The check used 600 calls and cost $1.02. The original 64.7% result and the new 36.3% result should not be treated as identical estimands: the former is Bean et al.'s original direct benchmark, while the latter is a raw-disclosed-information prompt sensitivity condition.
