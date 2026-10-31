"""Validate and report the no-API Study 1 analysis.

The primary estimand is accuracy under a uniform distribution over the ten
observed scenarios. Patient-stage uncertainty is participant-clustered while
preserving the condition-2/3/4 pairing within each case id.

Run from the repository root with:
    python analysis/study_1_report.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


N_BOOT = 5000
RNG = np.random.default_rng(0)
EXPECTED_SCENARIOS = 10
OUT_DIR = Path('experiments/reports/study1')


def read_inputs():
    direct = pd.read_csv('data/study1/direct_trials_condition.csv', index_col=0)
    examples = pd.read_csv('data/study1/clean_examples.csv')
    saved = pd.read_csv('data/study1/saved_results.csv', index_col=0)
    prescored = pd.read_csv('data/study1/clean_prescored.csv')
    scenarios = pd.read_csv('data/study1/scenarios.csv')
    return direct, examples, saved, prescored, scenarios


def fail(message):
    raise ValueError(message)


def require_unique(df, column, label):
    if df[column].duplicated().any():
        duplicates = df.loc[df[column].duplicated(), column].unique().tolist()
        fail(f'{label} has duplicate {column} values: {duplicates[:5]}')


def require_same_ids(left, right, label):
    left_ids = set(left)
    right_ids = set(right)
    if left_ids != right_ids:
        fail(
            f'{label} ID mismatch: '
            f'{len(left_ids - right_ids)} missing and {len(right_ids - left_ids)} extra'
        )


def to_binary(values, label):
    def convert(value):
        if pd.isna(value):
            return np.nan
        if isinstance(value, (bool, np.bool_)):
            return int(value)
        text = str(value).strip()
        if text == 'True':
            return 1
        if text == 'False':
            return 0
        if text == '1':
            return 1
        if text == '0':
            return 0
        return np.nan

    converted = values.map(convert)
    invalid = values[converted.isna() & values.notna()]
    if len(invalid) > 0 or converted.isna().any():
        examples = invalid.astype(str).unique().tolist()[:5]
        fail(f'{label} contains missing or non-binary values: {examples}')
    return converted.astype(int)


def validate_and_merge(examples, saved, prescored, scenarios):
    # saved_results.csv contains treatment 1 (Llama) IDs. It is not the
    # primary GPT-4o condition in the revised information decomposition.
    treatment = examples.loc[examples['treatment_id'] == 1].copy()
    if len(treatment) != 600:
        fail(f'Expected 600 treatment-1 rows, found {len(treatment)}')
    require_unique(treatment, 'id', 'treatment-1 examples')
    require_unique(saved, 'id', 'saved first-turn results')
    require_unique(prescored, 'id', 'prescored results')
    require_unique(scenarios, 'scenario_id', 'scenario metadata')

    require_same_ids(treatment['id'], saved['id'], 'treatment-1 vs saved results')
    prescored = prescored.loc[prescored['id'].isin(treatment['id'])].copy()
    require_same_ids(treatment['id'], prescored['id'], 'treatment-1 vs prescored results')
    if len(scenarios) != EXPECTED_SCENARIOS:
        fail(f'Expected {EXPECTED_SCENARIOS} scenarios, found {len(scenarios)}')
    if not set(treatment['scenario_id']).issubset(set(scenarios['scenario_id'])):
        fail('Treatment rows contain scenario IDs absent from scenarios.csv')

    saved = saved[['id', 'scenario_id', 'correct']].copy()
    saved['p2'] = to_binary(saved.pop('correct'), 'saved_results.correct')
    saved = saved.rename(columns={'scenario_id': 'saved_scenario_id'})

    scored = prescored[['id', 'differential_correct_bot', 'differential_correct']].copy()
    scored['p3'] = to_binary(
        scored.pop('differential_correct_bot'),
        'clean_prescored.differential_correct_bot',
    )
    scored['p4'] = to_binary(
        scored.pop('differential_correct'),
        'clean_prescored.differential_correct',
    )

    merged = treatment.merge(saved, on='id', how='inner', validate='one_to_one')
    merged = merged.merge(scored, on='id', how='inner', validate='one_to_one')
    if len(merged) != 600:
        fail(f'Validated patient analysis frame has {len(merged)} rows, not 600')
    if not (merged['scenario_id'] == merged['saved_scenario_id']).all():
        fail('Scenario IDs disagree between clean_examples.csv and saved_results.csv')
    if merged[['p2', 'p3', 'p4']].isna().any().any():
        fail('Patient analysis frame contains missing binary outcomes')
    return merged.drop(columns='saved_scenario_id')


def scenario_balanced_mean(df, outcome):
    means = df.groupby('scenario_id', sort=True)[outcome].mean()
    if len(means) != EXPECTED_SCENARIOS:
        fail(f'{outcome} is missing one or more scenarios')
    return means.mean()


def bootstrap_direct(direct, outcome):
    scenarios = np.sort(direct['scenario_id'].unique())
    draws = np.zeros(N_BOOT)
    for scenario in scenarios:
        values = direct.loc[direct['scenario_id'] == scenario, outcome].to_numpy()
        indices = RNG.integers(0, len(values), size=(N_BOOT, len(values)))
        draws += values[indices].mean(axis=1)
    return draws / len(scenarios)


def bootstrap_patient(patient):
    outcomes = ['p2', 'p3', 'p4']
    clusters = patient['participant_id'].drop_duplicates().to_numpy()
    scenarios = np.sort(patient['scenario_id'].unique())
    index = pd.MultiIndex.from_product(
        [clusters, scenarios], names=['participant_id', 'scenario_id']
    )
    grouped = patient.groupby(['participant_id', 'scenario_id'], sort=False)
    sums = grouped[outcomes].sum().reindex(index, fill_value=0)
    counts = grouped.size().reindex(index, fill_value=0)
    sums = sums.to_numpy().reshape(len(clusters), len(scenarios), len(outcomes))
    counts = counts.to_numpy().reshape(len(clusters), len(scenarios))

    indices = RNG.integers(0, len(clusters), size=(N_BOOT, len(clusters)))
    sampled_sums = sums[indices].sum(axis=1)
    sampled_counts = counts[indices].sum(axis=1)
    scenario_means = sampled_sums / sampled_counts[:, :, None]
    means = scenario_means.mean(axis=1)

    result = {outcome: means[:, j] for j, outcome in enumerate(outcomes)}
    for left, right in [('p2', 'p3'), ('p3', 'p4'), ('p2', 'p4')]:
        if left not in outcomes or right not in outcomes:
            continue
        left_idx, right_idx = outcomes.index(left), outcomes.index(right)
        differences = (
            sampled_sums[:, :, right_idx] - sampled_sums[:, :, left_idx]
        ) / sampled_counts
        result[f'delta_{left}_{right}'] = differences.mean(axis=1)
    return result


def bootstrap_patient_rows(patient):
    """Resample patient rows within scenario, preserving p2/p3/p4 pairing."""
    outcomes = ['p2', 'p3', 'p4']
    scenarios = np.sort(patient['scenario_id'].unique())
    draws = {outcome: np.zeros(N_BOOT) for outcome in outcomes}
    differences = {
        f'delta_{left}_{right}': np.zeros(N_BOOT)
        for left, right in [('p2', 'p3'), ('p3', 'p4'), ('p2', 'p4')]
    }

    for scenario in scenarios:
        values = patient.loc[
            patient['scenario_id'] == scenario, outcomes
        ].to_numpy(dtype=float)
        indices = RNG.integers(0, len(values), size=(N_BOOT, len(values)))
        sampled = values[indices].mean(axis=1)
        for j, outcome in enumerate(outcomes):
            draws[outcome] += sampled[:, j]
        for left, right in [('p2', 'p3'), ('p3', 'p4'), ('p2', 'p4')]:
            left_idx, right_idx = outcomes.index(left), outcomes.index(right)
            differences[f'delta_{left}_{right}'] += (
                values[indices, right_idx] - values[indices, left_idx]
            ).mean(axis=1)

    for values in list(draws.values()) + list(differences.values()):
        values /= len(scenarios)
    return {**draws, **differences}


def bootstrap_scenarios(df, outcomes):
    """Resample scenario means, giving each sampled scenario equal weight."""
    scenario_means = df.groupby('scenario_id', sort=True)[outcomes].mean()
    values = scenario_means.to_numpy(dtype=float)
    indices = RNG.integers(0, len(values), size=(N_BOOT, len(values)))
    sampled = values[indices].mean(axis=1)
    result = {outcome: sampled[:, j] for j, outcome in enumerate(outcomes)}
    for left, right in [('p2', 'p3'), ('p3', 'p4'), ('p2', 'p4')]:
        if left not in outcomes or right not in outcomes:
            continue
        left_idx, right_idx = outcomes.index(left), outcomes.index(right)
        result[f'delta_{left}_{right}'] = (
            values[indices, right_idx] - values[indices, left_idx]
        ).mean(axis=1)
    return result


def percentile_ci(values):
    return np.percentile(values, [2.5, 97.5])


def make_main_table(direct, patient):
    direct_boot = bootstrap_direct(direct, 'p1')
    patient_boot = bootstrap_patient(patient)
    point = {
        'p1': scenario_balanced_mean(direct, 'p1'),
        'p2': scenario_balanced_mean(patient, 'p2'),
        'p3': scenario_balanced_mean(patient, 'p3'),
        'p4': scenario_balanced_mean(patient, 'p4'),
    }
    boots = {
        'p1': direct_boot,
        'p2': patient_boot['p2'],
        'p3': patient_boot['p3'],
        'p4': patient_boot['p4'],
    }
    changes = {
        'p2': boots['p2'] - boots['p1'],
        'p3': patient_boot['delta_p2_p3'],
        'p4': patient_boot['delta_p3_p4'],
    }
    point_changes = {
        'p2': point['p2'] - point['p1'],
        'p3': patient['p3'].sub(patient['p2']).groupby(patient['scenario_id']).mean().mean(),
        'p4': patient['p4'].sub(patient['p3']).groupby(patient['scenario_id']).mean().mean(),
    }
    labels = {
        'p1': 'Expert query, single-turn',
        'p2': 'Patient first message, single-turn',
        'p3': 'GPT-4o in real multi-turn',
        'p4': 'Human final answer',
    }
    rows = []
    for key in ['p1', 'p2', 'p3', 'p4']:
        outcome = direct['p1'] if key == 'p1' else patient[key]
        row = {
            'evaluation_condition': labels[key],
            'N': len(outcome),
            'correct': int(outcome.sum()),
            'estimate': point[key],
            'estimate_ci_low': percentile_ci(boots[key])[0],
            'estimate_ci_high': percentile_ci(boots[key])[1],
            'change_from_previous': np.nan if key == 'p1' else point_changes[key],
            'change_ci_low': np.nan if key == 'p1' else percentile_ci(changes[key])[0],
            'change_ci_high': np.nan if key == 'p1' else percentile_ci(changes[key])[1],
        }
        rows.append(row)
    return pd.DataFrame(rows), point, boots, patient_boot


def interval_sensitivity(direct, patient, primary_boot):
    """Compare primary, row-level, and scenario-clustered intervals."""
    row_boot = bootstrap_patient_rows(patient)
    scenario_boot = bootstrap_scenarios(patient, ['p2', 'p3', 'p4'])
    direct_row_boot = bootstrap_direct(direct, 'p1')
    direct_scenario_boot = bootstrap_scenarios(direct.assign(p2=direct['p1']), ['p2'])
    primary_boot = {**primary_boot, 'p1': direct_row_boot}

    boot_sets = {
        'participant_clustered': primary_boot,
        'row_level': {**row_boot, 'p1': direct_row_boot},
        'scenario_clustered': {
            **scenario_boot,
            'p1': direct_scenario_boot['p2'],
        },
    }
    quantities = {
        'p1': lambda b: b['p1'],
        'p2': lambda b: b['p2'],
        'p3': lambda b: b['p3'],
        'p4': lambda b: b['p4'],
        'delta_1_to_2': lambda b: b['p2'] - b['p1'],
        'delta_2_to_3': lambda b: b['delta_p2_p3'],
        'delta_3_to_4': lambda b: b['delta_p3_p4'],
        'delta_2_to_4': lambda b: b['delta_p2_p4'],
    }
    rows = []
    for method, boot in boot_sets.items():
        for quantity, get_values in quantities.items():
            values = get_values(boot)
            lo, hi = percentile_ci(values)
            rows.append({
                'resampling_method': method,
                'quantity': quantity,
                'estimate': values.mean(),
                'ci_low': lo,
                'ci_high': hi,
                'ci_width': hi - lo,
            })
    return pd.DataFrame(rows)


def transition_table(patient):
    rows = []
    for left, right, label in [
        ('p2', 'p3', '2_to_3'),
        ('p3', 'p4', '3_to_4'),
        ('p2', 'p4', '2_to_4'),
    ]:
        transitions = patient[left].astype(str) + '→' + patient[right].astype(str)
        counts = transitions.value_counts().to_dict()
        scenario_change = patient[right].sub(patient[left]).groupby(
            patient['scenario_id']
        ).mean().mean()
        rows.append({
            'transition': label,
            '0_to_0': counts.get('0→0', 0),
            '0_to_1': counts.get('0→1', 0),
            '1_to_0': counts.get('1→0', 0),
            '1_to_1': counts.get('1→1', 0),
            'scenario_balanced_mean_change': scenario_change,
        })
    return pd.DataFrame(rows)


def direct_diagnostics(direct):
    model = direct.groupby('model')['differential_correct'].agg(
        N='size', correct='sum', estimate='mean'
    ).reset_index()
    reverse = direct.groupby(['model', 'reverse'])['differential_correct'].agg(
        N='size', correct='sum', estimate='mean'
    ).reset_index()
    return model, reverse


def scenario_diagnostics(direct, patient, scenarios):
    frames = []
    direct_main = direct.loc[direct['model'] == 'GPT 4o', ['scenario_id', 'p1']]
    frames.append(direct_main.assign(evaluation_condition='p1'))
    for key in ['p2', 'p3', 'p4']:
        frames.append(patient[['scenario_id', key]].rename(columns={key: 'p1'}).assign(
            evaluation_condition=key
        ))
    combined = pd.concat(frames, ignore_index=True)
    estimates = combined.groupby(
        ['scenario_id', 'evaluation_condition']
    )['p1'].agg(N='size', correct='sum', estimate='mean').reset_index()
    metadata = scenarios[['scenario_id', 'condition', 'urgency', 'urgency_text']]
    return estimates.merge(metadata, on='scenario_id', how='left', validate='many_to_one')


def path_assessment(direct):
    history_columns = [
        column for column in direct.columns
        if any(term in column.lower() for term in ['chat', 'conversation', 'turn', 'message'])
    ]
    return pd.DataFrame([
        {'query_source': 'Expert', 'single_turn': 'available', 'multi_turn': 'unavailable'},
        {'query_source': 'Patient', 'single_turn': 'available', 'multi_turn': 'available'},
    ]), {
        'direct_history_like_columns': history_columns,
        'expert_multi_turn_cell': 'unavailable',
        'identified_path': '(expert, single) -> (patient, single) -> (patient, multi)',
        'limitation': 'The data do not identify the expert-query/multi-turn cell or path-independent additive effects.',
    }


def write_report(main, transitions, model, reverse, scenario, path_table, path_text,
                 sensitivity):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    main.to_csv(OUT_DIR / 'main_table.csv', index=False)
    transitions.loc[transitions['transition'] != '2_to_4'].to_csv(
        OUT_DIR / 'paired_transitions.csv', index=False
    )
    transitions.loc[transitions['transition'] == '2_to_4'].to_csv(
        OUT_DIR / 'paired_2_to_4.csv', index=False
    )
    model.to_csv(OUT_DIR / 'direct_model_comparison.csv', index=False)
    reverse.to_csv(OUT_DIR / 'direct_reverse_comparison.csv', index=False)
    scenario.to_csv(OUT_DIR / 'scenario_diagnostics.csv', index=False)
    sensitivity.to_csv(OUT_DIR / 'interval_sensitivity.csv', index=False)
    path_table.to_csv(OUT_DIR / 'path_assessment.csv', index=False)
    config = {
        'n_boot': N_BOOT,
        'seed': 0,
        'primary_weighting': 'equal across ten scenarios',
        'direct_resampling': 'within-scenario rows, independently',
        'patient_resampling': 'participant clusters with all rows retained',
        'paired_conditions': 'same id for conditions 2-4',
        'condition_2_file': 'data/study1/saved_results.csv',
    }
    (OUT_DIR / 'bootstrap_config.json').write_text(json.dumps(config, indent=2))

    lines = [
        'Study 1 report',
        '',
        'Primary estimates use equal weighting across the ten observed scenarios.',
        'Patient-stage intervals use participant-clustered bootstrap resampling.',
        'Interval sensitivity results are in interval_sensitivity.csv.',
        '',
        main.to_string(index=False),
        '',
        'Paired transitions:',
        transitions.to_string(index=False),
        '',
        'Direct model comparison:',
        model.to_string(index=False),
        '',
        'Direct reverse-order comparison:',
        reverse.to_string(index=False),
        '',
        'Interval sensitivity:',
        sensitivity.to_string(index=False),
        '',
        'Path assessment:',
        path_text['identified_path'],
        path_text['limitation'],
        '',
        'All direct model and reverse-order comparisons are descriptive static-trial analyses.',
    ]
    (OUT_DIR / 'report.txt').write_text('\n'.join(lines))


def main():
    direct, examples, saved, prescored, scenarios = read_inputs()
    direct = direct.loc[direct['model'].notna()].copy()
    direct['differential_correct'] = to_binary(
        direct['differential_correct'], 'direct_trials.differential_correct'
    )
    direct['p1'] = direct['differential_correct']
    direct['reverse'] = to_binary(direct['reverse'], 'direct_trials.reverse')

    patient = validate_and_merge(examples, saved, prescored, scenarios)
    main_table, _, _, patient_boot = make_main_table(
        direct.loc[direct['model'] == 'GPT 4o'].copy(), patient
    )
    transitions = transition_table(patient)
    model, reverse = direct_diagnostics(direct)
    scenario = scenario_diagnostics(
        direct.loc[direct['model'] == 'GPT 4o'].copy(), patient, scenarios
    )
    path_table, path_text = path_assessment(direct)
    sensitivity = interval_sensitivity(
        direct.loc[direct['model'] == 'GPT 4o'].copy(), patient, patient_boot
    )
    write_report(
        main_table, transitions, model, reverse, scenario, path_table, path_text,
        sensitivity,
    )
    print(f'Report written to {OUT_DIR}')


if __name__ == '__main__':
    main()
