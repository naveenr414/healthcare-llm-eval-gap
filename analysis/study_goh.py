"""No-API analysis for the Goh et al. score decomposition.

The primary estimate gives the five cases equal weight. Bootstrap resampling
keeps repeated physician or GPT-run observations together and resamples the
three groups independently.

Run from the repository root with:
    python analysis/study_goh.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


N_BOOT = 5000
BOOTSTRAP_SEED = 2023
CASE_COLUMN = 'Case_n'
ID_COLUMN = 'anon_id'
GROUP_COLUMN = 'Group.final2'
GROUPS = {
    'H': 'Physicians + Conventional Resources only',
    'C': 'Physicians+GPT-4',
    'M': 'GPT Alone',
}
OUTCOMES = [
    'total_pct',
    'management_pct',
    'factual_pct',
    'diagnostic_pct',
    'specific_pct',
    'general_pct',
]
SOURCE = Path('data/goh/source_data_fig1.csv')
OUT_DIR = Path('outputs/study_goh')


def fail(message):
    raise ValueError(message)


def load_scores():
    df = pd.read_csv(SOURCE)
    if len(df) != 400:
        fail(f'Expected 400 Goh records, found {len(df)}')
    required = {CASE_COLUMN, ID_COLUMN, GROUP_COLUMN, *OUTCOMES}
    missing = sorted(required - set(df.columns))
    if missing:
        fail(f'Goh source is missing columns: {missing}')
    required_columns = [CASE_COLUMN, ID_COLUMN, GROUP_COLUMN, 'total_pct']
    if df[required_columns].isna().any().any():
        fail('Goh source contains missing IDs, groups, cases, or total scores')
    if set(df[GROUP_COLUMN]) != set(GROUPS.values()):
        fail('Goh source has unexpected group labels')
    if sorted(df[CASE_COLUMN].unique().tolist()) != [1, 2, 3, 4, 5]:
        fail('Goh source does not contain exactly cases 1 through 5')
    if df[ID_COLUMN].nunique() != 97:
        fail(f'Expected 97 Goh IDs, found {df[ID_COLUMN].nunique()}')
    expected_records = {
        GROUPS['H']: 197,
        GROUPS['C']: 178,
        GROUPS['M']: 25,
    }
    expected_ids = {
        GROUPS['H']: 46,
        GROUPS['C']: 46,
        GROUPS['M']: 5,
    }
    for group, expected in expected_records.items():
        group_df = df.loc[df[GROUP_COLUMN] == group]
        if len(group_df) != expected:
            fail(f'{group} has {len(group_df)} records, expected {expected}')
        if group_df[ID_COLUMN].nunique() != expected_ids[group]:
            fail(
                f'{group} has {group_df[ID_COLUMN].nunique()} IDs, '
                f'expected {expected_ids[group]}'
            )
        counts = group_df.groupby(ID_COLUMN).size()
        if group == GROUPS['M']:
            if not (counts == 5).all():
                fail('Every GPT-alone run ID must contain five cases')
        elif not counts.between(2, 5).all():
            fail('Physician IDs must have between two and five case records')
    return df


def case_balanced_mean(df, outcome):
    observed_cases = set(df.loc[df[outcome].notna(), CASE_COLUMN])
    case_means = df.dropna(subset=[outcome]).groupby(
        CASE_COLUMN, sort=True
    )[outcome].mean()
    if not observed_cases or set(case_means.index) != observed_cases:
        fail(f'{outcome} has no defined case means')
    return float(case_means.mean())


def weighted_case_balanced_mean(df, outcome, sampled_ids):
    counts = pd.Series(sampled_ids).value_counts()
    sampled = df.copy()
    sampled['_bootstrap_weight'] = (
        sampled[ID_COLUMN].map(counts).fillna(0)
    )
    sampled = sampled.loc[sampled['_bootstrap_weight'] > 0]
    sampled = sampled.dropna(subset=[outcome])
    weighted_total = (
        sampled[outcome] * sampled['_bootstrap_weight']
    ).groupby(sampled[CASE_COLUMN]).sum()
    weight_total = sampled.groupby(CASE_COLUMN)['_bootstrap_weight'].sum()
    case_means = weighted_total / weight_total
    observed_cases = set(df.loc[df[outcome].notna(), CASE_COLUMN])
    if set(case_means.index) != observed_cases or case_means.isna().any():
        return np.nan
    return float(case_means.mean())


def resampled_case_balanced_mean(df, outcome, rng):
    ids = df[ID_COLUMN].drop_duplicates().to_numpy()
    redraws = 0
    while True:
        sampled_ids = rng.choice(ids, size=len(ids), replace=True)
        value = weighted_case_balanced_mean(df, outcome, sampled_ids)
        # Redraw if the sampled IDs omit a case on which this outcome is
        # defined, rather than silently changing the case-balanced estimand.
        if not np.isnan(value):
            return value, redraws
        redraws += 1


def bootstrap_group(df, outcome, rng):
    group_bootstrap = np.empty(N_BOOT)
    redraws = 0
    for replicate in range(N_BOOT):
        value, n_redraws = resampled_case_balanced_mean(
            df, outcome, rng
        )
        group_bootstrap[replicate] = value
        redraws += n_redraws
    return group_bootstrap, redraws


def percentile_ci(values):
    return np.percentile(values, [2.5, 97.5])


def analyze(df):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    group_frames = {
        key: df.loc[df[GROUP_COLUMN] == label].copy()
        for key, label in GROUPS.items()
    }
    point = {
        (group, outcome): case_balanced_mean(frame, outcome)
        for group, frame in group_frames.items()
        for outcome in OUTCOMES
    }
    boot = {}
    redraws = {}
    for group, frame in group_frames.items():
        for outcome in OUTCOMES:
            boot[group, outcome], redraws[group, outcome] = bootstrap_group(
                frame, outcome, rng
            )

    rows = []
    for outcome in OUTCOMES:
        for group in ['H', 'C', 'M']:
            low, high = percentile_ci(boot[group, outcome])
            rows.append({
                'outcome': outcome,
                'group': group,
                'group_label': GROUPS[group],
                'estimate': point[group, outcome],
                'ci_low': low,
                'ci_high': high,
                'n_records': len(group_frames[group]),
                'n_ids': group_frames[group][ID_COLUMN].nunique(),
            })
        for contrast, left, right in [
            ('C_minus_H', 'C', 'H'),
            ('M_minus_C', 'M', 'C'),
            ('M_minus_H', 'M', 'H'),
        ]:
            values = boot[left, outcome] - boot[right, outcome]
            low, high = percentile_ci(values)
            rows.append({
                'outcome': outcome,
                'group': contrast,
                'group_label': contrast,
                'estimate': point[left, outcome] - point[right, outcome],
                'ci_low': low,
                'ci_high': high,
                'n_records': np.nan,
                'n_ids': np.nan,
            })
    results = pd.DataFrame(rows)
    results.attrs['redraws'] = {
        f'{group}_{outcome}': count
        for (group, outcome), count in redraws.items()
    }
    return results


def write_outputs(df, results):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT_DIR / 'goh_decomposition.csv', index=False)
    df.to_csv(OUT_DIR / 'goh_validated_analysis_frame.csv', index=False)
    case_means = (
        df.groupby([GROUP_COLUMN, CASE_COLUMN], sort=True)[OUTCOMES]
        .mean()
        .reset_index()
    )
    case_means.to_csv(OUT_DIR / 'goh_case_level_sensitivity.csv', index=False)
    heterogeneity = make_heterogeneity_table(df)
    heterogeneity.to_csv(OUT_DIR / 'goh_heterogeneity.csv', index=False)
    metadata = {
        'source': str(SOURCE),
        'n_records': len(df),
        'n_ids': int(df[ID_COLUMN].nunique()),
        'n_cases': int(df[CASE_COLUMN].nunique()),
        'bootstrap_replicates': N_BOOT,
        'bootstrap_seed': BOOTSTRAP_SEED,
        'bootstrap_redraws': results.attrs.get('redraws', {}),
        'group_id_units': {
            'H': 'physician anonymized IDs',
            'C': 'physician anonymized IDs',
            'M': 'GPT run replicate IDs',
        },
        'primary_estimator': 'mean of the five case-specific means',
        'outcome_case_support': {
            outcome: sorted(
                df.loc[df[outcome].notna(), CASE_COLUMN].unique().tolist()
            )
            for outcome in OUTCOMES
        },
        'secondary_subscore_estimator': (
            'For each subscore, average equally across cases with observed '
            'values; structurally undefined case-subscore cells are not scored as zero.'
        ),
        'group_counts': {
            key: {
                'records': int((df[GROUP_COLUMN] == label).sum()),
                'ids': int(df.loc[df[GROUP_COLUMN] == label, ID_COLUMN].nunique()),
            }
            for key, label in GROUPS.items()
        },
    }
    (OUT_DIR / 'goh_analysis_metadata.json').write_text(
        json.dumps(metadata, indent=2) + '\n'
    )


def make_heterogeneity_table(df):
    rows = []
    dimensions = {
        'resident_attending': 'Type',
        'specialty': 'specialty',
        'years_experience': 'years.experience',
        'time_spent': 'time_spent',
    }
    for dimension, column in dimensions.items():
        if column not in df:
            fail(f'Goh source is missing heterogeneity column: {column}')
        for group, group_df in df.groupby(GROUP_COLUMN, sort=True):
            for level, subset in group_df.groupby(column, dropna=False, sort=True):
                rows.append({
                    'dimension': dimension,
                    'level': str(level),
                    'group': group,
                    'n_records': len(subset),
                    'n_ids': subset[ID_COLUMN].nunique(),
                    'n_cases': subset[CASE_COLUMN].nunique(),
                    'mean_total_pct': subset['total_pct'].mean(),
                    'case_balanced_total_pct': case_balanced_mean(
                        subset, 'total_pct'
                    ) if subset[CASE_COLUMN].nunique() == 5 else np.nan,
                })
    return pd.DataFrame(rows)


def main():
    df = load_scores()
    results = analyze(df)
    write_outputs(df, results)


if __name__ == '__main__':
    main()
