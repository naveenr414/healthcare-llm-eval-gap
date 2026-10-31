"""Run the Bean information and interaction decomposition.

The script reuses the stored GPT-4o direct trials and human conversations. It
only makes new API calls with ``--run-api``: D is the raw cumulative-turn
curve, while E1 and E2 are the two stitched one-shot conditions. All prompts
and responses are saved as JSONL so the analysis can be resumed and audited.

Run from the repository root. The no-API path is safe to run before spending
money and validates the stored A/B/C inputs.
"""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import regex


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'bean'
REPORTS = ROOT / 'outputs' / 'study_bean' / 'information_decomposition'

MODEL_ID = 'gpt-4o-2024-05-13'
MODEL_ARM_ID = 2
# Standard GPT-4o rates in USD per one million tokens. Keep these alongside
# the run metadata so the spend estimate is reproducible from the JSONL logs.
INPUT_PRICE_PER_MILLION = 2.50
OUTPUT_PRICE_PER_MILLION = 10.00
TEMPERATURE = 0.8
MAX_TOKENS = 512
E2_EXTRACTOR_MAX_TOKENS = 2_048
N_BOOT = 5_000
SEED = 0

DESCRIPTION = (
    'Below is a fictional medical scenario. Based on the information provided, '
    'help to answer the questions at the end.'
)
QUESTION = """Please answer the two following questions: 1) What healthcare service does this person need? Choose from the following options in the UK National Health Service:
                    Ambulance: The patient is in immediate life-threatening danger; The patient needs
                    treatment administered en-route to the hospital.
                    A&E: The patient needs emergency hospital treatment.
                    Urgent Primary Care: The patient should be seen today, by a GP, urgent care
                    centre, or similar.
                    Routine GP: The patient should be seen at some point, but it can wait.
                    Self-care: The patient can handle this at home or with over-the-counter
                    medication.

                    2) Why did you make the choice you did? Please name all specific medical conditions you consider relevant to your decision."""

CATEGORIES = ('Ambulance', 'A&E', 'Urgent Primary Care', 'Routine GP', 'Self-care')


def request_cost(input_tokens, output_tokens):
    return (
        input_tokens * INPUT_PRICE_PER_MILLION
        + output_tokens * OUTPUT_PRICE_PER_MILLION
    ) / 1_000_000


def parse_literal(value):
    """Parse the Python-literal lists stored in the HELPMed CSV files."""
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        parsed = ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return []
    return list(parsed) if isinstance(parsed, (list, tuple)) else []


def parse_chat(raw):
    try:
        return ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        return {'user': [], 'bot': []}


def build_prompt(body):
    return f'{DESCRIPTION}\n\n{body}\n\n{QUESTION}'


def prompt_hash(prompt):
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()


