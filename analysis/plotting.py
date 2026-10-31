"""Create the three manuscript figures from the canonical input tables."""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from data import load_benchmark_assumptions, load_future_evals


ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / 'plots'
EVIDENCE = [
    'representative_inputs', 'incomplete_information',
    'sequential_interactions', 'human_behavior',
    'downstream_outcomes_and_task_alignment',
]
EVIDENCE_LABELS = [
    'Representative inputs', 'Incomplete information',
    'Sequential interactions', 'Human behavior',
    'Downstream outcomes / task alignment',
]
COLORS = ['#619CFF', '#5DBB7A', '#E68159', '#F1CF63', '#B78BE0']


def _style():
    plt.rcParams.update({
        'font.family': 'serif', 'font.serif': ['STIXGeneral', 'DejaVu Serif'],
        'font.size': 10, 'axes.edgecolor': '#c3c2b7',
        'xtick.color': '#898781', 'ytick.color': '#898781',
        'figure.facecolor': '#ffffff', 'axes.facecolor': '#ffffff',
        'savefig.facecolor': '#ffffff', 'pdf.fonttype': 42,
    })


def _finish(fig, name):
    PLOTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOTS / f'{name}.pdf', bbox_inches='tight')
    plt.close(fig)


def bean_mechanism_contrasts():
    """Plot Bean condition-identification and disposition contrasts."""
    _style()
    values = ([94.7, 91.1, 64.9, 35.7], [58.7, 46.9, 43.8])
    labels = (['Direct\nevaluation', 'Rewritten\ndisclosed info',
               'GPT-4o\nfinal turn', 'Participant'],
              ['Direct\nevaluation', 'Model on disclosed\ninformation',
               'Participant'])
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.9), sharey=True)
    for ax, series, ticks, title, colors in zip(
            axes, values, labels, ['Conditions', 'Dispositions'],
            [['#477fc9', '#efcbb8', '#b8cde6', '#e14949'],
             ['#477fc9', '#b8cde6', '#e14949']]):
        bars = ax.bar(np.arange(len(series)), series, color=colors,
                      width=0.58, edgecolor='none')
        for bar, value in zip(bars, series):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 2,
                    f'{value:.1f}%', ha='center', fontsize=9,
                    fontweight='bold')
        ax.set_xticks(np.arange(len(series)), ticks)
        ax.set_title(title, loc='left', fontweight='bold', fontsize=11)
        ax.set_ylim(0, 108)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(axis='y', color='#e1e0d9', lw=0.6)
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].set_ylabel('accuracy')
    fig.tight_layout(pad=0.55, w_pad=0.9)
    _finish(fig, 'bean_mechanism_contrasts')


def benchmark_cards_assumption_scores_bars():
    """Plot assumption missingness by benchmark format."""
    _style()
    frame = load_benchmark_assumptions()
    groups = list(frame['benchmark_type'].drop_duplicates())
    scores = np.array([
        [1 - frame.loc[frame['benchmark_type'].eq(group), column].mean()
         for column in EVIDENCE]
        for group in groups
    ])
    fig, ax = plt.subplots(figsize=(8.2, 3.15))
    x = np.arange(len(groups))
    width = 0.14
    for index, (label, color) in enumerate(zip(EVIDENCE_LABELS, COLORS)):
        ax.bar(x + (index - 2) * width, scores[:, index], width * 0.9,
               color=color, label=label, edgecolor='none')
    ax.set_xticks(x, groups)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('mean assumption missingness')
    ax.grid(axis='y', color='#e1e0d9', lw=0.6)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc='upper center',
              bbox_to_anchor=(0.5, 1.26), fontsize=8)
    fig.tight_layout(pad=0.5)
    _finish(fig, 'benchmark_cards_assumption_scores_bars')


def benchmark_cards_format_evidence():
    """Plot future-evaluation evidence requirements by benchmark format."""
    _style()
    frame = load_future_evals()
    groups = list(frame['benchmark_type'].drop_duplicates())
    counts = np.array([
        [frame.loc[frame['benchmark_type'].eq(group), column].mean()
         for column in EVIDENCE]
        for group in groups
    ])
    fig, ax = plt.subplots(figsize=(8.2, 3.15))
    x = np.arange(len(groups))
    width = 0.14
    for index, (label, color) in enumerate(zip(EVIDENCE_LABELS, COLORS)):
        ax.bar(x + (index - 2) * width, counts[:, index], width * 0.9,
               color=color, label=label, edgecolor='none')
    ax.set_xticks(x, groups)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('fraction of benchmarks requiring evidence')
    ax.grid(axis='y', color='#e1e0d9', lw=0.6)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc='upper center',
              bbox_to_anchor=(0.5, 1.26), fontsize=8)
    fig.tight_layout(pad=0.5)
    _finish(fig, 'benchmark_cards_format_evidence')


def make_all_plots():
    """Write only the three requested PDF figures."""
    bean_mechanism_contrasts()
    benchmark_cards_assumption_scores_bars()
    benchmark_cards_format_evidence()


if __name__ == '__main__':
    make_all_plots()
