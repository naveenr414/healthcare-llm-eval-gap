"""Focused tests for the Goh case-balanced decomposition helpers."""

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / 'analysis' / 'study_goh.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unsampled_ids_have_zero_weight():
    goh = load_module('study_goh_test')
    frame = pd.DataFrame({
        'anon_id': ['a', 'a', 'b', 'b'],
        'Case_n': [1, 2, 1, 2],
        'total_pct': [1.0, 1.0, 0.0, 0.0],
    })
    value = goh.weighted_case_balanced_mean(frame, 'total_pct', ['a', 'a'])
    assert value == 1.0


def test_sampled_id_multiplicity_changes_weights():
    goh = load_module('study_goh_multiplicity_test')
    frame = pd.DataFrame({
        'anon_id': ['a', 'a', 'b', 'b'],
        'Case_n': [1, 2, 1, 2],
        'total_pct': [1.0, 1.0, 0.0, 0.0],
    })
    value = goh.weighted_case_balanced_mean(frame, 'total_pct', ['a', 'b'])
    assert value == 0.5