def fuzzy_match(targets, text, threshold=80):
    """Return whether a stored differential term occurs in text."""
    text = str(text).lower()
    for target in targets:
        target = str(target).lower()
        tolerance = max(0, (100 - threshold) * len(target) // 100)
        pattern = rf'({re.escape(target)})' + rf'{{e<={tolerance}}}'
        if regex.search(pattern, text, flags=regex.IGNORECASE):
            return True
    return False


def first_answer(text):
    """Keep the service answer and avoid counting diagnoses in question 2."""
    text = str(text)
    match = re.search(r'\b2\s*[).:]', text)
    return text[:match.start()] if match else text[:800]


def parse_disposition(text):
    """Extract only a clear primary service recommendation.

    Ambiguous advice is intentionally returned as None and is counted as
    incorrect in the primary accuracy denominator.
    """
    answer = first_answer(text)
    patterns = [
        ('Ambulance', r'\bambulance\b|call\s+(?:an?\s+)?ambulance|emergency services'),
        ('A&E', r'\ba\s*&\s*e\b|accident\s+and\s+emergency|emergency room|emergency department'),
        ('Urgent Primary Care', r'urgent\s+(?:primary\s+care|care)|urgent\s+care\s+centre|same[- ]day\s+(?:gp|doctor)'),
        ('Routine GP', r'\broutine\s+gp\b|see\s+(?:your\s+)?(?:regular\s+)?gp|make\s+a\s+(?:routine\s+)?appointment'),
        ('Self-care', r'\bself[- ]care\b|manage\s+this\s+at\s+home|home\s+care'),
    ]
    matches = []
    for category, pattern in patterns:
        match = re.search(pattern, answer, flags=re.IGNORECASE)
        if match:
            matches.append((match.start(), category))
    if len(matches) != 1:
        return None
    return matches[0][1]


def gold_disposition(urgency_text):
    for category in CATEGORIES:
        if str(urgency_text).startswith(category):
            return category
    raise ValueError(f'Unknown gold disposition: {urgency_text}')


def outcome_record(condition, row, scenario, response, turn=None):
    full_diff = parse_literal(scenario['full_differential'])
    red_flags = parse_literal(scenario['red_flags'])
    disposition = parse_disposition(response)
    return {
        'condition': condition,
        'id': str(row['id']),
        'scenario_id': str(row['scenario_id']),
        'participant_id': str(row.get('participant_id', '')),
        'turn': turn,
        'response': response,
        'disposition': disposition,
        'gold_disposition': gold_disposition(scenario['urgency_text']),
        'disposition_correct': int(disposition is not None and disposition == gold_disposition(scenario['urgency_text'])),
        'relevant_correct': int(fuzzy_match(full_diff, response)),
        'red_flag_correct': int(fuzzy_match(red_flags, response)),
    }


def load_inputs():
    scenarios = pd.read_csv(DATA / 'scenarios.csv', dtype={'scenario_id': str}).set_index('scenario_id')
    examples = pd.read_csv(DATA / 'clean_examples.csv', dtype={'id': str, 'scenario_id': str, 'participant_id': str})
    examples = examples[examples['treatment_id'].astype(str) == str(MODEL_ARM_ID)].copy()
    prescored = pd.read_csv(DATA / 'clean_prescored.csv', dtype={'id': str})
    direct = pd.read_csv(DATA / 'direct_trials_condition.csv', dtype={'scenario_id': str})
    direct = direct[direct['model'].eq('GPT 4o')].copy()
    if len(examples) != 600:
        raise ValueError(f'Expected 600 GPT-4o conversations, found {len(examples)}')
    if examples['id'].duplicated().any():
        raise ValueError('GPT-4o conversation IDs are not unique')
    return scenarios, examples, prescored, direct


def stored_records(scenarios, examples, prescored, direct):
    """Build A, B-final, B-any-turn, and C without an API call."""
    records = []
    for direct_row_number, (_, row) in enumerate(direct.iterrows()):
        row = row.copy()
        row['id'] = f'A-direct-{direct_row_number}'
        scenario = scenarios.loc[str(row['scenario_id'])]
        records.append(outcome_record('A', row, scenario, row['model_text']))

    score_by_id = prescored.set_index('id')
    for _, row in examples.iterrows():
        chat = parse_chat(row['chat_history'])
        bots = sorted(chat.get('bot', []), key=lambda x: x.get('id', 0))
        if not bots:
            continue
        scenario = scenarios.loc[str(row['scenario_id'])]
        final = outcome_record('B', row, scenario, bots[-1].get('text', ''))
        final['parsed_final_relevant'] = final['relevant_correct']
        final['parsed_final_red_flag'] = final['red_flag_correct']
        final['stored_relevant'] = int(score_by_id.loc[str(row['id']), 'differential_correct_bot'])
        final['stored_red_flag'] = int(score_by_id.loc[str(row['id']), 'red_flag_correct_bot'])
        final['relevant_correct'] = final['stored_relevant']
        final['red_flag_correct'] = final['stored_red_flag']
        final['stored_score_matches_parser'] = int(
            final['parsed_final_relevant'] == final['stored_relevant']
            and final['parsed_final_red_flag'] == final['stored_red_flag']
        )
        final['score_source'] = 'clean_prescored.*_bot'
        records.append(final)

        any_record = final.copy()
        any_record['condition'] = 'B_any'
        any_record['relevant_correct'] = int(score_by_id.loc[str(row['id']), 'differential_correct_any'])
        any_record['red_flag_correct'] = int(score_by_id.loc[str(row['id']), 'red_flag_correct_any'])
        any_record['score_source'] = 'clean_prescored.*_any'
        records.append(any_record)

        human = outcome_record('C', row, scenario, row['likely_cause'])
        human['disposition'] = str(row['next_step']).split(' (', 1)[0]
        human['disposition_correct'] = int(human['disposition'] == human['gold_disposition'])
        human['relevant_correct'] = int(score_by_id.loc[str(row['id']), 'differential_correct'])
        human['red_flag_correct'] = int(score_by_id.loc[str(row['id']), 'red_flag_correct'])
        records.append(human)
    return pd.DataFrame(records)


def user_turns(chat):
    return sorted(chat.get('user', []), key=lambda x: x.get('id', 0))


def raw_body(turns):
    return '\n\n'.join(f'PATIENT TURN {i}: {turn.get("text", "")}' for i, turn in enumerate(turns, 1))


E2_EXTRACTION_INSTRUCTIONS = """Rewrite the patient messages into a structured canonical case representation.

Use only information explicitly present in the patient messages. Do not infer,
diagnose, correct, complete, or add any fact. Preserve every proposition,
including uncertainty, negation, and patient-supplied diagnostic beliefs. A
belief must be labeled as patient-reported rather than stated as an objective
fact. Return JSON with exactly this shape:

{"propositions": [{"source_turn": 1, "source_text": "exact quote from one patient turn", "canonical_text": "faithful neutral rewrite", "kind": "clinical_fact|patient_belief|context|other", "section": "Specific Case Details|General Life Details|Additional Medical History|Patient-Reported Information"}]}

Create at least one proposition for every sentence or clause containing
information. `source_text` must be copied exactly from the input. The
canonical case will be rendered from your JSON after validation, so do not
include explanations outside the JSON object."""


def patient_sentences(turns):
    return [(i, sentence.strip()) for i, turn in enumerate(turns, 1) for sentence in re.split(r'(?<=[.!?])\s+', str(turn.get('text', '')).strip()) if sentence.strip()]


def extraction_prompt(turns):
    return f"{E2_EXTRACTION_INSTRUCTIONS}\n\nPATIENT MESSAGES:\n{raw_body(turns)}"


def parse_json_response(text):
    text = str(text).strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.IGNORECASE | re.DOTALL)
    return json.loads(text)


