"""Figures for the descriptive BenchmarkCards analysis.

The report currently contains the finalized cross-tabs, but the annotation-level
CSV files are not present in the repository. The matrices below therefore mirror
the report exactly; they are presentation inputs, not a second analysis.

E5 (downstream outcomes) and E7 (target-task alignment) are presented as one
category in the revised taxonomy. The source tables indicate disjoint counts at
the displayed benchmark-format level, so the combined counts are their union.
"""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / 'plots'

INK, MUTED, GRID, SURFACE = '#0b0b0b', '#898781', '#e1e0d9', '#ffffff'
EVIDENCE_COLORS = {
    'Representative inputs': '#619CFF',
    'Incomplete information': '#5DBB7A',
    'Sequential interactions': '#E68159',
    'Human behavior': '#F1CF63',
    'Downstream outcomes': '#B78BE0',
}

EVIDENCE = list(EVIDENCE_COLORS)

# Section 5 of experiments/reports/benchmark_cards_analysis.md.
FORMAT_LABELS = [
    'Static QA',
    'Clinical cases',
    'User questions /\nconversations',
    'Simulated care',
    'Workflow tasks',
    'Mixed-source QA',
]
FORMAT_COUNTS = np.array([
    [7, 7, 7, 7, 3],
    [2, 2, 3, 3, 0],
    [0, 0, 1, 2, 1],
    [3, 1, 2, 1, 2],
    [1, 1, 0, 1, 1],
    [0, 1, 1, 1, 0],
])
FORMAT_SIZES = np.array([7, 3, 2, 3, 2, 1])

# Benchmark-level assumption scores supplied for the companion figures:
# yes = 1, partial = 0.5, no = 0 before inversion. The plotted quantity is
# missingness = 1 - mean score, so 1 means the assumption is missing/mismatched
# and 0 means it holds. The rows are ordered by benchmark archetype below so
# that the aggregation remains transparent and reproducible.
ASSUMPTION_SCORE_LABELS = [
    'Representative\ninputs',
    'Incomplete\ninformation',
    'Sequential\ninteractions',
    'Human\nbehavior',
    'Downstream\noutcomes',
]
ASSUMPTION_QUESTION_LABELS = [
    'Example sourcing',
    'Information sufficiency',
    'Interaction structure',
    'Decision mediation',
    'Outcome measurement',
]
ASSUMPTION_SCORE_GROUPS = [
    'Static QA',
    'Clinical cases',
    'User questions /\nconversations',
    'Simulated care',
    'Workflow tasks',
    'Mixed-source QA',
]
ASSUMPTION_SCORE_DATA = [
    ('Static QA', [0.5, 0, 0, 0, 0.5]),
    ('Static QA', [0.5, 0, 0, 0, 0.5]),
    ('Mixed-source QA', [1, 0, 0, 0.5, 0.5]),
    ('Static QA', [0, 0, 0, 0, 0]),
    ('User questions /\nconversations', [1, 1, 0.5, 0.5, 0.5]),
    ('Static QA', [0.5, 0, 0, 0, 0.5]),
    ('Static QA', [0, 0.5, 0.5, 0.5, 0.5]),
    ('User questions /\nconversations', [1, 1, 1, 0, 0]),
    ('Simulated care', [0.5, 1, 1, 1, 0.5]),
    ('Workflow tasks', [1, 1, 1, 1, 1]),
    ('Simulated care', [0, 0.5, 1, 1, 0.5]),
    ('Clinical cases', [0.5, 0, 0, 0, 0.5]),
    ('Clinical cases', [1, 1, 0, 0, 0.5]),
    ('Clinical cases', [0.5, 0, 0, 0, 0.5]),
    ('Static QA', [0.5, 0.5, 0.5, 0, 0]),
    ('Static QA', [0.5, 0.5, 0, 0, 0.5]),
    ('Simulated care', [0.5, 1, 0.5, 0, 0.5]),
    ('Workflow tasks', [0.5, 0.5, 1, 0.5, 0.5]),
]

# Section 3 of the same report: rows are assumption dimensions and columns are
# explicitly coded missing-evidence categories.
ASSUMPTION_LABELS = [
    'Example sourcing',
    'Information sufficiency',
    'Interaction structure',
    'Actor / decision-maker',
    'Outcome measure',
]
ASSUMPTION_COUNTS = np.array([
    [12, 0, 0, 0, 0],
    [3, 12, 0, 0, 0],
    [2, 0, 13, 0, 0],
    [0, 0, 0, 15, 1],
    [0, 0, 1, 13, 8],
])

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 10,
    'text.color': INK,
    'axes.edgecolor': '#c3c2b7',
    'axes.labelcolor': INK,
    'axes.labelsize': 10,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'figure.facecolor': SURFACE,
    'axes.facecolor': SURFACE,
    'savefig.facecolor': SURFACE,
    'axes.linewidth': 0.7,
    'pdf.fonttype': 42,
})


def strip_axes(ax, keep=('left', 'bottom')):
    """Hide the unnecessary spines and keep the figure visually light."""
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)
    ax.tick_params(length=3, width=0.6)


