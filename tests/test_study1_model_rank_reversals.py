"""Unit tests for the stored Bean A/B/C rank-reversal calculations."""

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))


def load_module():
    spec = importlib.util.spec_from_file_location(
        'study1_model_rank_reversals_abc',
        ROOT / 'analysis' / 'study1_model_rank_reversals_abc.py',
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_holm_adjustment_preserves_order_and_controls_smallest_p_value():
    module = load_module()
    adjusted = module.holm_adjust([0.01, 0.04, 0.20])
    assert adjusted.tolist() == [0.03, 0.08, 0.20]


def test_reversal_classifier_requires_opposite_signed_intervals():
    module = load_module()
    assert module.classify_reversal(0.2, -0.1, (0.1, 0.3), (-0.2, 0.0)) == 'point_estimate_reversal'
    assert module.classify_reversal(0.2, -0.1, (0.1, 0.3), (-0.3, -0.05)) == 'confirmed_reversal'
    assert module.classify_reversal(0.2, 0.1, (-0.1, 0.3), (-0.1, 0.2)) == 'indeterminate'