def validate_extraction(extraction, turns):
    """Require exact source coverage and add conservative fallback propositions."""
    source_sentences = patient_sentences(turns)
    propositions = extraction.get('propositions', []) if isinstance(extraction, dict) else []
    validated = []
    covered = set()
    for proposition in propositions:
        source_text = str(proposition.get('source_text', '')).strip()
        canonical_text = str(proposition.get('canonical_text', '')).strip()
        turn = int(proposition.get('source_turn', 0))
        if not source_text or not canonical_text or turn < 1:
            continue
        if turn > len(turns) or source_text not in str(turns[turn - 1].get('text', '')):
            continue
        validated.append({
            'source_turn': turn,
            'source_text': source_text,
            'canonical_text': canonical_text,
            'kind': str(proposition.get('kind', 'other')),
            'section': str(proposition.get('section', 'Patient-Reported Information')),
        })
        for index, (_, sentence) in enumerate(source_sentences):
            if source_text in sentence or sentence in source_text:
                covered.add(index)
    for index, (turn, sentence) in enumerate(source_sentences):
        if index not in covered:
            validated.append({
                'source_turn': turn,
                'source_text': sentence,
                'canonical_text': sentence,
                'kind': 'other',
                'section': 'Patient-Reported Information',
            })
    return {'propositions': validated}


def render_extraction(extraction):
    sections = {}
    for proposition in extraction['propositions']:
        section = proposition['section']
        label = 'Patient-reported'
        if proposition['kind'] == 'patient_belief':
            label = 'Patient-reported belief'
        sections.setdefault(section, []).append(
            f"{label}, turn {proposition['source_turn']}: {proposition['canonical_text']}"
        )
    body = ['Patient-reported case information:']
    for section, propositions in sections.items():
        body.append(f'\n{section}:')
        body.extend(f'- {proposition}' for proposition in propositions)
    return '\n'.join(body)


def call_api(prompt, max_retries=3, temperature=TEMPERATURE, max_tokens=MAX_TOKENS, json_mode=False):
    from openai import OpenAI

    client = OpenAI()
    for attempt in range(max_retries):
        try:
            request = {
                'model': MODEL_ID,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': temperature,
                'max_tokens': max_tokens,
            }
            if json_mode:
                request['response_format'] = {'type': 'json_object'}
            response = client.chat.completions.create(
                **request,
            )
            usage = getattr(response, 'usage', None)
            return {
                'response': response.choices[0].message.content or '',
                'input_tokens': int(getattr(usage, 'prompt_tokens', 0) or 0),
                'output_tokens': int(getattr(usage, 'completion_tokens', 0) or 0),
                'retries': attempt,
            }
        except Exception:
            if attempt + 1 == max_retries:
                raise
            time.sleep(2 ** attempt)


def prepare_e2_extractions(examples, extraction_path, metadata_path, workers=8):
    """Generate and validate the one-time GPT-assisted E2 transformations."""
    completed = {}
    if extraction_path.exists():
        for line in extraction_path.read_text().splitlines():
            if line.strip():
                item = json.loads(line)
                completed[str(item['id'])] = item
    extraction_path.parent.mkdir(parents=True, exist_ok=True)
    pending = []
    for _, row in examples.iterrows():
        interaction_id = str(row['id'])
        if interaction_id in completed:
            continue
        turns = user_turns(parse_chat(row['chat_history']))
        prompt = extraction_prompt(turns)
        pending.append((row, turns, prompt))
    with extraction_path.open('a') as out, metadata_path.open('a') as metadata, ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(call_api, prompt, temperature=0.0, max_tokens=E2_EXTRACTOR_MAX_TOKENS, json_mode=True): (row, turns, prompt)
            for row, turns, prompt in pending
        }
        for completed_number, future in enumerate(as_completed(futures), 1):
            row, turns, prompt = futures[future]
            interaction_id = str(row['id'])
            api = future.result()
            try:
                extraction = validate_extraction(parse_json_response(api['response']), turns)
                status = 'validated'
            except (json.JSONDecodeError, TypeError, ValueError, KeyError):
                extraction = validate_extraction({}, turns)
                status = 'fallback_after_invalid_json'
            item = {
                'id': interaction_id,
                'scenario_id': str(row['scenario_id']),
                'model': MODEL_ID,
                'prompt_hash': prompt_hash(prompt),
                'input_tokens': api['input_tokens'],
                'output_tokens': api['output_tokens'],
                'estimated_cost_usd': request_cost(api['input_tokens'], api['output_tokens']),
                'retries': api['retries'],
                'status': status,
                **extraction,
            }
            out.write(json.dumps(item) + '\n')
            out.flush()
            metadata.write(json.dumps({
                'condition': 'E2_preprocessing',
                'id': interaction_id,
                'scenario_id': str(row['scenario_id']),
                'prompt_hash': item['prompt_hash'],
                'model': MODEL_ID,
                'input_tokens': api['input_tokens'],
                'output_tokens': api['output_tokens'],
                'estimated_cost_usd': request_cost(api['input_tokens'], api['output_tokens']),
                'retries': api['retries'],
                'status': status,
            }) + '\n')
            metadata.flush()
            if completed_number % 25 == 0 or completed_number == len(pending):
                print(f'E2 preprocessing: {completed_number}/{len(pending)} new calls complete', flush=True)


