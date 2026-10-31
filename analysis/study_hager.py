"""Public entry points for Hager's scoring and API workflows."""

from _hager_api import main as run_api
from _hager_scoring import score_results, write_inventory


def run(make_inventory=False, result_paths=None, sample='main'):
    """Build the case inventory or score previously generated JSONL results."""
    if make_inventory:
        return write_inventory()
    if result_paths:
        return score_results(result_paths, sample=sample)
    raise ValueError('choose make_inventory or result_paths')


if __name__ == '__main__':
    run(make_inventory=True)
