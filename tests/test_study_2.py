"""Focused tests for the Study 2 estimators and result contracts.

These tests are intentionally not executed as part of implementation. They can
be run later with pytest after the repository environment is installed.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'analysis' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_goh_unsampled_ids_have_zero_weight():
    goh = load_module('study_2_goh_test', 'study_2_goh.py')
    frame = pd.DataFrame({
        'anon_id': ['a', 'a', 'b', 'b'],
        'Case_n': [1, 2, 1, 2],
        'total_pct': [1.0, 1.0, 0.0, 0.0],
    })
    # ID b is not selected. Its rows remain in the input frame but must have
    # zero weight rather than NaN weight.
    value = goh.weighted_case_balanced_mean(frame, 'total_pct', ['a', 'a'])
    assert value == 1.0


def test_goh_sampled_id_multiplicity_changes_weights():
    goh = load_module('study_2_goh_multiplicity_test', 'study_2_goh.py')
    frame = pd.DataFrame({
        'anon_id': ['a', 'a', 'b', 'b'],
        'Case_n': [1, 2, 1, 2],
        'total_pct': [1.0, 1.0, 0.0, 0.0],
    })
    value = goh.weighted_case_balanced_mean(frame, 'total_pct', ['a', 'b'])
    assert value == 0.5


def test_hager_missing_output_is_canonicalized():
    hager = load_module('study_2_hager_result_test', 'study_2_hager.py')
    result = hager.canonical_result({
        'hadm_id': 123,
        'pathology': 'appendicitis',
        'condition': 'full_information',
        'raw_output': '',
    })
    assert result['hadm_id'] == '123'
    assert result['raw_output'] == ''
    assert result['trajectory'] == []


def test_hager_missing_output_scores_zero(monkeypatch):
    hager = load_module('study_2_hager_missing_score_test', 'study_2_hager.py')

    class FakeEvaluator:
        answers = {'Treatment Required': {'Procedure': True}}

    monkeypatch.setattr(hager, 'load_evaluator', lambda pathology: FakeEvaluator())
    scored = hager.score_one(
        {
            'hadm_id': '1',
            'pathology': 'appendicitis',
            'condition': 'full_information',
            'raw_output': '',
            'trajectory': [],
            'rounds': None,
            'model_id': 'test',
            'usage': {},
        },
        {1: {'patient_history': ''}},
    )
    assert scored['diagnosis_score'] == 0
    assert scored['treatment_components'] == {'Procedure': 0}


def test_hager_requires_both_conditions_for_each_selected_id():
    hager = load_module('study_2_hager_pairs_test', 'study_2_hager.py')
    frame = pd.DataFrame({
        'hadm_id': ['1', '1', '2', '2'],
        'condition': [
            'full_information', 'sequential',
            'full_information', 'sequential',
        ],
    })
    hager.validate_condition_pairs(frame, {'1', '2'})


def test_hager_usage_summary_totals_successes_and_failures():
    api = load_module('study_2_hager_api_usage_test', 'study_2_hager_api.py')
    usage = [
        {
            'request_status': 'success',
            'input_tokens': 10,
            'output_tokens': 4,
            'total_tokens': 14,
            'request_cost': 0.01,
        },
        {
            'request_status': 'failure',
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'request_cost': 0.0,
        },
    ]
    summary = api.summarize_usage(usage, 'sequential', 'pilot', 1)
    assert summary['input_tokens'] == 10
    assert summary['output_tokens'] == 4
    assert summary['successful_requests'] == 1
    assert summary['failed_requests'] == 1


def test_hager_sequential_schema_authorizes_microbiology():
    api = load_module('study_2_hager_prompt_test', 'study_2_hager_api.py')
    assert '"action":"microbiology"' in api.sequential_system_prompt()


def test_hager_optional_empty_domains_do_not_define_required_fields():
    hager = load_module('study_2_hager_optional_fields_test', 'study_2_hager.py')
    assert 'microbiology.csv' in hager.OPTIONAL_ID_FILES
    assert 'icd_procedures.csv' in hager.OPTIONAL_ID_FILES
    assert 'microbiology.csv' not in hager.REQUIRED_ID_FILES
    assert 'icd_procedures.csv' not in hager.REQUIRED_ID_FILES


def test_hager_api_records_retry_and_success():
    api = load_module('study_2_hager_api_retry_test', 'study_2_hager_api.py')

    class Usage:
        prompt_tokens = 3
        completion_tokens = 2

    class Message:
        content = 'ok'

    class Choice:
        message = Message()

    class Response:
        usage = Usage()
        choices = [Choice()]

    class Completions:
        attempts = 0

        def create(self, **kwargs):
            self.attempts += 1
            if self.attempts == 1:
                raise RuntimeError('temporary failure')
            return Response()

    class Client:
        chat = type('Chat', (), {'completions': Completions()})()

    usage = []
    output = api.call_model(Client(), [], 'full_information', '1', 1, usage)
    assert output == 'ok'
    assert [row['request_status'] for row in usage] == ['failure', 'success']


def test_stratified_hager_draw_uses_same_ids_for_both_conditions():
    rng = np.random.default_rng(2023)
    pathology_ids = {
        pathology: np.arange(index * 25, (index + 1) * 25)
        for index, pathology in enumerate([
            'appendicitis', 'cholecystitis', 'diverticulitis', 'pancreatitis'
        ])
    }
    sampled = {
        pathology: rng.choice(ids, size=25, replace=True)
        for pathology, ids in pathology_ids.items()
    }
    assert all(len(ids) == 25 for ids in sampled.values())
    assert set(sampled) == set(pathology_ids)