def load_e2_extractions(extraction_path):
    if not extraction_path.exists():
        raise FileNotFoundError(
            f'{extraction_path} is missing; run with --prepare-e2 before --run-api'
        )
    return {str(item['id']): item for item in (json.loads(line) for line in extraction_path.read_text().splitlines() if line.strip())}


def run_api_conditions(scenarios, examples, output_path, metadata_path, e2_extractions, workers=8):
    """Generate E1/E2 first, then D, skipping completed JSONL keys.

    E1 and E2 are the shorter fixed-length prompts. Running them as a separate
    phase makes those results available before the longer cumulative-turn D
    curve, while retaining resumability within each phase.
    """
    completed = set()
    if output_path.exists():
        for line in output_path.read_text().splitlines():
            if line.strip():
                item = json.loads(line)
                completed.add((item['condition'], item['id'], item.get('turn')))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pending_by_condition = {'E1': [], 'E2': [], 'D': []}
    for _, row in examples.iterrows():
        chat = parse_chat(row['chat_history'])
        turns = user_turns(chat)
        scenario = scenarios.loc[str(row['scenario_id'])]
        e2_body = render_extraction(e2_extractions[str(row['id'])])
        for condition, body in (('E1', raw_body(turns)), ('E2', e2_body)):
            key = (condition, str(row['id']), None)
            if key not in completed:
                pending_by_condition[condition].append((condition, row, scenario, None, body))
        for turn_number in range(1, len(turns) + 1):
            key = ('D', str(row['id']), turn_number)
            if key not in completed:
                body = raw_body(turns[:turn_number])
                pending_by_condition['D'].append(('D', row, scenario, turn_number, body))

    for condition in ('E1', 'E2', 'D'):
        pending = pending_by_condition[condition]
        if not pending:
            continue
        print(f'Starting {condition}: {len(pending)} new calls', flush=True)
        with output_path.open('a') as out, metadata_path.open('a') as metadata, ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(call_api, build_prompt(body)): (condition, row, scenario, turn, body)
                for condition, row, scenario, turn, body in pending
            }
            for completed_number, future in enumerate(as_completed(futures), 1):
                condition, row, scenario, turn, body = futures[future]
                api = future.result()
                prompt = build_prompt(body)
                record = outcome_record(condition, row, scenario, api['response'], turn)
                record.update({'body': body, 'prompt_hash': prompt_hash(prompt), 'model': MODEL_ID, **{k: api[k] for k in ('input_tokens', 'output_tokens', 'retries')}})
                out.write(json.dumps(record) + '\n')
                out.flush()
                metadata.write(json.dumps({'condition': condition, 'id': str(row['id']), 'turn': turn, 'scenario_id': str(row['scenario_id']), 'prompt_hash': prompt_hash(prompt), 'model': MODEL_ID, 'input_tokens': api['input_tokens'], 'output_tokens': api['output_tokens'], 'estimated_cost_usd': request_cost(api['input_tokens'], api['output_tokens']), 'retries': api['retries']}) + '\n')
                metadata.flush()
                if completed_number % 50 == 0 or completed_number == len(pending):
                    print(f'Counterfactual evaluation {condition}: {completed_number}/{len(pending)} new calls complete', flush=True)


def scenario_mean(df, outcome):
    return df.groupby('scenario_id', sort=True)[outcome].mean().mean()


def point_table(records):
    rows = []
    outcomes = ('disposition_correct', 'relevant_correct', 'red_flag_correct')
    for condition, group in records.groupby('condition'):
        for outcome in outcomes:
            rows.append({
                'condition': condition,
                'outcome': outcome,
                'estimate': scenario_mean(group, outcome),
                'n': len(group),
                'ambiguous_or_missing_disposition': int(group['disposition'].isna().sum()),
            })
    return pd.DataFrame(rows)


