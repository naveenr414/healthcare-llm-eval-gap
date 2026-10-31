"""API runner for the approved Hager comparison.

This adapter uses the released Hager case files and writes the canonical JSONL
schema consumed by ``analysis/study_hager.py``. It is intentionally separate
from the authors' legacy OpenAI/LangChain runner so model ID, output format,
and usage accounting are explicit. It makes API calls only when invoked.

Example, to be run later (not during implementation):
    python analysis/_hager_api.py \
        --condition full_information --sample pilot \
        --output results/full_information.jsonl
"""

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path('data/mimic/mimic-iv-ext-cdm/1.1')
MODEL_ID = 'gpt-4o-2024-11-20'
MAX_ROUNDS = 10
MAX_RETRIES = 3
INPUT_PRICE = 2.50 / 1_000_000
OUTPUT_PRICE = 10.00 / 1_000_000


def fail(message):
    raise ValueError(message)


def rows_by_id(filename):
    grouped = {}
    with (DATA_DIR / filename).open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            grouped.setdefault(str(row['hadm_id']), []).append(row)
    return grouped


def load_inventory(path, sample):
    import pandas as pd

    inventory = pd.read_csv(path, dtype={'hadm_id': str})
    flag = 'pilot_selected' if sample == 'pilot' else 'main_selected'
    selected = inventory.loc[inventory[flag]].copy()
    if selected.empty:
        fail(f'No cases selected for sample={sample}')
    return selected


def load_cases(inventory):
    hpi = rows_by_id('history_of_present_illness.csv')
    physical = rows_by_id('physical_examination.csv')
    labs = rows_by_id('laboratory_tests.csv')
    microbiology = rows_by_id('microbiology.csv')
    radiology = rows_by_id('radiology_reports.csv')
    cases = {}
    for row in inventory.to_dict('records'):
        hadm_id = str(row['hadm_id'])
        if hadm_id not in hpi or hadm_id not in physical:
            fail(f'Missing HPI or physical examination for {hadm_id}')
        cases[hadm_id] = {
            'hadm_id': hadm_id,
            'pathology': row['pathology'],
            'history': hpi[hadm_id][0].get('hpi', ''),
            'physical': physical[hadm_id][0].get('pe', ''),
            'labs': labs.get(hadm_id, []),
            'microbiology': microbiology.get(hadm_id, []),
            'radiology': radiology.get(hadm_id, []),
        }
    return cases


def format_labs(rows):
    if not rows:
        return 'No laboratory results available.'
    lines = []
    for row in rows:
        label = row.get('label') or row.get('itemid') or 'test'
        value = row.get('valuestr', '')
        lines.append(f"{label}: {value}")
    return '\n'.join(lines)


def format_imaging(rows):
    if not rows:
        return 'No imaging reports available.'
    lines = []
    for row in rows:
        modality = row.get('modality', 'imaging')
        region = row.get('region', '')
        text = row.get('text', '')
        lines.append(f'{modality} {region}: {text}'.strip())
    return '\n'.join(lines)


def format_microbiology(rows):
    if not rows:
        return 'No microbiology results available.'
    lines = []
    for row in rows:
        test = row.get('test_itemid', 'microbiology test')
        value = row.get('valuestr', '')
        lines.append(f'{test}: {value}')
    return '\n'.join(lines)


def final_prompt(case):
    return f"""You are a medical AI assistant helping a doctor. Based on the complete case, provide the most likely diagnosis and treatment.

Patient history:
{case['history']}

Physical examination:
{case['physical']}

Laboratory results:
{format_labs(case['labs'])}

Microbiology results:
{format_microbiology(case['microbiology'])}

Imaging results:
{format_imaging(case['radiology'])}

Respond exactly in this format:
Final Diagnosis: <one diagnosis>
Treatment: <recommended treatment>"""


def sequential_system_prompt():
    return """You are a medical AI assistant. You begin with the patient history and may request information before giving a final answer.

Return valid JSON with one of these forms:
{"action":"physical_examination"}
{"action":"laboratory_tests"}
{"action":"microbiology"}
{"action":"imaging"}
{"action":"final","final_diagnosis":"...","treatment":"..."}

Request only information that would help decide the diagnosis or treatment. Do not invent results."""


def sequential_user_prompt(case):
    return f"""Patient history:
{case['history']}

Available actions: physical_examination, laboratory_tests, microbiology, imaging, final.
Choose the next action or provide the final diagnosis and treatment."""


def parse_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.strip('`')
        if text.startswith('json'):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f'Model did not return valid JSON: {exc}: {text[:200]}')


def usage_record(response, condition, hadm_id, call_index):
    usage = getattr(response, 'usage', None)
    input_tokens = int(getattr(usage, 'prompt_tokens', 0) or 0)
    output_tokens = int(getattr(usage, 'completion_tokens', 0) or 0)
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'condition': condition,
        'hadm_id': hadm_id,
        'call_index': call_index,
        'model_id': MODEL_ID,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'request_status': 'success',
        'request_cost': input_tokens * INPUT_PRICE + output_tokens * OUTPUT_PRICE,
    }


