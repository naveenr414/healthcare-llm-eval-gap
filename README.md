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
python analysis/study_1.py
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

@article{bean2026reliability,
  title={Reliability of LLMs as medical assistants for the general public: a randomized preregistered study},
  author={Bean, Andrew M and Payne, Rebecca Elizabeth and Parsons, Guy and Kirk, Hannah Rose and Ciro, Juan and Mosquera-G{\'o}mez, Rafael and Hincapi{\'e} M, Sara and Ekanayaka, Aruna S and Tarassenko, Lionel and Rocher, Luc and others},
  journal={Nature Medicine},
  pages={1--7},
  year={2026},
  publisher={Nature Publishing Group US New York}
}
```