def paired_difference(left, right, outcome, keys=('id', 'scenario_id')):
    """Scenario-balanced paired difference, using the common interaction IDs."""
    cols = list(keys) + [outcome]
    joined = left[cols].merge(right[cols], on=list(keys), suffixes=('_left', '_right'))
    joined['difference'] = joined[f'{outcome}_left'] - joined[f'{outcome}_right']
    return scenario_mean(joined.rename(columns={'difference': outcome}), outcome), len(joined)


def contrast_table(records):
    """Compute the planned ordered contrasts from scored records."""
    outcomes = ('disposition_correct', 'relevant_correct', 'red_flag_correct')
    pairs = [('E1', 'E2'), ('B', 'E1'), ('B', 'C')]
    rows = []
    for left_name, right_name in pairs:
        if not {left_name, right_name}.issubset(set(records['condition'])):
            continue
        left = records[records['condition'].eq(left_name)]
        right = records[records['condition'].eq(right_name)]
        for outcome in outcomes:
            estimate, n = paired_difference(left, right, outcome)
            rows.append({'contrast': f'{left_name}-{right_name}', 'outcome': outcome, 'estimate': estimate, 'n_paired': n})

    if {'A', 'E2'}.issubset(set(records['condition'])):
        a = records[records['condition'].eq('A')]
        e2 = records[records['condition'].eq('E2')]
        for outcome in outcomes:
            rows.append({
                'contrast': 'A-E2',
                'outcome': outcome,
                'estimate': scenario_mean(a, outcome) - scenario_mean(e2, outcome),
                'n_paired': 0,
            })
    return pd.DataFrame(rows)


def release_curve(records):
    """Return available-panel levels and fixed-panel adjacent-turn changes."""
    d = records[records['condition'].eq('D')].copy()
    if d.empty:
        return pd.DataFrame()
    rows = []
    outcomes = ('disposition_correct', 'relevant_correct', 'red_flag_correct')
    turns = sorted(d['turn'].dropna().astype(int).unique())
    for turn in turns:
        available = d[d['turn'].eq(turn)]
        for outcome in outcomes:
            rows.append({'curve': 'available_panel', 'turn': turn, 'comparison': 'level', 'outcome': outcome, 'estimate': scenario_mean(available, outcome), 'n_ids': available['id'].nunique()})
        later = d[d['turn'].eq(turn + 1)]
        if later.empty:
            continue
        common = available[['id', 'scenario_id']].merge(later[['id', 'scenario_id']], on=['id', 'scenario_id'])
        for outcome in outcomes:
            left = available.merge(common, on=['id', 'scenario_id'])
            right = later.merge(common, on=['id', 'scenario_id'])
            estimate, n = paired_difference(left, right, outcome)
            rows.append({'curve': 'fixed_panel', 'turn': turn, 'comparison': f'{turn}_to_{turn + 1}', 'outcome': outcome, 'estimate': estimate, 'n_ids': n})
    return pd.DataFrame(rows)


def bootstrap(records, direct, n_boot=N_BOOT):
    """Scenario-balanced clustered bootstrap for stored and generated rows."""
    rng = np.random.default_rng(SEED)
    scenarios = np.sort(records['scenario_id'].dropna().unique())
    patient = records[records['condition'].isin(['B', 'B_any', 'C', 'D', 'E1', 'E2'])].copy()
    patient_ids = patient['participant_id'].drop_duplicates().to_numpy()
    outcomes = ('disposition_correct', 'relevant_correct', 'red_flag_correct')
    patient_conditions = [
        condition for condition in records['condition'].unique()
        if condition != 'A'
    ]
    values = {(c, o): np.zeros(n_boot) for c in patient_conditions for o in outcomes}
    direct_values = {o: np.zeros(n_boot) for o in outcomes}

    for b in range(n_boot):
        sampled_ids = rng.choice(patient_ids, size=len(patient_ids), replace=True)
        sampled = pd.concat([patient[patient['participant_id'].eq(pid)] for pid in sampled_ids], ignore_index=True)
        for condition in sampled['condition'].unique():
            group = sampled[sampled['condition'].eq(condition)]
            for outcome in outcomes:
                values[(condition, outcome)][b] = scenario_mean(group, outcome)
        for outcome in outcomes:
            draws = []
            for scenario in scenarios:
                vals = direct.loc[direct['scenario_id'].eq(scenario), outcome].to_numpy(dtype=float)
                if len(vals):
                    draws.append(vals[rng.integers(0, len(vals), len(vals))].mean())
            direct_values[outcome][b] = np.mean(draws)

    rows = []
    for (condition, outcome), draws in values.items():
        rows.append({'condition': condition, 'outcome': outcome, 'estimate': float(np.mean(draws)), 'ci_low': np.percentile(draws, 2.5), 'ci_high': np.percentile(draws, 97.5)})
    for outcome, draws in direct_values.items():
        rows.append({'condition': 'A', 'outcome': outcome, 'estimate': float(np.mean(draws)), 'ci_low': np.percentile(draws, 2.5), 'ci_high': np.percentile(draws, 97.5)})
    return pd.DataFrame(rows)


