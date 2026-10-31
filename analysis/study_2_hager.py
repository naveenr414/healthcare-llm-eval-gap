"""Prepare and score the no-API Hager Study 2 analysis.

This script owns the authoritative case inventory, canonical result schema,
diagnosis/treatment-component scoring, and stratified paired bootstrap. It does
not make model calls. API runners should write JSONL records with the schema
documented in ``canonical_result`` before this script is used for scoring.

Run from the repository root with one of:
    python analysis/study_2_hager.py --write-inventory
    python analysis/study_2_hager.py --score-results RESULTS.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path('data/mimic/physionet.org/files/mimic-iv-ext-cdm/1.1')
OUT_DIR = Path('experiments/reports/study2/hager')
PATHOLOGIES = [
    'appendicitis',
    'cholecystitis',
    'diverticulitis',
    'pancreatitis',
]
CASE_SAMPLING_SEED = 2023
PILOT_SIZE_PER_PATHOLOGY = 4
MAIN_SIZE_PER_PATHOLOGY = 25
N_BOOT = 5000
BOOTSTRAP_SEED = 2023
CONDITIONS = ['full_information', 'sequential']

REQUIRED_ID_FILES = {
    'history_of_present_illness.csv': 'clinical history',
    'physical_examination.csv': 'physical examination',
    'discharge_diagnosis.csv': 'discharge diagnosis',
    'icd_diagnosis.csv': 'ICD diagnosis',
}

# These domains can legitimately be empty for a case. The evaluator and API
# adapter represent that situation with an empty list or an explicit no-result
# observation rather than excluding the case from the authoritative universe.
OPTIONAL_ID_FILES = {
    'laboratory_tests.csv': 'laboratory results',
    'microbiology.csv': 'microbiology results',
    'radiology_reports.csv': 'radiology reports',
    'icd_procedures.csv': 'ICD procedures',
    'discharge_procedures.csv': 'discharge procedures',
}


def fail(message):
    raise ValueError(message)


def read_id_set(filename):
    df = pd.read_csv(DATA_DIR / filename, usecols=['hadm_id'])
    return set(df['hadm_id'].astype(str))


def load_authoritative_ids():
    path = DATA_DIR / 'pathology_ids.json'
    mapping = json.loads(path.read_text())
    if set(mapping) != set(PATHOLOGIES):
        fail(f'Unexpected pathology_ids.json keys: {sorted(mapping)}')
    result = {}
    all_ids = []
    for pathology in PATHOLOGIES:
        ids = [str(value) for value in mapping[pathology]]
        if len(ids) != len(set(ids)):
            fail(f'{pathology} contains duplicate hadm_id values')
        result[pathology] = ids
        all_ids.extend(ids)
    if len(all_ids) != 2400 or len(set(all_ids)) != 2400:
        fail('pathology_ids.json must contain 2,400 unique cases')
    return result


def build_inventory():
    """Build the complete inventory from pathology_ids.json only."""
    authoritative = load_authoritative_ids()
    available = {
        filename: read_id_set(filename)
        for filename in [*REQUIRED_ID_FILES, *OPTIONAL_ID_FILES]
    }
    rows = []
    for pathology in PATHOLOGIES:
        for hadm_id in sorted(authoritative[pathology], key=int):
            missing = [
                description
                for filename, description in REQUIRED_ID_FILES.items()
                if hadm_id not in available[filename]
            ]
            empty_domains = [
                description
                for filename, description in OPTIONAL_ID_FILES.items()
                if hadm_id not in available[filename]
            ]
            rows.append({
                'hadm_id': hadm_id,
                'pathology': pathology,
                'eligibility_source': 'pathology_ids.json',
                'inclusion_status': 'eligible' if not missing else 'ineligible',
                'exclusion_reason': '; '.join(missing),
                'empty_optional_domains': '; '.join(empty_domains),
                'pilot_selected': False,
                'main_selected': False,
            })
    inventory = pd.DataFrame(rows)
    rng = np.random.default_rng(CASE_SAMPLING_SEED)
    for pathology in PATHOLOGIES:
        eligible = inventory.loc[
            (inventory['pathology'] == pathology)
            & (inventory['inclusion_status'] == 'eligible')
        ]
        if len(eligible) < MAIN_SIZE_PER_PATHOLOGY:
            fail(f'{pathology} has fewer than 25 eligible cases')
        main_ids = rng.choice(
            eligible['hadm_id'].to_numpy(),
            size=MAIN_SIZE_PER_PATHOLOGY,
            replace=False,
        )
        pilot_ids = rng.choice(
            eligible['hadm_id'].to_numpy(),
            size=PILOT_SIZE_PER_PATHOLOGY,
            replace=False,
        )
        inventory.loc[inventory['hadm_id'].isin(main_ids), 'main_selected'] = True
        inventory.loc[inventory['hadm_id'].isin(pilot_ids), 'pilot_selected'] = True
    selected = inventory.loc[inventory['main_selected']]
    if len(selected) != 100 or selected['pathology'].value_counts().nunique() != 1:
        fail('Main Hager inventory is not balanced at 25 cases per pathology')
    return inventory


def write_inventory():
    inventory = build_inventory()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(OUT_DIR / 'hager_case_inventory.csv', index=False)
    metadata = {
        'eligibility_source': 'data/mimic/physionet.org/files/mimic-iv-ext-cdm/1.1/pathology_ids.json',
        'case_sampling_seed': CASE_SAMPLING_SEED,
        'pilot_size': 16,
        'pilot_size_per_pathology': PILOT_SIZE_PER_PATHOLOGY,
        'main_size': 100,
        'main_size_per_pathology': MAIN_SIZE_PER_PATHOLOGY,
        'pathologies': PATHOLOGIES,
        'required_id_files': REQUIRED_ID_FILES,
        'optional_id_files': OPTIONAL_ID_FILES,
    }
    (OUT_DIR / 'hager_inventory_metadata.json').write_text(
        json.dumps(metadata, indent=2) + '\n'
    )
    return inventory


def canonical_result(record):
    """Validate one runner output before it enters the common evaluator."""
    required = {'hadm_id', 'pathology', 'condition', 'raw_output'}
    missing = sorted(required - set(record))
    if missing:
        fail(f'Hager result is missing fields: {missing}')
    if record['condition'] not in CONDITIONS:
        fail(f"Unexpected Hager condition: {record['condition']}")
    return {
        'hadm_id': str(record['hadm_id']),
        'pathology': record['pathology'],
        'condition': record['condition'],
        'raw_output': record.get('raw_output') or '',
        'trajectory': record.get('trajectory', []),
        'rounds': record.get('rounds'),
        'model_id': record.get('model_id'),
        'usage': record.get('usage', {}),
    }


def load_results(paths):
    if isinstance(paths, (str, Path)):
        paths = [paths]
    records = []
    for path in paths:
        with Path(path).open() as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(canonical_result(json.loads(line)))
                except json.JSONDecodeError as exc:
                    fail(f'Invalid JSON on line {line_number} of {path}: {exc}')
    if not records:
        fail('Hager result file is empty')
    return records


def load_evaluator(pathology):
    framework = Path('external/MIMIC-Clinical-Decision-Making-Framework')
    sys.path.insert(0, str(framework.resolve()))
    from evaluators.appendicitis_evaluator import AppendicitisEvaluator
    from evaluators.cholecystitis_evaluator import CholecystitisEvaluator
    from evaluators.diverticulitis_evaluator import DiverticulitisEvaluator
    from evaluators.pancreatitis_evaluator import PancreatitisEvaluator

    evaluators = {
        'appendicitis': AppendicitisEvaluator,
        'cholecystitis': CholecystitisEvaluator,
        'diverticulitis': DiverticulitisEvaluator,
        'pancreatitis': PancreatitisEvaluator,
    }
    try:
        return evaluators[pathology]()
    except KeyError:
        fail(f'Unknown Hager pathology: {pathology}')


def reference_tables():
    def grouped(filename, value_column):
        df = pd.read_csv(DATA_DIR / filename)
        return df.groupby('hadm_id')[value_column].apply(list).to_dict()

    discharge = pd.read_csv(DATA_DIR / 'discharge_diagnosis.csv')
    hpi = pd.read_csv(DATA_DIR / 'history_of_present_illness.csv')
    physical = pd.read_csv(DATA_DIR / 'physical_examination.csv')
    icd = grouped('icd_diagnosis.csv', 'icd_diagnosis')
    discharge_procedures = grouped('discharge_procedures.csv', 'discharge_procedure')
    procedures = pd.read_csv(DATA_DIR / 'icd_procedures.csv')
    procedure_groups = {}
    for hadm_id, group in procedures.groupby('hadm_id'):
        procedure_groups[hadm_id] = {
            'icd9': group.loc[group['icd_version'] == 9, 'icd_code'].tolist(),
            'icd10': group.loc[group['icd_version'] != 9, 'icd_code'].tolist(),
        }
    discharge_map = dict(zip(discharge['hadm_id'], discharge['discharge_diagnosis']))
    hpi_map = dict(zip(hpi['hadm_id'], hpi['hpi']))
    physical_map = dict(zip(physical['hadm_id'], physical['pe']))
    return {
        hadm_id: {
            'discharge_diagnosis': discharge_map[hadm_id],
            'icd_diagnosis': icd.get(hadm_id, []),
            'procedures_icd9': procedure_groups.get(hadm_id, {}).get('icd9', []),
            'procedures_icd10': procedure_groups.get(hadm_id, {}).get('icd10', []),
            'procedures_discharge': discharge_procedures.get(hadm_id, []),
            'patient_history': hpi_map[hadm_id],
            'physical_examination': physical_map[hadm_id],
        }
        for hadm_id in set(discharge_map) & set(hpi_map) & set(physical_map)
    }


def score_one(record, references):
    """Score diagnosis and treatment components identically across conditions."""
    raw_output = record['raw_output']
    reference = references[int(record['hadm_id'])]
    evaluator = load_evaluator(record['pathology'])
    if not raw_output.strip():
        answers = {'Diagnosis': '', 'Treatment': ''}
        scores = {'Diagnosis': 0, 'Treatment Parsing': 0}
        treatment_components = {
            key: 0
            for key in evaluator.answers['Treatment Required']
        }
    else:
        evaluation = evaluator._evaluate_agent_trajectory(
            prediction=raw_output,
            input=reference['patient_history'],
            agent_trajectory=[],
            reference=(
                reference['discharge_diagnosis'],
                reference['icd_diagnosis'],
                reference['procedures_icd9'],
                reference['procedures_icd10'],
                reference['procedures_discharge'],
            ),
        )
        # The upstream evaluator skips treatment when the trajectory is empty.
        # Full-information results have no trajectory, so score the parsed
        # Treatment field explicitly after the shared diagnosis evaluation.
        evaluator.parse_treatment(raw_output)
        evaluator.score_treatment()
        answers = evaluator.answers
        scores = evaluation['scores']
        treatment_components = {
            key: int(value)
            for key, value in answers['Treatment Requested'].items()
        }
    return {
        **record,
        'final_diagnosis': answers['Diagnosis'],
        'treatment': answers['Treatment'],
        'diagnosis_score': int(scores.get('Diagnosis', 0)),
        'treatment_components': treatment_components,
    }


def point_estimates(scored):
    diagnosis = scored.drop_duplicates(['hadm_id', 'condition'])
    rows = []
    for pathology in [None, *PATHOLOGIES]:
        subset = scored if pathology is None else scored.loc[
            scored['pathology'] == pathology
        ]
        diag_subset = diagnosis if pathology is None else diagnosis.loc[
            diagnosis['pathology'] == pathology
        ]
        label = 'overall' if pathology is None else pathology
        for condition in CONDITIONS:
            values = diag_subset.loc[
                diag_subset['condition'] == condition, 'diagnosis_score'
            ]
            rows.append({
                'stratum': label,
                'condition': condition,
                'outcome': 'diagnosis',
                'component': 'diagnosis',
                'estimate': values.mean(),
            })
            for component, group in subset.groupby('treatment_component'):
                values = group.loc[
                    group['condition'] == condition, 'treatment_score'
                ]
                rows.append({
                    'stratum': label,
                    'condition': condition,
                    'outcome': 'treatment',
                    'component': component,
                    'estimate': values.mean(),
                })
    return pd.DataFrame(rows)


def overall_bootstrap_point(scored):
    diagnosis = scored.drop_duplicates(['hadm_id', 'condition'])
    point = {}
    for condition in CONDITIONS:
        point[f'{condition}_diagnosis'] = diagnosis.loc[
            diagnosis['condition'] == condition, 'diagnosis_score'
        ].mean()
        components = scored['treatment_component'].unique()
        for component in components:
            point[f'{condition}_{component}'] = scored.loc[
                (scored['condition'] == condition)
                & (scored['treatment_component'] == component),
                'treatment_score',
            ].mean()
    point['sequential_minus_full_diagnosis'] = (
        point['sequential_diagnosis'] - point['full_information_diagnosis']
    )
    for component in scored['treatment_component'].unique():
        point[f'sequential_minus_full_{component}'] = (
            point[f'sequential_{component}']
            - point[f'full_information_{component}']
        )
    return point


def bootstrap_intervals(bootstrap_results, point):
    rows = []
    for column in bootstrap_results.columns:
        if column == 'replicate':
            continue
        values = bootstrap_results[column].dropna().to_numpy()
        low, high = np.percentile(values, [2.5, 97.5])
        rows.append({
            'outcome': column,
            'estimate': point[column],
            'ci_low': low,
            'ci_high': high,
        })
    return pd.DataFrame(rows)


def score_results(results_paths, sample='main'):
    inventory = build_inventory()
    selection_flag = 'main_selected' if sample == 'main' else 'pilot_selected'
    selected = inventory.loc[inventory[selection_flag]].copy()
    selected_ids = set(selected['hadm_id'])
    expected_pathologies = dict(zip(selected['hadm_id'], selected['pathology']))
    records = load_results(results_paths)
    result_frame = pd.DataFrame(records)
    validate_condition_pairs(result_frame, selected_ids)
    if any(
        expected_pathologies.get(record['hadm_id']) != record['pathology']
        for record in records
    ):
        fail('Hager result pathology does not match the selected inventory')
    references = reference_tables()
    scored = [score_one(record, references) for record in records]
    canonical_rows = []
    for record in scored:
        canonical_rows.append({
            'hadm_id': record['hadm_id'],
            'pathology': record['pathology'],
            'condition': record['condition'],
            'raw_output': record['raw_output'],
            'final_diagnosis': record['final_diagnosis'],
            'treatment': record['treatment'],
            'treatment_components': json.dumps(
                record['treatment_components'], sort_keys=True
            ),
            'trajectory': json.dumps(record['trajectory']),
            'rounds': record['rounds'],
            'model_id': record['model_id'],
            'usage': json.dumps(record['usage'], sort_keys=True),
            'diagnosis_score': record['diagnosis_score'],
        })
    pd.DataFrame(canonical_rows).to_json(
        OUT_DIR / f'hager_{sample}_canonical_results.jsonl',
        orient='records',
        lines=True,
    )
    rows = []
    for record in scored:
        for component, value in record['treatment_components'].items():
            rows.append({
                'hadm_id': record['hadm_id'],
                'pathology': record['pathology'],
                'condition': record['condition'],
                'diagnosis_score': record['diagnosis_score'],
                'raw_output': record['raw_output'],
                'final_diagnosis': record['final_diagnosis'],
                'treatment': record['treatment'],
                'treatment_components': json.dumps(
                    record['treatment_components'], sort_keys=True
                ),
                'trajectory': json.dumps(record['trajectory']),
                'model_id': record['model_id'],
                'usage': json.dumps(record['usage'], sort_keys=True),
                'treatment_component': component,
                'treatment_score': value,
                'rounds': record['rounds'],
            })
    scored_frame = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scored_frame.to_csv(
        OUT_DIR / f'hager_{sample}_scored_results.csv', index=False
    )
    point_estimates(scored_frame).to_csv(
        OUT_DIR / f'hager_{sample}_point_estimates.csv', index=False
    )
    if sample == 'main':
        bootstrap_results = bootstrap(scored_frame)
        bootstrap_results.to_csv(OUT_DIR / 'hager_bootstrap_results.csv', index=False)
        bootstrap_intervals(
            bootstrap_results, overall_bootstrap_point(scored_frame)
        ).to_csv(
            OUT_DIR / 'hager_bootstrap_intervals.csv', index=False
        )
        metadata = {
            'sample': sample,
            'bootstrap_replicates': N_BOOT,
            'bootstrap_seed': BOOTSTRAP_SEED,
            'case_sampling_seed': CASE_SAMPLING_SEED,
            'stratification': 'pathology',
            'cases_per_pathology_per_replicate': MAIN_SIZE_PER_PATHOLOGY,
            'paired_conditions': CONDITIONS,
            'missing_output_rule': 'zero for diagnosis and every applicable treatment component',
        }
        (OUT_DIR / 'hager_analysis_metadata.json').write_text(
            json.dumps(metadata, indent=2) + '\n'
        )
        return scored_frame, bootstrap_results
    return scored_frame, None


def validate_condition_pairs(result_frame, selected_ids):
    if set(result_frame['hadm_id']) != selected_ids:
        fail('Hager results do not match the selected case inventory')
    if set(result_frame['condition']) != set(CONDITIONS):
        fail('Hager results must contain both conditions')
    if result_frame.duplicated(['hadm_id', 'condition']).any():
        fail('Hager results contain duplicate case-condition records')
    condition_sets = result_frame.groupby('hadm_id')['condition'].agg(set)
    if not (condition_sets == set(CONDITIONS)).all():
        fail('Every selected Hager ID must have both condition results')


def bootstrap(scored):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    cases = scored[['hadm_id', 'pathology']].drop_duplicates()
    if len(cases) != 100:
        fail('Hager bootstrap requires exactly 100 selected cases')
    outcomes = []
    treatment_components = sorted(scored['treatment_component'].unique())
    for pathology in PATHOLOGIES:
        if (cases['pathology'] == pathology).sum() != 25:
            fail(f'Hager bootstrap stratum {pathology} does not contain 25 cases')
    wide = scored.pivot_table(
        index=['hadm_id', 'pathology'],
        columns=['condition', 'treatment_component'],
        values='treatment_score',
        aggfunc='first',
    )
    diagnosis = scored.drop_duplicates(['hadm_id', 'condition']).pivot(
        index=['hadm_id', 'pathology'], columns='condition', values='diagnosis_score'
    )
    for replicate in range(N_BOOT):
        sampled_ids = []
        for pathology in PATHOLOGIES:
            ids = cases.loc[cases['pathology'] == pathology, 'hadm_id'].to_numpy()
            sampled_ids.extend(rng.choice(ids, size=25, replace=True))
        sampled_index = pd.Index(sampled_ids, name='hadm_id')
        sampled_cases = cases.set_index('hadm_id').loc[sampled_index].reset_index()
        row = {'replicate': replicate}
        for condition in CONDITIONS:
            diag_values = diagnosis.loc[sampled_ids, condition].to_numpy()
            row[f'{condition}_diagnosis'] = diag_values.mean()
            for component in treatment_components:
                column = (condition, component)
                if column not in wide:
                    continue
                values = wide.loc[sampled_ids, column].to_numpy()
                # Treatment components are pathology-specific. Non-applicable
                # pathology cells are NaN and must not enter that component's
                # denominator.
                row[f'{condition}_{component}'] = np.nanmean(values)
        row['sequential_minus_full_diagnosis'] = (
            row['sequential_diagnosis'] - row['full_information_diagnosis']
        )
        for component in treatment_components:
            full_key = f'full_information_{component}'
            seq_key = f'sequential_{component}'
            if full_key in row and seq_key in row:
                row[f'sequential_minus_full_{component}'] = (
                    row[seq_key] - row[full_key]
                )
        outcomes.append(row)
    result = pd.DataFrame(outcomes)
    result.attrs['bootstrap_seed'] = BOOTSTRAP_SEED
    result.attrs['bootstrap_replicates'] = N_BOOT
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-inventory', action='store_true')
    parser.add_argument('--score-results', nargs='+')
    parser.add_argument('--sample', choices=['pilot', 'main'], default='main')
    args = parser.parse_args()
    if bool(args.write_inventory) == bool(args.score_results):
        parser.error('choose exactly one of --write-inventory or --score-results')
    if args.write_inventory:
        write_inventory()
    else:
        score_results(args.score_results, sample=args.sample)


if __name__ == '__main__':
    main()
