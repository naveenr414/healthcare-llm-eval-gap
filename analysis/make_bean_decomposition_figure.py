"""Plot the Bean et al. condition-identification decomposition.

The primary path is the descriptive comparison used in the manuscript:
direct evaluation, GPT-4o's stored final conversation turn, and the
participant's final answer. The canonicalized disclosed-information result is
shown separately because it is a diagnostic comparison, not an additive stage
in the main decomposition.
"""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / 'plots'

INK = '#0b0b0b'
MUTED = '#898781'
GRID = '#e1e0d9'
SURFACE = '#ffffff'
BLUE = '#477fc9'
LIGHT_BLUE = '#b8cde6'
RED = '#e14949'
PEACH = '#efcbb8'

EVALUATION = 94.7
FINAL_MODEL_TURN = 64.9
PARTICIPANT = 35.7
CANONICALIZED_DISCLOSED = 91.1

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
    """Hide unnecessary spines and retain the light paper-style axes."""
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)
    ax.tick_params(length=3, width=0.6)


def save(fig):
    """Save the figure in the formats used for drafting and preview."""
    PLOTS.mkdir(parents=True, exist_ok=True)
    for suffix, kwargs in (('.pdf', {}), ('.png', {'dpi': 220})):
        fig.savefig(PLOTS / f'bean_condition_decomposition{suffix}',
                    bbox_inches='tight', **kwargs)
    plt.close(fig)
    print('  wrote plots/bean_condition_decomposition.pdf and .png')


def make_figure():
    """Draw the condition-identification performance path and gap shares."""
    task_gap = EVALUATION - FINAL_MODEL_TURN
    outcome_gap = FINAL_MODEL_TURN - PARTICIPANT
    total_gap = EVALUATION - PARTICIPANT

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(6.9, 2.85),
                                   gridspec_kw={'width_ratios': [1.05, 1]})

    # Panel A: the observable performance path, with the diagnostic condition
    # offset slightly so it is not mistaken for a fourth stage in the path.
    x = np.arange(3)
    values = [EVALUATION, FINAL_MODEL_TURN, PARTICIPANT]
    colors = [BLUE, LIGHT_BLUE, RED]
    bars = ax.bar(x, values, width=0.56, color=colors, edgecolor='none')
    ax.bar(3.05, CANONICALIZED_DISCLOSED, width=0.30, color=PEACH,
           edgecolor='none', alpha=0.95)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2.0,
                f'{value:.1f}%', ha='center', va='bottom',
                fontsize=9, fontweight='bold', color=INK)
    ax.text(3.05, CANONICALIZED_DISCLOSED + 2.0, f'{CANONICALIZED_DISCLOSED:.1f}%',
            ha='center', va='bottom', fontsize=8.5, color=INK)
    ax.set_xticks([0, 1, 2, 3.05])
    ax.set_xticklabels(['Evaluation', 'GPT-4o\nfinal turn', 'Participant',
                        'Rewritten\ndisclosed info'])
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel('condition-identification accuracy')
    ax.grid(axis='y', color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    strip_axes(ax)
    ax.axvline(2.52, color=GRID, lw=0.8, ls=(0, (2, 2)))
    ax.text(3.05, 1.5, 'diagnostic\ncomparison', ha='center', va='bottom',
            fontsize=7.5, color=MUTED)

    # Panel B: the total gap is partitioned into the two sequential contrasts.
    base = PARTICIPANT
    ax2.bar(0, PARTICIPANT, width=0.60, color=RED, edgecolor='none',
            label='participant baseline')
    ax2.bar(0, outcome_gap, bottom=base, width=0.60, color=PEACH,
            edgecolor='none', label='human-mediated outcome gap')
    ax2.bar(0, task_gap, bottom=base + outcome_gap, width=0.60,
            color=LIGHT_BLUE, edgecolor='none', label='task / interaction gap')
    ax2.text(0, PARTICIPANT / 2, f'{PARTICIPANT:.1f}%', ha='center', va='center',
             fontsize=8.5, color='white', fontweight='bold')
    ax2.text(0, base + outcome_gap / 2, f'{outcome_gap:.1f} pp',
             ha='center', va='center', fontsize=8.5, color='#7c4a37',
             fontweight='bold')
    ax2.text(0, base + outcome_gap + task_gap / 2, f'{task_gap:.1f} pp',
             ha='center', va='center', fontsize=8.5, color='#385778',
             fontweight='bold')
    ax2.text(0, EVALUATION + 2.0, f'{EVALUATION:.1f}%', ha='center',
             va='bottom', fontsize=9, fontweight='bold')
    ax2.text(0.42, base + outcome_gap + task_gap / 2,
             f'{task_gap / total_gap:.1%} of total gap', ha='left', va='center',
             fontsize=8, color='#385778')
    ax2.set_xlim(-0.8, 1.2)
    ax2.set_ylim(0, 108)
    ax2.set_xticks([0])
    ax2.set_xticklabels(['Evaluation-to-\nparticipant gap'])
    ax2.set_yticks([0, 25, 50, 75, 100])
    ax2.set_ylabel('accuracy')
    ax2.grid(axis='y', color=GRID, lw=0.6)
    ax2.set_axisbelow(True)
    strip_axes(ax2)
    ax2.legend(frameon=False, fontsize=7.2, loc='lower right',
               bbox_to_anchor=(1.0, 0.03), handlelength=0.9,
               handletextpad=0.35, labelspacing=0.25)

    fig.tight_layout(pad=0.55, w_pad=1.0)
    save(fig)


if __name__ == '__main__':
    make_figure()