def bootstrap_contrasts(records, direct, n_boot=N_BOOT):
    """Bootstrap the planned contrasts while preserving patient clusters."""
    rng = np.random.default_rng(SEED + 1)
    patient = records[records['condition'].isin(['B', 'B_any', 'C', 'D', 'E1', 'E2'])].copy()
    participant_ids = patient['participant_id'].drop_duplicates().to_numpy()
    outcomes = ('disposition_correct', 'relevant_correct', 'red_flag_correct')
    names = ('E1-E2', 'B-E1', 'B-C', 'A-E2')
    draws = {(name, outcome): np.zeros(n_boot) for name in names for outcome in outcomes}
    for b in range(n_boot):
        sampled_ids = rng.choice(participant_ids, size=len(participant_ids), replace=True)
        sampled = pd.concat([patient[patient['participant_id'].eq(pid)] for pid in sampled_ids], ignore_index=True)
        means = {}
        for condition in sampled['condition'].unique():
            group = sampled[sampled['condition'].eq(condition)]
            means[condition] = {outcome: scenario_mean(group, outcome) for outcome in outcomes}
        a = {}
        for outcome in outcomes:
            scenario_means = []
            for scenario in records['scenario_id'].dropna().unique():
                vals = direct.loc[direct['scenario_id'].eq(scenario), outcome].to_numpy(dtype=float)
                if len(vals):
                    scenario_means.append(vals[rng.integers(0, len(vals), len(vals))].mean())
            a[outcome] = np.mean(scenario_means)
        for outcome in outcomes:
            if {'E1', 'E2'} <= means.keys():
                draws[('E1-E2', outcome)][b] = means['E1'][outcome] - means['E2'][outcome]
            if {'B', 'E1'} <= means.keys():
                draws[('B-E1', outcome)][b] = means['B'][outcome] - means['E1'][outcome]
            if {'B', 'C'} <= means.keys():
                draws[('B-C', outcome)][b] = means['B'][outcome] - means['C'][outcome]
            if 'E2' in means:
                draws[('A-E2', outcome)][b] = a[outcome] - means['E2'][outcome]
    point = contrast_table(records).set_index(['contrast', 'outcome'])
    rows = []
    for key, values in draws.items():
        estimate = point.loc[key, 'estimate'] if key in point.index else np.nan
        rows.append({'contrast': key[0], 'outcome': key[1], 'estimate': estimate, 'ci_low': np.percentile(values, 2.5), 'ci_high': np.percentile(values, 97.5)})
    return pd.DataFrame(rows)


def bootstrap_release_curve(records, n_boot=N_BOOT):
    """Bootstrap D levels and fixed-panel adjacent-turn changes."""
    rng = np.random.default_rng(SEED + 2)
    d = records[records['condition'].eq('D')].copy()
    if d.empty:
        return pd.DataFrame()
    participants = d['participant_id'].drop_duplicates().to_numpy()
    turns = sorted(d['turn'].dropna().astype(int).unique())
    outcomes = ('disposition_correct', 'relevant_correct', 'red_flag_correct')
    draws = {}
    for turn in turns:
        for outcome in outcomes:
            draws[('available_panel', turn, 'level', outcome)] = np.zeros(n_boot)
            if turn + 1 in turns:
                draws[('fixed_panel', turn, f'{turn}_to_{turn + 1}', outcome)] = np.zeros(n_boot)
    for b in range(n_boot):
        sampled_ids = rng.choice(participants, size=len(participants), replace=True)
        sampled_parts = []
        for sample_instance, pid in enumerate(sampled_ids):
            part = d[d['participant_id'].eq(pid)].copy()
            part['_sample_instance'] = sample_instance
            sampled_parts.append(part)
        sampled = pd.concat(sampled_parts, ignore_index=True)
        for turn in turns:
            available = sampled[sampled['turn'].eq(turn)]
            for outcome in outcomes:
                draws[('available_panel', turn, 'level', outcome)][b] = scenario_mean(available, outcome)
            later = sampled[sampled['turn'].eq(turn + 1)]
            if later.empty:
                continue
            common = available[['_sample_instance', 'id', 'scenario_id']].merge(
                later[['_sample_instance', 'id', 'scenario_id']],
                on=['_sample_instance', 'id', 'scenario_id'],
            )
            for outcome in outcomes:
                left = available.merge(common, on=['_sample_instance', 'id', 'scenario_id'])
                right = later.merge(common, on=['_sample_instance', 'id', 'scenario_id'])
                value, _ = paired_difference(left, right, outcome, keys=('_sample_instance', 'id', 'scenario_id'))
                draws[('fixed_panel', turn, f'{turn}_to_{turn + 1}', outcome)][b] = value
    rows = []
    for key, values in draws.items():
        rows.append({'curve': key[0], 'turn': key[1], 'comparison': key[2], 'outcome': key[3], 'ci_low': np.percentile(values, 2.5), 'ci_high': np.percentile(values, 97.5)})
    return pd.DataFrame(rows)