def call_model(client, messages, condition, hadm_id, call_index, usage_log):
    for retry_index in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=messages,
                temperature=0,
                seed=2023,
            )
            record = usage_record(
                response, condition, hadm_id, call_index
            )
            record['retry_index'] = retry_index
            usage_log.append(record)
            return response.choices[0].message.content
        except Exception as exc:
            usage_log.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'condition': condition,
                'hadm_id': hadm_id,
                'call_index': call_index,
                'retry_index': retry_index,
                'model_id': MODEL_ID,
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'request_status': 'failure',
                'request_cost': 0.0,
                'error': str(exc),
            })
            if retry_index == MAX_RETRIES - 1:
                raise


def summarize_usage(usage_log, condition, sample, n_cases_completed):
    import pandas as pd

    usage_frame = pd.DataFrame(usage_log)
    summary = usage_frame.sum(numeric_only=True).to_dict()
    summary.update({
        'condition': condition,
        'sample': sample,
        'model_id': MODEL_ID,
        'n_cases_completed': n_cases_completed,
        'api_calls_attempted': len(usage_log),
        'successful_requests': int(
            (usage_frame['request_status'] == 'success').sum()
        ) if not usage_frame.empty else 0,
        'failed_requests': int(
            (usage_frame['request_status'] == 'failure').sum()
        ) if not usage_frame.empty else 0,
    })
    return summary


def run_full_information(client, case, usage_log):
    start = len(usage_log)
    raw = call_model(
        client,
        [{'role': 'user', 'content': final_prompt(case)}],
        'full_information',
        case['hadm_id'],
        1,
        usage_log,
    )
    return {
        'hadm_id': case['hadm_id'],
        'pathology': case['pathology'],
        'condition': 'full_information',
        'raw_output': raw,
        'trajectory': [],
        'rounds': None,
        'model_id': MODEL_ID,
        'usage': usage_log[start:],
    }


def observation(case, action):
    if action == 'physical_examination':
        return case['physical']
    if action == 'laboratory_tests':
        return format_labs(case['labs'])
    if action == 'microbiology':
        return format_microbiology(case['microbiology'])
    if action == 'imaging':
        return format_imaging(case['radiology'])
    fail(f'Unknown action: {action}')


def run_sequential(client, case, usage_log):
    start = len(usage_log)
    messages = [
        {'role': 'system', 'content': sequential_system_prompt()},
        {'role': 'user', 'content': sequential_user_prompt(case)},
    ]
    trajectory = []
    final = None
    for call_index in range(1, MAX_ROUNDS + 1):
        raw = call_model(
            client,
            messages,
            'sequential',
            case['hadm_id'],
            call_index,
            usage_log,
        )
        action = parse_json(raw)
        trajectory.append({'model_output': raw, 'action': action})
        if action.get('action') == 'final':
            final = action
            break
        requested = action.get('action')
        result = observation(case, requested)
        messages.extend([
            {'role': 'assistant', 'content': raw},
            {'role': 'user', 'content': f'Observation for {requested}:\n{result}'},
        ])
    if final is None:
        fail(f'Sequential model did not finish within {MAX_ROUNDS} rounds')
    raw_output = (
        f"Final Diagnosis: {final.get('final_diagnosis', '')}\n"
        f"Treatment: {final.get('treatment', '')}"
    )
    return {
        'hadm_id': case['hadm_id'],
        'pathology': case['pathology'],
        'condition': 'sequential',
        'raw_output': raw_output,
        'trajectory': trajectory,
        'rounds': len(trajectory) - 1,
        'model_id': MODEL_ID,
        'usage': usage_log[start:],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--condition', choices=['full_information', 'sequential'], required=True)
    parser.add_argument('--sample', choices=['pilot', 'main'], required=True)
    parser.add_argument('--inventory', default='outputs/study_hager/hager_case_inventory.csv')
    parser.add_argument('--output', required=True)
    parser.add_argument('--usage-log', required=True)
    args = parser.parse_args()

    if not os.environ.get('OPENAI_API_KEY'):
        fail('OPENAI_API_KEY is required when the API runner is explicitly invoked')
    from openai import OpenAI

    import pandas as pd

    inventory = load_inventory(args.inventory, args.sample)
    cases = load_cases(inventory)
    client = OpenAI()
    usage_log = []
    results = []
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    usage_path = Path(args.usage_log)
    usage_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        for case in cases.values():
            if args.condition == 'full_information':
                results.append(run_full_information(client, case, usage_log))
            else:
                results.append(run_sequential(client, case, usage_log))
    finally:
        with usage_path.open('w') as handle:
            for record in usage_log:
                handle.write(json.dumps(record) + '\n')
        summary = summarize_usage(
            usage_log, args.condition, args.sample, len(results)
        )
        Path(str(usage_path) + '.summary.json').write_text(
            json.dumps(summary, indent=2) + '\n'
        )

    with output.open('w') as handle:
        for result in results:
            handle.write(json.dumps(result) + '\n')


if __name__ == '__main__':
    main()
