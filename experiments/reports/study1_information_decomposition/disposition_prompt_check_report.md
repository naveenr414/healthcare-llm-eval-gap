# Disposition-only prompt check

This check reruns E1 on the same 600 GPT-4o conversations, using raw cumulative patient messages but a disposition-only prompt. It does not replace the primary decomposition.

- New disposition-only E1, scenario-balanced: **36.3%** (95% CI 32.5%–40.1%)
- Existing combined-prompt E1, scenario-balanced: **43.8%** (95% CI 39.9%–47.7%)
- New minus existing E1: **-7.5%** (95% CI -10.8%–-4.3%)
- Exact outcome agreement: **498/600**
- New ambiguous/missing dispositions: **149/600**
- API cost recorded by this check: **$1.02**

The Bean et al. GPT-4o direct disposition benchmark is 64.7%. That original benchmark is not replaced by this check; the check identifies how much the combined versus disposition-only prompt changes the raw-information counterfactual.