def write_report(main, contrasts, release, records):
    """Write a compact factual report from the same tables used downstream."""
    lines = [
        '# Bean Information and Interaction Decomposition',
        '',
        'This report was generated from the saved records and counterfactual JSONL outputs.',
        'The comparisons are ordered descriptive counterfactual contrasts, not causal shares.',
        "A's disposition row is the newly parsed raw-response outcome; Bean et al.'s original GPT-4o direct disposition benchmark is 64.7% and is reported separately below.",
        'E1 is a one-shot GPT-4o response to the concatenated patient messages in their original wording. E2 is a one-shot GPT-4o response to the same disclosed patient information after a GPT-assisted, source-validated rewrite into vignette-style propositions; E2 is not the hidden complete case.',
        '',
        '## Main estimates',
        '',
        main.to_string(index=False),
        '',
        '## Stored-score validation',
        '',
        'Stored B-final parser agreement is reported below.',
        '',
        '## Contrasts',
        '',
        contrasts.to_string(index=False) if not contrasts.empty else 'No newly generated contrast conditions are present.',
        '',
        '## Information-release curve',
        '',
        release.to_string(index=False) if not release.empty else 'D has not been generated.',
        '',
    ]
    main_lookup = {
        (str(row.condition), str(row.outcome)): float(row.estimate)
        for row in main.itertuples()
    }
    if all((condition, 'relevant_correct') in main_lookup for condition in ('A', 'B', 'E2')):
        benchmark = main_lookup[('A', 'relevant_correct')]
        observed = main_lookup[('B', 'relevant_correct')]
        canonical = main_lookup[('E2', 'relevant_correct')]
        total_gap = benchmark - observed
        canonical_drop = benchmark - canonical
        share = canonical_drop / total_gap if total_gap else float('nan')
        lines.extend([
            '## Canonicalized patient-information comparison',
            '',
            f'For relevant-condition accuracy, the direct benchmark is **{benchmark:.1%}**, the stored final model-turn outcome is **{observed:.1%}**, and the canonicalized disclosed-information condition E2 is **{canonical:.1%}**.',
            f'The benchmark-to-E2 decline is {canonical_drop:.1%} ({canonical_drop * 100:.1f} percentage points), which is **{share:.0%}** of the benchmark-to-final-turn gap. The remaining **{1 - share:.0%}** is associated with the observed conversational setting and response path. This is an ordered descriptive comparison, not a causal attribution.',
            '',
        ])
    prompt_check = REPORTS / 'disposition_prompt_check_summary.json'
    if prompt_check.exists():
        check = json.loads(prompt_check.read_text())
        ci = check['bootstrap']
        lines.extend([
            '## Disposition-only prompt sensitivity check',
            '',
            'This is a secondary prompt-format check. It reruns E1 on the same 600 raw patient-information inputs with a disposition-only question; it does not replace the primary combined-prompt E1 condition.',
            '',
            'Bean et al. original GPT-4o direct disposition benchmark: **64.7%**.',
            f"New disposition-only E1: **{check['new_scenario_balanced_accuracy']:.1%}** (95% CI {ci['new_ci_low']:.1%}–{ci['new_ci_high']:.1%}).",
            f"Existing combined-prompt E1: **{check['existing_e1_scenario_balanced_accuracy']:.1%}** (95% CI {ci['existing_ci_low']:.1%}–{ci['existing_ci_high']:.1%}).",
            f"Disposition-only minus combined-prompt E1: **{check['new_minus_existing_scenario_balanced']:+.1%}** (95% CI {ci['difference_ci_low']:+.1%}–{ci['difference_ci_high']:+.1%}).",
            f"The two E1 outcomes agree for {check['agreement']}/{check['n']} interactions; the new condition has {check['ambiguous_new']}/{check['n']} ambiguous or missing dispositions.",
            f"The check used {check['n']} calls and cost ${check['api_cost_usd']:.2f}. The original 64.7% result and the new 36.3% result should not be treated as identical estimands: the former is Bean et al.'s original direct benchmark, while the latter is a raw-disclosed-information prompt sensitivity condition.",
            '',
        ])
    b = records[records['condition'].eq('B')]
    if 'stored_score_matches_parser' in b:
        lines.insert(
            lines.index('Stored B-final parser agreement is reported below.') + 1,
            f"B final-turn parser agrees with stored differential/red-flag labels for {int(b['stored_score_matches_parser'].sum())}/{len(b)} rows.",
        )
    (REPORTS / 'information_decomposition_report.md').write_text('\n'.join(lines))


