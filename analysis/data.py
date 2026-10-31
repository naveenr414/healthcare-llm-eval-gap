"""Canonical paths and loaders for the four studies and benchmark analyses."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
BEAN = DATA / 'bean'
MIMIC = DATA / 'mimic' / 'mimic-iv-ext-cdm' / '1.1'
BENCHMARKS = DATA / 'benchmarks'
BENCHMARK_ASSUMPTIONS = BENCHMARKS / 'benchmark_assumptions.csv'
FUTURE_EVALS = BENCHMARKS / 'future_evals.csv'
BENCHMARK_ASSUMPTIONS_SECOND = (
    BENCHMARKS / 'benchmark_assumptions_second_annotator.csv'
)
FUTURE_EVALS_SECOND = BENCHMARKS / 'future_evals_second_annotator.csv'
FUTURE_EVALS_SECOND_LEGACY = (
    BENCHMARKS / 'future_evals_second_annotator_legacy.csv'
)


def load_bean_inputs():
    """Load the released Bean files used by all Bean analyses."""
    return {
        'direct': pd.read_csv(BEAN / 'direct_trials_condition.csv'),
        'examples': pd.read_csv(BEAN / 'clean_examples.csv'),
        'saved': pd.read_csv(BEAN / 'saved_results.csv'),
        'prescored': pd.read_csv(BEAN / 'clean_prescored.csv'),
        'scenarios': pd.read_csv(BEAN / 'scenarios.csv'),
    }


def load_goh_data():
    """Load the Goh et al. source table."""
    return pd.read_csv(DATA / 'goh' / 'source_data_fig1.csv')


def load_benchmark_assumptions():
    """Load the 18 benchmark-by-assumption match scores (1 = yes)."""
    return pd.read_csv(BENCHMARK_ASSUMPTIONS)


def load_future_evals():
    """Load proposed future-evaluation evidence requirements."""
    return pd.read_csv(FUTURE_EVALS)


def load_second_annotator_benchmark_data():
    """Load the second annotator's assumption and evidence codings."""
    return {
        'assumptions': pd.read_csv(BENCHMARK_ASSUMPTIONS_SECOND),
        'future_evals': pd.read_csv(FUTURE_EVALS_SECOND),
        'future_evals_legacy': pd.read_csv(FUTURE_EVALS_SECOND_LEGACY),
    }
