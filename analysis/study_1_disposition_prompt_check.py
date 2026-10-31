"""Check the disposition-only prompt against the existing combined E1 prompt.

The current Study 1 E1 calls ask for both disposition and conditions. Bean et al.
report the direct disposition benchmark from a disposition-only prompt. This
script reruns the 600 GPT-4o raw-information cases with only the disposition
question, preserving the same user messages and model settings, then compares
the paired outcomes without changing the primary decomposition.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path

import numpy as np
import pandas as pd

from study_1_information_decomposition import (
    INPUT_PRICE_PER_MILLION,
    MODEL_ID,
    OUTPUT_PRICE_PER_MILLION,
    call_api,
    gold_disposition,
    load_inputs,
    parse_disposition,
    prompt_hash,
    raw_body,
    request_cost,
    user_turns,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'experiments' / 'reports' / 'study1_information_decomposition'
RESULTS = REPORTS / 'disposition_prompt_check_results.jsonl'
METADATA = REPORTS / 'disposition_prompt_check_metadata.jsonl'
SUMMARY = REPORTS / 'disposition_prompt_check_summary.json'
N_BOOT = 5_000
SEED = 0

DESCRIPTION = (
    'Below is a fictional medical scenario. Based on the information provided, '
    'help to answer the question at the end.'
)
DISPOSITION_QUESTION = """Please answer the following question: What healthcare service does this person need? Choose from the following options in the UK National Health Service:
                    Ambulance: The patient is in immediate life-threatening danger; The patient needs
                    treatment administered en-route to the hospital.
                    A&E: The patient needs emergency hospital treatment.
                    Urgent Primary Care: The patient should be seen today, by a GP, urgent care
                    centre, or similar.
                    Routine GP: The patient should be seen at some point, but it can wait.
                    Self-care: The patient can handle this at home or with over-the-counter
                    medication."""


def build_disposition_prompt(body):
    return f'{DESCRIPTION}\n\n{body}\n\n{DISPOSITION_QUESTION}'


def run_calls(examples, scenarios, workers):
    existing = {}
    if RESULTS.exists():
        existing = {
            row['id']: row
            for row in (
                json.loads(line)
                for line in RESULTS.read_text().splitlines()
                if line.strip()
            )
        }

    pending = []
    for _, row in examples.iterrows():
        chat = ast_literal_chat(row['chat_history'])
        turns = user_turns(chat)
        body = raw_body(turns)
        prompt = build_disposition_prompt(body)
        key = str(row['id'])
        if key not in existing:
            pending.append((row, scenarios.loc[str(row['scenario_id'])], body, prompt))

    REPORTS.mkdir(parents=True, exist_ok=True)
    with RESULTS.open('a') as results, METADATA.open('a') as metadata:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(call_api, prompt, max_tokens=128): (row, scenario, body, prompt)
                for row, scenario, body, prompt in pending
            }
            for number, future in enumerate(as_completed(futures), 1):
                row, scenario, body, prompt = futures[future]
                api = future.result()
                response = api['response']
                disposition = parse_disposition(response)
                gold = gold_disposition(scenario['urgency_text'])
                record = {
                    'id': str(row['id']),
                    'scenario_id': str(row['scenario_id']),
                    'participant_id': str(row['participant_id']),
                    'body': body,
                    'prompt': prompt,
                    'prompt_hash': prompt_hash(prompt),
                    'response': response,
                    'disposition': disposition,
                    'gold_disposition': gold,
                    'disposition_correct': int(disposition is not None and disposition == gold),
                    'input_tokens': api['input_tokens'],
                    'output_tokens': api['output_tokens'],
                    'retries': api['retries'],
                    'model': MODEL_ID,
                }
                results.write(json.dumps(record) + '\n')
                results.flush()
                metadata.write(json.dumps({
                    'condition': 'E1_disposition_only',
                    'id': record['id'],
                    'scenario_id': record['scenario_id'],
                    'prompt_hash': record['prompt_hash'],
                    'model': MODEL_ID,
                    'input_tokens': api['input_tokens'],
                    'output_tokens': api['output_tokens'],
                    'estimated_cost_usd': request_cost(api['input_tokens'], api['output_tokens']),
                    'retries': api['retries'],
                }) + '\n')
                metadata.flush()
                if number % 50 == 0 or number == len(pending):
                    print(f'Disposition-only E1: {number}/{len(pending)} new calls complete', flush=True)


def ast_literal_chat(raw):
    import ast

    try:
        return ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        return {'user': [], 'bot': []}


def scenario_mean(d, outcome):
    return d.groupby('scenario_id', sort=True)[outcome].mean().mean()


def bootstrap(d, n_boot=N_BOOT):
    rng = np.random.default_rng(SEED)
    clusters = d['participant_id'].drop_duplicates().to_numpy()
    draws = np.zeros((n_boot, 3))
    for b in range(n_boot):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        sample = pd.concat([d[d['participant_id'].eq(cluster)] for cluster in sampled], ignore_index=True)
        draws[b, 0] = scenario_mean(sample, 'new_disposition_correct')
        draws[b, 1] = scenario_mean(sample, 'existing_e1_disposition_correct')
        draws[b, 2] = draws[b, 0] - draws[b, 1]
    return draws


def summarize(examples):
    current = pd.read_json(REPORTS / 'counterfactual_results.jsonl', lines=True)
    current = current[current['condition'].eq('E1')][['id', 'disposition_correct']].copy()
    current['id'] = current['id'].astype(str)
    new = pd.DataFrame(
        json.loads(line)
        for line in RESULTS.read_text().splitlines()
        if line.strip()
    )
    new['id'] = new['id'].astype(str)
    d = examples[['id', 'participant_id', 'scenario_id']].copy()
    d['id'] = d['id'].astype(str)
    d['participant_id'] = d['participant_id'].astype(str)
    d['scenario_id'] = d['scenario_id'].astype(str)
    d = d.merge(new[['id', 'disposition_correct']], on='id', validate='one_to_one')
    d = d.rename(columns={'disposition_correct': 'new_disposition_correct'})
    d = d.merge(current.rename(columns={'disposition_correct': 'existing_e1_disposition_correct'}), on='id', validate='one_to_one')

    draws = bootstrap(d)
    summary = {
        'model': MODEL_ID,
        'n': int(len(d)),
        'new_raw_row_accuracy': float(d['new_disposition_correct'].mean()),
        'existing_e1_raw_row_accuracy': float(d['existing_e1_disposition_correct'].mean()),
        'new_scenario_balanced_accuracy': float(scenario_mean(d, 'new_disposition_correct')),
        'existing_e1_scenario_balanced_accuracy': float(scenario_mean(d, 'existing_e1_disposition_correct')),
        'new_minus_existing_scenario_balanced': float(scenario_mean(d, 'new_disposition_correct') - scenario_mean(d, 'existing_e1_disposition_correct')),
        'bootstrap': {
            'new_ci_low': float(np.quantile(draws[:, 0], 0.025)),
            'new_ci_high': float(np.quantile(draws[:, 0], 0.975)),
            'existing_ci_low': float(np.quantile(draws[:, 1], 0.025)),
            'existing_ci_high': float(np.quantile(draws[:, 1], 0.975)),
            'difference_ci_low': float(np.quantile(draws[:, 2], 0.025)),
            'difference_ci_high': float(np.quantile(draws[:, 2], 0.975)),
        },
        'agreement': int((d['new_disposition_correct'] == d['existing_e1_disposition_correct']).sum()),
        'ambiguous_new': int(new['disposition'].isna().sum()),
        'api_cost_usd': float(sum(
            request_cost(row['input_tokens'], row['output_tokens'])
            for row in (
                json.loads(line)
                for line in METADATA.read_text().splitlines()
                if line.strip()
            )
        )),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + '\n')
    report = [
        '# Disposition-only prompt check',
        '',
        'This check reruns E1 on the same 600 GPT-4o conversations, using raw cumulative patient messages but a disposition-only prompt. It does not replace the primary decomposition.',
        '',
        f"- New disposition-only E1, scenario-balanced: **{summary['new_scenario_balanced_accuracy']:.1%}** (95% CI {summary['bootstrap']['new_ci_low']:.1%}–{summary['bootstrap']['new_ci_high']:.1%})",
        f"- Existing combined-prompt E1, scenario-balanced: **{summary['existing_e1_scenario_balanced_accuracy']:.1%}** (95% CI {summary['bootstrap']['existing_ci_low']:.1%}–{summary['bootstrap']['existing_ci_high']:.1%})",
        f"- New minus existing E1: **{summary['new_minus_existing_scenario_balanced']:+.1%}** (95% CI {summary['bootstrap']['difference_ci_low']:+.1%}–{summary['bootstrap']['difference_ci_high']:+.1%})",
        f"- Exact outcome agreement: **{summary['agreement']}/{summary['n']}**",
        f"- New ambiguous/missing dispositions: **{summary['ambiguous_new']}/{summary['n']}**",
        f"- API cost recorded by this check: **${summary['api_cost_usd']:.2f}**",
        '',
        'The Bean et al. GPT-4o direct disposition benchmark is 64.7%. That original benchmark is not replaced by this check; the check identifies how much the combined versus disposition-only prompt changes the raw-information counterfactual.',
    ]
    (REPORTS / 'disposition_prompt_check_report.md').write_text('\n'.join(report) + '\n')
    print('\n'.join(report))


def main(workers=32):
    scenarios, examples, _, _ = load_inputs()
    run_calls(examples, scenarios, workers)
    summarize(examples)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=32)
    args = parser.parse_args()
    main(workers=args.workers)