def main(run_api=False, prepare_e2=False, limit=None, workers=8):
    scenarios, examples, prescored, direct = load_inputs()
    if limit is not None:
        examples = examples.head(limit).copy()
    REPORTS.mkdir(parents=True, exist_ok=True)
    records = stored_records(scenarios, examples, prescored, direct)
    metadata_path = REPORTS / 'counterfactual_prompt_metadata.jsonl'
    if prepare_e2:
        prepare_e2_extractions(
            examples,
            REPORTS / 'e2_extractions.jsonl',
            metadata_path,
            workers=workers,
        )
    if run_api:
        e2_extractions = load_e2_extractions(REPORTS / 'e2_extractions.jsonl')
        run_api_conditions(
            scenarios,
            examples,
            REPORTS / 'counterfactual_results.jsonl',
            metadata_path,
            e2_extractions,
            workers=workers,
        )
        generated = pd.read_json(REPORTS / 'counterfactual_results.jsonl', lines=True)
        for column in ('id', 'scenario_id', 'participant_id'):
            generated[column] = generated[column].astype(str)
        records = pd.concat([records, generated], ignore_index=True)
    if metadata_path.exists():
        metadata = pd.DataFrame(
            json.loads(line)
            for line in metadata_path.read_text().splitlines()
            if line.strip()
        )
        if not metadata.empty:
            metadata['estimated_cost_usd'] = metadata.apply(
                lambda row: request_cost(row['input_tokens'], row['output_tokens']),
                axis=1,
            )
            cost_summary = {
                'model': MODEL_ID,
                'input_price_per_million_usd': INPUT_PRICE_PER_MILLION,
                'output_price_per_million_usd': OUTPUT_PRICE_PER_MILLION,
                'completed_calls': int(len(metadata)),
                'input_tokens': int(metadata['input_tokens'].sum()),
                'output_tokens': int(metadata['output_tokens'].sum()),
                'estimated_cost_usd': float(metadata['estimated_cost_usd'].sum()),
                'by_condition': {
                    str(condition): {
                        'completed_calls': int(group.shape[0]),
                        'input_tokens': int(group['input_tokens'].sum()),
                        'output_tokens': int(group['output_tokens'].sum()),
                        'estimated_cost_usd': float(group['estimated_cost_usd'].sum()),
                    }
                    for condition, group in metadata.groupby('condition')
                },
            }
            (REPORTS / 'api_cost_summary.json').write_text(
                json.dumps(cost_summary, indent=2) + '\n'
            )
    records.to_csv(REPORTS / 'information_decomposition_records.csv', index=False)
    direct_records = records[records['condition'].eq('A')].copy()
    bootstrap_summary = bootstrap(records, direct_records)
    bootstrap_summary.to_csv(REPORTS / 'information_decomposition_bootstrap.csv', index=False)
    main = point_table(records).merge(
        bootstrap_summary[['condition', 'outcome', 'ci_low', 'ci_high']],
        on=['condition', 'outcome'],
        how='left',
    )
    main.to_csv(REPORTS / 'information_decomposition_main.csv', index=False)
    contrasts = contrast_table(records)
    if {'E1', 'E2'}.issubset(set(records['condition'])):
        contrast_bootstrap = bootstrap_contrasts(records, direct_records)
        contrast_bootstrap.to_csv(REPORTS / 'information_decomposition_contrasts_bootstrap.csv', index=False)
        contrasts = contrasts.merge(
            contrast_bootstrap[['contrast', 'outcome', 'ci_low', 'ci_high']],
            on=['contrast', 'outcome'],
            how='left',
        )
    contrasts.to_csv(REPORTS / 'information_decomposition_contrasts.csv', index=False)
    release = release_curve(records)
    if not release.empty:
        release_bootstrap = bootstrap_release_curve(records)
        release = release.merge(
            release_bootstrap,
            on=['curve', 'turn', 'comparison', 'outcome'],
            how='left',
        )
    release.to_csv(REPORTS / 'information_release_curve.csv', index=False)
    write_report(main, contrasts, release, records)
    print(f'Wrote {len(records)} scored records to {REPORTS}')
    if not run_api and not prepare_e2:
        print('No API calls made. Re-run with --prepare-e2, then --run-api.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-api', action='store_true', help='Generate D, E1, and E2 with GPT-4o.')
    parser.add_argument('--prepare-e2', action='store_true', help='Generate and validate the one-time GPT-assisted E2 rewrite.')
    parser.add_argument('--limit', type=int, help='Limit conversations for a dry run.')
    parser.add_argument('--workers', type=int, default=8, help='Maximum concurrent API requests (default: 8).')
    args = parser.parse_args()
    main(run_api=args.run_api, prepare_e2=args.prepare_e2, limit=args.limit, workers=args.workers)
