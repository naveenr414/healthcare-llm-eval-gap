# Healthcare LLM Benchmarks Are Necessary but Not Sufficient
                                                                  
Code for the case study in [Healthcare LLM Benchmarks Are Necessary but Not 
Sufficient](https://arxiv.org/abs/XXXX.XXXXX).

We decompose the gap between benchmark performance and deployment performance using the [RCT Dataset](https://www.nature.com/articles/s41591-025-04074-y) (Bean et al. 2026), where patients interacted with GTP-4o. 

## Gap decomposition

| Condition | Description |
|---|---|
| #1 Expert query, single-turn | Benchmark ceiling: full scenario given directly to the model |
| #2 Patient first turn, single-turn | Model sees only the patient's opening message |
| #3 GPT-4o in real multi-turn | Model accuracy during actual patient conversations |
| #4 Human final answer | What the patient concluded after the conversation |

The gap from #1 to #4 decomposes into a conversational component (#1 to #3) and a consequential
component (#3 to #4).

## Setup

```bash
pip install openai pandas regex
export OPENAI_API_KEY=...
python analysis/study_1.py
```

Citation

If you use this code, please cite both our paper and the original dataset:

```
@inproceedings{raman2025position,
title     = {Position: Healthcare {LLM} Benchmarks Are Necessary but Not Sufficient},
author    = {...},
booktitle = {ArXiv},
year      = {2025}
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
