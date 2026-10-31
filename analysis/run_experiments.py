"""Top-level runner for the four studies and the three manuscript figures.

Examples:
    python analysis/run_experiments.py --study bean
    python analysis/run_experiments.py --study all --plots
"""

import argparse

from study_bean import information_decomposition, model_comparison, report
from study_goh import main as goh_study
from study_hager import run as hager_run
from plotting import make_all_plots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', choices=['bean', 'hager', 'goh', 'comparison', 'all'],
                        default='all')
    parser.add_argument('--plots', action='store_true',
                        help='also write the three manuscript PDFs')
    parser.add_argument('--hager-results', nargs='+',
                        help='Hager JSONL result files to score')
    parser.add_argument('--hager-sample', choices=['pilot', 'main'], default='main')
    args = parser.parse_args()

    if args.study in {'bean', 'all'}:
        report()
        information_decomposition()
    if args.study in {'hager', 'all'}:
        if args.hager_results:
            hager_run(result_paths=args.hager_results, sample=args.hager_sample)
        else:
            hager_run(make_inventory=True)
    if args.study in {'goh', 'all'}:
        goh_study()
    if args.study in {'comparison', 'all'}:
        model_comparison()
    if args.plots:
        make_all_plots()


if __name__ == '__main__':
    main()