def save(fig, name):
    """Save a figure in both publication and quick-preview formats."""
    PLOTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOTS / f'{name}.pdf', bbox_inches='tight')
    fig.savefig(PLOTS / f'{name}.png', dpi=220, bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote plots/{name}.pdf and plots/{name}.png')


def make_format_bars():
    """Grouped bars for benchmark format by required evidence type."""
    fig, ax = plt.subplots(figsize=(8.2, 3.15))
    x = np.arange(len(FORMAT_LABELS))
    width = 0.12
    offsets = (np.arange(len(EVIDENCE)) - 2) * width
    fractions = FORMAT_COUNTS / FORMAT_SIZES[:, None]
    for evidence, offset, column in zip(EVIDENCE, offsets, fractions.T):
        ax.bar(x + offset, column, width=width * 0.9,
               color=EVIDENCE_COLORS[evidence], label=evidence,
               edgecolor='none')

    ax.set_xticks(x)
    ax.set_xticklabels(FORMAT_LABELS)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel('fraction of benchmarks requiring evidence')
    ax.grid(axis='y', color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    strip_axes(ax)
    ax.legend(frameon=False, ncol=3, loc='upper center',
              bbox_to_anchor=(0.5, 1.26), handlelength=0.9,
              columnspacing=1.7, handletextpad=0.45)
    fig.tight_layout(pad=0.5)
    save(fig, 'benchmark_cards_format_evidence')


def make_assumption_heatmap():
    """Heatmap of assumption dimensions by explicitly coded evidence needs."""
    fig, ax = plt.subplots(figsize=(6.8, 3.15))
    cmap = plt.get_cmap('YlOrBr')
    image = ax.imshow(ASSUMPTION_COUNTS, cmap=cmap, vmin=0, vmax=15,
                      aspect='auto')
    ax.set_xticks(np.arange(len(EVIDENCE)))
    ax.set_xticklabels(EVIDENCE, rotation=25, ha='right')
    ax.set_yticks(np.arange(len(ASSUMPTION_LABELS)))
    ax.set_yticklabels(ASSUMPTION_LABELS)
    for i in range(ASSUMPTION_COUNTS.shape[0]):
        for j in range(ASSUMPTION_COUNTS.shape[1]):
            value = ASSUMPTION_COUNTS[i, j]
            ax.text(j, i, str(value), ha='center', va='center',
                    color='white' if value >= 8 else INK, fontsize=9)

    ax.set_xlabel('missing evidence category')
    ax.set_xticks(np.arange(len(EVIDENCE)), minor=True)
    ax.grid(which='minor', color=SURFACE, lw=1.5)
    ax.tick_params(which='minor', bottom=False, left=False)
    strip_axes(ax, keep=())
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
    colorbar.set_label('assessment-level assignments', fontsize=8.5)
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(labelsize=8)
    fig.tight_layout(pad=0.5)
    save(fig, 'benchmark_cards_assumption_evidence_heatmap')


def make_assumption_score_heatmap():
    """Heatmap of mean deployment-match scores by benchmark archetype."""
    scores = np.array([row[1] for row in ASSUMPTION_SCORE_DATA])
    groups = [row[0] for row in ASSUMPTION_SCORE_DATA]
    means = np.array([
        scores[[group == label for group in groups]].mean(axis=0)
        for label in ASSUMPTION_SCORE_GROUPS
    ])
    means = 1 - means

    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    image = ax.imshow(means, cmap='YlGnBu', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(np.arange(len(ASSUMPTION_SCORE_LABELS)))
    ax.set_xticklabels(ASSUMPTION_SCORE_LABELS)
    ax.set_yticks(np.arange(len(ASSUMPTION_SCORE_GROUPS)))
    ax.set_yticklabels(ASSUMPTION_SCORE_GROUPS)
    for i in range(means.shape[0]):
        for j in range(means.shape[1]):
            value = means[i, j]
            ax.text(j, i, f'{value:.2f}', ha='center', va='center',
                    color='white' if value >= 0.65 else INK, fontsize=8.5)

    ax.set_xlabel('BenchmarkCard assumption')
    ax.set_xticks(np.arange(len(ASSUMPTION_SCORE_LABELS)), minor=True)
    ax.set_yticks(np.arange(len(ASSUMPTION_SCORE_GROUPS)), minor=True)
    ax.grid(which='minor', color=SURFACE, lw=1.5)
    ax.tick_params(which='minor', bottom=False, left=False)
    strip_axes(ax, keep=())
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
    colorbar.set_label('mean assumption missingness', fontsize=8.5)
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(labelsize=8)
    fig.tight_layout(pad=0.5)
    save(fig, 'benchmark_cards_assumption_scores')


def make_assumption_score_bars():
    """Grouped bars of mean assumption scores by benchmark archetype."""
    scores = np.array([row[1] for row in ASSUMPTION_SCORE_DATA])
    groups = [row[0] for row in ASSUMPTION_SCORE_DATA]
    means = np.array([
        scores[[group == label for group in groups]].mean(axis=0)
        for label in ASSUMPTION_SCORE_GROUPS
    ])
    means = 1 - means

    fig, ax = plt.subplots(figsize=(8.2, 3.15))
    x = np.arange(len(ASSUMPTION_SCORE_GROUPS))
    width = 0.14
    offsets = (np.arange(len(ASSUMPTION_QUESTION_LABELS)) - 2) * width
    colors = list(EVIDENCE_COLORS.values())
    for label, offset, row, color in zip(
            ASSUMPTION_QUESTION_LABELS, offsets, means.T, colors):
        ax.bar(x + offset, row, width=width * 0.9, color=color,
               label=label.replace('\n', ' '), edgecolor='none')

    ax.set_xticks(x)
    ax.set_xticklabels(ASSUMPTION_SCORE_GROUPS)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel('mean assumption missingness')
    ax.grid(axis='y', color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    strip_axes(ax)
    ax.legend(frameon=False, ncol=3, loc='upper center',
              bbox_to_anchor=(0.5, 1.26), handlelength=0.9,
              columnspacing=1.7, handletextpad=0.45)
    fig.tight_layout(pad=0.5)
    save(fig, 'benchmark_cards_assumption_scores_bars')


if __name__ == '__main__':
    make_format_bars()
    make_assumption_heatmap()
    make_assumption_score_heatmap()
    make_assumption_score_bars()
