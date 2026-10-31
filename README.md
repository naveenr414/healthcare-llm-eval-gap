# Healthcare LLM Benchmarks Are Necessary but Not Sufficient
                                                                  
Code for the case study in [Healthcare LLM Benchmarks Are Necessary but Not 
Sufficient](https://arxiv.org/abs/2605.22612).

We decompose the gap between benchmark performance and deployment performance using the [RCT Dataset](https://www.nature.com/articles/s41591-025-04074-y) (Bean et al. 2026), where patients interacted with GTP-4o. 

## Gap decomposition

| Condition | Description |
|---|---|
| #1 Expert query, single-turn | Benchmark ceiling: full scenario given directly to the model |
| #2 Patient first turn, single-turn | Model sees only the patient's opening message |
| #3 GPT-4o in real multi-turn | Model accuracy during actual patient conversations |
| #4 Human final answer | What the patient concluded after the conversation |

The gap from #1 to #4 decomposes into a task component (#1 to #3) and an outcome component (#3 to #4).

## Setup

```bash
pip install openai pandas regex
export OPENAI_API_KEY=...
python analysis/run_experiments.py --study bean
```

## Analysis organization

The reproducible entry points are organized around four studies:

- `analysis/study_bean.py` is the public Bean entry point; its private helpers contain the information decomposition, report, and model-comparison calculations.
- `analysis/study_hager.py` is the public Hager entry point; its private helpers contain scoring and API execution.
- `analysis/study_goh.py` contains the Goh decomposition.
- `analysis/data.py` contains shared paths and loaders for Bean, Hager/MIMIC, Goh, and the benchmark tables.
- `analysis/plotting.py` writes only `bean_mechanism_contrasts.pdf`, `benchmark_cards_assumption_scores_bars.pdf`, and `benchmark_cards_format_evidence.pdf`.
- `analysis/run_experiments.py` is the top-level runner. Hager inventory creation is local; Hager model results must be supplied explicitly as JSONL.

The raw data are organized into `data/bean/`, `data/goh/`, `data/mimic/`, and `data/benchmarks/`. The benchmark tables are `data/benchmarks/benchmark_assumptions.csv` and `data/benchmarks/future_evals.csv`. Scores in the assumptions table use `1 = yes`, `0.5 = partial`, and `0 = no`; the assumption figure plots missingness as `1 - mean(score)`.

The canonical Markdown plans are `experiments/plans/study_bean.md`, `study_hager.md`, and `study_goh.md`; the corresponding reports are `experiments/reports/study_bean.md`, `study_hager.md`, and `study_goh.md`. Generated tables, metadata, and run records are stored under `outputs/`, while the separate BenchmarkCards narrative remains at `experiments/reports/benchmarks/benchmark_cards_analysis.md`.

The Hager evaluator support code is vendored at `data/mimic/hager_framework/`. It is executable support code rather than raw MIMIC data, but keeping it beside the MIMIC inputs makes the repository self-contained. The former `external/` directory is no longer required.

Examples:

```bash
python analysis/run_experiments.py --study bean
python analysis/run_experiments.py --study hager
python analysis/run_experiments.py --study all --plots
```

Citation

If you use this code, please cite both our paper and the original dataset:

```bibtex
@article{raman2026healthcare,
  title={Healthcare LLM Benchmarks Are Only as Good as Their Explicit Assumptions},
  author={Raman, Naveen and Cortes-Gomez, Santiago and Rubio, Mateo Dulce and Fang, Fei and Wilder, Bryan},
  journal={arXiv preprint arXiv:2605.22612},
  year={2026}
}
```
