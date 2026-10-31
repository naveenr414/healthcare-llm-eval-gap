"""Compare Bean model rankings across the stored A/B/C outcomes.

This is a no-API analysis.  A uses the stored direct trials, B uses the stored
final model-turn scores, and C uses the stored participant outcomes.  The
primary comparison is the change in each pairwise model difference from A to B.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from _bean_information import fuzzy_match, parse_chat, parse_literal


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'bean'
REPORTS = ROOT / 'outputs' / 'study_bean' / 'model_rank_reversals'

ARM_TO_MODEL = {
    1: 'Llama 3 70B',
    2: 'GPT-4o',
    4: 'Command R+',
}
MODELS = tuple(ARM_TO_MODEL.values())
OUTCOMES = ('relevant_correct', 'red_flag_correct')
N_BOOT = 5_000
SEED = 0


def scenario_mean(frame, outcome):
    """Give each of the ten scenarios equal weight."""
    return frame.groupby('scenario_id')[outcome].mean().mean()


def binary(value):
    """Convert the mixed boolean encodings in the CSV files to 0/1."""
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {'true', '1'}:
            return 1
        if value in {'false', '0'}:
            return 0
    if pd.isna(value):
        raise ValueError('Missing binary outcome')
    return int(bool(value))


def holm_adjust(p_values):
    """Return Holm-adjusted p-values in the input order."""
    p_values = np.asarray(p_values, dtype=float)
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def classify_reversal(point_a, point_b, ci_a, ci_b):
    """Classify a pair using point estimates and intervals for A and B."""
    point_reversal = point_a * point_b < 0
    if not point_reversal:
        if point_a == 0 or point_b == 0:
            return 'indeterminate'
        same_side = (
            ci_a[0] > 0 and ci_b[0] > 0
            or ci_a[1] < 0 and ci_b[1] < 0
        )
        return 'stable_ranking' if same_side else 'indeterminate'
    interval_reversal = (
        (ci_a[1] < 0 and ci_b[0] > 0)
        or (ci_a[0] > 0 and ci_b[1] < 0)
    )
    return 'confirmed_reversal' if interval_reversal else 'point_estimate_reversal'


def load_inputs():
    scenarios = pd.read_csv(DATA / 'scenarios.csv', dtype={'scenario_id': str})
    scenarios = scenarios.set_index('scenario_id')
    examples = pd.read_csv(
        DATA / 'clean_examples.csv',
        dtype={'id': str, 'scenario_id': str, 'participant_id': str},
    )
    prescored = pd.read_csv(DATA / 'clean_prescored.csv', dtype={'id': str})
    direct = pd.read_csv(
        DATA / 'direct_trials_condition.csv',
        dtype={'scenario_id': str},
    )
    return scenarios, examples, prescored, direct


def validate_inputs(examples, prescored, direct):
    """Check the treatment mapping and complete A/B/C cells."""
    counts = examples['treatment_id'].value_counts().to_dict()
    for arm in ARM_TO_MODEL:
        if counts.get(arm, 0) != 600:
            raise ValueError(f'Expected 600 rows for treatment {arm}, found {counts.get(arm, 0)}')
    if not examples['id'].is_unique:
        raise ValueError('clean_examples.csv IDs are not unique')
    if not prescored['id'].is_unique:
        raise ValueError('clean_prescored.csv IDs are not unique')
    if not set(examples['id']).issubset(set(prescored['id'])):
        raise ValueError('Some example IDs are absent from clean_prescored.csv')
    for model in MODELS:
        n_direct = int((direct['model'] == model.replace('-', ' ')).sum())
        if model == 'GPT-4o':
            n_direct = int((direct['model'] == 'GPT 4o').sum())
        if n_direct != 600:
            raise ValueError(f'Expected 600 direct rows for {model}, found {n_direct}')


def build_records(scenarios, examples, prescored, direct):
    """Build stored A, B-final, B-any, and C records for all model arms."""
    scores = prescored.set_index('id')
    records = []

    direct_names = {'GPT 4o': 'GPT-4o', 'Llama 3 70B': 'Llama 3 70B', 'Command R+': 'Command R+'}
    for _, row in direct.iterrows():
        model = direct_names[row['model']]
        records.append({
            'model': model,
            'stage': 'A',
            'id': f"A-{model}-{row.name}",
            'scenario_id': str(row['scenario_id']),
            'participant_id': '',
            'relevant_correct': binary(row['differential_correct']),
            'red_flag_correct': binary(row['red_flag_correct']),
        })

    examples = examples[examples['treatment_id'].isin(ARM_TO_MODEL)].copy()
    for _, row in examples.iterrows():
        model = ARM_TO_MODEL[int(row['treatment_id'])]
        score = scores.loc[str(row['id'])]
        chat = parse_chat(row['chat_history'])
        bots = sorted(chat.get('bot', []), key=lambda item: item.get('id', 0))
        if not bots:
            raise ValueError(f'Missing model response for {row["id"]}')
        records.extend([
            {
                'model': model,
                'stage': 'B',
                'id': str(row['id']),
                'scenario_id': str(row['scenario_id']),
                'participant_id': str(row['participant_id']),
                'relevant_correct': binary(score['differential_correct_bot']),
                'red_flag_correct': binary(score['red_flag_correct_bot']),
            },
            {
                'model': model,
                'stage': 'B_any',
                'id': str(row['id']),
                'scenario_id': str(row['scenario_id']),
                'participant_id': str(row['participant_id']),
                'relevant_correct': binary(score['differential_correct_any']),
                'red_flag_correct': binary(score['red_flag_correct_any']),
            },
            {
                'model': model,
                'stage': 'C',
                'id': str(row['id']),
                'scenario_id': str(row['scenario_id']),
                'participant_id': str(row['participant_id']),
                'relevant_correct': binary(score['differential_correct']),
                'red_flag_correct': binary(score['red_flag_correct']),
            },
        ])
    return pd.DataFrame(records)


def validate_final_scores(scenarios, examples, prescored):
    """Diagnose stored B-final labels against the last raw model message."""
    scores = prescored.set_index('id')
    checked = 0
    matches = 0
    for _, row in examples[examples['treatment_id'].isin(ARM_TO_MODEL)].iterrows():
        chat = parse_chat(row['chat_history'])
        bots = sorted(chat.get('bot', []), key=lambda item: item.get('id', 0))
        final_text = bots[-1].get('text', '')
        scenario = scenarios.loc[str(row['scenario_id'])]
        parsed_relevant = fuzzy_match(parse_literal(scenario['full_differential']), final_text)
        parsed_red_flag = fuzzy_match(parse_literal(scenario['red_flags']), final_text)
        stored = scores.loc[str(row['id'])]
        matches += int(parsed_relevant == bool(binary(stored['differential_correct_bot'])))
        matches += int(parsed_red_flag == bool(binary(stored['red_flag_correct_bot'])))
        checked += 2
    return matches, checked


def point_estimates(records):
    rows = []
    for (model, stage), group in records.groupby(['model', 'stage']):
        for outcome in OUTCOMES:
            rows.append({
                'model': model,
                'stage': stage,
                'outcome': outcome,
                'estimate': scenario_mean(group, outcome),
                'n': len(group),
            })
    return pd.DataFrame(rows)


def bootstrap(records, direct, n_boot):
    """Bootstrap A within scenario and B/C by participant cluster."""
    rng = np.random.default_rng(SEED)
    scenarios = np.sort(records['scenario_id'].unique())
    pairs = [(MODELS[i], MODELS[j]) for i in range(3) for j in range(i + 1, 3)]
    keys = [(pair, comparison, outcome) for pair in pairs for comparison in ('A-B', 'A-C', 'B-C') for outcome in OUTCOMES]
    draws = {key: np.zeros(n_boot) for key in keys}
    difference_draws = {
        (pair, stage, outcome): np.zeros(n_boot)
        for pair in pairs
        for stage in ('A', 'B', 'C')
        for outcome in OUTCOMES
    }

    patient = records[records['stage'].isin(['B', 'C'])]
    patient_matrices = {}
    for model in MODELS:
        model_patient = patient[patient['model'] == model]
        participant_ids = np.sort(model_patient['participant_id'].unique())
        matrices = {}
        participant_index = {pid: index for index, pid in enumerate(participant_ids)}
        scenario_index = {scenario: index for index, scenario in enumerate(scenarios)}
        for stage in ('B', 'C'):
            for outcome in OUTCOMES:
                sums = np.zeros((len(participant_ids), len(scenarios)))
                counts = np.zeros((len(participant_ids), len(scenarios)))
                grouped = model_patient[model_patient['stage'] == stage].groupby(
                    ['participant_id', 'scenario_id']
                )[outcome].agg(['sum', 'count'])
                for (participant_id, scenario), value in grouped.iterrows():
                    row_index = participant_index[participant_id]
                    column_index = scenario_index[scenario]
                    sums[row_index, column_index] = value['sum']
                    counts[row_index, column_index] = value['count']
                matrices[(stage, outcome)] = (sums, counts)
        patient_matrices[model] = (participant_ids, matrices)

    direct_matrices = {}
    direct_names = {'GPT 4o': 'GPT-4o', 'Llama 3 70B': 'Llama 3 70B', 'Command R+': 'Command R+'}
    direct = direct.copy()
    direct['model_name'] = direct['model'].map(direct_names)
    direct_outcomes = {
        'relevant_correct': 'differential_correct',
        'red_flag_correct': 'red_flag_correct',
    }
    for model in MODELS:
        model_direct = direct[direct['model_name'] == model]
        for outcome in OUTCOMES:
            matrix = []
            for scenario in scenarios:
                source_outcome = direct_outcomes[outcome]
                values = model_direct.loc[model_direct['scenario_id'] == scenario, source_outcome].map(binary).to_numpy(dtype=float)
                matrix.append(values)
            direct_matrices[(model, outcome)] = matrix

    for draw in range(n_boot):
        means = {}
        for model in MODELS:
            participant_ids, matrices = patient_matrices[model]
            sampled_ids = rng.choice(participant_ids, size=len(participant_ids), replace=True)
            sampled_indices = np.searchsorted(participant_ids, sampled_ids)
            for stage in ('B', 'C'):
                means[(model, stage)] = {
                    outcome: float(
                        (
                            matrices[(stage, outcome)][0][sampled_indices].sum(axis=0)
                            / matrices[(stage, outcome)][1][sampled_indices].sum(axis=0)
                        ).mean()
                    )
                    for outcome in OUTCOMES
                }
            means[(model, 'A')] = {}
            for outcome in OUTCOMES:
                scenario_values = []
                for values in direct_matrices[(model, outcome)]:
                    sampled_values = values[rng.integers(0, len(values), len(values))]
                    scenario_values.append(sampled_values.mean())
                means[(model, 'A')][outcome] = np.mean(scenario_values)

        for pair in pairs:
            left, right = pair
            for outcome in OUTCOMES:
                d_a = means[(left, 'A')][outcome] - means[(right, 'A')][outcome]
                d_b = means[(left, 'B')][outcome] - means[(right, 'B')][outcome]
                d_c = means[(left, 'C')][outcome] - means[(right, 'C')][outcome]
                difference_draws[(pair, 'A', outcome)][draw] = d_a
                difference_draws[(pair, 'B', outcome)][draw] = d_b
                difference_draws[(pair, 'C', outcome)][draw] = d_c
                draws[(pair, 'A-B', outcome)][draw] = d_b - d_a
                draws[(pair, 'A-C', outcome)][draw] = d_c - d_a
                draws[(pair, 'B-C', outcome)][draw] = d_c - d_b
    return draws, difference_draws


def empirical_p_value(draws):
    """Two-sided bootstrap sign p-value for a zero reversal contrast."""
    return min(1.0, 2 * min(np.mean(draws <= 0), np.mean(draws >= 0)))


def pairwise_table(records, draws, difference_draws):
    rows = []
    for (left, right), comparison, outcome in draws:
        stage_left, stage_right = comparison.split('-')
        point_left = scenario_mean(records[(records['model'] == left) & (records['stage'] == stage_left)], outcome)
        point_right = scenario_mean(records[(records['model'] == right) & (records['stage'] == stage_left)], outcome)
        point_left_right = scenario_mean(records[(records['model'] == left) & (records['stage'] == stage_right)], outcome)
        point_right_right = scenario_mean(records[(records['model'] == right) & (records['stage'] == stage_right)], outcome)
        d_left = point_left - point_right
        d_right = point_left_right - point_right_right
        bootstrap_draws = draws[((left, right), comparison, outcome)]
        left_ci = np.percentile(
            difference_draws[((left, right), stage_left, outcome)], [2.5, 97.5]
        )
        right_ci = np.percentile(
            difference_draws[((left, right), stage_right, outcome)], [2.5, 97.5]
        )
        rows.append({
            'model_left': left,
            'model_right': right,
            'comparison': comparison,
            'outcome': outcome,
            'difference_left': d_left,
            'difference_right': d_right,
            'rank_change': d_right - d_left,
            'ci_low': np.percentile(bootstrap_draws, 2.5),
            'ci_high': np.percentile(bootstrap_draws, 97.5),
            'p_value': empirical_p_value(bootstrap_draws),
            'point_estimate_reversal': d_left * d_right < 0,
            'classification': classify_reversal(d_left, d_right, left_ci, right_ci),
        })
    result = pd.DataFrame(rows)
    primary = result[(result['comparison'] == 'A-B') & (result['outcome'] == 'relevant_correct')]
    result.loc[primary.index, 'holm_p_value'] = holm_adjust(primary['p_value'].to_numpy())
    return result


def main(n_boot=N_BOOT, validate=True):
    scenarios, examples, prescored, direct = load_inputs()
    validate_inputs(examples, prescored, direct)
    records = build_records(scenarios, examples, prescored, direct)
    if validate:
        matches, checked = validate_final_scores(scenarios, examples, prescored)
        print(
            f'B-final parser cross-check: {matches}/{checked} labels match; '
            'using clean_prescored.*_bot as the primary stored B-final outcome.'
        )
    estimates = point_estimates(records)
    draws, difference_draws = bootstrap(records, direct, n_boot)
    pairwise = pairwise_table(records, draws, difference_draws)
    REPORTS.mkdir(parents=True, exist_ok=True)
    estimates.to_csv(REPORTS / 'bean_abc_model_condition_estimates.csv', index=False)
    pairwise.to_csv(REPORTS / 'bean_abc_pairwise_rank_changes.csv', index=False)
    pd.DataFrame([
        {'model': model, 'treatment_id': arm, 'n': int((examples['treatment_id'] == arm).sum())}
        for arm, model in ARM_TO_MODEL.items()
    ]).to_csv(REPORTS / 'bean_abc_model_condition_inventory.csv', index=False)
    print(pairwise.to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-boot', type=int, default=N_BOOT)
    parser.add_argument('--skip-validation', action='store_true')
    args = parser.parse_args()
    main(args.n_boot, validate=not args.skip_validation)
