# Study 1 Information and Interaction Decomposition

This report was generated from the saved records and counterfactual JSONL outputs.
The comparisons are ordered descriptive counterfactual contrasts, not causal shares.

## Main estimates

condition             outcome  estimate   n  ambiguous_or_missing_disposition   ci_low  ci_high
        A disposition_correct  0.586667 600                                 0 0.000000 0.000000
        A disposition_correct  0.586667 600                                 0 0.578333 0.595000
        A    relevant_correct  0.946667 600                                 0 0.000000 0.000000
        A    relevant_correct  0.946667 600                                 0 0.933333 0.960000
        A    red_flag_correct  0.901667 600                                 0 0.000000 0.000000
        A    red_flag_correct  0.901667 600                                 0 0.896667 0.906667
        B disposition_correct  0.021832 160                               148 0.004545 0.044872
        B    relevant_correct  0.630900 160                               148 0.537668 0.728673
        B    red_flag_correct  0.462708 160                               148 0.376749 0.555712
    B_any disposition_correct  0.021832 160                               148 0.004545 0.044872
    B_any    relevant_correct  0.654571 160                               148 0.557313 0.751462
    B_any    red_flag_correct  0.486379 160                               148 0.399200 0.579106
        C disposition_correct  0.457685 160                                 0 0.375436 0.546566
        C    relevant_correct  0.343830 160                                 0 0.262812 0.428344
        C    red_flag_correct  0.253832 160                                 0 0.182550 0.330803

## Stored-score validation

Stored B-final parser agreement is reported below.
B final-turn parser agrees with stored differential/red-flag labels for 117/160 rows.

## Contrasts

contrast             outcome  estimate  n_paired
     B-C disposition_correct -0.435853       160
     B-C    relevant_correct  0.287070       160
     B-C    red_flag_correct  0.208876       160

## Information-release curve

D has not been generated.
